import base64

from django.conf import settings
from django.http import HttpResponse
from django.utils.crypto import constant_time_compare


def basicauth(view):
    def wrap(request, *args, **kwargs):
        if 'HTTP_AUTHORIZATION' in request.META:
            if (
                getattr(settings, 'DOCS_USER', None) is not None
                and getattr(settings, 'DOCS_PASSWORD', None) is not None
            ):
                auth = request.META['HTTP_AUTHORIZATION'].split()
                if len(auth) == 2:
                    if auth[0].lower() == 'basic':
                        uname, passwd = base64.b64decode(auth[1]).decode('utf8').split(':')
                        # prevent timing atacks with contant_time_compare
                        if constant_time_compare(uname, settings.DOCS_USER) and constant_time_compare(
                            passwd, settings.DOCS_PASSWORD
                        ):
                            return view(request, *args, **kwargs)

        response = HttpResponse()
        response.status_code = 401
        response['WWW-Authenticate'] = f'Basic realm="{settings.DOCS_REALM}"'
        return response

    return wrap
