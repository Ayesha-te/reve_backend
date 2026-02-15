from typing import Callable


class EnsureCORSHeadersMiddleware:
    """
    Fallback CORS header injector. django-cors-headers should already handle
    responses, but some upstream responses (e.g., errors before middleware or
    platform-added redirects) can miss the header. This middleware mirrors the
    request Origin when present so the browser doesn't block.
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        origin = request.headers.get("Origin")
        if origin:
            response.setdefault("Access-Control-Allow-Origin", origin)
            response.setdefault("Vary", "Origin")
            response.setdefault("Access-Control-Allow-Credentials", "true")
        return response
