from django.urls import path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path("", RedirectView.as_view(url="rankings/")),
    path("rankings/", views.all_rankings_view, name="index"),
    path("player_list/", views.all_rankings_view, name="player_list"),
    path("search/", views.player_search, name="player_search"),
    path("player/<account_id>/", views.player_view, name="player_view"),
]
