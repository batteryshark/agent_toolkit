from datetime import datetime
from collections import deque
import threading
import time
from typing import Dict

class RateLimiter:
    def __init__(self, max_requests: int, time_window_seconds: int):
        self.max_requests = max_requests
        self.time_window_seconds = time_window_seconds
        self.requests = deque()
        self.lock = threading.Lock()

    def can_make_request(self) -> bool:
        now = datetime.now()
        with self.lock:
            while self.requests and (now - self.requests[0]).total_seconds() > self.time_window_seconds:
                self.requests.popleft()
            
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True
            return False

    def wait_for_slot(self):
        while not self.can_make_request():
            time.sleep(1)

# Global registry of rate limiters
_rate_limiters: Dict[str, RateLimiter] = {}

def get_rate_limiter(tool_name: str, max_requests: int, time_window_seconds: int) -> RateLimiter:
    """Get or create a rate limiter for a specific tool."""
    if tool_name not in _rate_limiters:
        _rate_limiters[tool_name] = RateLimiter(max_requests, time_window_seconds)
    return _rate_limiters[tool_name] 