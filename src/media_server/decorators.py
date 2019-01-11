from django.http import HttpResponseForbidden
from django.conf import settings


def is_allowed(view_func):
    def _wrapped_view_func(request, *args, **kwargs):
        try:
            path_user_id = settings.HASHIDS.decode(kwargs['path'].split('/')[1])[0]
            if request.user and request.user.id == path_user_id:
                return view_func(request, *args, **kwargs)
        except IndexError:
            pass
        return HttpResponseForbidden()
    return _wrapped_view_func
