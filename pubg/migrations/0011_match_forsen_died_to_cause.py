# Generated by Django 4.0.4 on 2022-04-17 17:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pubg", "0010_rename_forsen_died_to_match_forsen_died_to_account"),
    ]

    operations = [
        migrations.AddField(
            model_name="match",
            name="forsen_died_to_cause",
            field=models.CharField(max_length=64, null=True),
        ),
    ]
