# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-10-04 08:51
from __future__ import unicode_literals

from django.conf import settings
import django.contrib.postgres.fields
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import general.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Entity',
            fields=[
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_changed', models.DateTimeField(auto_now=True)),
                ('id', general.models.ShortUUIDField(primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=255)),
                ('subtitle', models.CharField(blank=True, max_length=255, null=True)),
                ('type', models.CharField(blank=True, choices=[['Monographie', 'Monographie'], ['Periodikum', 'Periodikum'], ['Sammelband', 'Sammelband'], ['Aufsatzsammlung', 'Aufsatzsammlung'], ['Künstlerbuch', 'Künstlerbuch'], ['Zeitungsbericht', 'Zeitungsbericht'], ['Interview', 'Interview'], ['Artikel', 'Artikel'], ['Kolumne', 'Kolumne'], ['Blog', 'Blog'], ['Ausstellungskatalog', 'Ausstellungskatalog'], ['Katalog', 'Katalog'], ['Rezension', 'Rezension'], ['Kritik', 'Kritik'], ['Kapitel', 'Kapitel'], ['Konferenzschrift', 'Konferenzschrift'], ['Aufsatz', 'Aufsatz'], ['Masterarbeit', 'Masterarbeit'], ['Diplomarbeit', 'Diplomarbeit'], ['Dissertation', 'Dissertation'], ['Bachelorarbeit', 'Bachelorarbeit'], ['Essay', 'Essay'], ['Studie', 'Studie']], max_length=255, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('reference', models.CharField(blank=True, max_length=255, null=True)),
                ('keywords', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=255), blank=True, default=list, size=None)),
                ('data', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-date_created',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Relation',
            fields=[
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_changed', models.DateTimeField(auto_now=True)),
                ('id', general.models.ShortUUIDField(primary_key=True, serialize=False)),
                ('from_entity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='from_entities', to='core.Entity')),
                ('to_entity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='to_entities', to='core.Entity')),
            ],
        ),
        migrations.AddField(
            model_name='entity',
            name='relations',
            field=models.ManyToManyField(related_name='related_to', through='core.Relation', to='core.Entity'),
        ),
        migrations.AlterUniqueTogether(
            name='relation',
            unique_together=set([('from_entity', 'to_entity')]),
        ),
    ]
