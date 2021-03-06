# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-06-05 13:11
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations
import media_server.validators


class Migration(migrations.Migration):

    dependencies = [
        ('media_server', '0010_auto_20190522_1549'),
    ]

    operations = [
        migrations.AlterField(
            model_name='audio',
            name='license',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True, validators=[media_server.validators.validate_license]),
        ),
        migrations.AlterField(
            model_name='document',
            name='license',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True, validators=[media_server.validators.validate_license]),
        ),
        migrations.AlterField(
            model_name='image',
            name='license',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True, validators=[media_server.validators.validate_license]),
        ),
        migrations.AlterField(
            model_name='other',
            name='license',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True, validators=[media_server.validators.validate_license]),
        ),
        migrations.AlterField(
            model_name='video',
            name='license',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True, validators=[media_server.validators.validate_license]),
        ),
    ]
