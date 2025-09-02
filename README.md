# Worst-Burger
Target is to find worst burger in specific area

Overview

This project scans a defined geographical area using the Google Places API to find burger restaurants, evaluates their ratings, and produces a ranked list of the best and worst burger spots in the region.

It is primarily designed for Istanbul, but can be adapted to any location by adjusting the bounding box coordinates.

------------------------------------------------

Features

🔍 Grid-based scanning with configurable step size and radius

📊 Exports results to CSV with detailed restaurant data

⭐ Highlights Top 10 best and Top 10 worst burger places

🛡 Handles Unicode safely for Turkish characters and international data

⚙️ Customizable parameters: area, step size, search radius, and minimum review count

------------------------------------------------

 Usage
 1)Clone this repository
 git clone https://github.com/your-username/worst-burger-finder.git
 cd worst-burger-finder
 
 2)Install requirements
 pip install requests

 3)Add your Google Places API key in the script
 API_KEY = "YOUR_API_KEY"

 4)Run the program
 
------------------------------------------------

 Configuration

You can edit these parameters inside the script:

AREA_NAME → Region name for scanning

BOUNDS → Coordinates [min_lat, max_lat, min_lng, max_lng]

STEP_SIZE → Grid step size (controls scan density)

SEARCH_RADIUS → Google Places API search radius (meters)

SEARCH_KEYWORD → Keyword for search (default: "burger")

MIN_RATINGS → Minimum number of reviews to include in ranking

------------------------------------------------

Dataset

This repository also includes a CSV file of burger restaurants across large parts of Istanbul, obtained by running this tool. It provides real-world data for analysis, comparison, or further processing.

Notes

⚠️ Scanning large areas can result in many API calls. Ensure you monitor your Google Places API quota.

🌍 This script is not limited to Istanbul—simply change the bounding coordinates to scan other cities.
 


 
