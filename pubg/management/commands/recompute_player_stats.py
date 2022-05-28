from django.core.management.base import BaseCommand
from tqdm import tqdm

from pubg.models import Player

class Command(BaseCommand):
    def handle(self, **_):
        for player in tqdm(Player.objects.all()):
            player.compute_stats()
