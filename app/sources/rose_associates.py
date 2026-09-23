"""Rose Associates' public site (roseassociates.com) is a corporate portfolio/services
site -- About, Services, Project Portfolio, Contact, a Report page -- with no rental
search, no listing pages, and no unit inventory anywhere in its nav or sitemap.
Investigated directly (not via sitemap pattern-matching): the sitemap only yields
blog/service/portfolio pages, confirming there's nothing to crawl here. Recorded as
BLOCKED_OR_MANUAL_REVIEW_REQUIRED rather than built as a real adapter."""
from __future__ import annotations

from sources.base import BaseAdapter


class RoseAssociatesAdapter(BaseAdapter):
    name = "rose_associates"
    base_url = "https://roseassociates.com"

    def fetch(self):
        return self.blocked_result(
            "roseassociates.com is a corporate portfolio/services site (about, services, "
            "project-portfolio, contact) -- no rental search, listing pages, or unit "
            "inventory found in its navigation or sitemap"
        )
