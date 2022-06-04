import datetime
import logging
import sys
from django.core.management.base import BaseCommand
from django.utils import timezone
from tqdm import tqdm

from pubg.models import Player, PlayerMatchStats, Match, Website
from pubg import FORSEN_PLAYERID

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.INFO)
logger.addHandler(stdout_handler)


class Command(BaseCommand):
    def handle(self, **_):
        forsen = Player.objects.get(id=FORSEN_PLAYERID)
        forsen.update_from_api()

        logger.info("Getting info from new games...")
        new_matches = Match.objects.filter(created_at__isnull=True)
        new_match_ids = []

        for match in tqdm(new_matches):
            match.update_from_api()
            new_match_ids.append(match.id)
        logger.info(f"Got info from {len(new_matches)} new games")

        print(f"Recomputing player stats...")
        players_to_update_list = (
            PlayerMatchStats.objects.filter(match__in=new_match_ids)
            .values_list("player", flat=True)
            .distinct()
        )
        players_to_update = Player.objects.filter(id__in=players_to_update_list)
        for player in tqdm(players_to_update):
            player.compute_stats()
        logger.info(f"Recomputed stats for {len(players_to_update)} players")

        website, _ = Website.objects.get_or_create(pk=1)
        website.last_update = timezone.now()
        website.save()
