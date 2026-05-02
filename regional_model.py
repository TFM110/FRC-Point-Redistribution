from collections import defaultdict
from tqdm import tqdm

from tba_api import (
    get_year_events,
    get_event_points,
    get_districts,
    get_district_teams
)

from utils import (
    is_demo_team,
    clean_team_number,
    calculate_bonus,
    is_regional_event,
    regional_slots,
    should_skip_district
)


def get_all_district_teams_for_year(year):
    district_teams = set()

    districts = [
        district for district in get_districts(year)
        if not should_skip_district(district)
    ]

    for district in tqdm(
        districts,
        desc=f"{year} regional model: loading district teams",
        unit="district",
        leave=False
    ):
        for team in get_district_teams(district["key"]):
            if not is_demo_team(team["key"]):
                district_teams.add(team["key"])

    return district_teams


def get_clean_event_points(event_key):
    points = get_event_points(event_key)

    return {
        team_key: point_data
        for team_key, point_data in points.items()
        if not is_demo_team(team_key)
    }


def simulate_regionals_for_year(year):
    print(f"  Running {year} regional model...")

    district_team_set = get_all_district_teams_for_year(year)

    events = [
        event for event in get_year_events(year)
        if is_regional_event(event)
    ]

    team_play_count = defaultdict(int)
    original_points = defaultdict(int)
    distributed_points = defaultdict(int)

    extra_events = defaultdict(list)
    non_counting_events = defaultdict(list)

    event_rows = []

    for event in tqdm(
        events,
        desc=f"{year} regionals",
        unit="event",
        leave=False
    ):
        event_key = event["key"]
        event_name = event.get("name", event_key)

        try:
            points = get_clean_event_points(event_key)
        except Exception:
            continue

        if not points:
            continue

        non_point_teams = []

        for team_key, point_data in points.items():
            earned_points = point_data.get("total", 0)

            if team_key in district_team_set:
                non_point_teams.append(team_key)
                non_counting_events[team_key].append(
                    f"{event_name} ({earned_points} district team at regional)"
                )
                continue

            team_play_count[team_key] += 1

            if team_play_count[team_key] <= 2:
                original_points[team_key] += earned_points
                distributed_points[team_key] += earned_points
            else:
                non_point_teams.append(team_key)
                non_counting_events[team_key].append(
                    f"{event_name} ({earned_points} 3rd+ regional non-counting points)"
                )

        eligible_teams = [
            team for team in points.keys()
            if team not in district_team_set
            and team_play_count[team] <= 2
            and team not in non_point_teams
        ]

        event_bonus_by_team = defaultdict(int)

        for non_point_team in non_point_teams:
            earned_points = points[non_point_team].get("total", 0)
            bonus_each = calculate_bonus(earned_points, len(eligible_teams))

            if bonus_each <= 0:
                continue

            reason = (
                "district team at regional"
                if non_point_team in district_team_set
                else "3rd+ regional"
            )

            for team in eligible_teams:
                distributed_points[team] += bonus_each
                event_bonus_by_team[team] += bonus_each
                extra_events[team].append(
                    f"{event_name}: +{bonus_each} from Team {clean_team_number(non_point_team)} ({reason})"
                )

        regional_teams_at_event = [
            team for team in points.keys()
            if team not in district_team_set
        ]

        original_event_ranked = sorted(
            regional_teams_at_event,
            key=lambda team: points[team].get("total", 0),
            reverse=True
        )

        distributed_event_ranked = sorted(
            regional_teams_at_event,
            key=lambda team: points[team].get("total", 0) + event_bonus_by_team[team],
            reverse=True
        )

        slots = regional_slots(event)

        original_auto = original_event_ranked[:slots]
        distributed_auto = distributed_event_ranked[:slots]

        event_rows.append({
            "Event": event_name,
            "Event Key": event_key,
            "Country": event.get("country", ""),
            "Auto Slots": slots,
            "Original Auto Qualifiers": ", ".join(
                clean_team_number(team) for team in original_auto
            ),
            "Distributed Auto Qualifiers": ", ".join(
                clean_team_number(team) for team in distributed_auto
            ),
            "Changed?": "Yes" if set(original_auto) != set(distributed_auto) else "No"
        })

    if not extra_events:
        return [], [], {}

    all_teams = set(original_points) | set(distributed_points)

    original_sorted = sorted(
        all_teams,
        key=lambda team: original_points[team],
        reverse=True
    )

    distributed_sorted = sorted(
        all_teams,
        key=lambda team: distributed_points[team],
        reverse=True
    )

    original_rank = {
        team: rank + 1
        for rank, team in enumerate(original_sorted)
    }

    distributed_rank = {
        team: rank + 1
        for rank, team in enumerate(distributed_sorted)
    }

    rows = []

    max_rank_gain = 0
    max_rank_loss = 0
    max_point_gain = 0

    for team in distributed_sorted:
        change_points = distributed_points[team] - original_points[team]
        change_rank = original_rank[team] - distributed_rank[team]

        max_rank_gain = max(max_rank_gain, change_rank)
        max_rank_loss = min(max_rank_loss, change_rank)
        max_point_gain = max(max_point_gain, change_points)

        event_notes = []

        if extra_events[team]:
            event_notes.append("Extra: " + "; ".join(extra_events[team]))

        if non_counting_events[team]:
            event_notes.append(
                "Non-counting: " + "; ".join(non_counting_events[team])
            )

        rows.append({
            "Team": clean_team_number(team),
            "Original Points": original_points[team],
            "OP Rank": original_rank[team],
            "Distributed Points": distributed_points[team],
            "DP Rank": distributed_rank[team],
            "Change Points": change_points,
            "Change Rank": change_rank,
            "Event(s)": " | ".join(event_notes)
        })

    summary = {
        "System": "Regional",
        "Year": year,
        "Group": "Regional Pool",
        "Key": f"{year}regional",
        "Actual Advancement Count": "",
        "Teams Gained Spot": "",
        "Teams Lost Spot": "",
        "Max Rank Gain": max_rank_gain,
        "Max Rank Loss": max_rank_loss,
        "Max Point Gain": max_point_gain,
        "Teams Affected": sum(
            1 for team in all_teams
            if distributed_points[team] != original_points[team]
        )
    }

    return rows, event_rows, summary