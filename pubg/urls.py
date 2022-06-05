from django.urls import path

from . import views

urlpatterns = [
    path("rankings/", views.all_rankings_view, name="index"),
    path("player_list/", views.all_rankings_view, name="player_list"),
    path("search/", views.player_search, name="player_search"),
]
