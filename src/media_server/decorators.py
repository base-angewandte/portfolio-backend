from django.http import HttpResponseForbidden

from .utils import decode_user_hash


def is_allowed(view_func):
    def _wrapped_view_func(request, *args, **kwargs):
        try:
            path_user_username = decode_user_hash(kwargs['path'].split('/')[0])
            if request.user and request.user.username == path_user_username:
                return view_func(request, *args, **kwargs)
        except IndexError:
            pass
        return HttpResponseForbidden()

    return _wrapped_view_func
