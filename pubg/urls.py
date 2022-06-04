from django.urls import path

from . import views

urlpatterns = [
    path("", views.all_rankings_view, name="index"),
    path("player_list/", views.all_rankings_view, name="player_list"),
]
