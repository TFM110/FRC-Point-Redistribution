import pandas as pd


def write_team_or_value(worksheet, row, col, value, column_name, text_format, number_format):
    if column_name == "Team":
        worksheet.write_number(row, col, int(value), number_format)
    elif column_name in ["Event(s)", "DCMP Status"]:
        worksheet.write(row, col, value, text_format)
    elif isinstance(value, str):
        worksheet.write(row, col, value, text_format)
    else:
        worksheet.write(row, col, value, number_format)


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

    worksheet.merge_range(start_row, start_col, start_row, end_col, title, title_format)
    worksheet.merge_range(start_row + 1, start_col, start_row + 1, end_col, subtitle, subtitle_format)

    for col_offset, column_name in enumerate(df.columns):
        worksheet.write(start_row + 2, start_col + col_offset, column_name, header_format)

    for row_offset, (_, row_data) in enumerate(df.iterrows(), start=start_row + 3):
        for col_offset, value in enumerate(row_data.values):
            column_name = df.columns[col_offset]
            write_team_or_value(
                worksheet,
                row_offset,
                start_col + col_offset,
                value,
                column_name,
                text_format,
                number_format
            )

    start_data_row = start_row + 3
    end_data_row = start_data_row + len(df) - 1

    for column_name in ["Change Points", "Change Rank"]:
        if column_name in df.columns:
            col = start_col + df.columns.get_loc(column_name)
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


def write_plain_table(workbook, worksheet, df):
    header_format = workbook.add_format({
        "bold": True,
        "align": "center",
        "border": 1
    })

    text_format = workbook.add_format({
        "border": 1,
        "text_wrap": True,
        "valign": "top"
    })

    number_format = workbook.add_format({
        "num_format": "0",
        "align": "center",
        "border": 1,
        "valign": "top"
    })

    for col, column_name in enumerate(df.columns):
        worksheet.write(0, col, column_name, header_format)

    for row_num, (_, row_data) in enumerate(df.iterrows(), start=1):
        for col_num, value in enumerate(row_data.values):
            column_name = df.columns[col_num]
            write_team_or_value(
                worksheet,
                row_num,
                col_num,
                value,
                column_name,
                text_format,
                number_format
            )

    worksheet.autofilter(0, 0, len(df), len(df.columns) - 1)
    worksheet.freeze_panes(1, 0)
    worksheet.set_column("A:Z", 22)


def write_summary_sheet(workbook, writer, summary_rows):
    worksheet = workbook.add_worksheet("Summary")
    writer.sheets["Summary"] = worksheet

    if not summary_rows:
        worksheet.write(0, 0, "No summary data found.")
        return

    df = pd.DataFrame(summary_rows)
    write_plain_table(workbook, worksheet, df)


def write_regional_events_sheet(workbook, writer, regional_event_rows):
    worksheet = workbook.add_worksheet("Regional Events")
    writer.sheets["Regional Events"] = worksheet

    if not regional_event_rows:
        worksheet.write(0, 0, "No regional event auto qualifier changes found.")
        return

    df = pd.DataFrame(regional_event_rows)
    write_plain_table(workbook, worksheet, df)