# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-02-06 10:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_auto_20190205_1040'),
    ]

    operations = [
        migrations.AddField(
            model_name='entity',
            name='published',
            field=models.BooleanField(default=False),
        ),
    ]
