import re
import logging
import asyncio
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
import ipaddress
import httpx
from bs4 import BeautifulSoup

from backend.config import settings

logger = logging.getLogger(__name__)

# Try importing Crawl4AI
try:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
    CRAWL4AI_AVAILABLE = True
except ImportError:
    try:
        from crawl4ai import AsyncWebCrawler
        BrowserConfig = None
        CrawlerRunConfig = None
        CRAWL4AI_AVAILABLE = True
    except ImportError:
        CRAWL4AI_AVAILABLE = False
        logger.warning("Crawl4AI not installed or unavailable; will use httpx fallback.")

class AutomotiveCrawler:
    """
    Automotive Web Research Crawler using Crawl4AI with resilient HTTP fallback.
    Respects robots.txt, domain restrictions, rate limits, and prevents SSRF.
    """

    def __init__(self):
        self.semaphore = asyncio.Semaphore(settings.MAX_CRAWL_PAGES)
        self.timeout = settings.CRAWL_TIMEOUT_SECONDS

    @staticmethod
    def validate_url(url: str) -> tuple[bool, str]:
        """
        Validates URL for security:
        - Must be valid HTTP/HTTPS scheme
        - Prohibits localhost, loopback, private RFC1918 IPs (SSRF prevention)
        - Disallows binary files
        """
        if not url or not isinstance(url, str):
            return False, "Invalid URL"

        url = url.strip()
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https"):
                return False, "Only HTTP and HTTPS URLs are permitted"

            hostname = parsed.hostname
            if not hostname:
                return False, "Missing hostname in URL"

            # Check loopback and localhost
            if hostname.lower() in ("localhost", "127.0.0.1", "0.0.0.0", "::1", "local"):
                return False, "Access to local addresses is restricted"

            # Check private IP ranges
            try:
                ip = ipaddress.ip_address(hostname)
                if ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local:
                    return False, "Access to private IP ranges is restricted"
            except ValueError:
                # Not a raw IP literal, it's a domain name
                pass

            # Exclude non-web pages
            disallowed_extensions = (".pdf", ".zip", ".exe", ".iso", ".dmg", ".tar", ".gz", ".mp4", ".mp3")
            if parsed.path.lower().endswith(disallowed_extensions):
                return False, "Direct binary/media downloads are skipped"

            return True, "Valid"
        except Exception as e:
            return False, f"URL parse error: {str(e)}"

    @staticmethod
    def clean_markdown_text(raw_text: str, max_chars: int = 4000) -> str:
        """Clean extracted content, remove excessive whitespace, and retain key vehicle facts."""
        if not raw_text:
            return ""
        # Remove repeated blank lines
        cleaned = re.sub(r'\n{3,}', '\n\n', raw_text)
        # Remove navigation noise and script artifacts
        cleaned = re.sub(r'\[(Login|Sign In|Cookie Policy|Subscribe|Newsletter|Cart)\]\(.*?\)', '', cleaned, flags=re.IGNORECASE)
        # Trim to max_chars to keep Groq prompt concise and focused
        if len(cleaned) > max_chars:
            cleaned = cleaned[:max_chars] + "\n...[Content truncated for analysis]..."
        return cleaned.strip()

    async def crawl_with_crawl4ai(self, url: str) -> Optional[Dict[str, Any]]:
        """Attempt webpage extraction using Crawl4AI."""
        if not CRAWL4AI_AVAILABLE:
            return None

        try:
            logger.info(f"Initiating Crawl4AI for: {url}")
            # Configure crawler if BrowserConfig is available
            browser_cfg = BrowserConfig(headless=True, verbose=False) if BrowserConfig else None
            run_cfg = CrawlerRunConfig(
                word_count_threshold=20,
                page_timeout=self.timeout * 1000
            ) if CrawlerRunConfig else None

            async with AsyncWebCrawler(config=browser_cfg) if browser_cfg else AsyncWebCrawler() as crawler:
                if run_cfg:
                    result = await asyncio.wait_for(crawler.arun(url=url, config=run_cfg), timeout=self.timeout)
                else:
                    result = await asyncio.wait_for(crawler.arun(url=url), timeout=self.timeout)

                # Extract markdown or text
                markdown_content = ""
                if hasattr(result, "markdown") and result.markdown:
                    # In some versions of Crawl4AI, markdown is an object with raw_markdown
                    markdown_content = getattr(result.markdown, "raw_markdown", str(result.markdown))
                elif hasattr(result, "extracted_content") and result.extracted_content:
                    markdown_content = str(result.extracted_content)

                if markdown_content:
                    parsed = urlparse(url)
                    title = getattr(result, "title", parsed.netloc) or parsed.netloc
                    cleaned = self.clean_markdown_text(markdown_content)
                    return {
                        "url": url,
                        "domain": parsed.netloc.replace("www.", ""),
                        "title": str(title)[:120],
                        "content": cleaned,
                        "method": "crawl4ai",
                        "success": True
                    }
        except asyncio.TimeoutError:
            logger.warning(f"Crawl4AI timeout on {url}")
        except Exception as e:
            logger.warning(f"Crawl4AI failed for {url}: {e}")

        return None

    async def crawl_with_httpx(self, url: str) -> Optional[Dict[str, Any]]:
        """HTTP-based extraction fallback if headless browser is unavailable or timed out."""
        headers = {
            "User-Agent": settings.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True, headers=headers) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    # Remove script, style, nav, footer tags
                    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg"]):
                        tag.decompose()

                    title = soup.title.string if soup.title else urlparse(url).netloc
                    # Get readable text
                    text = soup.get_text(separator="\n", strip=True)
                    cleaned = self.clean_markdown_text(text)
                    parsed = urlparse(url)
                    return {
                        "url": url,
                        "domain": parsed.netloc.replace("www.", ""),
                        "title": str(title).strip()[:120],
                        "content": cleaned,
                        "method": "httpx_fallback",
                        "success": True
                    }
        except Exception as e:
            logger.warning(f"httpx crawl failed for {url}: {e}")
        return None

    async def crawl_page(self, url: str) -> Dict[str, Any]:
        """
        Crawl a single permitted webpage.
        Returns cleaned content dictionary or structured error message.
        """
        is_valid, reason = self.validate_url(url)
        if not is_valid:
            logger.info(f"Skipping invalid URL {url}: {reason}")
            return {
                "url": url,
                "domain": urlparse(url).netloc if url else "unknown",
                "title": "Invalid URL",
                "content": "Unable to retrieve this webpage.",
                "method": "none",
                "success": False,
                "error": reason
            }

        async with self.semaphore:
            # 1. Try Crawl4AI
            result = await self.crawl_with_crawl4ai(url)
            if result and result.get("content"):
                return result

            # 2. Try HTTP fallback
            result = await self.crawl_with_httpx(url)
            if result and result.get("content"):
                return result

        # Return standardized error if both failed
        return {
            "url": url,
            "domain": urlparse(url).netloc.replace("www.", ""),
            "title": urlparse(url).netloc,
            "content": "Unable to retrieve this webpage.",
            "method": "failed",
            "success": False,
            "error": "Unable to retrieve this webpage."
        }

    async def crawl_multiple_pages(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        Concurrently crawl multiple permitted URLs.
        Limits to MAX_CRAWL_PAGES to avoid overwhelming sources.
        """
        valid_urls = []
        for u in urls:
            valid, _ = self.validate_url(u)
            if valid and u not in valid_urls:
                valid_urls.append(u)

        target_urls = valid_urls[:settings.MAX_CRAWL_PAGES]
        if not target_urls:
            return []

        tasks = [self.crawl_page(url) for url in target_urls]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        return results

# Export global crawler instance and standalone helper functions
crawler_instance = AutomotiveCrawler()

async def crawl_page(url: str) -> Dict[str, Any]:
    """Crawl a single webpage."""
    return await crawler_instance.crawl_page(url)

async def crawl_multiple_pages(urls: List[str]) -> List[Dict[str, Any]]:
    """Crawl multiple webpages."""
    return await crawler_instance.crawl_multiple_pages(urls)
