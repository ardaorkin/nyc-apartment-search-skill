from sources.sitemap_adapter import SitemapAdapter


class BrownHarrisStevensAdapter(SitemapAdapter):
    name = "brown_harris_stevens"
    base_url = "https://www.bhsusa.com"
    sitemap_urls = ["https://www.bhsusa.com/sitemaps/bhs.xml"]
    require_area_match = False
