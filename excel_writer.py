import pandas as pd


def write_table_block(worksheet, workbook, df, title, subtitle, start_row, start_col):
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

    end_col = start_col + len(df.columns) - 1

    worksheet.merge_range(
        start_row,
        start_col,
        start_row,
        end_col,
        title,
        title_format
    )

    worksheet.merge_range(
        start_row + 1,
        start_col,
        start_row + 1,
        end_col,
        subtitle,
        subtitle_format
    )

    for col_offset, column_name in enumerate(df.columns):
        worksheet.write(
            start_row + 2,
            start_col + col_offset,
            column_name,
            header_format
        )

    for row_offset, (_, row_data) in enumerate(df.iterrows(), start=start_row + 3):
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

    start_data_row = start_row + 3
    end_data_row = start_data_row + len(df) - 1

    if "Change Points" in df.columns:
        col = start_col + df.columns.get_loc("Change Points")
        worksheet.conditional_format(
            start_data_row,
            col,
            end_data_row,
            col,
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

    if "Change Rank" in df.columns:
        col = start_col + df.columns.get_loc("Change Rank")
        worksheet.conditional_format(
            start_data_row,
            col,
            end_data_row,
            col,
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

    worksheet.set_column(start_col, start_col + len(df.columns) - 2, 16)
    worksheet.set_column(start_col + len(df.columns) - 1, start_col + len(df.columns) - 1, 60)

    return end_data_row + 2


def apply_dcmp_formatting(worksheet, workbook, df, start_col, cutoff):
    if cutoff <= 0:
        return

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

    start_row = 3
    end_row = start_row + len(df) - 1

    op_rank_col = start_col + df.columns.get_loc("OP Rank")
    dp_rank_col = start_col + df.columns.get_loc("DP Rank")

    worksheet.conditional_format(
        start_row,
        op_rank_col,
        end_row,
        op_rank_col,
        {
            "type": "cell",
            "criteria": "<=",
            "value": cutoff,
            "format": yellow_rank_format
        }
    )

    worksheet.conditional_format(
        start_row,
        dp_rank_col,
        end_row,
        dp_rank_col,
        {
            "type": "cell",
            "criteria": "<=",
            "value": cutoff,
            "format": yellow_rank_format
        }
    )

    if "DCMP Status" in df.columns:
        status_col = start_col + df.columns.get_loc("DCMP Status")

        worksheet.conditional_format(
            start_row,
            status_col,
            end_row,
            status_col,
            {
                "type": "text",
                "criteria": "containing",
                "value": "Gained",
                "format": gained_format
            }
        )

        worksheet.conditional_format(
            start_row,
            status_col,
            end_row,
            status_col,
            {
                "type": "text",
                "criteria": "containing",
                "value": "Lost",
                "format": lost_format
            }
        )


def write_summary_sheet(workbook, writer, summary_rows, regional_event_rows):
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

    worksheet.set_column("A:K", 22)

    chart1 = workbook.add_chart({"type": "column"})
    chart1.add_series({
        "name": "Teams Affected",
        "categories": ["Summary", 1, 2, len(df), 2],
        "values": [
            "Summary",
            1,
            df.columns.get_loc("Teams Affected"),
            len(df),
            df.columns.get_loc("Teams Affected")
        ]
    })
    chart1.set_title({"name": "Teams Affected by Redistribution"})
    worksheet.insert_chart("M2", chart1)

    chart2 = workbook.add_chart({"type": "column"})
    chart2.add_series({
        "name": "Max Rank Gain",
        "categories": ["Summary", 1, 2, len(df), 2],
        "values": [
            "Summary",
            1,
            df.columns.get_loc("Max Rank Gain"),
            len(df),
            df.columns.get_loc("Max Rank Gain")
        ]
    })
    chart2.set_title({"name": "Max Rank Gain by Group"})
    worksheet.insert_chart("M18", chart2)

    if regional_event_rows:
        start_row = len(df) + 4
        event_df = pd.DataFrame(regional_event_rows)

        worksheet.write(
            start_row,
            0,
            "Regional Event Auto Qualifier Changes",
            header_format
        )

        for col, column_name in enumerate(event_df.columns):
            worksheet.write(start_row + 1, col, column_name, header_format)

        for row_num, (_, row_data) in enumerate(event_df.iterrows(), start=start_row + 2):
            for col_num, value in enumerate(row_data.values):
                if isinstance(value, str):
                    worksheet.write(row_num, col_num, value, text_format)
                else:
                    worksheet.write(row_num, col_num, value, number_format)