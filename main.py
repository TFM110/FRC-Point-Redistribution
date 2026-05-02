import time
import pandas as pd
from tqdm import tqdm

from config import (
    START_YEAR,
    END_YEAR,
    SKIP_YEARS,
    REGIONAL_START_YEAR,
    OUTPUT_FILE
)

from tba_api import get_districts
from utils import should_skip_district
from district_model import simulate_district_pre_dcmp
from regional_model import simulate_regionals_for_year
from excel_writer import (
    write_table_block,
    apply_dcmp_formatting,
    write_summary_sheet
)


def seconds_to_text(seconds):
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}m {secs}s"


def build_workbook():
    total_start = time.perf_counter()

    summary_rows = []
    regional_event_rows = []

    with pd.ExcelWriter(OUTPUT_FILE, engine="xlsxwriter") as writer:
        workbook = writer.book

        years = [
            year for year in range(END_YEAR, START_YEAR - 1, -1)
            if year not in SKIP_YEARS
        ]

        for year in tqdm(years, desc="Years", unit="year"):
            year_start = time.perf_counter()

            worksheet = workbook.add_worksheet(str(year))
            writer.sheets[str(year)] = worksheet

            start_col = 0
            included_blocks = 0

            districts = [
                district for district in get_districts(year)
                if not should_skip_district(district)
            ]

            for district in tqdm(
                districts,
                desc=f"{year} districts",
                unit="district",
                leave=False
            ):
                district_start = time.perf_counter()

                district_key = district["key"]
                district_name = district.get("display_name", district_key)

                rows, summary, dcmp_cutoff = simulate_district_pre_dcmp(
                    year,
                    district
                )

                if not rows:
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

                spacer_col = start_col + len(df.columns)
                worksheet.set_column(spacer_col, spacer_col, 4)

                start_col += len(df.columns) + 1

            if year >= REGIONAL_START_YEAR:
                regional_start = time.perf_counter()

                regional_rows, event_rows, regional_summary = simulate_regionals_for_year(year)

                if regional_rows:
                    regional_summary["Runtime"] = seconds_to_text(
                        time.perf_counter() - regional_start
                    )

                    summary_rows.append(regional_summary)
                    regional_event_rows.extend(event_rows)
                    included_blocks += 1

                    df_regional = pd.DataFrame(regional_rows)

                    write_table_block(
                        worksheet,
                        workbook,
                        df_regional,
                        f"{year} Regional Pool Redistribution",
                        "Same redistribution rule applied to 3rd+ regional plays and district teams at regionals",
                        0,
                        start_col
                    )

                    regional_event_df = pd.DataFrame(event_rows)

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

            if included_blocks == 0:
                worksheet.write(0, 0, "No redistributed points found this year.")

            worksheet.freeze_panes(3, 0)

            print(f"{year} completed in {seconds_to_text(time.perf_counter() - year_start)}")

        write_summary_sheet(
            workbook,
            writer,
            summary_rows,
            regional_event_rows
        )

    print()
    print(f"Created {OUTPUT_FILE}")
    print(f"Total runtime: {seconds_to_text(time.perf_counter() - total_start)}")


if __name__ == "__main__":
    build_workbook()