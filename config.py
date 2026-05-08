from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

TBA_KEY = os.getenv("TBA_KEY")

START_YEAR = 2009

now = datetime.now()

if now.month < 5:
    END_YEAR = now.year - 1
else:
    END_YEAR = now.year

SKIP_YEARS = {2020, 2021}

REGIONAL_START_YEAR = 2026

RUN_SINGLE_YEAR = True
TARGET_YEAR = 2026

OUTPUT_FILE = "frc_district_and_regional_redistribution.xlsx"