# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-03-13 14:29
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('media_server', '0005_auto_20190215_1203'),
    ]

    operations = [
        migrations.RenameField(
            model_name='audio',
            old_name='entity_id',
            new_name='entry_id',
        ),
        migrations.RenameField(
            model_name='document',
            old_name='entity_id',
            new_name='entry_id',
        ),
        migrations.RenameField(
            model_name='image',
            old_name='entity_id',
            new_name='entry_id',
        ),
        migrations.RenameField(
            model_name='other',
            old_name='entity_id',
            new_name='entry_id',
        ),
        migrations.RenameField(
            model_name='video',
            old_name='entity_id',
            new_name='entry_id',
        ),
    ]