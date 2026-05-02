import requests
import math
import pandas as pd
from collections import defaultdict

TBA_KEY = "iCJqGdgL5jCstecAFQSrT24ExEVc1cRstoboGOzaVUhIHbEorl1IzkCBqtW4mRnJ"

BASE = "https://www.thebluealliance.com/api/v3"
HEADERS = {"X-TBA-Auth-Key": TBA_KEY}

START_YEAR = 2009
END_YEAR = 2026
SKIP_YEARS = {2020, 2021}

OUTPUT_FILE = "frc_district_redistribution_comparison.xlsx"


def get(path):
    response = requests.get(BASE + path, headers=HEADERS)
    response.raise_for_status()
    return response.json()


def is_demo_team(team_key):
    try:
        team_number = int(team_key.replace("frc", ""))
        return 9970 <= team_number <= 9999
    except ValueError:
        return False


def should_skip_district(district):
    district_key = district.get("key", "").lower()
    district_name = district.get("display_name", "").lower()

    return (
        "canada" in district_name
        or "ontario" in district_name
        or district_key.endswith("ont")
    )


def calculate_bonus(points_earned, eligible_count):
    if points_earned <= 0 or eligible_count <= 0:
        return 0

    raw_bonus = points_earned / eligible_count

    if raw_bonus < 1:
        return 1

    return math.floor(raw_bonus + 0.5)


def get_districts(year):
    return get(f"/districts/{year}")


def get_events(district_key):
    events = get(f"/district/{district_key}/events")
    return sorted(events, key=lambda e: e.get("start_date", ""))


def get_event_points(event_key):
    data = get(f"/event/{event_key}/district_points")
    points = data.get("points", {})

    return {
        team_key: point_data
        for team_key, point_data in points.items()
        if not is_demo_team(team_key)
    }


def get_district_teams(district_key):
    teams = get(f"/district/{district_key}/teams")

    return set(
        team["key"]
        for team in teams
        if not is_demo_team(team["key"])
    )


def get_event_team_keys(event_key):
    teams = get(f"/event/{event_key}/teams")

    return set(
        team["key"]
        for team in teams
        if not is_demo_team(team["key"])
    )


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


def get_dcmp_attending_teams(district_key, district_teams):
    events = get_events(district_key)

    dcmp_events = [
        event for event in events
        if is_dcmp_event(event)
    ]

    dcmp_team_keys = set()

    for event in dcmp_events:
        event_teams = get_event_team_keys(event["key"])

        for team in event_teams:
            if team in district_teams:
                dcmp_team_keys.add(team)

    return dcmp_team_keys


def simulate_district_pre_dcmp(year, district_key, district_name):
    events = get_events(district_key)
    district_teams = get_district_teams(district_key)
    dcmp_attending_teams = get_dcmp_attending_teams(district_key, district_teams)

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

        points = get_event_points(event_key)

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

            reason = "inter-district" if non_point_team not in district_teams else "3rd+ play"

            for team in eligible_teams:
                distributed_points[team] += bonus_each
                extra_events[team].append(
                    f"{event_name}: +{bonus_each} from Team {non_point_team.replace('frc', '')} ({reason})"
                )

    if not extra_events:
        return [], {}, 0

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

    actual_cutoff_rank = 0

    if dcmp_attending_teams:
        attending_ranked_teams = [
            team for team in dcmp_attending_teams
            if team in original_rank
        ]

        if attending_ranked_teams:
            actual_cutoff_rank = max(
                original_rank[team]
                for team in attending_ranked_teams
            )

    rows = []

    gained_dcmp = 0
    lost_dcmp = 0
    max_rank_gain = 0
    max_rank_loss = 0
    max_point_gain = 0

    for team in distributed_sorted:
        event_notes = []

        if extra_events[team]:
            event_notes.append("Extra: " + "; ".join(extra_events[team]))

        if over_two_events[team]:
            event_notes.append("3rd+ play: " + "; ".join(over_two_events[team]))

        original_qualified = team in dcmp_attending_teams

        distributed_qualified = (
            actual_cutoff_rank > 0
            and distributed_rank[team] <= actual_cutoff_rank
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

        rows.append({
            "Team": team.replace("frc", ""),
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
        "Year": year,
        "District": district_name,
        "District Key": district_key,
        "Actual DCMP Cutoff Rank": actual_cutoff_rank,
        "Teams Gained DCMP Spot": gained_dcmp,
        "Teams Lost DCMP Spot": lost_dcmp,
        "Max Rank Gain": max_rank_gain,
        "Max Rank Loss": max_rank_loss,
        "Max Point Gain": max_point_gain,
        "Teams Affected By Extra Points": sum(
            1 for team in all_teams if distributed_points[team] != original_points[team]
        )
    }

    return rows, summary, actual_cutoff_rank


def write_summary_sheet(workbook, writer, summary_rows):
    worksheet = workbook.add_worksheet("Summary")
    writer.sheets["Summary"] = worksheet

    if not summary_rows:
        worksheet.write(0, 0, "No summary data found.")
        return

    df = pd.DataFrame(summary_rows)

    header_format = workbook.add_format({
        "bold": True,
        "align": "center",
        "border": 1
    })

    text_format = workbook.add_format({
        "border": 1
    })

    number_format = workbook.add_format({
        "num_format": "0",
        "align": "center",
        "border": 1
    })

    for col, column_name in enumerate(df.columns):
        worksheet.write(0, col, column_name, header_format)

    for row_num, (_, row_data) in enumerate(df.iterrows(), start=1):
        for col_num, value in enumerate(row_data.values):
            if isinstance(value, str):
                worksheet.write(row_num, col_num, value, text_format)
            else:
                worksheet.write(row_num, col_num, value, number_format)

    worksheet.autofilter(0, 0, len(df), len(df.columns) - 1)
    worksheet.freeze_panes(1, 0)

    worksheet.set_column("A:A", 10)
    worksheet.set_column("B:B", 24)
    worksheet.set_column("C:C", 14)
    worksheet.set_column("D:J", 20)


def build_workbook():
    summary_rows = []

    with pd.ExcelWriter(OUTPUT_FILE, engine="xlsxwriter") as writer:
        workbook = writer.book

        title_format = workbook.add_format({
            "bold": True,
            "font_size": 13,
            "align": "center",
            "valign": "vcenter",
            "border": 1
        })

        subtitle_format = workbook.add_format({
            "italic": True,
            "align": "center",
            "valign": "vcenter",
            "border": 1
        })

        header_format = workbook.add_format({
            "bold": True,
            "align": "center",
            "valign": "vcenter",
            "border": 1
        })

        text_format = workbook.add_format({
            "valign": "top",
            "text_wrap": True,
            "border": 1
        })

        number_format = workbook.add_format({
            "num_format": "0",
            "align": "center",
            "valign": "top",
            "border": 1
        })

        yellow_rank_format = workbook.add_format({
            "bg_color": "#FFF2CC",
            "border": 1,
            "align": "center",
            "valign": "top"
        })

        gained_format = workbook.add_format({
            "bg_color": "#C6EFCE",
            "font_color": "#006100",
            "border": 1,
            "text_wrap": True,
            "valign": "top"
        })

        lost_format = workbook.add_format({
            "bg_color": "#FFC7CE",
            "font_color": "#9C0006",
            "border": 1,
            "text_wrap": True,
            "valign": "top"
        })

        for year in range(END_YEAR, START_YEAR - 1, -1):
            if year in SKIP_YEARS:
                print(f"Skipping {year}...")
                continue

            print(f"Running {year}...")

            worksheet = workbook.add_worksheet(str(year))
            writer.sheets[str(year)] = worksheet

            start_col = 0
            included_districts = 0

            for district in get_districts(year):
                if should_skip_district(district):
                    print(f"  Skipping {district.get('display_name', district.get('key'))}...")
                    continue

                district_key = district["key"]
                district_name = district.get("display_name", district_key)

                print(f"  Checking {district_name}...")

                rows, summary, dcmp_cutoff = simulate_district_pre_dcmp(
                    year,
                    district_key,
                    district_name
                )

                if not rows:
                    print("    Skipped, no redistributed points.")
                    continue

                summary_rows.append(summary)
                included_districts += 1

                df = pd.DataFrame(rows)

                end_col = start_col + len(df.columns) - 1

                worksheet.merge_range(
                    0,
                    start_col,
                    0,
                    end_col,
                    district_name,
                    title_format
                )

                worksheet.merge_range(
                    1,
                    start_col,
                    1,
                    end_col,
                    f"Actual DCMP cutoff based on attendees: Rank {dcmp_cutoff}",
                    subtitle_format
                )

                for col_offset, column_name in enumerate(df.columns):
                    worksheet.write(
                        2,
                        start_col + col_offset,
                        column_name,
                        header_format
                    )

                for row_offset, (_, row_data) in enumerate(df.iterrows(), start=3):
                    for col_offset, value in enumerate(row_data.values):
                        column_name = df.columns[col_offset]

                        if column_name in ["Team", "Event(s)", "DCMP Status"]:
                            worksheet.write(
                                row_offset,
                                start_col + col_offset,
                                value,
                                text_format
                            )
                        else:
                            worksheet.write(
                                row_offset,
                                start_col + col_offset,
                                value,
                                number_format
                            )

                start_row = 3
                end_row = start_row + len(df) - 1

                col_op_rank = start_col + df.columns.get_loc("OP Rank")
                col_dp_rank = start_col + df.columns.get_loc("DP Rank")
                col_change_points = start_col + df.columns.get_loc("Change Points")
                col_change_rank = start_col + df.columns.get_loc("Change Rank")
                col_dcmp_status = start_col + df.columns.get_loc("DCMP Status")

                if dcmp_cutoff > 0:
                    worksheet.conditional_format(
                        start_row,
                        col_op_rank,
                        end_row,
                        col_op_rank,
                        {
                            "type": "cell",
                            "criteria": "<=",
                            "value": dcmp_cutoff,
                            "format": yellow_rank_format
                        }
                    )

                    worksheet.conditional_format(
                        start_row,
                        col_dp_rank,
                        end_row,
                        col_dp_rank,
                        {
                            "type": "cell",
                            "criteria": "<=",
                            "value": dcmp_cutoff,
                            "format": yellow_rank_format
                        }
                    )

                worksheet.conditional_format(
                    start_row,
                    col_change_points,
                    end_row,
                    col_change_points,
                    {
                        "type": "3_color_scale",
                        "min_type": "min",
                        "min_color": "#F8696B",
                        "mid_type": "num",
                        "mid_value": 0,
                        "mid_color": "#FFFFFF",
                        "max_type": "max",
                        "max_color": "#63BE7B"
                    }
                )

                worksheet.conditional_format(
                    start_row,
                    col_change_rank,
                    end_row,
                    col_change_rank,
                    {
                        "type": "3_color_scale",
                        "min_type": "min",
                        "min_color": "#F8696B",
                        "mid_type": "num",
                        "mid_value": 0,
                        "mid_color": "#FFFFFF",
                        "max_type": "max",
                        "max_color": "#63BE7B"
                    }
                )

                worksheet.conditional_format(
                    start_row,
                    col_dcmp_status,
                    end_row,
                    col_dcmp_status,
                    {
                        "type": "text",
                        "criteria": "containing",
                        "value": "Gained DCMP spot",
                        "format": gained_format
                    }
                )

                worksheet.conditional_format(
                    start_row,
                    col_dcmp_status,
                    end_row,
                    col_dcmp_status,
                    {
                        "type": "text",
                        "criteria": "containing",
                        "value": "Lost DCMP spot",
                        "format": lost_format
                    }
                )

                worksheet.set_column(start_col, start_col, 10)
                worksheet.set_column(start_col + 1, start_col + 6, 16)
                worksheet.set_column(start_col + 7, start_col + 7, 20)
                worksheet.set_column(start_col + 8, start_col + 8, 60)

                spacer_col = start_col + len(df.columns)
                worksheet.set_column(spacer_col, spacer_col, 4)

                start_col += len(df.columns) + 1

            if included_districts == 0:
                worksheet.write(
                    0,
                    0,
                    "No districts had redistributed points this year."
                )

            worksheet.freeze_panes(3, 0)

        write_summary_sheet(workbook, writer, summary_rows)

    print(f"Created {OUTPUT_FILE}")


if __name__ == "__main__":
    build_workbook()