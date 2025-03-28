import json
import logging
import re
import requests
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from google import genai
from google.genai import types
import os
from ..config.loader import ConfigLoader

logger = logging.getLogger(__name__)

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

def extract_title_from_html(html_content: str) -> str | None:
    """Extract title from HTML content using regex."""
    title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_content, re.IGNORECASE)
    return title_match.group(1).strip() if title_match else None

def follow_redirect(url: str, timeout: int = 5) -> tuple[str, str | None]:
    """Follow a URL redirect and return the final URL and page title."""
    try:
        # Clean and encode the URL
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
        
        # First try with HEAD request to get redirects without downloading content
        response = requests.head(url, allow_redirects=True, timeout=timeout)
        final_url = response.url
        
        # If it's still a Google redirect URL, try to get the actual content
        if "vertexaisearch.cloud.google.com" in final_url:
            response = requests.get(final_url, stream=True, timeout=timeout)
            content = next(response.iter_content(8192)).decode('utf-8', errors='ignore')
            response.close()
            
            # Try to extract the actual URL from the response
            url_match = re.search(r'href="([^"]+)"', content)
            if url_match:
                final_url = url_match.group(1)
                # Follow the actual URL
                response = requests.get(final_url, stream=True, timeout=timeout)
                content = next(response.iter_content(8192)).decode('utf-8', errors='ignore')
                response.close()
        else:
            # For non-Google URLs, just get the content
            response = requests.get(final_url, stream=True, timeout=timeout)
            content = next(response.iter_content(8192)).decode('utf-8', errors='ignore')
            response.close()
        
        title = extract_title_from_html(content)
        if title and any(x in title for x in ["Attention Required! | Cloudflare", "Just a moment...", "Security check"]):
            return final_url, None
            
        return final_url, title
    except Exception as e:
        logger.error(f"Error following redirect: {e}")
        return url, None

def extract_references(response, max_references: int = 10) -> List[WebSearchReference]:
    """Extract detailed references from Gemini response."""
    try:
        raw_response = json.loads(response.model_dump_json())
        logger.debug(f"Raw response: {json.dumps(raw_response, indent=2)}")
        
        candidates = raw_response.get("candidates", [])
        if not candidates:
            logger.warning("No candidates found in response")
            return []
            
        grounding_metadata = candidates[0].get("grounding_metadata", {})
        if not grounding_metadata:
            logger.warning("No grounding metadata found in first candidate")
            return []
            
        # Ensure we have lists, even if empty
        grounding_supports = grounding_metadata.get("grounding_supports") or []
        grounding_chunks = grounding_metadata.get("grounding_chunks") or []
        
        logger.debug(f"Found {len(grounding_supports)} supports and {len(grounding_chunks)} chunks")
        
        references = []
        
        for support in grounding_supports:
            if len(references) >= max_references:
                break
                
            # Skip if no chunk indices
            chunk_indices = support.get("grounding_chunk_indices") or []
            if not chunk_indices:
                logger.debug("Support has no chunk indices, skipping")
                continue
                
            for chunk_idx in chunk_indices:
                # Skip if chunk index is out of range
                if chunk_idx >= len(grounding_chunks):
                    logger.warning(f"Chunk index {chunk_idx} out of range, skipping")
                    continue
                    
                chunk = grounding_chunks[chunk_idx]
                if "web" not in chunk:
                    logger.debug(f"Chunk {chunk_idx} has no web data, skipping")
                    continue
                    
                try:
                    url = chunk["web"]["uri"]
                    final_url, actual_title = follow_redirect(url)
                    
                    # Get text content safely
                    text = support.get("segment", {}).get("text", "")
                    if not text:
                        logger.warning("Support has no text content, skipping")
                        continue
                    
                    # Get confidence score safely
                    confidence_scores = support.get("confidence_scores") or []
                    confidence = confidence_scores[0] if confidence_scores else None
                    
                    reference = WebSearchReference(
                        content=text,
                        url=final_url,
                        title=actual_title or chunk["web"].get("title", ""),
                        confidence=confidence
                    )
                    references.append(reference)
                    logger.debug(f"Added reference: {reference.model_dump()}")
                    
                    if len(references) >= max_references:
                        break
                except Exception as e:
                    logger.error(f"Error processing chunk {chunk_idx}: {e}")
                    continue
        
        logger.info(f"Successfully extracted {len(references)} references")
        return references
    except Exception as e:
        logger.error(f"Error extracting references: {e}", exc_info=True)
        return []

async def search_web(query: str) -> WebSearchResponse:
    """Perform web search using Gemini."""
    if not query:
        return WebSearchResponse(
            status="error",
            error="No query provided"
        )
    
    # Load configuration
    config = ConfigLoader.load_config("web_search")
    gemini_key = config["api"]["gemini"]["key"]
    if gemini_key.startswith("${") and gemini_key.endswith("}"):
        # Handle environment variable interpolation
        env_var = gemini_key[2:-1]
        gemini_key = os.getenv(env_var)
    
    if not gemini_key:
        return WebSearchResponse(
            status="error",
            error="Gemini API key not configured"
        )
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            client = genai.Client(api_key=gemini_key)
            response = client.models.generate_content(
                model=config["api"]["gemini"]["model"],
                contents=query,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())]
                )
            )
            
            raw_response = json.loads(response.model_dump_json())
            candidates = raw_response.get("candidates", [])
            if not candidates:
                logger.warning("No candidates in response")
                return WebSearchResponse(
                    status="error",
                    error="No response from Gemini"
                )
                
            grounding_metadata = candidates[0].get("grounding_metadata", {})
            if not grounding_metadata:
                logger.warning("No grounding metadata in response")
                return WebSearchResponse(
                    status="error",
                    error="No grounding metadata in response"
                )
            
            references = extract_references(response, config["search"]["max_references"])
            logger.info(f"Extracted {len(references)} references")
            
            return WebSearchResponse(
                status="success",
                data={
                    "prompt": query,
                    "search_query": grounding_metadata.get("web_search_queries", []),
                    "response": response.text,
                    "references": references
                }
            )
        except Exception as e:
            logger.error(f"Search attempt {attempt + 1} failed: {e}", exc_info=True)
            if attempt == max_retries - 1:
                return WebSearchResponse(
                    status="error",
                    error=str(e)
                ) 