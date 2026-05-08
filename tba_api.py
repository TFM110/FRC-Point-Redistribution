import requests
from config import TBA_KEY

BASE = "https://www.thebluealliance.com/api/v3"
HEADERS = {"X-TBA-Auth-Key": TBA_KEY}


def get(path):
    response = requests.get(BASE + path, headers=HEADERS)

    if response.status_code == 401:
        raise Exception("401 Unauthorized: Your TBA API key is missing or invalid.")

    response.raise_for_status()
    return response.json()


def get_districts(year):
    return get(f"/districts/{year}")


def get_year_events(year):
    return sorted(
        get(f"/events/{year}"),
        key=lambda event: event.get("start_date", "")
    )


def get_district_events(district_key):
    return sorted(
        get(f"/district/{district_key}/events"),
        key=lambda event: event.get("start_date", "")
    )


def get_event_points(event_key):
    data = get(f"/event/{event_key}/district_points")
    return data.get("points", {})


def get_district_teams(district_key):
    return get(f"/district/{district_key}/teams")