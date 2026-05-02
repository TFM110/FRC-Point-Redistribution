from datetime import datetime

TBA_KEY = "PUT_YOUR_TBA_API_KEY_HERE"

START_YEAR = 2009

now = datetime.now()

# FRC season ends in April → use May as cutoff
if now.month < 5:
    END_YEAR = now.year - 1
else:
    END_YEAR = now.year

SKIP_YEARS = {2020, 2021}

REGIONAL_START_YEAR = 2026

OUTPUT_FILE = "frc_district_and_regional_redistribution.xlsx"