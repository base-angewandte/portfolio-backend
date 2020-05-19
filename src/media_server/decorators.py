from django.http import HttpResponseForbidden

from .models import Media
from .utils import decode_user_hash


def is_allowed(view_func):
    def _wrapped_view_func(request, *args, **kwargs):
        try:
            path_dict = kwargs['path'].split('/')
            path_user_username = decode_user_hash(path_dict[0])
            if (request.user and request.user.username == path_user_username) or Media.objects.get(
                id=path_dict[1]
            ).published:
                return view_func(request, *args, **kwargs)
        except IndexError:
            pass
        except Media.DoesNotExist:
            try:
                # original file doesn't contain Media id in path
                if Media.objects.get(owner__username=path_user_username, file=kwargs['path']).published:
                    return view_func(request, *args, **kwargs)
            except Media.DoesNotExist:
                pass
        return HttpResponseForbidden()

    return _wrapped_view_func
