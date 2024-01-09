# Parts of code from https://github.com/chander/django-clamav/
import logging

import clamd

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


def get_scanner():
    return clamd.ClamdNetworkSocket(settings.CLAMAV_TCP_ADDR, settings.CLAMAV_TCP_PORT)


def validate_file_infection(file):
    if not settings.CLAMAV_ENABLED:
        return

    # Ensure file pointer is at beginning of the file
    file.seek(0)

    scanner = get_scanner()
    try:
        result = scanner.instream(file)
    except OSError:
        # Ping the server if it fails than the server is down
        scanner.ping()
        # Server is up. This means that the file is too big.
        logger.warning(
            f'ClamD: The file is too large for ClamD to scan it. Bytes Read {file.tell()}'
        )
        file.seek(0)
        return
    except clamd.BufferTooLongError as e:
        logger.warning(f'ClamD: {str(e)}')
        file.seek(0)
        return

    if result and result['stream'][0] == 'FOUND':
        raise ValidationError(_('File is infected with malware'), code='infected')

    # Return file pointer to beginning of the file again
    file.seek(0)
