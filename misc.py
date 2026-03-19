#!usr/bin/python
# -*- coding: utf-8 -*-import string

import os
import json
from datetime import datetime, date
import math
import re


MAP_DIM_TILE = 256
MAP_DEFAULT_ZOOM = 14

date_format = r"\d\d\d\d-\d\d-\d\d"
date_regex = re.compile(date_format)
def check_datestr_format(datestr:str) -> bool:
	# check if dates are in isoformat (we don't care if dates are actually correct)
	if datestr is not None and date_regex.match(datestr) is None:
		return False
	return True

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
def pace_to_float(pace_str:str) -> float:
    try:
        minutes, seconds = map(int, pace_str.strip().split(':'))
        return minutes + seconds / 60
    except Exception as e:
        print(f"Fehler beim Parsen von Pace '{pace_str}': {e}")
        return None

# Helper function to transform time in minutes from float to "m:ss"-String
def float_to_pace_str(pace_float:float) -> str:
    total_seconds = int(round(pace_float * 60))
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes}:{seconds:02d}"
	
def format_time(seconds:int) -> str:
	'''
	formats an int of time in seconds into a string of min:sec
	'''
	if seconds <= 0 or seconds is None:
		return None
	minutes = int(seconds // 60)
	secs = int(seconds % 60)
	return f"{minutes}:{secs:02}"

def parse_full_date(date_str:str) -> datetime.date:
	# date_str: in format YYYY-MM-DDT....
	try:
		date_part = date_str.split('T')[0] if date_str else None
		date_as_date = datetime.strptime(date_part, '%Y-%m-%d').date() if date_part else None
		return date_as_date 
	except Exception as e:
		print(f"Error while parsing date '{date_str}': {e}")
		return None
		
def parse_isodatestring(date_str:str) -> datetime.date:
	'''
	Parses a string in format YYYY-MM-DD to the corresponding datetime.date-object
	'''
	if date_str is None:
		return None
	datesplit = date_str.split('-')
	return date(int(datesplit[0]), int(datesplit[1]), int(datesplit[2]))

def latlong_to_merccoords(lat:float, lon:float, zoom:int=MAP_DEFAULT_ZOOM):
	'''
	computes the (x,y)-coordinates from (latitude, longitude) data, to fetch map tiles from mercerator projected online map service

	maths from https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Derivation_of_tile_names
	'''
	x = int((lon+180)/360 * 2**zoom)
	y = int((1-(math.log(math.tan(lat*(math.pi/180))+(1/(math.cos(lat*(math.pi/180))))))/math.pi)*2**(zoom-1))
	return (x,y)

def tile_xy_to_latlon(x:int, y:int, zoom:int=MAP_DEFAULT_ZOOM):
	lon = (x/(2**zoom))*360-180
	lat = math.atan(math.sinh(math.pi-(y/2**zoom)*2*math.pi))*(180/math.pi)
	return (lat, lon)

def check_daterange(datestring:datetime.date, min_date:datetime.date, max_date:datetime.date) -> bool:
	'''
	datestring: specifies a date in the format DD.MM.YYYY
	Checks if the date specified by datestring is within [self.min_date, self.max_date]
	If one of min_date, max_date is None, interval is considered to be open (in that direction)
	'''
	if min_date is not None and min_date > datestring:
		# datestring before min_date
		return False
	if max_date is not None and max_date < datestring:
		# datestring after max_date
		return False
	return True