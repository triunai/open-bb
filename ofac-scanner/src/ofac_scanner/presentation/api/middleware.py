"""
Private Network Access Middleware

Handles Chrome's Private Network Access (PNA) security feature.
Required for requests from public HTTPS sites to localhost.

See: https://developer.chrome.com/blog/private-network-access-preflight/
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class PrivateNetworkAccessMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle Private Network Access preflight requests.
    
    Chrome 94+ blocks requests from public websites (like https://pro.openbb.co)
    to private networks (like localhost) unless the server explicitly allows it.
    
    This middleware adds the required headers to preflight responses.
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Handle preflight requests
        if request.method == "OPTIONS":
            response = Response(
                content="",
                status_code=204,
                headers={
                    "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                    "Access-Control-Allow-Headers": "*",
                    "Access-Control-Allow-Credentials": "true",
                    # This is the key header for Private Network Access
                    "Access-Control-Allow-Private-Network": "true",
                },
            )
            return response
        
        # For non-preflight requests, add PNA header to response
        response = await call_next(request)
        
        # Add PNA header
        response.headers["Access-Control-Allow-Private-Network"] = "true"
        
        return response
