import logging

from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler

default_app_config = 'api.apps.ApiConfig'

logger = logging.getLogger(__name__)


class PermanentRedirect(APIException):
    # TODO: in the current version rest_framework.status has a status.HTTP_307_TEMPORARY_REDIRECT, but it is missing a
    #       status.HTTP_308_PERMANENT_REDIRECT, which is available in a newer version of rest_framework. Update this,
    #       as soon as rest_framework is updated.
    # status_code = status.HTTP_308_PERMANENT_REDIRECT
    status_code = 308
    default_detail = 'This resource has moved'
    default_code = 'permanent_redirect'

    def __init__(self, detail=None, to=None):
        self.to = to
        if detail is None:
            detail = self.default_detail
        super().__init__(detail)


def portfolio_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    if isinstance(exc, PermanentRedirect):
        pk = context['kwargs']['pk']
        old_path = context['request']._request.path
        if exc.to:
            new_path = old_path.replace(pk, exc.to)
            response.data['to'] = new_path
            # TODO: update to response.headers['Location'] once django is updated to >= 3.2
            response['Location'] = new_path
        else:
            # TODO: in case to was not set when the exception was raised, should we
            #       rather convert this to a 404, or should we even raise another
            #       exception and go for a 500?
            response.data['to'] = 'location not disclosed'
            logger.warning(f'PermanentRedirect: no to parameter was provided for {old_path}')

    return response
