import os
import json
import requests
from config import TBA_KEY, CACHE_FOLDER

BASE = "https://www.thebluealliance.com/api/v3"
HEADERS = {"X-TBA-Auth-Key": TBA_KEY}


def safe_cache_name(path):
    return path.strip("/").replace("/", "__") + ".json"


def get(path):
    os.makedirs(CACHE_FOLDER, exist_ok=True)

    cache_file = os.path.join(CACHE_FOLDER, safe_cache_name(path))

    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)

    response = requests.get(BASE + path, headers=HEADERS)
    response.raise_for_status()

    data = response.json()

    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(data, f)

    return data


def get_districts(year):
    return get(f"/districts/{year}")


def get_year_events(year):
    return sorted(
        get(f"/events/{year}"),
        key=lambda e: e.get("start_date", "")
    )


def get_district_events(district_key):
    return sorted(
        get(f"/district/{district_key}/events"),
        key=lambda e: e.get("start_date", "")
    )


def get_event_points(event_key):
    data = get(f"/event/{event_key}/district_points")
    return data.get("points", {})


def get_district_teams(district_key):
    return get(f"/district/{district_key}/teams")


def get_event_teams(event_key):
    return get(f"/event/{event_key}/teams")


def get_team_districts(team_key):
    return get(f"/team/{team_key}/districts")