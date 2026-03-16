#!usr/bin/python
# -*- coding: utf-8 -*-import string

import os
import json
from datetime import datetime, date
import math


MAP_DIM_TILE = 256
MAP_DEFAULT_ZOOM = 14
# metrics of interest that is kept after parsing:
METRICS_OF_INTEREST = ["sumDistance", "sumDuration", "directElevation", "directHeartRate", "directLongitude", "directLatitude"]

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