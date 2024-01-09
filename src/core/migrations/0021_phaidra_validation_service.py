from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_auto_20230822_1854'),
    ]

    operations = [
        migrations.AddField(
            model_name='entry',
            name='archive_URI',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='entry',
            name='archive_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='entry',
            name='archive_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
