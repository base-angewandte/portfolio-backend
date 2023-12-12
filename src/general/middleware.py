from django.conf import settings
from django.http import HttpResponse


class SetRemoteAddrFromForwardedFor:
    """Middleware that sets REMOTE_ADDR based on HTTP_X_FORWARDED_FOR, if the
    latter is set.

    This is useful if you're sitting behind a reverse proxy that causes
    each request's REMOTE_ADDR to be set to 127.0.0.1. Note that this
    does NOT validate HTTP_X_FORWARDED_FOR. If you're not behind a
    reverse proxy that sets HTTP_X_FORWARDED_FOR automatically, do not
    use this middleware. Anybody can spoof the value of
    HTTP_X_FORWARDED_FOR, and because this sets REMOTE_ADDR based on
    HTTP_X_FORWARDED_FOR, that means anybody can "fake" their IP
    address. Only use this when you can absolutely trust the value of
    HTTP_X_FORWARDED_FOR.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            real_ip = request.headers['x-forwarded-for']
        except KeyError:
            pass
        else:
            # HTTP_X_FORWARDED_FOR can be a comma-separated list of IPs.
            # Take just the first one.
            real_ip = real_ip.split(',')[0]
            request.META['REMOTE_ADDR'] = real_ip

        return self.get_response(request)


class HealthCheckMiddleware:
    """Middleware for providing a health check endpoint.

    It needs to be added before
    django.middleware.common.CommonMiddleware in order to ensure that it
    also works for calls via localhost. Otherwise, health checks might
    fail if localhost is not in ALLOWED_HOSTS.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.health_check_path = f'{settings.FORCE_SCRIPT_NAME}/health'

    def __call__(self, request):
        if request.path == self.health_check_path:
            return HttpResponse('OK')
        return self.get_response(request)
