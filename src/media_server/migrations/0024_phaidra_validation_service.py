from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('media_server', '0023_auto_20230822_1854'),
    ]

    operations = [
        migrations.AddField(
            model_name='media',
            name='archive_URI',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='media',
            name='archive_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='media',
            name='archive_status',
            field=models.IntegerField(
                choices=[(0, 'not archived'), (1, 'to be archived'), (2, 'archival in progress'), (3, 'archived'),
                         (4, 'error'), (5, 'archival update in queue')], default=0),
        ),
        migrations.AddField(
            model_name='media',
            name='archive_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
