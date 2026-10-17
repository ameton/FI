# Site Parser Parsing Method

This method is used to extract fishing schedule data from web pages and convert it into a CSV format.

## Process
1.  **Fetch Content**: Use `webfetch` to retrieve the page content.
2.  **Analyze Structure**: Identify the recurring patterns for each date (Date, Day, Tide, Target Fish, etc.).
3.  **Extraction**: Parse the data into the following CSV structure:
    `Date,Day,Tide,BoatName,TargetFish,OperatingHours,Status,Reservations,Available`
4.  **Save**: Write the structured data to a `.csv` file.
