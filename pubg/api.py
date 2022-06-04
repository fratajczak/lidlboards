import requests
from pprint import pprint
from os import getenv

API_URL = "https://api.pubg.com/shards/steam/"
API_KEY = getenv("PUBG_API_KEY")
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Accept": "application/vnd.api+json"}


class APIError(Exception):
    pass


def get_player_info(id: str) -> dict:
    url = API_URL + "players/" + id
    req = requests.get(url, headers=HEADERS)

    if req.status_code == 200:
        return req.json()
    else:
        raise APIError(req.status_code, req.content)


def get_match_info(id: str) -> dict:
    url = API_URL + "matches/" + id
    req = requests.get(url, headers=HEADERS)

    if req.status_code == 200:
        return req.json()
    else:
        raise APIError(req.status_code, req.content)


def get_telemetry_data(telemetry_url: str) -> bytes:
    req = requests.get(telemetry_url, headers=HEADERS)

    if req.status_code == 200:
        return req.content
    else:
        raise APIError(req.status_code, req.content)
