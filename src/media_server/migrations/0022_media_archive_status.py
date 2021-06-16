# Generated by Django 2.2.16 on 2021-03-22 14:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('media_server', '0021_remove_media_archive_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='media',
            name='archive_status',
            field=models.IntegerField(choices=[(0, 'not archived'), (1, 'to be archived'), (2, 'archival in progress'), (3, 'archived'), (4, 'error')], default=0),
        ),
    ]
