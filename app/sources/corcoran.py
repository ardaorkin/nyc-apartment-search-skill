from sources.sitemap_adapter import SitemapAdapter


class CorcoranAdapter(SitemapAdapter):
    name = "corcoran"
    base_url = "https://www.corcoran.com"
    sitemap_urls = ["https://www.corcoran.com/sitemap.xml"]
    require_area_match = False
