#!/usr/bin/env python3
"""CLI entry point for nyc-apartment-search. Usage: python search.py [--sources a,b]
[--no-cache] [--max-rent N] [--dry-run]"""
from __future__ import annotations

import argparse
import logging
import statistics
from datetime import datetime, timezone
from pathlib import Path

import yaml
from rich.console import Console
from rich.table import Table

from models import ActiveStatus, Listing, RiskLevel, SourceStatus
from parsers.address import classify_geo, extract_street_number
from parsers.dedupe import deduplicate
from parsers.freshness import classify_freshness
from parsers.pets import household_pet_accepted
from parsers.preferences import required_preference_rejections
from parsers.risk import application_flags, assess_risk
from parsers.scoring import score_listing
from reports import load_previous_snapshot, save_snapshot, write_changes, write_csv_json, write_shortlist
from sources.blocked import blocked_results
from sources.brown_harris_stevens import BrownHarrisStevensAdapter
from sources.compass import CompassAdapter
from sources.corcoran import CorcoranAdapter
from sources.douglas_elliman import DouglasEllimanAdapter
from sources.equity_residential import EquityResidentialAdapter
from sources.glenwood import GlenwoodAdapter
from sources.manhattan_skyline import ManhattanSkylineAdapter
from sources.prex import PrexAdapter
from sources.related_rentals import RelatedRentalsAdapter
from sources.rose_associates import RoseAssociatesAdapter

ROOT = Path(__file__).resolve().parent
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("nyc_apartment_search")
console = Console()

ADAPTERS = [
    CompassAdapter,
    CorcoranAdapter,
    DouglasEllimanAdapter,
    BrownHarrisStevensAdapter,
    GlenwoodAdapter,
    RoseAssociatesAdapter,
    EquityResidentialAdapter,
    ManhattanSkylineAdapter,
    RelatedRentalsAdapter,
    PrexAdapter,
]


def load_config() -> dict:
    config_path = ROOT / "config.yaml"
    with config_path.open() as f:
        return yaml.safe_load(f)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="NYC apartment search")
    parser.add_argument("--sources", type=str, default=None, help="Comma-separated adapter names to run (default: all)")
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--max-rent", type=float, default=None)
    parser.add_argument("--dry-run", action="store_true", help="Run adapters but skip writing reports/snapshots")
    return parser.parse_args()


def run_adapters(config: dict, use_cache: bool, only: list[str] | None) -> tuple[list[Listing], list[tuple[str, str]], int]:
    listings: list[Listing] = []
    blocked: list[tuple[str, str]] = []
    raw_count = 0

    active_adapters = [a for a in ADAPTERS if not only or a.name in only]  # type: ignore[attr-defined]
    for adapter_cls in active_adapters:
        adapter = adapter_cls(config, use_cache=use_cache)
        console.print(f"[bold]Fetching[/bold] {adapter.name} ...")
        try:
            result = adapter.fetch()
        except Exception as exc:  # noqa: BLE001 -- one failing source never aborts the run
            logger.error("%s: adapter raised unexpectedly: %s", adapter.name, exc)
            blocked.append((adapter.name, f"unexpected error: {exc}"))
            continue

        raw_count += len(result.listings)
        if result.status == SourceStatus.BLOCKED_OR_MANUAL_REVIEW_REQUIRED:
            blocked.append((result.name, result.note or "blocked"))
        elif result.status == SourceStatus.ERROR:
            blocked.append((result.name, result.note or "error"))
        else:
            listings.extend(result.listings)
            if result.note:
                console.print(f"  [yellow]partial:[/yellow] {result.note}")

    for result in blocked_results():
        if only and result.name not in only:
            continue
        blocked.append((result.name, result.note or ""))

    return listings, blocked, raw_count


def apply_filters(listings: list[Listing], config: dict) -> tuple[list[Listing], list[tuple[Listing, str]]]:
    location = config.get("location", {})
    household = config.get("household", {})
    preferences = config.get("preferences", {})
    has_dog = bool(household.get("dogs"))
    has_cat = bool(household.get("cats"))

    kept: list[Listing] = []
    rejected: list[tuple[Listing, str]] = []

    for listing in listings:
        cross_street_number = extract_street_number(listing.address)
        # No adapter threads a real per-listing borough through today -- guessing
        # "Manhattan" here (as this used to) is wrong for any other borough and
        # silently rejects every real listing as OUT_OF_RANGE. None is honest: when
        # a borough filter is configured, classify_geo already flags unknown-borough
        # listings as GEOGRAPHY_NEEDS_CONFIRMATION instead of rejecting them.
        listing.geo_status = classify_geo(
            listing_borough=None,
            listing_neighborhood=listing.neighborhood,
            cross_street_number=cross_street_number,
            location_config=location,
        )
        if listing.geo_status == "OUT_OF_RANGE":
            rejected.append((listing, "outside configured area"))
            continue

        if has_dog or has_cat:
            accepted = household_pet_accepted(listing.pet_status, listing.dog_allowed, has_dog, has_cat)
            if not accepted:
                rejected.append((listing, f"pet policy excludes household pet(s): {listing.pet_policy or listing.pet_status}"))
                continue

        preference_rejections = required_preference_rejections(listing, preferences)
        if preference_rejections:
            rejected.append((listing, "; ".join(preference_rejections)))
            continue

        kept.append(listing)

    return kept, rejected


def enrich(listings: list[Listing], config: dict) -> None:
    rents = [l.monthly_rent for l in listings if l.monthly_rent is not None]
    median_rent = statistics.median(rents) if rents else None

    for listing in listings:
        listing.active_status = classify_freshness(listing)
        listing.risk_level, listing.risk_notes = assess_risk(listing, median_rent)
        listing.application_flags = application_flags(listing)
        if listing.active_status in (ActiveStatus.ACTIVE, ActiveStatus.LIKELY_ACTIVE):
            listing.score, listing.score_reasons = score_listing(listing, config, rents)
        if listing.pet_status == "PET_POLICY_NEEDS_CONFIRMATION":
            listing.confidence_notes.append("Pet policy not stated by source -- confirm before applying")
        if listing.geo_status == "GEOGRAPHY_NEEDS_CONFIRMATION":
            listing.confidence_notes.append("Could not confirm this falls within the configured area")


def print_summary(sources_run: int, raw_count: int, after_geo: int, after_pets: int, after_dedupe: int, active_count: int, ranked: list[Listing], blocked: list[tuple[str, str]]) -> None:
    console.rule("Run summary")
    console.print(f"Sources searched: {sources_run}")
    console.print(f"Raw listings found: {raw_count}")
    console.print(f"After geographic filtering: {after_geo}")
    console.print(f"After pet filtering: {after_pets}")
    console.print(f"After dedupe: {after_dedupe}")
    console.print(f"Active / likely-active: {active_count}")

    if blocked:
        console.print("\n[bold red]Blocked / manual-review sources:[/bold red]")
        for name, note in blocked:
            console.print(f"  - {name}: {note}")

    table = Table(title="Top 10 ranked listings")
    table.add_column("Score")
    table.add_column("Address")
    table.add_column("Rent")
    table.add_column("Beds")
    table.add_column("Source")
    for listing in ranked[:10]:
        table.add_row(
            str(listing.score or ""),
            listing.address or "unknown",
            f"${listing.monthly_rent:.0f}" if listing.monthly_rent else "?",
            str(listing.bedrooms) if listing.bedrooms is not None else "?",
            listing.source,
        )
    console.print(table)


def main() -> None:
    args = parse_args()
    config = load_config()
    if args.max_rent is not None:
        config.setdefault("apartment", {})["max_rent"] = args.max_rent

    only = args.sources.split(",") if args.sources else None
    use_cache = config.get("search", {}).get("use_cache", True) and not args.no_cache

    raw_listings, blocked, raw_count = run_adapters(config, use_cache, only)
    now = datetime.now(timezone.utc)
    for listing in raw_listings:
        listing.checked_at = listing.checked_at or now
        listing.first_seen = listing.first_seen or now.date()
        listing.last_seen = now.date()

    after_geo, rejected = apply_filters(raw_listings, config)
    after_pets = len(after_geo)  # pet/preference filtering happens inside apply_filters
    deduped = deduplicate(after_geo)
    enrich(deduped, config)

    ranked = sorted(
        [l for l in deduped if l.active_status in (ActiveStatus.ACTIVE, ActiveStatus.LIKELY_ACTIVE)],
        key=lambda l: l.score or 0,
        reverse=True,
    )

    print_summary(
        sources_run=len(ADAPTERS) + len(blocked_results()),
        raw_count=raw_count,
        after_geo=len(after_geo) + len(rejected),
        after_pets=after_pets,
        after_dedupe=len(deduped),
        active_count=len(ranked),
        ranked=ranked,
        blocked=blocked,
    )

    if args.dry_run:
        console.print("\n[yellow]--dry-run set: skipping report/snapshot writes[/yellow]")
        return

    reports_dir = ROOT / config.get("output", {}).get("reports_dir", "reports")
    data_dir = ROOT / "data"

    previous_snapshot = load_previous_snapshot(data_dir)
    write_csv_json(deduped, reports_dir)
    write_shortlist(deduped, rejected, blocked, reports_dir)
    write_changes(deduped, previous_snapshot, reports_dir)
    save_snapshot(deduped, data_dir, config.get("output", {}).get("keep_snapshots", 30))

    console.print(f"\n[green]Reports written to {reports_dir}[/green]")


if __name__ == "__main__":
    main()
