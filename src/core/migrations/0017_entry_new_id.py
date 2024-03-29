# Generated by Django 2.2.21 on 2021-07-12 15:34

from django.db import migrations, models


def set_new_id(apps, schema_editor):
    Entry = apps.get_model('core', 'Entry')
    Relation = apps.get_model('core', 'Relation')
    for e in Entry.objects.all():
        new_id = e.id[::-1]
        Relation.objects.filter(from_entry=e.id).update(from_entry=new_id)
        Relation.objects.filter(to_entry=e.id).update(to_entry=new_id)
        Entry.objects.filter(id=e.id).update(id=new_id, date_changed=e.date_changed)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_auto_20190806_1131'),
    ]

    operations = [
        migrations.RunPython(code=set_new_id, reverse_code=set_new_id),
    ]
