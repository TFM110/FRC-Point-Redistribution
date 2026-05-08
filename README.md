# FRC Point Redistribution Tool

This project analyzes FRC district and regional point systems using The Blue Alliance API.

It simulates a redistribution model where:
- Teams competing at their 3rd+ play do NOT receive points
- Inter-district teams do NOT receive points
- Those removed points are redistributed evenly to eligible teams
- Regional redistribution also works for the new regional point system (2026+)

The tool exports everything into a formatted Excel workbook.

---

# Features

## District Analysis
- Original district rankings
- Redistributed rankings
- Rank movement
- Point movement
- DCMP qualification changes
- Actual DCMP advancement counts from TBA
- Inter-district redistribution
- 3rd+ play redistribution
- Conditional formatting
- Summary sheet

## Regional Analysis (2026+)
- Regional pool redistribution
- Regional auto-qualifier comparison
- Prevents duplicate auto-qualified teams
- Inter-district regional redistribution
- 3rd+ regional redistribution

---

# Requirements

Install Python packages:

```bash
pip install requests pandas xlsxwriter tqdm python-dotenv
```

---

# Folder Structure

```text
FRC-Point-Redistribution/
│
├── main.py
├── config.py
├── tba_api.py
├── utils.py
├── district_model.py
├── regional_model.py
├── excel_writer.py
├── .env
├── .gitignore
└── README.md
```

---

# API Key Setup

## Create `.env`

Create a file named:

```text
.env
```

Inside:

```env
TBA_KEY=YOUR_REAL_TBA_API_KEY
```

---

# Getting a TBA API Key

1. Go to:
   https://www.thebluealliance.com/account

2. Log in

3. Create a Read API Key

4. Copy the key

5. Paste it into `.env`

---

# Running the Script

Open terminal in the project folder:

```bash
python main.py
```

---

# Running a Single Year

Inside `config.py`:

```python
RUN_SINGLE_YEAR = True
TARGET_YEAR = 2026
```

This is much faster and recommended for testing.

---

# Running All Years

Inside `config.py`:

```python
RUN_SINGLE_YEAR = False
```

The script will automatically run:
- 2009 → current FRC season
- skips 2020 and 2021

---

# Automatic Season Detection

The script automatically determines the latest valid FRC season.

Logic:
- January–April → previous year
- May–December → current year

No manual year updating required.

---

# Excel Output

The workbook contains:
- One tab per year
- Districts placed side-by-side
- Regional redistribution tables (2026+)
- Summary tab with charts

Columns:

| Column | Description |
|---|---|
| Team | FRC team number |
| Original Points | Official points |
| OP Rank | Official ranking |
| Distributed Points | Points after redistribution |
| DP Rank | Ranking after redistribution |
| Change Points | Distributed - Original |
| Change Rank | Original Rank - Distributed Rank |
| DCMP Status | Qualification change |
| Event(s) | Redistribution details |

---

# Conditional Formatting

## Change Columns
- Green = positive gain
- Red = negative loss
- White = zero change

## DCMP
- Yellow = qualified for DCMP
- Green = gained qualification
- Red = lost qualification

---

# Demo Teams Removed

The script automatically excludes:
- 9970–9999

These teams:
- do not receive redistributed points
- do not count toward eligible team counts

---

# Common Errors

## 401 Unauthorized

Your TBA API key is invalid.

Fix:
- Check `.env`
- Verify the API key

---

## Permission Denied

Example:

```text
PermissionError: [Errno 13]
```

This means the Excel file is open.

Fix:
- Close the workbook
- Run again

---

# Performance Notes

## Single Year
Usually:
- 30 seconds to 2 minutes

## All Years
Usually:
- several minutes

The regional system is much heavier than districts.

---

# Regional System Notes

Regional redistribution only applies for:
- 2026+
- future regional point systems

Pre-2026 regionals used wildcard advancement and are not modeled.

---

# GitHub Safety

The project uses:
- `.env`
- `.gitignore`

to prevent:
- API keys
- cache files
- generated Excel files

from being uploaded to GitHub.

---

# Terminal Output Example

```text
=== Running 2026 ===

  Checking FIRST California...
  Checking FIRST Chesapeake...
  Checking FIRST in Texas...

  Running 2026 regional model...

2026 completed in 1m 25s

Created frc_district_and_regional_redistribution.xlsx
```

---

# Credits

Data provided by:
- The Blue Alliance API

https://www.thebluealliance.com/