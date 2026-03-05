import time
from typing import Dict, DefaultDict
from collections import defaultdict
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
import asyncio
from functools import wraps
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

class InMemoryRateLimiter:
    def __init__(self):
        self.default_rate_limit = int(os.getenv("RATE_LIMIT_PER_MINUTE", 60))
        self.login_rate_limit = int(os.getenv("LOGIN_RATE_LIMIT_PER_MINUTE", 5))
        self.request_counts: Dict[str, list] = defaultdict(list)
        self.blocked_ips: Dict[str, datetime] = {}
        self.dos_threshold = int(os.getenv("DOS_THRESHOLD_PER_MINUTE", 100))
        self.block_duration_minutes = int(os.getenv("BLOCK_DURATION_MINUTES", 15))
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request"""
        # Check for forwarded IP first (in case of proxy)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Check for real IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fall back to client host
        return request.client.host if request.client else "unknown"
    
    def _cleanup_old_requests(self, key: str, window_seconds: int = 60):
        """Remove old request timestamps outside the window"""
        current_time = time.time()
        self.request_counts[key] = [
            timestamp for timestamp in self.request_counts[key]
            if current_time - timestamp < window_seconds
        ]
    
    def _cleanup_blocked_ips(self):
        """Remove expired IP blocks"""
        current_time = datetime.utcnow()
        expired_ips = [
            ip for ip, block_time in self.blocked_ips.items()
            if current_time > block_time + timedelta(minutes=self.block_duration_minutes)
        ]
        for ip in expired_ips:
            del self.blocked_ips[ip]
    
    async def is_ip_blocked(self, request: Request) -> bool:
        """Check if IP is currently blocked"""
        self._cleanup_blocked_ips()
        client_ip = self._get_client_ip(request)
        return client_ip in self.blocked_ips
    
    async def check_dos_protection(self, request: Request) -> bool:
        """Check for potential DoS attacks and block if necessary"""
        client_ip = self._get_client_ip(request)
        key = f"dos_check:{client_ip}"
        
        self._cleanup_old_requests(key)
        
        # Count requests in the last minute
        current_count = len(self.request_counts[key])
        
        if current_count >= self.dos_threshold:
            # Block this IP
            self.blocked_ips[client_ip] = datetime.utcnow()
            return False
        
        # Add current request
        self.request_counts[key].append(time.time())
        return True
    
    async def check_rate_limit(self, request: Request, endpoint: str, limit_per_minute: int = None) -> bool:
        """Check if request exceeds rate limit"""
        # First check if IP is blocked
        if await self.is_ip_blocked(request):
            return False
        
        # Check for DoS
        if not await self.check_dos_protection(request):
            return False
        
        if limit_per_minute is None:
            limit_per_minute = self.default_rate_limit
        
        client_ip = self._get_client_ip(request)
        key = f"rate_limit:{endpoint}:{client_ip}"
        
        # Clean old requests
        self._cleanup_old_requests(key)
        
        # Count current requests in window
        current_count = len(self.request_counts[key])
        
        if current_count >= limit_per_minute:
            return False
        
        # Add current request
        self.request_counts[key].append(time.time())
        return True
    
    async def get_remaining_attempts(self, request: Request, endpoint: str, limit_per_minute: int = None) -> int:
        """Get remaining attempts for current window"""
        if limit_per_minute is None:
            limit_per_minute = self.default_rate_limit
        
        client_ip = self._get_client_ip(request)
        key = f"rate_limit:{endpoint}:{client_ip}"
        
        # Clean old requests
        self._cleanup_old_requests(key)
        
        # Count current requests
        current_count = len(self.request_counts[key])
        
        return max(0, limit_per_minute - current_count)

# Global rate limiter instance
rate_limiter = InMemoryRateLimiter()

def rate_limit(endpoint: str, limit_per_minute: int = None):
    """Decorator for rate limiting endpoints"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find the request object in arguments
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            # Also check in kwargs
            if not request and 'request' in kwargs:
                request = kwargs['request']
            
            if request and not await rate_limiter.check_rate_limit(request, endpoint, limit_per_minute):
                remaining = await rate_limiter.get_remaining_attempts(request, endpoint, limit_per_minute)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "Rate limit exceeded",
                        "retry_after": 60,
                        "remaining_attempts": remaining
                    }
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Specific decorators for different endpoints
def login_rate_limit(func):
    """Rate limiter specifically for login attempts"""
    return rate_limit("login", rate_limiter.login_rate_limit)(func)

def api_rate_limit(func):
    """General API rate limiter"""
    return rate_limit("api", rate_limiter.default_rate_limit)(func)

def dos_protection(func):
    """DoS protection decorator"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Find the request object
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        
        if not request and 'request' in kwargs:
            request = kwargs['request']
        
        if request:
            # Check if IP is blocked
            if await rate_limiter.is_ip_blocked(request):
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail="Your IP has been temporarily blocked due to suspicious activity"
                )
            
            # Check DoS protection
            if not await rate_limiter.check_dos_protection(request):
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail="Too many requests. Your IP has been temporarily blocked."
                )
        
        return await func(*args, **kwargs)
    return wrapper

class RateLimitMiddleware:
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Create a simple request object for IP checking
            class SimpleRequest:
                def __init__(self, scope):
                    self.scope = scope
                    self.client = scope.get("client")
                    self.headers = dict(scope.get("headers", []))
            
            request = SimpleRequest(scope)
            
            # Check if IP is blocked
            if await rate_limiter.is_ip_blocked(request):
                response = JSONResponse(
                    status_code=423,
                    content={"detail": "Your IP has been temporarily blocked due to suspicious activity"}
                )
                await response(scope, receive, send)
                return
        
        await self.app(scope, receive, send)
