from pubg.models import Website

def add_website_stats_to_context(_):
    return {
        'update_datetime': Website.objects.get(pk=1).last_update,
    }
