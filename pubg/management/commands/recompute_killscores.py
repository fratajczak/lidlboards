from django.core.management.base import BaseCommand
from tqdm import tqdm

from pubg.models import Player, PlayerMatchStats


class Command(BaseCommand):
    def handle(self, **_):
        pms_with_forsen_kills = PlayerMatchStats.objects.filter(
            killed_forsen_with__isnull=False, forsen_final_rank__isnull=False
        )
        print("Recomputing match killscores...")
        for pms in tqdm(pms_with_forsen_kills):
            pms.killscore = pms.compute_killscore()
            pms.save()
        print("Recomputing player killscores...")
        for player in tqdm(Player.objects.all()):
            player.compute_stats()
