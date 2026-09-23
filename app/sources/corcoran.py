from sources.sitemap_adapter import SitemapAdapter


class CorcoranAdapter(SitemapAdapter):
    name = "corcoran"
    base_url = "https://www.corcoran.com"
    # Old /sitemap.xml now 404s -- Corcoran restructured their sitemaps at some
    # point after this was first verified (2026-09-22). Found the current location
    # via their own robots.txt, which still lists dozens of per-region sitemaps;
    # this one is NYC rentals specifically (already for-rent-only, verified live
    # with today's lastmod timestamps), so no broader sitemap-index crawl is needed.
    sitemap_urls = ["https://www.corcoran.com/sitemap/nyc/homes-for-rent-listings/exclusives/exclusive-listings-nyc.xml"]
    require_area_match = False
