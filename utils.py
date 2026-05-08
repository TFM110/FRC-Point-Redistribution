import math

from config import (
    DISABLED_DISTRICTS,
    ENABLED_DISTRICTS
)


def is_demo_team(team_key):
    try:
        team_number = int(team_key.replace("frc", ""))
        return 9970 <= team_number <= 9999
    except ValueError:
        return False


def clean_team_number(team_key):
    return team_key.replace("frc", "")


def team_number(team_key):
    return int(team_key.replace("frc", ""))


def calculate_bonus(points_earned, eligible_count):
    if points_earned <= 0 or eligible_count <= 0:
        return 0

    raw_bonus = points_earned / eligible_count

    if raw_bonus < 1:
        return 1

    return math.floor(raw_bonus + 0.5)


def should_skip_district(district):
    district_key = district.get("key", "").lower()
    district_name = district.get("display_name", "").lower()
    abbreviation = district.get("abbreviation", "").lower()

    disabled = {
        item.lower()
        for item in DISABLED_DISTRICTS
    }

    enabled = {
        item.lower()
        for item in ENABLED_DISTRICTS
    }

    district_identifiers = {
        district_key,
        district_name,
        abbreviation
    }

    # If enabled list exists,
    # only allow matching districts
    if enabled and not district_identifiers.intersection(enabled):
        return True

    # Skip disabled districts
    if district_identifiers.intersection(disabled):
        return True

    return False


def is_dcmp_event(event):
    event_type = event.get("event_type")
    name = event.get("name", "").lower()

    return (
        event_type == 2
        or "district championship" in name
        or "district champs" in name
        or "dcmp" in name
        or "state championship" in name
    )


def is_regional_event(event):
    return event.get("event_type") == 0


def regional_slots(event):
    return 3 if event.get("country") == "USA" else 4