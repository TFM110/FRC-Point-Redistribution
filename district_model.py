from collections import defaultdict
from tba_api import get_district_events, get_event_points, get_district_teams
from utils import (
    is_demo_team,
    clean_team_number,
    calculate_bonus,
    is_dcmp_event
)


def get_clean_district_teams(district_key):
    teams = get_district_teams(district_key)

    return {
        team["key"]
        for team in teams
        if not is_demo_team(team["key"])
    }


def get_clean_event_points(event_key):
    points = get_event_points(event_key)

    return {
        team_key: point_data
        for team_key, point_data in points.items()
        if not is_demo_team(team_key)
    }


def simulate_district_pre_dcmp(year, district):
    district_key = district["key"]
    district_name = district.get("display_name", district_key)

    dcmp_count = district.get(
        "official_advancement_counts", {}
    ).get("dcmp", 0)

    events = get_district_events(district_key)
    district_teams = get_clean_district_teams(district_key)

    team_play_count = defaultdict(int)
    original_points = defaultdict(int)
    distributed_points = defaultdict(int)

    extra_events = defaultdict(list)
    over_two_events = defaultdict(list)

    for event in events:
        if is_dcmp_event(event):
            continue

        event_key = event["key"]
        event_name = event.get("name", event_key)

        points = get_clean_event_points(event_key)

        if not points:
            continue

        non_point_teams = []

        for team_key, point_data in points.items():
            earned_points = point_data.get("total", 0)

            if team_key not in district_teams:
                non_point_teams.append(team_key)
                continue

            team_play_count[team_key] += 1

            if team_play_count[team_key] <= 2:
                original_points[team_key] += earned_points
                distributed_points[team_key] += earned_points
            else:
                non_point_teams.append(team_key)
                over_two_events[team_key].append(
                    f"{event_name} ({earned_points} 3rd+ play non-counting points)"
                )

        eligible_teams = [
            team for team in points.keys()
            if team in district_teams
            and team_play_count[team] <= 2
            and team not in non_point_teams
        ]

        for non_point_team in non_point_teams:
            earned_points = points[non_point_team].get("total", 0)
            bonus_each = calculate_bonus(earned_points, len(eligible_teams))

            if bonus_each <= 0:
                continue

            reason = (
                "inter-district"
                if non_point_team not in district_teams
                else "3rd+ play"
            )

            for team in eligible_teams:
                distributed_points[team] += bonus_each
                extra_events[team].append(
                    f"{event_name}: +{bonus_each} from Team {clean_team_number(non_point_team)} ({reason})"
                )

    if not extra_events:
        return [], {}, dcmp_count

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

    gained_dcmp = 0
    lost_dcmp = 0
    max_rank_gain = 0
    max_rank_loss = 0
    max_point_gain = 0

    for team in distributed_sorted:
        original_qualified = (
            dcmp_count > 0
            and original_rank[team] <= dcmp_count
        )

        distributed_qualified = (
            dcmp_count > 0
            and distributed_rank[team] <= dcmp_count
        )

        if original_qualified and distributed_qualified:
            dcmp_status = "Qualified in both"
        elif original_qualified and not distributed_qualified:
            dcmp_status = "Lost DCMP spot"
            lost_dcmp += 1
        elif not original_qualified and distributed_qualified:
            dcmp_status = "Gained DCMP spot"
            gained_dcmp += 1
        else:
            dcmp_status = ""

        change_points = distributed_points[team] - original_points[team]
        change_rank = original_rank[team] - distributed_rank[team]

        max_rank_gain = max(max_rank_gain, change_rank)
        max_rank_loss = min(max_rank_loss, change_rank)
        max_point_gain = max(max_point_gain, change_points)

        event_notes = []

        if extra_events[team]:
            event_notes.append("Extra: " + "; ".join(extra_events[team]))

        if over_two_events[team]:
            event_notes.append("3rd+ play: " + "; ".join(over_two_events[team]))

        rows.append({
            "Team": clean_team_number(team),
            "Original Points": original_points[team],
            "OP Rank": original_rank[team],
            "Distributed Points": distributed_points[team],
            "DP Rank": distributed_rank[team],
            "Change Points": change_points,
            "Change Rank": change_rank,
            "DCMP Status": dcmp_status,
            "Event(s)": " | ".join(event_notes)
        })

    summary = {
        "System": "District",
        "Year": year,
        "Group": district_name,
        "Key": district_key,
        "Actual Advancement Count": dcmp_count,
        "Teams Gained Spot": gained_dcmp,
        "Teams Lost Spot": lost_dcmp,
        "Max Rank Gain": max_rank_gain,
        "Max Rank Loss": max_rank_loss,
        "Max Point Gain": max_point_gain,
        "Teams Affected": sum(
            1 for team in all_teams
            if distributed_points[team] != original_points[team]
        )
    }

    return rows, summary, dcmp_count