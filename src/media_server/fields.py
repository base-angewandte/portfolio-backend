import json
import logging
from pathlib import Path

from django.db import models

from exiffield.fields import ExifField as DjangoExifField, get_exif

from .utils import humanize_size

logger = logging.getLogger(__name__)


class ExifField(DjangoExifField):
    def update_exif(
            self,
            instance: models.Model,
            force: bool = False,
            commit: bool = False,
            **kwargs,
    ) -> None:
        """
        Load exif data from file.
        """
        file_ = getattr(instance, self.source)
        if not file_:
            # there is no file attached to the FileField
            return

        # check whether extraction of the exif is required
        exif_data = getattr(instance, self.name, None) or {}
        has_exif = bool(exif_data)
        filename = Path(file_.path).name
        exif_for_filename = exif_data.get('FileName', {}).get('val', '')
        file_changed = exif_for_filename != filename or not file_._committed

        if has_exif and not file_changed and not force:
            # nothing to do since the file has not been changed
            return

        try:
            exif_json = get_exif(file_)
        except Exception:
            # modified by Philipp Mayer
            logger.warning('Could not read metainformation from file: %s', file_.path)
            # create fallback data
            exif_json = json.dumps([{
                'FileSize': {
                    'desc': 'File Size',
                    'num': file_.size,
                    'val': humanize_size(file_.size),
                },
                'MIMEType': {
                    'desc': 'MIME Type',
                    'val': instance.mime_type,
                },
            }])

        try:
            exif_data = json.loads(exif_json)[0]
        except IndexError:
            return
        else:
            if 'FileName' not in exif_data:
                # If the file is uncommited, exiftool cannot extract a filenmae
                # We guess, that no other file with the same filename exists in
                # the storage.
                # In the worst case the exif is extracted twice...
                exif_data['FileName'] = {
                    'desc': 'Filename',
                    'val': filename,
                }
            setattr(instance, self.name, exif_data)

        if commit:
            instance.save()
