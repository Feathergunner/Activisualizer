#!usr/bin/python
# -*- coding: utf-8 -*-import string

import os
import json
from datetime import datetime, date

# metrics of interest that is kept after parsing:
METRICS_OF_INTEREST = ["sumDistance", "sumDuration", "directElevation", "directHeartRate"]

def load_json(filepath:str):
	with open(filepath, "r", encoding="utf-8") as f:
		return json.load(f)

def save_json(data, filepath:str):
	with open(filepath, "w", encoding="utf-8") as f:
		json.dump(data, f, indent=2)
		
def display_json(title:str, jsondata):
    """Format API output for better readability."""
    dashed = "-"*20
    header = f"{dashed} {title} {dashed}"
    footer = "-"*len(header)
    print(header)
    print(json.dumps(jsondata, indent=4))
    print(footer)
	
def ensure_dir_exists(directory:str):
	if not os.path.exists(directory):
		os.makedirs(directory)
		

# Helper function to transform pace time from "m:ss"-format to float
def pace_to_float(pace_str:str):
    try:
        minutes, seconds = map(int, pace_str.strip().split(':'))
        return minutes + seconds / 60
    except Exception as e:
        print(f"Fehler beim Parsen von Pace '{pace_str}': {e}")
        return None

# Helper function to transform time in minutes from float to "m:ss"-String
def float_to_pace_str(pace_float:float):
    total_seconds = int(round(pace_float * 60))
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes}:{seconds:02d}"
	
def parse_full_date(date_str:str) -> datetime.date:
	# date_str: in format YYYY-MM-DDT....
	try:
		date_part = date_str.split('T')[0] if date_str else None
		date_as_date = datetime.strptime(date_part, '%Y-%m-%d').date() if date_part else None
		return date_as_date 
	except Exception as e:
		print(f"Error while parsing date '{date_str}': {e}")
		return None
		
def parse_datestring(date_str:str) -> datetime.date:
	# date_str: in format DD.MM.YYYY
	if date_str is None:
		return None
	datesplit = date_str.split('.')
	return date(int(datesplit[2]), int(datesplit[1]), int(datesplit[0]))