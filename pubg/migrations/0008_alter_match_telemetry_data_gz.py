# Generated by Django 4.0.4 on 2022-04-17 14:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pubg', '0007_remove_match_telemetry_url_match_telemetry_data_gz'),
    ]

    operations = [
        migrations.AlterField(
            model_name='match',
            name='telemetry_data_gz',
            field=models.BinaryField(null=True, verbose_name='Telemetry Data'),
        ),
    ]