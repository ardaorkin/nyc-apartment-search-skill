"""Shared plumbing for source adapters: cached, rate-limited, robots.txt-respecting
fetches. Every adapter subclasses BaseAdapter and implements fetch()."""
from __future__ import annotations

import hashlib
import logging
import time
import urllib.robotparser as robotparser
from pathlib import Path
from urllib.parse import urlparse

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from models import SourceResult, SourceStatus

logger = logging.getLogger("nyc_apartment_search")

CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"


class BlockedError(Exception):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


class BaseAdapter:
    name: str = "base"
    base_url: str = ""

    def __init__(self, config: dict, use_cache: bool = True):
        self.config = config
        self.use_cache = use_cache
        search_cfg = config.get("search", {})
        self.request_delay = search_cfg.get("request_delay_seconds", 3)
        self.user_agent = search_cfg.get("user_agent", "Mozilla/5.0")
        self._robots_cache: dict[str, robotparser.RobotFileParser] = {}
        self._last_request_at = 0.0

    # -- robots.txt -----------------------------------------------------
    def _robots_for(self, url: str) -> robotparser.RobotFileParser:
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        if origin not in self._robots_cache:
            rp = robotparser.RobotFileParser()
            rp.set_url(f"{origin}/robots.txt")
            try:
                resp = httpx.get(f"{origin}/robots.txt", headers={"User-Agent": self.user_agent}, timeout=10, follow_redirects=True)
                if resp.status_code >= 400:
                    rp.disallow_all = True
                else:
                    rp.parse(resp.text.splitlines())
            except httpx.HTTPError:
                rp.disallow_all = True
            self._robots_cache[origin] = rp
        return self._robots_cache[origin]

    def _check_allowed(self, url: str) -> None:
        rp = self._robots_for(url)
        if getattr(rp, "disallow_all", False):
            raise BlockedError(f"robots.txt unreachable or fully disallowed for {url}")
        if not rp.can_fetch(self.user_agent, url):
            raise BlockedError(f"robots.txt disallows fetching {url}")

    # -- cache ------------------------------------------------------------
    def _cache_path(self, url: str) -> Path:
        key = hashlib.sha256(url.encode()).hexdigest()[:24]
        source_dir = CACHE_DIR / self.name
        source_dir.mkdir(parents=True, exist_ok=True)
        return source_dir / f"{key}.html"

    def _rate_limit(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self.request_delay:
            time.sleep(self.request_delay - elapsed)
        self._last_request_at = time.monotonic()

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=5), reraise=True)
    def _http_get(self, url: str) -> httpx.Response:
        self._rate_limit()
        return httpx.get(url, headers={"User-Agent": self.user_agent}, timeout=15, follow_redirects=True)

    def get(self, url: str) -> str:
        """Cached, robots-respecting, rate-limited GET. Raises BlockedError if the
        site's robots.txt disallows the URL or is itself unreachable."""
        self._check_allowed(url)
        cache_path = self._cache_path(url)
        if self.use_cache and cache_path.exists():
            return cache_path.read_text(encoding="utf-8", errors="replace")
        try:
            resp = self._http_get(url)
        except httpx.HTTPError as exc:
            raise BlockedError(f"network error fetching {url}: {exc}") from exc
        if resp.status_code in (403, 429) or "captcha" in resp.text.lower()[:2000]:
            raise BlockedError(f"HTTP {resp.status_code} or bot-challenge page at {url}")
        if resp.status_code >= 400:
            raise BlockedError(f"HTTP {resp.status_code} at {url}")
        cache_path.write_text(resp.text, encoding="utf-8")
        return resp.text

    # -- contract -----------------------------------------------------
    def fetch(self) -> SourceResult:
        """Subclasses override this. Must never raise -- catch BlockedError/Exception
        internally and return a SourceResult with the right status instead."""
        raise NotImplementedError

    def blocked_result(self, note: str) -> SourceResult:
        logger.warning("%s: BLOCKED_OR_MANUAL_REVIEW_REQUIRED -- %s", self.name, note)
        return SourceResult(name=self.name, status=SourceStatus.BLOCKED_OR_MANUAL_REVIEW_REQUIRED, listings=[], note=note)

    def error_result(self, note: str) -> SourceResult:
        logger.error("%s: ERROR -- %s", self.name, note)
        return SourceResult(name=self.name, status=SourceStatus.ERROR, listings=[], note=note)
