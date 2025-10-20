from django.shortcuts import redirect
from django.conf import settings

class AuthMiddleware:
    """
    Middleware that restricts access to authenticated users except for specified public paths.
    Add 'Institute_Management.middleware.AuthMiddleware' to your MIDDLEWARE in settings.py.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # List of URL paths that do not require authentication
        self.excluded_paths = [
            '/login/',
            '/login',      # handles both with and without trailing slash
            # Add more public URLs here, e.g.:
            # '/',          # Uncomment if your homepage is public
            # '/signup/',
            # '/password_reset/',
        ]

    def __call__(self, request):
        # Allow unauthenticated access to static and media files
        if request.path.startswith(settings.STATIC_URL) or request.path.startswith(settings.MEDIA_URL):
            return self.get_response(request)

        # Allow access to excluded paths (with or without trailing slash)
        path = request.path
        if path in self.excluded_paths:
            return self.get_response(request)

        # Redirect to login if not authenticated and not on an excluded path
        if not request.user.is_authenticated:
            return redirect('login')

        # Process the request
        return self.get_response(request)
