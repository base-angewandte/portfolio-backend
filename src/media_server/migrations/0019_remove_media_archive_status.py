# Generated by Django 2.2.16 on 2021-03-22 10:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('media_server', '0018_media_archive_status'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='media',
            name='archive_status',
        ),
    ]