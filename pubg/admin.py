from django.contrib import admin

from .models import Player, Match, PlayerMatchStats


class PlayerAdmin(admin.ModelAdmin):
    search_fields = [
        "name",
        "id",
    ]


admin.site.register(Player, PlayerAdmin)
admin.site.register(Match)
admin.site.register(PlayerMatchStats)
