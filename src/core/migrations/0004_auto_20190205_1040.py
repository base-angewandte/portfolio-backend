# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-02-05 09:40
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_auto_20181217_1541'),
    ]

    operations = [
        migrations.AlterField(
            model_name='entity',
            name='type',
            field=models.CharField(blank=True, choices=[['Gebäude', 'Gebäude'], ['Bau', 'Bau'], ['Struktur', 'Struktur'], ['Architekturdesign', 'Architekturdesign'], ['Statik', 'Statik'], ['Architekturmodell', 'Architekturmodell'], ['Architekturentwurf', 'Architekturentwurf'], ['Architekturprojekt', 'Architekturprojekt'], ['Podcast', 'Podcast'], ['Radiointerview', 'Radiointerview'], ['Radiofeature', 'Radiofeature'], ['Radiobeitrag', 'Radiobeitrag'], ['Audiobeitrag', 'Audiobeitrag'], ['Reportage', 'Reportage'], ['Hörspiel', 'Hörspiel'], ['Hörbuch', 'Hörbuch'], ['Rundfunkausstrahlung', 'Rundfunkausstrahlung'], ['Radiokunst', 'Radiokunst'], ['Konzertmitschnitt', 'Konzertmitschnitt'], ['Studioeinspielung', 'Studioeinspielung'], ['Tonaufnahme', 'Tonaufnahme'], ['Audioaufzeichnung', 'Audioaufzeichnung'], ['mp3', 'mp3'], ['Kammermusik CD', 'Kammermusik CD'], ['CD Aufnahme', 'CD Aufnahme'], ['Album', 'Album'], ['CD-Box', 'CD-Box'], ['Wettbewerb', 'Wettbewerb'], ['artist in residence', 'artist in residence'], ['Preis', 'Preis'], ['Auszeichnung', 'Auszeichnung'], ['Nominierung', 'Nominierung'], ['Generalprobe', 'Generalprobe'], ['Soundperformance', 'Soundperformance'], ['Konzert', 'Konzert'], ['Keynote', 'Keynote'], ['Konferenzteilnahme', 'Konferenzteilnahme'], ['Präsentation', 'Präsentation'], ['Symposium', 'Symposium'], ['Tagung', 'Tagung'], ['Konferenz', 'Konferenz'], ['Vortrag', 'Vortrag'], ['Talk', 'Talk'], ['Lesung', 'Lesung'], ['Gespräch', 'Gespräch'], ['Artistic Research Meeting', 'Artistic Research Meeting'], ['Podiumsdiskussion', 'Podiumsdiskussion'], ['Projektpräsentation', 'Projektpräsentation'], ['Künstler / innengesprächlecture performance', 'Künstler / innengesprächlecture performance'], ['Monographie', 'Monographie'], ['Periodikum', 'Periodikum'], ['Sammelband', 'Sammelband'], ['Aufsatzsammlung', 'Aufsatzsammlung'], ['Künstlerbuch', 'Künstlerbuch'], ['Zeitungsbericht', 'Zeitungsbericht'], ['Interview', 'Interview'], ['Zeitungsartikel', 'Zeitungsartikel'], ['Kolumne', 'Kolumne'], ['Blog', 'Blog'], ['Ausstellungskatalog', 'Ausstellungskatalog'], ['Katalog', 'Katalog'], ['Rezension', 'Rezension'], ['Kritik', 'Kritik'], ['Beitrag in Sammelband', 'Beitrag in Sammelband'], ['Aufsatz', 'Aufsatz'], ['Beitrag in Fachzeitschrift (SCI,  SSCI, A&HCI)', 'Beitrag in Fachzeitschrift (SCI,  SSCI, A&HCI)'], ['Masterarbeit', 'Masterarbeit'], ['Diplomarbeit', 'Diplomarbeit'], ['Dissertation', 'Dissertation'], ['Bachelorarbeit', 'Bachelorarbeit'], ['Essay', 'Essay'], ['Studie', 'Studie'], ['Tagungsbericht', 'Tagungsbericht'], ['Kommentar', 'Kommentar'], ['Fanzine', 'Fanzine'], ['Buchreihe', 'Buchreihe'], ['Schriftenreihe', 'Schriftenreihe'], ['Edition', 'Edition'], ['Drehbuch', 'Drehbuch'], ['Libretto', 'Libretto'], ['Gutachten', 'Gutachten'], ['Clipping', 'Clipping'], ['Zeitschrift', 'Zeitschrift'], ['Magazin', 'Magazin'], ['Archivalie', 'Archivalie'], ['Printbeitrag', 'Printbeitrag'], ['Onlinebeitrag', 'Onlinebeitrag'], ['wissenschaftliche Veröffentlichung', 'wissenschaftliche Veröffentlichung'], ['künstlerische Veröffentlichung', 'künstlerische Veröffentlichung'], ['Katalog/künstlerisches Druckwerk', 'Katalog/künstlerisches Druckwerk'], ['künstlerischer Ton-/Bild-/Datenträger', 'künstlerischer Ton-/Bild-/Datenträger'], ['Beitrag zu künstlerischem Ton-/Bild-/Datenträger', 'Beitrag zu künstlerischem Ton-/Bild-/Datenträger'], ['Auslandsaufenthalt', 'Auslandsaufenthalt'], ['Buchpräsentation', 'Buchpräsentation'], ['Premiere', 'Premiere'], ['Screening', 'Screening'], ['Sneak Preview', 'Sneak Preview'], ['Filmvorführung', 'Filmvorführung'], ['Vorschau', 'Vorschau'], ['Release', 'Release'], ['Vorpremiere', 'Vorpremiere'], ['Vorführung', 'Vorführung'], ['Pressevorführung', 'Pressevorführung'], ['Pressekonferenz', 'Pressekonferenz'], ['ExpertInnentätigkeit', 'ExpertInnentätigkeit'], ['Live-Präsentation', 'Live-Präsentation'], ['Medienbeitrag', 'Medienbeitrag'], ['Veranstaltung', 'Veranstaltung'], ['Arbeitsschwerpunkt/laufendes Projekt', 'Arbeitsschwerpunkt/laufendes Projekt'], ['Einzelausstellung', 'Einzelausstellung'], ['Gruppenausstellung', 'Gruppenausstellung'], ['Vernissage', 'Vernissage'], ['Finissage', 'Finissage'], ['Messe-Präsentation', 'Messe-Präsentation'], ['Retrospektive', 'Retrospektive'], ['Soloausstellung', 'Soloausstellung'], ['Werkschau', 'Werkschau'], ['Festival', 'Festival'], ['Fotografie', 'Fotografie'], ['Gemälde', 'Gemälde'], ['Zeichnung', 'Zeichnung'], ['Collage', 'Collage'], ['Druckgrafik', 'Druckgrafik'], ['Ausstellungsansicht', 'Ausstellungsansicht'], ['Werkabbildung', 'Werkabbildung'], ['Videostill', 'Videostill'], ['Mixed Media', 'Mixed Media'], ['Kunst am Bau', 'Kunst am Bau'], ['Drittmittelprojekt', 'Drittmittelprojekt'], ['Projekt', 'Projekt'], ['Forschungsprojekt', 'Forschungsprojekt'], ['Artistic Research', 'Artistic Research'], ['Installation', 'Installation'], ['Auftragsarbeit', 'Auftragsarbeit'], ['Kunst im öffentlichen Raum', 'Kunst im öffentlichen Raum'], ['Skulptur', 'Skulptur'], ['Plastik', 'Plastik'], ['Keramik', 'Keramik'], ['Textil', 'Textil'], ['Schmuck', 'Schmuck'], ['Fernsehbericht', 'Fernsehbericht'], ['Dokumentation', 'Dokumentation'], ['Spielfilm', 'Spielfilm'], ['Film', 'Film'], ['Fernsehbeitrag', 'Fernsehbeitrag'], ['TV-Beitrag', 'TV-Beitrag'], ['Kurzfilm', 'Kurzfilm'], ['Videoaufzeichnung', 'Videoaufzeichnung'], ['Video', 'Video'], ['Videoarbeit', 'Videoarbeit'], ['Filmarbeit', 'Filmarbeit'], ['Animationsfilm', 'Animationsfilm'], ['Experimentalfilm', 'Experimentalfilm'], ['Trailer', 'Trailer'], ['Dokumentarfilm', 'Dokumentarfilm'], ['DVD und Blu Ray', 'DVD und Blu Ray'], ['Lehrvideo-Einleitung', 'Lehrvideo-Einleitung'], ['Lehrvideo', 'Lehrvideo'], ['DVD', 'DVD'], ['Vimeo Video', 'Vimeo Video'], ['Zeitbasierte Medien', 'Zeitbasierte Medien'], ['Kinderunikunst', 'Kinderunikunst'], ['Weiterbildung', 'Weiterbildung'], ['Kurs', 'Kurs'], ['Seminar', 'Seminar'], ['postgraduales Studienangebot', 'postgraduales Studienangebot'], ['Doktoratsstudium', 'Doktoratsstudium'], ['Einzelcoaching', 'Einzelcoaching'], ['individuelle Maßnahme', 'individuelle Maßnahme'], ['projektorientierte Lehrtätigkeit', 'projektorientierte Lehrtätigkeit'], ['Interdisziplinäre Lehrtätigkeit', 'Interdisziplinäre Lehrtätigkeit'], ['Interdisziplinäre / projektorientierte Lehrtätigkeit', 'Interdisziplinäre / projektorientierte Lehrtätigkeit']], max_length=255, null=True, verbose_name='type'),
        ),
    ]
