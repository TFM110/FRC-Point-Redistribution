# FRC Point Redistribution Tool

This project analyzes FRC district and regional point systems using The Blue Alliance API.

It simulates a redistribution model where:
- Teams competing at their 3rd+ play do NOT receive points
- Inter-district teams do NOT receive points
- Those removed points are redistributed evenly to eligible teams at that same event
- Demo teams from 9970 to 9999 are ignored
- Regional redistribution works for the new regional point system starting in 2026

The tool exports everything into a formatted Excel workbook.

---

# Features

## District Analysis

- Original district rankings
- Redistributed district rankings
- Rank movement
- Point movement
- DCMP qualification changes
- Actual DCMP advancement counts from TBA
- Inter-district redistribution
- 3rd+ play redistribution
- District tiebreaker logic
- Conditional formatting
- Summary tab

## Regional Analysis

- Regional pool redistribution
- Regional auto-qualifier comparison
- Prevents duplicate auto-qualified teams
- District teams at regionals do not receive points
- 3rd+ regional plays do not receive points
- Regional tiebreaker logic
- Regional Events tab

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
├── .env                                 # ignored by Git
├── .gitignore
├── config.py
├── district_model.py
├── excel_writer.py
├── frc_district_and_regional_redistribution.xlsx   # ignored by Git
├── main.py
├── README.md
├── regional_model.py
├── tba_api.py
└── utils.py
```

---

# API Key Setup

Create a file named:

```text
.env
```

Inside `.env`:

```env
TBA_KEY=YOUR_REAL_TBA_API_KEY
```

Do not put quotes around the key.

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

This is recommended for testing.

---

# Running All Years

Inside `config.py`:

```python
RUN_SINGLE_YEAR = False
```

The script will automatically run:
- 2009 to current completed FRC season
- skips 2020 and 2021

---

# Automatic Season Detection

The script automatically determines the latest valid FRC season.

Logic:
- January to April: previous year
- May to December: current year

This is because the FRC season usually ends in April.

---

# Excel Output

The workbook contains:
- One tab per year
- Districts placed side-by-side
- Regional redistribution tables for 2026+
- Summary tab
- Regional Events tab

---

# Main Columns

| Column | Description |
|---|---|
| Team | FRC team number |
| Original Points | Official points |
| OP Rank | Official ranking |
| Distributed Points | Points after redistribution |
| DP Rank | Ranking after redistribution |
| Change Points | Distributed Points - Original Points |
| Change Rank | Original Rank - Distributed Rank |
| DCMP Status | Whether the team gained or lost DCMP qualification |
| Event(s) | Redistribution details |

---

# District Redistribution Rules

At a district event:
- Teams from that district on their 1st or 2nd play keep their points
- Teams on their 3rd+ play do not receive points
- Teams from another district do not receive points
- Removed points are redistributed to eligible teams at that same event

Redistribution math:

```text
Non-counting team points / number of eligible teams
```

Rounding:
- 1.3 becomes 1
- 1.7 becomes 2
- Anything below 1 still becomes 1

---

# Regional Redistribution Rules

At a regional event:
- Regional teams on their 1st or 2nd play keep their points
- Regional teams on their 3rd+ play do not receive points
- District teams at regionals do not receive points
- Removed points are redistributed to eligible regional teams at that same event
- Already auto-qualified teams are skipped when selecting future auto-qualifiers

---

# Tiebreakers

## District Tiebreakers Used

The script uses these available TBA point fields:

1. Total district points
2. Total playoff points
3. Best playoff points at a single event
4. Total alliance selection points
5. Best alliance selection points at a single event
6. Total qualification points
7. Lower team number as fallback

## Regional Tiebreakers Used

The script uses:

1. Total regional points
2. Best playoff points at a single event
3. Best alliance selection points at a single event
4. Best qualification points at a single event
5. Lower team number as fallback

## Missing Official Tiebreakers

The official manuals also include individual match score tiebreakers.

Those are not included because they require parsing every match score from every event.

---

# Conditional Formatting

## Change Columns

- Green means positive gain
- Red means negative loss
- White means zero change

## DCMP

- Yellow means within DCMP qualification range
- Green means gained DCMP spot
- Red means lost DCMP spot

---

# Demo Teams Removed

The script automatically excludes:

```text
9970 to 9999
```

These teams:
- do not receive redistributed points
- do not create redistributed points
- do not count toward eligible team counts
- do not appear in the final workbook

---

# Common Errors

## 401 Unauthorized

Your TBA API key is invalid or missing.

Fix:
- Check `.env`
- Verify the key on The Blue Alliance account page

---

## Permission Denied

Example:

```text
PermissionError: [Errno 13]
```

This usually means the Excel file is open.

Fix:
- Close the workbook
- Run the script again

---

# Performance Notes

## Single Year

Usually:
- 30 seconds to 2 minutes

## All Years

Usually:
- several minutes

The regional system is heavier than districts because it must compare all regional teams and district teams.

---

# GitHub Safety

The project uses `.env` and `.gitignore` to prevent secrets from being uploaded.

The `.env` file should never be committed.

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

Data provided by The Blue Alliance API:

https://www.thebluealliance.com/