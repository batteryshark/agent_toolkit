import requests
import json
import os
from dotenv import load_dotenv
from typing import Optional, Dict, Any
from pydantic import BaseModel

class WebSearchReference(BaseModel):
    """Model for a single web search reference."""
    content: str
    url: str
    title: str
    confidence: Optional[float] = None

class WebSearchResponse(BaseModel):
    """Response model for web search."""
    status: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

def search_web(query: str) -> WebSearchResponse:
    headers = {"X-API-Key": os.getenv("API_KEY")}
    data = {"query": query}
    
    try:
        response = requests.post("http://127.0.0.1:32823/search_web", json=data, headers=headers)
        if response.status_code == 200:
            return WebSearchResponse(**response.json())
        else:
            return WebSearchResponse(
                status="error",
                error=f"Server error: {response.status_code} {response.text}"
            )
    except Exception as e:
        return WebSearchResponse(
            status="error",
            error=f"Request failed: {str(e)}"
        )

def main():
    load_dotenv()
    result = search_web("what is the capital of france?")
    print(json.dumps(result.model_dump(), indent=2))

if __name__ == "__main__":
    main() 