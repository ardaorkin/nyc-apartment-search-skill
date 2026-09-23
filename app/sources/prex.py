"""PREX Realty's building pages (prexrealty.com/properties/<slug>/) are marketing copy
for whole buildings with an "Inquire Now" contact form -- no price, bedroom count, or
availability for individual units. The dedicated "Current Availabilities" page (the
one place per-unit pricing would live) renders with no server-side data or embedded
JSON in its initial HTML and no discoverable public API backing it -- it's client-
rendered with nothing crawlable in the static page. Recorded as
BLOCKED_OR_MANUAL_REVIEW_REQUIRED rather than built as a real adapter; playwright
was deliberately not reached for here since the goal was confirming whether static/
structured content exists at all, and it doesn't."""
from __future__ import annotations

from sources.base import BaseAdapter


class PrexAdapter(BaseAdapter):
    name = "prex"
    base_url = "https://prexrealty.com"

    def fetch(self):
        return self.blocked_result(
            "building pages (properties/<slug>/) are building-level marketing copy with "
            "an inquiry contact form, no per-unit price/bedroom/availability data; the "
            "Current Availabilities page (where that would live) is client-rendered with "
            "no server-rendered data or public API discovered in its static HTML"
        )
