# Generated by Django 4.0.4 on 2022-05-28 12:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pubg', '0016_playermatchstats_forsen_final_rank_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='killscore',
            field=models.IntegerField(default=0),
        ),
    ]