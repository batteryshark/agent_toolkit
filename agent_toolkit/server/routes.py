from fastapi import HTTPException
from .app import app, SearchQuery, rate_limit
from ..tools.web_search import search_web, WebSearchResponse
from ..tools.url_scraper import scrape_url, ScraperResponse
from ..config.loader import ConfigLoader
from pydantic import BaseModel

# Load configurations
web_search_config = ConfigLoader.load_config("web_search")
url_scraper_config = ConfigLoader.load_config("url_scraper")

@app.post("/search_web", response_model=WebSearchResponse)
@rate_limit(
    "web_search",
    max_requests=web_search_config["rate_limit"]["max_requests"],
    time_window_seconds=web_search_config["rate_limit"]["time_window_seconds"]
)
async def handle_web_search(query: SearchQuery):
    """Handle web search requests."""
    try:
        result = await search_web(query.query)
        if result.status == "error":
            raise HTTPException(status_code=400, detail=result.error)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class URLScraperQuery(BaseModel):
    """Input model for URL scraping."""
    url: str
    render_js: bool = False

@app.post("/scrape_url", response_model=ScraperResponse)
@rate_limit(
    "url_scraper",
    max_requests=url_scraper_config["rate_limit"]["max_requests"],
    time_window_seconds=url_scraper_config["rate_limit"]["time_window_seconds"]
)
async def handle_url_scrape(query: URLScraperQuery):
    """Handle URL scraping requests."""
    try:
        result = await scrape_url(query.url, query.render_js)
        if result.status == "error":
            raise HTTPException(status_code=400, detail=result.error)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 