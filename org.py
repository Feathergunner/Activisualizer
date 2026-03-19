#!usr/bin/python
# -*- coding: utf-8 -*-import string

DIR_DOWNLOAD = "full_activity_data"
DIR_PARSED = "parsed_activity_data"

VALID_ACTIVITY_TYPES = ["cycling", "running", "swimming", "multi_sport", "fitness_equipment", "hiking", "walking", "other"]

# parsing:
METRICS_OF_INTEREST = ["sumDistance", "sumDuration", "directElevation", "directHeartRate", "directLongitude", "directLatitude"]

# plotting:
VALID_AXIS_KEYS = ["elapsed_time", "pace", "elevation_gain", "avg_heartrate", "previous_distance", "previous_elapsed_time", "previous_elevation", "date"]
MARKERSCALE = 100