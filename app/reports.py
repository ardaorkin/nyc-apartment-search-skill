"""Report generation: listings.csv, listings.json, shortlist.md, changes.md."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from models import ActiveStatus, GeoStatus, Listing, PetStatus, RiskLevel


def _listing_to_flat_dict(listing: Listing) -> dict[str, Any]:
    d = listing.model_dump(mode="json")
    d["source_urls"] = "; ".join(listing.source_urls)
    d["observed_prices"] = "; ".join(f"${p.value:.0f}@{p.source}" for p in listing.observed_prices)
    d["risk_notes"] = "; ".join(listing.risk_notes)
    d["application_flags"] = "; ".join(listing.application_flags)
    d["score_reasons"] = "; ".join(listing.score_reasons)
    d["confidence_notes"] = "; ".join(listing.confidence_notes)
    return d


def write_csv_json(listings: list[Listing], reports_dir: Path) -> None:
    reports_dir.mkdir(parents=True, exist_ok=True)
    rows = [_listing_to_flat_dict(l) for l in listings]
    df = pd.DataFrame(rows)
    if "monthly_rent" in df.columns:
        df = df.sort_values("monthly_rent", na_position="last")
    df.to_csv(reports_dir / "listings.csv", index=False)

    full = [json.loads(l.model_dump_json()) for l in listings]
    (reports_dir / "listings.json").write_text(json.dumps(full, indent=2, default=str), encoding="utf-8")


def _listing_block(listing: Listing) -> str:
    lines = [f"## {listing.address or 'Unknown address'}{f' Unit {listing.unit}' if listing.unit else ''} -- "
             f"{'$%.0f/month' % listing.monthly_rent if listing.monthly_rent else 'rent unknown'}"]
    lines.append(f"- Bedrooms / bathrooms: {listing.bedrooms if listing.bedrooms is not None else 'unknown'} / {listing.bathrooms if listing.bathrooms is not None else 'unknown'}")
    lines.append(f"- Active status: {listing.active_status}")
    lines.append(f"- Pet policy: {listing.pet_status} ({listing.pet_policy or 'no policy text captured'})")
    lines.append(f"- Laundry: {listing.laundry or ('in-unit' if listing.in_unit_washer_dryer else 'unknown')}")
    lines.append(f"- Dishwasher: {listing.dishwasher}")
    lines.append(f"- Elevator / floor: {listing.elevator} / {listing.floor or 'unknown'}")
    lines.append(f"- Broker fee: {listing.broker_fee_status or 'unknown'}")
    lines.append(f"- Other mandatory fees: {listing.amenity_fees or 'none captured'}")
    lines.append(f"- Availability: {listing.available_date or 'unknown'}")
    if listing.score_reasons:
        lines.append(f"- Why it's a good fit: {', '.join(listing.score_reasons)}")
    concerns = list(listing.confidence_notes) + list(listing.risk_notes)
    lines.append(f"- Concerns / missing info: {'; '.join(concerns) if concerns else 'none noted'}")
    lines.append(f"- Direct link(s): {', '.join(listing.source_urls) if listing.source_urls else 'n/a'}")
    return "\n".join(lines)


def write_shortlist(
    listings: list[Listing],
    rejected: list[tuple[Listing, str]],
    blocked_sources: list[tuple[str, str]],
    reports_dir: Path,
) -> None:
    reports_dir.mkdir(parents=True, exist_ok=True)
    active = [l for l in listings if l.active_status in (ActiveStatus.ACTIVE, ActiveStatus.LIKELY_ACTIVE)]
    active.sort(key=lambda l: l.score or 0, reverse=True)

    stale = [l for l in listings if l.active_status in (ActiveStatus.STALE, ActiveStatus.OFF_MARKET)]

    follow_up = [
        l for l in listings
        if l.geo_status == GeoStatus.GEOGRAPHY_NEEDS_CONFIRMATION
        or l.pet_status == PetStatus.PET_POLICY_NEEDS_CONFIRMATION
        or "APPLICATION_REQUIREMENTS_NEED_CONFIRMATION" in l.application_flags
        or l.risk_level in (RiskLevel.REVIEW, RiskLevel.HIGH_RISK)
    ]

    parts = ["# Best Current Matches\n"]
    if active:
        parts.extend(_listing_block(l) + "\n" for l in active[:10])
    else:
        parts.append("_No active or likely-active listings matched the configured filters this run._\n")

    parts.append("\n# Listings Requiring Follow-Up\n")
    if follow_up:
        parts.extend(_listing_block(l) + "\n" for l in follow_up)
    else:
        parts.append("_None._\n")

    parts.append("\n# Stale / Off-Market Listings\n")
    if stale:
        parts.extend(f"- {l.address or 'Unknown'} -- {l.active_status} ({', '.join(l.source_urls)})\n" for l in stale)
    else:
        parts.append("_None._\n")

    parts.append("\n# Rejected Listings\n")
    if rejected:
        parts.extend(f"- {l.address or 'Unknown'}: {reason}\n" for l, reason in rejected)
    else:
        parts.append("_None._\n")

    parts.append("\n# Sources That Could Not Be Automatically Accessed\n")
    if blocked_sources:
        parts.extend(f"- **{name}**: {reason}\n" for name, reason in blocked_sources)
    else:
        parts.append("_None -- every configured source was reachable._\n")

    (reports_dir / "shortlist.md").write_text("\n".join(parts), encoding="utf-8")


def _snapshot_key(listing: Listing) -> str:
    return f"{listing.address}|{listing.unit or ''}|{listing.source}"


def write_changes(current: list[Listing], previous: list[dict] | None, reports_dir: Path) -> None:
    reports_dir.mkdir(parents=True, exist_ok=True)
    if not previous:
        (reports_dir / "changes.md").write_text(
            "# Changes\n\n_No previous snapshot to diff against -- this is the first run._\n",
            encoding="utf-8",
        )
        return

    prev_by_key = {f"{p.get('address')}|{p.get('unit') or ''}|{p.get('source')}": p for p in previous}
    cur_by_key = {_snapshot_key(l): l for l in current}

    lines = ["# Changes\n"]
    for key, listing in cur_by_key.items():
        if key not in prev_by_key:
            lines.append(f"- **NEW**: {listing.address} -- ${listing.monthly_rent}/mo\n")
            continue
        prev = prev_by_key[key]
        if listing.monthly_rent is not None and prev.get("monthly_rent") is not None:
            if listing.monthly_rent < prev["monthly_rent"]:
                lines.append(f"- **PRICE_DROP**: {listing.address} -- ${prev['monthly_rent']} -> ${listing.monthly_rent}\n")
            elif listing.monthly_rent > prev["monthly_rent"]:
                lines.append(f"- **PRICE_INCREASE**: {listing.address} -- ${prev['monthly_rent']} -> ${listing.monthly_rent}\n")
        if listing.active_status == "OFF_MARKET" and prev.get("active_status") != "OFF_MARKET":
            lines.append(f"- **REMOVED**: {listing.address}\n")
        if prev.get("active_status") in ("STALE", "OFF_MARKET") and listing.active_status in ("ACTIVE", "LIKELY_ACTIVE"):
            lines.append(f"- **BACK_ON_MARKET**: {listing.address}\n")
        for field in ("pet_status", "broker_fee_status", "available_date"):
            cur_val = getattr(listing, field)
            prev_val = prev.get(field)
            if cur_val != prev_val and (cur_val or prev_val):
                lines.append(f"- **DETAIL_CHANGED** ({field}): {listing.address} -- {prev_val} -> {cur_val}\n")

    for key, prev in prev_by_key.items():
        if key not in cur_by_key:
            lines.append(f"- **REMOVED** (no longer seen): {prev.get('address')}\n")

    if len(lines) == 1:
        lines.append("_No changes detected since the previous run._\n")

    (reports_dir / "changes.md").write_text("\n".join(lines), encoding="utf-8")


def save_snapshot(listings: list[Listing], data_dir: Path, keep_snapshots: int = 30) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    snapshot_path = data_dir / f"snapshot-{today}.json"
    payload = [json.loads(l.model_dump_json()) for l in listings]
    snapshot_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    snapshots = sorted(data_dir.glob("snapshot-*.json"))
    for old in snapshots[:-keep_snapshots]:
        old.unlink(missing_ok=True)


def load_previous_snapshot(data_dir: Path) -> list[dict] | None:
    snapshots = sorted(data_dir.glob("snapshot-*.json"))
    if not snapshots:
        return None
    latest = snapshots[-1]
    try:
        return json.loads(latest.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
