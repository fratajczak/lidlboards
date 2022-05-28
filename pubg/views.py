from django.core.paginator import Paginator
from django.db.models import Avg, Case, F, FloatField, ExpressionWrapper, When
from django.shortcuts import render
from django.templatetags.static import static
from django.utils.safestring import mark_safe
from django.views.generic.base import TemplateView

import django_tables2 as tables

from pubg.models import Match, Player, PlayerMatchStats 

class OnePagePaginator(Paginator):
    def __init__(self, object_list, per_page, orphans=0, allow_empty_first_page=True):
        super().__init__(object_list, per_page, orphans, allow_empty_first_page)
        self.num_pages = 1

def get_icon_html(icon_name):
    return mark_safe(f'<img src="{static("pubg/icons/" + icon_name)}" width="48">')

class PlayerKillScoreTable(tables.Table):
    name = tables.Column()
    killscore = tables.Column('Kill score')
    kills= tables.Column('Total')
    vehicle_explosion = tables.Column(get_icon_html('Vehicle_Explosion.png'), empty_values=())
    punch = tables.Column(get_icon_html('Punch.png'), empty_values=())
    c4 = tables.Column(get_icon_html('Item_Weapon_C4_C.png'), empty_values=())
    molotov = tables.Column(get_icon_html('Item_Weapon_Molotov_C.png'), empty_values=())
    grenade = tables.Column(get_icon_html('Item_Weapon_Grenade_C.png'), empty_values=())
    throw = tables.Column(get_icon_html('Melee_Throw.png'), empty_values=())
    vehicle = tables.Column(get_icon_html('Vehicle.png'), empty_values=())
    panzerfaust = tables.Column(get_icon_html('Item_Weapon_PanzerFaust100M_C.png'), empty_values=())
    gun = tables.Column(get_icon_html('Item_Weapon_AK47_C.png'), empty_values=())


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def render_vehicle_explosion(self, **kwargs):
        player = kwargs['record']
        return PlayerMatchStats.objects.filter(player=player, killed_forsen_with='Damage_Explosion_Vehicle').count()

    def render_punch(self, **kwargs):
        player = kwargs['record']
        return PlayerMatchStats.objects.filter(player=player, killed_forsen_with__in=('Damage_Punch', 'Damage_Melee')).count()

    def render_c4(self, **kwargs):
        player = kwargs['record']
        return PlayerMatchStats.objects.filter(player=player, killed_forsen_with='Damage_Explosion_C4').count()

    def render_molotov(self, **kwargs):
        player = kwargs['record']
        return PlayerMatchStats.objects.filter(player=player, killed_forsen_with='Damage_Molotov').count()

    def render_grenade(self, **kwargs):
        player = kwargs['record']
        return PlayerMatchStats.objects.filter(player=player, killed_forsen_with='Damage_Explosion_Grenade').count()

    def render_throw(self, **kwargs):
        player = kwargs['record']
        return PlayerMatchStats.objects.filter(player=player, killed_forsen_with='Damage_MeleeThrow').count()

    def render_vehicle(self, **kwargs):
        player = kwargs['record']
        return PlayerMatchStats.objects.filter(player=player, killed_forsen_with='Damage_VehicleHit').count()

    def render_panzerfaust(self, **kwargs):
        player = kwargs['record']
        return PlayerMatchStats.objects.filter(player=player, killed_forsen_with='Damage_Explosion_PanzerFaustWarhead').count()

    def render_gun(self, **kwargs):
        player = kwargs['record']
        return PlayerMatchStats.objects.filter(player=player, killed_forsen_with='Damage_Gun').count()
    #def render_avg(self, **kwargs):
    #    player = kwargs['record']
    #    avg = PlayerMatchStats.objects.filter(player=player, killscore__gt=0).aggregate(Avg('forsen_final_rank'))['forsen_final_rank__avg']
    #    return f'{avg:.2f}'

    #def order_avg(self, queryset, is_descending):
    #    queryset = queryset.annotate(avg=Case(
    #        When(games_sniped=0, then=0.0),
    #        default=ExpressionWrapper(F('deaths') * 1.0 / F('games_sniped'), output_field=FloatField())
    #        )).order_by(("-" if is_descending else "") + "avg")
    #    return queryset, True

    class Meta:
        model = Player
        exclude = ('id', 'is_forsen', 'deaths', 'games_sniped')
        sequence = ('name', 'killscore', '...', 'kills')


class PlayerKDTable(tables.Table):
    name = tables.Column(attrs={'th': {'width': '55%'}})
    kd = tables.Column('K/D', attrs={'th': {'width': '15%'}})
    kills = tables.Column(attrs={'th': {'width': '15%'}})
    deaths = tables.Column(attrs={'th': {'width': '15%'}})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def render_kd(self, **kwargs):
        player = kwargs['record']
        return f'{0 if player.deaths == 0 else player.kills / player.deaths:.2f}'

    def order_kd(self, queryset, is_descending):
        queryset = queryset.annotate(kd=Case(
            When(deaths=0, then=0.0),
            default=ExpressionWrapper(F('kills') * 1.0 / F('deaths'), output_field=FloatField())
            )).order_by(("-" if is_descending else "") + "kd", "-deaths")
        return queryset, True

    class Meta:
        model = Player
        exclude = ('id', 'is_forsen', 'games_sniped', 'killscore')


class PlayerDeathTable(tables.Table):
    name = tables.Column(attrs={'th': {'width': '55%'}})
    dpg = tables.Column('Deaths per game', attrs={'th': {'width': '15%'}})
    deaths = tables.Column(attrs={'th': {'width': '15%'}})
    games_sniped = tables.Column('Games', attrs={'th': {'width': '15%'}})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def render_dpg(self, **kwargs):
        player = kwargs['record']
        return f'{0 if player.games_sniped == 0 else player.deaths / player.games_sniped:.2f}'

    def order_dpg(self, queryset, is_descending):
        queryset = queryset.annotate(dpg=Case(
            When(games_sniped=0, then=0.0),
            default=ExpressionWrapper(F('deaths') * 1.0 / F('games_sniped'), output_field=FloatField())
            )).order_by(("-" if is_descending else "") + "dpg")
        return queryset, True

    class Meta:
        model = Player
        exclude = ('id', 'is_forsen', 'kills', 'killscore')


class PlayerKillTable(tables.Table):
    name = tables.Column(attrs={'th': {'width': '35%'}})
    kills = tables.Column(attrs={'th': {'width': '15%'}})
    games_sniped = tables.Column('Games', attrs={'th': {'width': '15%'}})
    kpg = tables.Column('Kills per game', attrs={'th': {'width': '35%'}})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def render_kpg(self, **kwargs):
        player = kwargs['record']
        gpk = f'{0 if player.kills == 0 else player.games_sniped / player.kills:.1f}'

        return mark_safe(f'1 in <b style="color: #f0f6fc">{gpk}</b>')

    def order_kpg(self, queryset, is_descending):
        queryset = queryset.annotate(kpg=Case(
            When(games_sniped=0, then=0.0),
            default=ExpressionWrapper(F('kills') * 1.0 / F('games_sniped'), output_field=FloatField())
            )).order_by(("-" if is_descending else "") + "kpg")
        return queryset, True

    class Meta:
        model = Player
        exclude = ('id', 'is_forsen', 'deaths', 'killscore')


def all_rankings_view(request):
    config = tables.RequestConfig(request, paginate={'paginator_class': OnePagePaginator})
    visible = {'class': 'table-container visible'}

    table_killscore = PlayerKillScoreTable(Player.objects.all(), attrs=visible)
    table_killscore.order_by = '-killscore'
    table_killscore.orderable = False
    config.configure(table_killscore)

    players_more_than_10_interactions = Player.objects.annotate(interactions=(F('deaths') + F('kills'))).filter(interactions__gt=10)

    table_best_kd = PlayerKDTable(players_more_than_10_interactions, attrs=visible)
    table_best_kd.order_by = '-kd'
    table_best_kd.orderable = False
    config.configure(table_best_kd)
    
    table_worst_kd = PlayerKDTable(players_more_than_10_interactions)
    table_worst_kd.order_by = 'kd'
    table_worst_kd.orderable = False
    config.configure(table_worst_kd)

    table_most_kills = PlayerKillTable(Player.objects.all(), exclude=('games_sniped', 'kpg'))
    table_most_kills.order_by = '-kills'
    table_most_kills.orderable = False
    config.configure(table_most_kills)

    table_most_kills_per_game = PlayerKillTable(players_more_than_10_interactions)
    table_most_kills_per_game.order_by = '-kpg'
    table_most_kills_per_game.orderable = False
    config.configure(table_most_kills_per_game)

    # Deaths section
    table_least_deaths_per_game = PlayerDeathTable(players_more_than_10_interactions, attrs=visible)
    table_least_deaths_per_game.order_by = 'dpg'
    table_least_deaths_per_game.orderable = False
    config.configure(table_least_deaths_per_game)

    table_most_deaths_per_game = PlayerDeathTable(players_more_than_10_interactions)
    table_most_deaths_per_game.order_by = '-dpg'
    table_most_deaths_per_game.orderable = False
    config.configure(table_most_deaths_per_game)

    table_most_deaths = PlayerDeathTable(players_more_than_10_interactions, exclude=('games_sniped', 'dpg'))
    table_most_deaths.order_by = '-deaths'
    table_most_deaths.orderable = False
    config.configure(table_most_deaths)

    # Games section
    table_most_games = PlayerDeathTable(players_more_than_10_interactions, exclude=('deaths', 'dpg'), attrs=visible)
    table_most_games.order_by = '-games_sniped'
    table_most_games.orderable = False
    config.configure(table_most_games)

    context = {
            'table_killscore': table_killscore,
            'table_best_kd': table_best_kd,
            'table_worst_kd': table_worst_kd,
            'table_most_kills': table_most_kills,
            'table_most_kills_per_game': table_most_kills_per_game,
            'table_most_deaths': table_most_deaths,
            'table_most_deaths_per_game': table_most_deaths_per_game,
            'table_least_deaths_per_game': table_least_deaths_per_game,
            'table_most_games': table_most_games,
            'nb_games': Match.objects.all().count(),
            'first_game_date': Match.objects.all().order_by('created_at')[0].created_at,
            'last_game_date': Match.objects.all().order_by('-created_at')[0].created_at,
    }

    return(render(request, "pubg/player_list.html", context))

def index(request):
    return(render(request, 'pubg/index.html', {}))