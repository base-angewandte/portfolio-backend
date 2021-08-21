from urllib.parse import urljoin

from media_server.archiver import uris

_mime_endoint_mapping = {
    'application/pdf': 'document',
    'application/x-pdf': 'document',
    'image/jpeg': 'picture',
    'image/gif': 'picture',
    'image/tiff': 'picture',
    'image/png': 'picture',
    'audio/x-wav': 'audio',
    'audio/wav': 'audio',
    'audio/mpeg': 'audio',
    'audio/flac': 'audio',
    'audio/ogg': 'audio',
    'audio/x-aiff': 'audio',
    'audio/aiff': 'audio',
    'video/mpeg': 'video',
    'video/avi': 'video',
    'video/x-msvideo': 'video',
    'video/mp4': 'video',
    'video/quicktime': 'video',
    'video/x-matroska': 'video',
}


def create_phaidra_object_create_uri(mime_type: str) -> str:
    object_type = _mime_endoint_mapping.get(mime_type, 'unknown')
    base = uris['BASE_URI']
    return urljoin(base=base, url=f'{object_type}/create')