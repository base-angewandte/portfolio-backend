# Generated by Django 2.2.16 on 2021-01-26 08:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('media_server', '0016_auto_20200519_1548'),
    ]

    operations = [
        migrations.AddField(
            model_name='media',
            name='archive_URI',
            field=models.CharField(default='', max_length=255),
        ),
        migrations.AddField(
            model_name='media',
            name='archive_id',
            field=models.CharField(default='', max_length=255),
        ),
    ]
