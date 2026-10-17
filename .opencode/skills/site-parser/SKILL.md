---
name: site-parser
description: Parses fishing schedule web pages into structured CSV files. Manages multiple sites, separates seat data, and filters available schedules.
---

# Site Parser Skill

This skill provides a structured approach to extracting fishing schedule data from web pages (specifically those following the sunsang24 structure) and converting them into structured CSV files.

## Workflow

1.  **Define Target Sites**: Maintain a `site_list.csv` file containing the URLs to parse.
2.  **Fetch Content**: Use `webfetch` to retrieve the HTML/Markdown content for each URL in `site_list.csv` for the next 3 months.
3.  **Analyze Structure**: Identify the recurring HTML or text pattern for each day's entry:
    *   Date, Day, Tide, BoatName, TargetFish, OperatingHours, Status
    *   Seats: Total capacity vs. currently reserved.
4.  **Extract & Normalize Data**: Parse the identified fields into a structured format.
5.  **Calculate & Format**:
    *   Split seat information into `예약좌석수` and `총좌석수`.
    *   Determine `예약가능여부` (Y/N) flag based on remaining seats and status.
    *   Structure the data into the required CSV format:
        `날짜,요일,물때,선명,선사위치,대상어종,운항시간,상태,예약좌석수,총좌석수,잔여석,예약가능여부`
6.  **Write Files**:
    *   Save all parsed data to `fishing_schedule.csv`.
    *   Filter for `예약가능여부 == 'Y'` and save those entries to `available_schedules.csv`.
