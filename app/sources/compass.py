from sources.sitemap_adapter import SitemapAdapter


class CompassAdapter(SitemapAdapter):
    name = "compass"
    base_url = "https://www.compass.com"
    sitemap_urls = ["https://www.compass.com/sitemaps/for-rent/index.xml"]
    require_area_match = False
