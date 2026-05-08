import time
import pandas as pd
from tqdm import tqdm

from config import (
    START_YEAR,
    END_YEAR,
    DISABLED_YEARS,
    ENABLED_YEARS,
    REGIONAL_START_YEAR,
    RUN_SINGLE_YEAR,
    TARGET_YEAR,
    OUTPUT_FILE
)

from tba_api import get_districts
from utils import should_skip_district
from district_model import simulate_district_pre_dcmp
from regional_model import simulate_regionals_for_year
from excel_writer import (
    write_table_block,
    apply_dcmp_formatting,
    write_summary_sheet,
    write_regional_events_sheet
)


def seconds_to_text(seconds):
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}m {secs}s"


def get_years_to_run():
    if RUN_SINGLE_YEAR:
        return [TARGET_YEAR]

    years = [
        year for year in range(END_YEAR, START_YEAR - 1, -1)
        if year not in DISABLED_YEARS
    ]

    if ENABLED_YEARS:
        years = [
            year for year in years
            if year in ENABLED_YEARS
        ]

    return years


def build_workbook():
    total_start = time.perf_counter()

    summary_rows = []
    regional_event_rows = []

    with pd.ExcelWriter(
        OUTPUT_FILE,
        engine="xlsxwriter"
    ) as writer:

        workbook = writer.book

        years = get_years_to_run()

        for year in years:
            year_start = time.perf_counter()

            tqdm.write("")
            tqdm.write(f"=== Running {year} ===")

            worksheet = workbook.add_worksheet(str(year))
            writer.sheets[str(year)] = worksheet

            start_col = 0
            included_blocks = 0

            districts = sorted(
                [
                    district for district in get_districts(year)
                    if not should_skip_district(district)
                ],
                key=lambda district: district.get(
                    "display_name",
                    district.get("key", "")
                ).lower()
            )

            for district in tqdm(
                districts,
                desc=f"{year} districts",
                unit="district",
                leave=True
            ):
                district_start = time.perf_counter()

                district_key = district["key"]
                district_name = district.get(
                    "display_name",
                    district_key
                )

                tqdm.write(
                    f"  Checking {district_name}..."
                )

                rows, summary, dcmp_cutoff = (
                    simulate_district_pre_dcmp(
                        year,
                        district
                    )
                )

                if not rows:
                    tqdm.write(
                        "    Skipped, no redistributed points."
                    )
                    continue

                summary["Runtime"] = seconds_to_text(
                    time.perf_counter() - district_start
                )

                summary_rows.append(summary)
                included_blocks += 1

                df = pd.DataFrame(rows)

                write_table_block(
                    worksheet,
                    workbook,
                    df,
                    district_name,
                    f"Official DCMP team count: {dcmp_cutoff}",
                    0,
                    start_col
                )

                apply_dcmp_formatting(
                    worksheet,
                    workbook,
                    df,
                    start_col,
                    dcmp_cutoff
                )

                spacer_col = (
                    start_col + len(df.columns)
                )

                worksheet.set_column(
                    spacer_col,
                    spacer_col,
                    4
                )

                start_col += (
                    len(df.columns) + 1
                )

            if year >= REGIONAL_START_YEAR:
                regional_start = time.perf_counter()

                regional_rows, event_rows, regional_summary = (
                    simulate_regionals_for_year(year)
                )

                if regional_rows:
                    regional_summary["Runtime"] = (
                        seconds_to_text(
                            time.perf_counter()
                            - regional_start
                        )
                    )

                    summary_rows.append(
                        regional_summary
                    )

                    regional_event_rows.extend(
                        event_rows
                    )

                    included_blocks += 1

                    df_regional = pd.DataFrame(
                        regional_rows
                    )

                    write_table_block(
                        worksheet,
                        workbook,
                        df_regional,
                        f"{year} Regional Pool Redistribution",
                        "Same redistribution rule applied to 3rd+ regional plays and district teams at regionals",
                        0,
                        start_col
                    )

                    regional_event_df = pd.DataFrame(
                        event_rows
                    )

                    if not regional_event_df.empty:
                        write_table_block(
                            worksheet,
                            workbook,
                            regional_event_df,
                            f"{year} Regional Event Auto Qualifier Comparison",
                            "Original vs redistributed event auto-qualifiers",
                            len(df_regional) + 6,
                            start_col
                        )

                else:
                    tqdm.write(
                        f"  No regional redistributed points found for {year}."
                    )

            if included_blocks == 0:
                worksheet.write(
                    0,
                    0,
                    "No redistributed points found this year."
                )

            worksheet.freeze_panes(3, 0)

            tqdm.write(
                f"{year} completed in "
                f"{seconds_to_text(time.perf_counter() - year_start)}"
            )

        write_summary_sheet(
            workbook,
            writer,
            summary_rows
        )

        write_regional_events_sheet(
            workbook,
            writer,
            regional_event_rows
        )

    tqdm.write("")
    tqdm.write(
        f"Created {OUTPUT_FILE}"
    )

    tqdm.write(
        "Total runtime: "
        f"{seconds_to_text(time.perf_counter() - total_start)}"
    )


if __name__ == "__main__":
    build_workbook()