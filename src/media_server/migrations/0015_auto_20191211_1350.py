# Generated by Django 2.2.5 on 2019-12-11 12:50

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('media_server', '0014_auto_20190625_1737'),
    ]

    operations = [
        migrations.AlterField(
            model_name='media',
            name='exif',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=dict),
        ),
    ]