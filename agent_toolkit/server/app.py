from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, Callable
import functools
import os
from dotenv import load_dotenv
from .rate_limiter import get_rate_limiter

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# API key middleware
@app.middleware("http")
async def check_api_key(request: Request, call_next):
    api_key = request.headers.get("X-API-Key")
    if not api_key or api_key != os.getenv("API_KEY"):
        return JSONResponse(
            status_code=403,
            content={"detail": "Invalid API key"}
        )
    return await call_next(request)

def rate_limit(tool_name: str, max_requests: int, time_window_seconds: int):
    """Decorator factory for rate limiting endpoints."""
    def decorator(func: Callable):
        rate_limiter = get_rate_limiter(tool_name, max_requests, time_window_seconds)
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if not rate_limiter.can_make_request():
                raise HTTPException(
                    status_code=429, 
                    detail=f"Rate limit exceeded for {tool_name}. Please try again later."
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator

class SearchQuery(BaseModel):
    query: str 