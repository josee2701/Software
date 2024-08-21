# middleware/htmx_middleware.py


class HTMXMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.htmx = "HX-Request" in request.headers
        response = self.get_response(request)
        return response
