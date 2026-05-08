from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

TBA_KEY = os.getenv("TBA_KEY")

START_YEAR = 2009

now = datetime.now()

# FRC season ends in April
if now.month < 5:
    END_YEAR = now.year - 1
else:
    END_YEAR = now.year

# Regional point system begins in 2026
REGIONAL_START_YEAR = 2026

# Faster for testing
RUN_SINGLE_YEAR = False
TARGET_YEAR = 2026

# Leave empty to run all valid years
ENABLED_YEARS = set()

# Years to skip
DISABLED_YEARS = {
    2020,
    2021
}

# Leave empty to allow all districts
ENABLED_DISTRICTS = set()

# Districts to skip
# Supports:
# - abbreviation
# - district key
# - display name
DISABLED_DISTRICTS = {
    "ont",
    "ca"
}

OUTPUT_FILE = "frc_district_and_regional_redistribution.xlsx"