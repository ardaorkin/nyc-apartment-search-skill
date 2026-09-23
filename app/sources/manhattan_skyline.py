"""Manhattan Skyline's site is a client-rendered SPA with no server-rendered listing
HTML or JSON-LD, but its own JS calls a public, unauthenticated JSON API
(manhattanskyline.com/api/units, /api/buildings) to populate the page -- the same
data the browser would fetch, just requested directly instead of executing the SPA's
JS. This is a public GET endpoint with no auth, exactly the kind of "prefer an API
over HTML scraping" case the adapter contract calls for."""
from __future__ import annotations

import logging

from models import Listing, SourceResult, SourceStatus
from parsers.address import normalize_address
from parsers.pets import classify_pet_policy
from parsers.rent import parse_rent
from sources.base import BaseAdapter, BlockedError

logger = logging.getLogger("nyc_apartment_search")


class ManhattanSkylineAdapter(BaseAdapter):
    name = "manhattan_skyline"
    base_url = "https://manhattanskyline.com"
    units_api = "https://manhattanskyline.com/api/units"
    buildings_api = "https://manhattanskyline.com/api/buildings"

    def _get_json(self, url: str):
        import json

        text = self.get(url)
        return json.loads(text)

    def fetch(self) -> SourceResult:
        try:
            buildings_payload = self._get_json(self.buildings_api)
        except BlockedError as exc:
            return self.blocked_result(str(exc))
        except Exception as exc:  # noqa: BLE001
            return self.error_result(f"failed to parse /api/buildings response: {exc}")

        buildings_by_id = {b["id"]: b for b in buildings_payload.get("buildings", []) if "id" in b}

        try:
            units_payload = self._get_json(self.units_api)
        except BlockedError as exc:
            return self.blocked_result(str(exc))
        except Exception as exc:  # noqa: BLE001
            return self.error_result(f"failed to parse /api/units response: {exc}")

        units = units_payload.get("units", {}).get("data", [])
        if not units:
            return SourceResult(
                name=self.name,
                status=SourceStatus.OK,
                listings=[],
                note="/api/units reachable but returned no unit data",
            )

        listings: list[Listing] = []
        errors = 0
        for unit in units:
            try:
                listing = self._listing_from_unit(unit, buildings_by_id)
                if listing:
                    listings.append(listing)
            except Exception as exc:  # noqa: BLE001
                errors += 1
                logger.warning("%s: parse failure on unit %s: %s", self.name, unit.get("slug"), exc)
                continue

        status = SourceStatus.OK if errors == 0 else SourceStatus.PARTIAL
        note = None if errors == 0 else f"{errors} of {len(units)} units failed to parse"
        return SourceResult(name=self.name, status=status, listings=listings, note=note)

    def _listing_from_unit(self, unit: dict, buildings_by_id: dict) -> Listing | None:
        building = unit.get("building") or {}
        building_id = building.get("id") if isinstance(building, dict) else None
        building_full = buildings_by_id.get(building_id, building if isinstance(building, dict) else {})

        address_block = building_full.get("address") or {}
        address = (address_block.get("display_name") if isinstance(address_block, dict) else address_block) or building_full.get("name")
        lat_lng = address_block.get("latLng") if isinstance(address_block, dict) else None
        latitude = lat_lng.get("lat") if isinstance(lat_lng, dict) else None
        longitude = lat_lng.get("lng") if isinstance(lat_lng, dict) else None
        neighborhood_block = building_full.get("neighborhood") or {}
        neighborhood = neighborhood_block.get("name") if isinstance(neighborhood_block, dict) else neighborhood_block
        rent = parse_rent(unit.get("price"))
        description = unit.get("body")
        pet_status, cat_allowed, dog_allowed = classify_pet_policy(description)
        combined_text = f"{description or ''} {building_full.get('body') or ''}"
        doorman = "doorman" in combined_text.lower() or None

        if not address and not rent:
            return None

        url = unit.get("url") or f"{self.base_url}/rentals/{building_full.get('slug', '')}/{unit.get('slug', '')}"

        return Listing(
            source=self.name,
            listing_url=url,
            source_urls=[url],
            address=normalize_address(address),
            unit=unit.get("number"),
            neighborhood=neighborhood,
            latitude=latitude,
            longitude=longitude,
            bedrooms=float(unit["bedrooms"]) if unit.get("bedrooms") is not None else None,
            bathrooms=float(unit["bathrooms"]) if unit.get("bathrooms") is not None else None,
            square_feet=float(unit["square_footage"]) if unit.get("square_footage") else None,
            available_date=unit.get("available_on"),
            monthly_rent=rent,
            description=description,
            doorman=doorman,
            pet_policy=description,
            pet_status=pet_status,
            cat_allowed=cat_allowed,
            dog_allowed=dog_allowed,
            brokerage_or_management_company="Manhattan Skyline",
        )
