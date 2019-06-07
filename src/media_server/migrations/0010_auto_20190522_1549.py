# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-05-22 13:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('media_server', '0009_auto_20190522_1548'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='audio',
            index=models.Index(fields=['entry_id'], name='media_serve_entry_i_ffc072_idx'),
        ),
        migrations.AddIndex(
            model_name='document',
            index=models.Index(fields=['entry_id'], name='media_serve_entry_i_9241bd_idx'),
        ),
        migrations.AddIndex(
            model_name='image',
            index=models.Index(fields=['entry_id'], name='media_serve_entry_i_73c186_idx'),
        ),
        migrations.AddIndex(
            model_name='other',
            index=models.Index(fields=['entry_id'], name='media_serve_entry_i_eb2d30_idx'),
        ),
        migrations.AddIndex(
            model_name='video',
            index=models.Index(fields=['entry_id'], name='media_serve_entry_i_77a4be_idx'),
        ),
    ]
