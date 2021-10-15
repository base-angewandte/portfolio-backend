# Generated by Django 2.2.21 on 2021-09-09 09:34

import os
import shutil
from django.db import migrations


def set_new_ids(apps, schema_editor):
    Media = apps.get_model('media_server', 'Media')
    for m in Media.objects.all():
        old_id = m.id
        new_id = m.id[::-1]
        new_entry_id = m.entry_id[::-1]
        old_path = os.path.join(os.path.dirname(m.file.path), old_id)
        new_path = os.path.join(os.path.dirname(m.file.path), new_id)
        Media.objects.filter(id=old_id).update(id=new_id, entry_id=new_entry_id, modified=m.modified)
        try:
            shutil.move(old_path, new_path)
        except FileNotFoundError:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('media_server', '0017_auto_20210721_1643'),
        ('core', '0017_entry_new_id'),
    ]

    operations = [
        migrations.RunPython(code=set_new_ids, reverse_code=set_new_ids),
    ]
