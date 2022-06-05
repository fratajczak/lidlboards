from pubg.models import Website
from pubg.forms import PlayerSearchForm


def add_website_stats_to_context(_):
    return {
        "update_datetime": Website.objects.get(pk=1).last_update,
    }


def add_player_search_form_to_context(_):
    return {
        "player_search_form": PlayerSearchForm(),
    }
