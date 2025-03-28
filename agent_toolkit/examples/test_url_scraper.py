import requests
import json
import os
from dotenv import load_dotenv
from typing import Optional
from pydantic import BaseModel

class ScraperResponse(BaseModel):
    """Response model for URL scraping."""
    status: str
    content: Optional[str] = None
    error: Optional[str] = None

def scrape_url(url: str, render_js: bool = False) -> ScraperResponse:
    headers = {"X-API-Key": os.getenv("API_KEY")}
    data = {
        "url": url,
        "render_js": render_js
    }
    try:
        response = requests.post("http://127.0.0.1:32823/scrape_url", json=data, headers=headers)
        if response.status_code == 200:
            return ScraperResponse(**response.json())
        else:
            return ScraperResponse(
                status="error",
                error=f"Server error: {response.status_code} {response.text}"
            )
    except Exception as e:
        return ScraperResponse(
            status="error",
            error=f"Request failed: {str(e)}"
        )

def main():
    load_dotenv()
    
    # Test regular scraping
    print("\nRegular scraping:")
    result = scrape_url("https://example.com", render_js=False)
    print(json.dumps(result.model_dump(), indent=2))
    
    # Test JavaScript-rendered scraping
    print("\nJavaScript-rendered scraping:")
    result = scrape_url("https://example.com", render_js=True)
    print(json.dumps(result.model_dump(), indent=2))

if __name__ == "__main__":
    main() 