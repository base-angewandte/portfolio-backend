# Generated by Django 2.2.28 on 2022-11-21 10:14

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_auto_20220422_0809'),
    ]

    operations = [
        migrations.AlterField(
            model_name='entry',
            name='data',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=dict),
        ),
    ]
