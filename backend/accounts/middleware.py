from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages


class TenantMiddleware:
    """
    Attaches the authenticated user's company to the request object.
    Ensures views always have easy access to request.company.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and hasattr(request.user, 'company'):
            request.company = request.user.company
        else:
            request.company = None
        return self.get_response(request)


class SubscriptionLockMiddleware:
    """
    Guards the application if the company's free trial has ended and
    there is no active paid subscription.
    Allows billing routes, logout, admin, and static/media.
    """
    EXEMPT_PATHS = [
        '/billing/',
        '/accounts/logout/',
        '/accounts/login/',
        '/admin/',
        '/static/',
        '/media/',
        '/terms/',
        '/privacy/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.is_superuser:
            company = getattr(request, 'company', None)
            if company and not company.is_subscription_active():
                path = request.path
                is_exempt = any(path.startswith(prefix) for prefix in self.EXEMPT_PATHS) or path == '/'
                if not is_exempt:
                    messages.warning(
                        request,
                        "Your 30-day free trial has expired. Please subscribe to continue using FinTrack."
                    )
                    return redirect(reverse('billing:pricing'))

        return self.get_response(request)
