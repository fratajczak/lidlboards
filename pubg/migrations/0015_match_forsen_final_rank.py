# Generated by Django 4.0.4 on 2022-05-28 10:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pubg", "0014_alter_website_last_update"),
    ]

    operations = [
        migrations.AddField(
            model_name="match",
            name="forsen_final_rank",
            field=models.IntegerField(null=True),
        ),
    ]
