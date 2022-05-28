from dateutil.parser import isoparse
from django.db import models
from math import log
import datetime
import gzip
import json
import logging

import pubg.api 

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

FORSEN_PLAYERID = "account.9f8afe4c244e4290abb265d6864eac3e"

KILLSCORE_WEAPON_MULTIPLIERS = {
    'Damage_Explosion_Vehicle': 10,
    'Damage_Melee': 5,
    'Damage_Punch': 5,
    'Damage_Explosion_C4': 3,
    'Damage_Molotov': 3,
    'Damage_Explosion_Grenade': 1.5,
    'Damage_MeleeThrow': 1.5,
    'Damage_VehicleHit': 1,
    'Damage_Explosion_PanzerFaustWarhead': 0.1,
    'Damage_Gun': 0.5, # Only in top 5 
    
}

class Website(models.Model):
    last_update = models.DateTimeField(default=datetime.datetime(2022, 1, 1))

class PlayerMatchStats(models.Model):
    """
    Stats for 1 player during 1 match
    """
    player = models.ForeignKey('Player', on_delete=models.CASCADE)
    match = models.ForeignKey('Match', on_delete=models.CASCADE)
    damage_dealt = models.IntegerField('Damage dealt', null=True)
    ride_distance = models.IntegerField('Distance in vehicles', null=True)
    walk_distance = models.IntegerField('Distance walked', null=True)
    time_survived = models.IntegerField('Time survived', null=True)
    killed_forsen_with = models.CharField(max_length=64, null=True)
    killed_by_forsen_with = models.CharField(max_length=64, null=True)
    damage_to_forsen = models.IntegerField('Damage dealt to forsen', null=True)
    forsen_final_rank = models.IntegerField(null=True)
    killscore = models.IntegerField(default=0)

    class Meta:
        unique_together = ('player', 'match')

    def compute_killscore(self):
        if self.killed_forsen_with == 'Damage_Gun' and self.forsen_final_rank > 5:
            # Gunfrogs out!
            return 0
        x = self.forsen_final_rank
        #base_kill_value = 2*(100-x)**2 + 1.11**(100-x) + 1000
        base_kill_value = 44682 + -9389 * log(x)
        multiplier = KILLSCORE_WEAPON_MULTIPLIERS.get(self.killed_forsen_with)
        if multiplier is None:
                logger.warning(f'Unhandled killscore multiplier for {self.killed_forsen_with} in match {self.match}')
                return base_kill_value
        return multiplier * base_kill_value


class Match(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    duration = models.IntegerField(null=True)
    created_at = models.DateTimeField('Date', null=True)
    map_name = models.CharField('Map name', max_length=64, null=True)
    nb_bots = models.IntegerField('Number of bots', null=True)
    nb_real_players = models.IntegerField('Number of real players', null=True)
    is_forsen_match = models.BooleanField(default=False)
    forsen_died_to_account = models.CharField(max_length=64, null=True) #idAccount
    forsen_died_to_cause = models.CharField(max_length=64, null=True) #idAccount
    forsen_final_rank = models.IntegerField(null=True)
    nb_forsen_kills = models.IntegerField(null=True)
    nb_forsen_bot_kills = models.IntegerField(null=True)
    telemetry_data_gz = models.BinaryField('Telemetry Data', null=True)

    def __str__(self):
        return self.id

    def update_from_api(self):
        """
        Get info from the PUBG API for a match
        Can fail and raise pubg.api.APIError
        """
        match_info = pubg.api.get_match_info(self.id)

        data = match_info['data']['attributes']
        self.created_at = isoparse(data['createdAt'])
        self.map_name = data['mapName']

        self.nb_bots = 0
        self.nb_real_players = 0
        included = match_info['included']
        telemetry_url = ''
        for entry in included:
            match entry['type']:
                case 'roster':
                    continue
                case 'asset':
                    if entry['attributes']['name'] == 'telemetry':
                        telemetry_url = entry['attributes']['URL']
                case 'participant':
                    player_stats = entry['attributes']['stats']

                    if player_stats['playerId'].startswith('ai.'):
                        self.nb_bots += 1
                        continue
                    elif player_stats['playerId'].startswith('npc.'):
                        continue
                    else:
                        self.nb_real_players += 1

                    player, created = Player.objects.get_or_create(id=player_stats['playerId'])
                    if created:
                        player.name = player_stats['name']
                        player.save()

                    if player.id == FORSEN_PLAYERID:
                        self.is_forsen_match = True

                    player_match_stats, _ = PlayerMatchStats.objects.get_or_create(player=player, match=self)
                    player_match_stats.damage_dealt = player_stats['damageDealt']
                    player_match_stats.ride_distance = player_stats['rideDistance']
                    player_match_stats.walk_distance = player_stats['walkDistance']
                    player_match_stats.time_survived = player_stats['timeSurvived']
                    player_match_stats.save()
                case _:
                    logger.warning(f"Type {entry['type']} is not handled")
        if telemetry_url and not self.telemetry_data_gz:
            try:
                telemetry_data = pubg.api.get_telemetry_data(telemetry_url)
                self.telemetry_data_gz = gzip.compress(telemetry_data)
                self.update_from_telemetry(telemetry_data=telemetry_data)
            except:
                logger.warning(f'Could not get telemetry for match {self.id}')
        elif self.telemetry_data_gz:
            self.update_from_telemetry()
        self.save()

    def update_stats_LogPlayerKillV2(self, telemetry_obj: dict):
        damage_type_category = telemetry_obj['killerDamageInfo']['damageTypeCategory']
        if damage_type_category == 'Damage_Explosion_StickyBomb':
            damage_type_category = 'Damage_Explosion_C4'
        self.forsen_died_to_cause = damage_type_category
        self.save()

        victim_accountid = telemetry_obj['victim']['accountId']
        if victim_accountid.startswith('npc.'):
            return
        if victim_accountid.startswith('ai.'):
            self.nb_forsen_bot_kills += 1
            self.nb_forsen_kills += 1
            self.save()
            return

        victim = Player.objects.get(id=victim_accountid)
        victim_stats = PlayerMatchStats.objects.get(match=self, player=victim)

        if telemetry_obj['isSuicide']:
            # Forsen killed himself LUL
            victim_stats.killed_by_forsen_with = damage_type_category
            victim_stats.killed_forsen_with = damage_type_category
            victim_stats.save()
            return

        if victim.id == FORSEN_PLAYERID:
            self.forsen_final_rank = telemetry_obj['victimGameResult']['rank']
            if telemetry_obj['killer']:
                killer_accountid = telemetry_obj['killer'].get('accountId')
            else:
                # Died to e.g vehicle without driver
                return
            self.forsen_died_to_account = killer_accountid
            self.save()
            if killer_accountid.startswith('npc.') or killer_accountid.startswith('ai.'):
                return
            killer = Player.objects.get(id=killer_accountid)
            killer_stats = PlayerMatchStats.objects.get(match=self, player=killer)
            killer_stats.killed_forsen_with = damage_type_category
            killer_stats.forsen_final_rank = telemetry_obj['victimGameResult']['rank']
            killer_stats.killscore = killer_stats.compute_killscore()
            killer_stats.save()
        else: #killer is forsen
            self.nb_forsen_kills += 1
            self.save()
            victim_stats.killed_by_forsen_with = damage_type_category
            victim_stats.save()


    def update_stats_LogPlayerTakeDamage(self, telemetry_obj: dict):
        if telemetry_obj['attacker'] is None:
            # Forsen damaged himself LUL
            return

        attacker_accountid = telemetry_obj['attacker']['accountId']
        if attacker_accountid.startswith('ai.') or attacker_accountid.startswith('npc.'):
            return

        attacker = Player.objects.get(id=attacker_accountid)
        attacker_stats = PlayerMatchStats.objects.get(match=self, player=attacker)
        attacker_stats.damage_to_forsen += telemetry_obj['damage']
        attacker_stats.save()


    def update_stats_LogVehicleRide(self, telemetry_obj: dict):
        pass

    def reset_all_incrementable_stats(self):
        """
        Reset every player's incrementable stats for this match
        """
        if self.is_forsen_match:
            self.nb_forsen_kills = 0
            self.nb_forsen_bot_kills = 0
        for player_match_stats in PlayerMatchStats.objects.filter(match=self):
            player_match_stats.damage_to_forsen = 0
            player_match_stats.save()
        self.save()


    def update_from_telemetry(self, telemetry_data=None) -> bool:
        """
        Get the telemetry info for a match and update stats
        Can fail and raise pubg.api.APIError
        """
        def attacker_is_forsen(telemetry_obj: dict) -> bool:
            attacker = telemetry_obj.get('attacker') or telemetry_obj.get('killer')
            return attacker is not None and attacker['accountId'] == FORSEN_PLAYERID

        def victim_is_forsen(telemetry_obj: dict) -> bool:
            return telemetry_obj['victim']['accountId'] == FORSEN_PLAYERID

        def is_forsen_related(telemetry_obj: dict) -> bool:
            if (fellow_passengers := telemetry_obj.get('fellowPassengers')) is not None:
                # LogVehicleRide
                return (telemetry_obj['character']['accountId'] == FORSEN_PLAYERID
                         or any([passenger['accountId'] == FORSEN_PLAYERID for passenger in fellow_passengers]))
            return attacker_is_forsen(telemetry_obj) or victim_is_forsen(telemetry_obj)

        if telemetry_data is None:
            if self.telemetry_data_gz:
                telemetry_data = gzip.decompress(self.telemetry_data_gz)
            else:
                return False

        self.reset_all_incrementable_stats()

        telemetry_json = json.loads(telemetry_data)
        for telemetry_obj in telemetry_json:
            match telemetry_obj['_T']:
                case 'LogPlayerKillV2' if is_forsen_related(telemetry_obj):
                    self.update_stats_LogPlayerKillV2(telemetry_obj)
                    if victim_is_forsen(telemetry_obj):
                    # We don't care about stats after forsen dies
                        return True
                case 'LogPlayerTakeDamage' if victim_is_forsen(telemetry_obj):
                    self.update_stats_LogPlayerTakeDamage(telemetry_obj)
                case 'LogVehicleRide' if is_forsen_related(telemetry_obj):
                    self.update_stats_LogVehicleRide(telemetry_obj)

        return True


class Player(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    name = models.CharField(max_length=16)
    matches = models.ManyToManyField(Match, through='PlayerMatchStats')
    is_forsen = models.BooleanField(default=False)
    kills = models.IntegerField(default=0)
    deaths = models.IntegerField(default=0)
    games_sniped = models.IntegerField(default=0)
    killscore = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    def update_from_api(self):
        """
        Get info from the PUBG API for a player (name + all matches):
        Can fail and raise pubg.api.APIError
        """
        player_info = pubg.api.get_player_info(self.id)['data']
        self.name = player_info['attributes']['name']
        self.save()

        for match_data in player_info['relationships']['matches']['data']:
            if match_data['type'] == 'match':
                match, _ = Match.objects.get_or_create(id = match_data['id'])
                PlayerMatchStats.objects.get_or_create(player=self, match=match)

    def compute_stats(self):
        if self.is_forsen:
            return
        pms_with_forsen_kills = PlayerMatchStats.objects.filter(player=self, killscore__gt=0)
        self.killscore = sum(pms_with_forsen_kills.values_list('killscore', flat=True))
        self.kills = len(pms_with_forsen_kills)
        self.deaths = PlayerMatchStats.objects.filter(player=self, killed_by_forsen_with__isnull=False).count()
        self.games_sniped = PlayerMatchStats.objects.filter(player=self, match__is_forsen_match=True).count()
        self.save()
