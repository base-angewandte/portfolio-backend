# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-12-17 14:41
from __future__ import unicode_literals

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_auto_20181029_1650'),
    ]

    operations = [
        migrations.AlterField(
            model_name='entity',
            name='keywords',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=255, verbose_name='keywords'), blank=True, default=list, size=None),
        ),
        migrations.AlterField(
            model_name='entity',
            name='notes',
            field=models.TextField(blank=True, null=True, verbose_name='notes'),
        ),
        migrations.AlterField(
            model_name='entity',
            name='reference',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='reference'),
        ),
        migrations.AlterField(
            model_name='entity',
            name='subtitle',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='subtitle'),
        ),
        migrations.AlterField(
            model_name='entity',
            name='title',
            field=models.CharField(max_length=255, verbose_name='title'),
        ),
        migrations.AlterField(
            model_name='entity',
            name='type',
            field=models.CharField(blank=True, choices=[['Gebäude', 'Gebäude'], ['Bau', 'Bau'], ['Struktur', 'Struktur'], ['Gebäudeentwurf', 'Gebäudeentwurf'], ['Entwurf', 'Entwurf'], ['Design', 'Design'], ['Statik', 'Statik'], ['Podcast', 'Podcast'], ['Radiointerview', 'Radiointerview'], ['Radiofeature', 'Radiofeature'], ['Radiobeitrag', 'Radiobeitrag'], ['Audiobeitrag', 'Audiobeitrag'], ['Reportage', 'Reportage'], ['Hörspiel', 'Hörspiel'], ['Hörbuch', 'Hörbuch'], ['Rundfunkausstrahlung', 'Rundfunkausstrahlung'], ['Wettbewerb', 'Wettbewerb'], ['artist in residence', 'artist in residence'], ['Concert', 'Concert'], ['Keynote', 'Keynote'], ['Konferenzteilnahme', 'Konferenzteilnahme'], ['Präsentation', 'Präsentation'], ['Symposium', 'Symposium'], ['Tagung', 'Tagung'], ['Veranstaltung', 'Veranstaltung'], ['Vortrag', 'Vortrag'], ['Monographie', 'Monographie'], ['Periodikum', 'Periodikum'], ['Sammelband', 'Sammelband'], ['Aufsatzsammlung', 'Aufsatzsammlung'], ['Künstlerbuch', 'Künstlerbuch'], ['Zeitungsbericht', 'Zeitungsbericht'], ['Interview', 'Interview'], ['Artikel', 'Artikel'], ['Kolumne', 'Kolumne'], ['Blog', 'Blog'], ['Ausstellungskatalog', 'Ausstellungskatalog'], ['Katalog', 'Katalog'], ['Rezension', 'Rezension'], ['Kritik', 'Kritik'], ['Kapitel', 'Kapitel'], ['Konferenzschrift', 'Konferenzschrift'], ['Aufsatz', 'Aufsatz'], ['Masterarbeit', 'Masterarbeit'], ['Diplomarbeit', 'Diplomarbeit'], ['Dissertation', 'Dissertation'], ['Bachelorarbeit', 'Bachelorarbeit'], ['Essay', 'Essay'], ['Studie', 'Studie'], ['Einzelausstellung', 'Einzelausstellung'], ['Gruppenausstellung', 'Gruppenausstellung'], ['Festival', 'Festival'], ['Fotografie', 'Fotografie'], ['Gemälde', 'Gemälde'], ['Zeichnung', 'Zeichnung'], ['Collage', 'Collage'], ['Installation', 'Installation'], ['Performance', 'Performance'], ['Theaterstück', 'Theaterstück'], ['Aufführung', 'Aufführung'], ['Intervention', 'Intervention'], ['Research Project', 'Research Project'], ['Sculpture', 'Sculpture'], ['Teaching', 'Teaching'], ['Fernsehbericht', 'Fernsehbericht'], ['Dokumentation', 'Dokumentation'], ['Spielfilm', 'Spielfilm'], ['Film', 'Film'], ['Fernsehbeitrag', 'Fernsehbeitrag'], ['TV-Beitrag', 'TV-Beitrag'], ['Workshop', 'Workshop']], max_length=255, null=True, verbose_name='type'),
        ),
    ]
