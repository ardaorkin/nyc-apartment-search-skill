from sources.sitemap_adapter import SitemapAdapter


class EquityResidentialAdapter(SitemapAdapter):
    name = "equity_residential"
    base_url = "https://www.equityapartments.com"
    sitemap_urls = ["https://www.equityapartments.com/sitemap.xml"]
    require_area_match = False
