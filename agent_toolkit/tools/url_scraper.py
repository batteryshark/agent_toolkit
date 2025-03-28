import requests
import urllib3
import asyncio
from typing import Dict, Any, Optional
from pydantic import BaseModel
from markdownify import markdownify
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from ..config.loader import ConfigLoader

class ScraperResponse(BaseModel):
    """Response model for URL scraping."""
    status: str
    content: Optional[str] = None
    error: Optional[str] = None

def clean_url(url: str) -> str:
    """Clean and encode a URL."""
    url = url.strip()
    if " " in url:
        # If it's a GitHub URL with spaces, try to fix it
        if "github.com" in url:
            parts = url.split()
            if len(parts) >= 2:
                url = f"{parts[0]}/{parts[1]}"
        else:
            # For other URLs, just encode spaces
            url = url.replace(" ", "%20")
    return url

async def scrape_with_playwright(url: str, config: Dict[str, Any]) -> ScraperResponse:
    """Scrape content using Playwright with JavaScript rendering."""
    try:
        url = clean_url(url)
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=config["user_agent"],
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = await context.new_page()
            
            try:
                await page.goto(url, wait_until="load", timeout=config["timeout"] * 1000)
            except PlaywrightTimeout:
                await page.goto(url, wait_until="domcontentloaded", timeout=config["timeout"] * 1000)
            
            try:
                await page.wait_for_load_state("networkidle", timeout=5000)
            except PlaywrightTimeout:
                pass
            
            # Scroll to trigger lazy loading
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)  # Wait for 2 seconds
            
            content = await page.content()
            await browser.close()
            
            return ScraperResponse(
                status="success",
                content=markdownify(content).strip().replace("\n\n\n", "\n\n")
            )
    except Exception as e:
        return ScraperResponse(
            status="error",
            error=f"Playwright error: {str(e)}"
        )

def scrape_with_requests(url: str, config: Dict[str, Any]) -> ScraperResponse:
    """Scrape content using requests."""
    try:
        url = clean_url(url)
        headers = {"User-Agent": config["user_agent"]}
        response = requests.get(url, headers=headers, timeout=config["timeout"])
        response.raise_for_status()

        content = markdownify(response.text).strip()
        content = content.replace("\n\n\n", "\n\n")

        return ScraperResponse(
            status="success",
            content=content
        )
    except requests.exceptions.RequestException as e:
        # Fallback to urllib3 if requests fails
        try:
            http = urllib3.PoolManager(
                headers=headers,
                timeout=urllib3.Timeout(connect=config["timeout"], read=config["timeout"])
            )
            response = http.request("GET", url)
            
            if response.status >= 400:
                raise urllib3.exceptions.HTTPError(f"HTTP {response.status}")

            content = markdownify(response.data.decode('utf-8')).strip()
            content = content.replace("\n\n\n", "\n\n")

            return ScraperResponse(
                status="success",
                content=content
            )
        except Exception as e:
            return ScraperResponse(
                status="error",
                error=str(e)
            )

async def scrape_url(url: str, render_js: bool = False) -> ScraperResponse:
    """Scrape content from a URL and convert it to markdown."""
    config = ConfigLoader.load_config("url_scraper")
    scraper_config = config["scraper"]
    print(f"-" * 20)
    print(f"## Scraping URL with render_js={render_js}\n```\n{url}\n```")
    print(f"-" * 20)
    if render_js:
        return await scrape_with_playwright(url, scraper_config)
    else:
        return scrape_with_requests(url, scraper_config) 