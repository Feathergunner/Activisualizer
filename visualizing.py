#!usr/bin/python
# -*- coding: utf-8 -*-import string

import os
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
from matplotlib.lines import Line2D

from misc import load_json, pace_to_float, float_to_pace_str, parse_full_date, parse_datestring

MARKERSCALE = 5
MARKERSCALE_DIST = 0.1

def visualize_activity_data(datadir:str, min_date:str="01.01.2000", activitytype:str="Unknown"):
	'''
	datadir: directory where parsed jsons with splitdata are located
	min_date: earliest considered date, in format DD.MM.YYYY
	activitytype
	'''
	if min_date is None:
		min_date = "01.01.2000"
	min_date_obj = parse_datestring(min_date)
	
	num_highlighted_ids = 0
	
	# compute total distance and total time
	totaldist = 0
	totaltime = 0
	
	# load data from jsons and find top ids (i.e. latest activities) that are to be highlighted in plot
	all_data = []
	highlighted_ids = []
	for filename in os.listdir(datadir):
		if filename.endswith('.json'):
			filepath = os.path.join(datadir, filename)
			data = load_json(filepath)
			all_data.append(data)
			date_str = data.get('date')
			
			activity_id = int(data.get('activityId'))
			if len(highlighted_ids) < num_highlighted_ids:
				highlighted_ids.append(activity_id)
				highlighted_ids.sort()
			elif num_highlighted_ids > 0 and activity_id > highlighted_ids[0]:
				highlighted_ids[0] = activity_id
				highlighted_ids.sort()
				
	x_vals, y_vals, sizes, color_ids = [], [], [], []
	x_vals_hl, y_vals_hl, sizes_hl = [], [], []
	
	for data in all_data:
		splits = data.get('splits', [])
		date_str = data.get('date')
		activity_id = int(data.get('activityId'))
		# parse date from date-string:
		date_obj = parse_full_date(date_str)
		
		# check if date is after minimum date:
		if date_obj < min_date_obj:
			continue
			
		activitydist = data.get('totaldist')
		activitytime = data.get('totaltime')
		totaldist += activitydist
		totaltime += activitytime
		# compute speed & pace:
		# pace in min/km
		pace = (data.get('totaltime')/60)/(data.get('totaldist')/1000)
		# speed in km/h:
		speed = (data.get('totaldist')/1000)/(data.get('totaltime')/(60*60))
		print ("dist:", activitydist, "time:", activitytime, "pace:", pace, "speed:", speed)
		if activitytype == "running":
			x_vals.append(pace)
		else:
			x_vals.append(speed)
		y_vals.append(data.get('avgHR'))
		sizes.append(data.get('totaldist') * MARKERSCALE_DIST)
		color_ids.append(date_obj.toordinal() if date_obj else 0)
			
		if activity_id in highlighted_ids:
			x_vals_hl.append(speed)
			y_vals_hl.append(data.get('avgHR'))
			sizes_hl.append(data.get('totaldist') * MARKERSCALE_DIST+1)
			
	print (x_vals)
	print (y_vals)
		
	print ("Total distance: "+str(int(totaldist))+"m")
	t_hours = int(totaltime//(3600))
	t_minutes = int((totaltime%3600)//60)
	t_seconds = int(totaltime%60)
	print ("Total time: "+str(t_hours)+":"+str(t_minutes)+":"+str(t_seconds))
	
	plt.figure(figsize=(10, 6))
	plt.scatter(x_vals_hl, y_vals_hl, s=sizes_hl, c='red', alpha=1, marker='*')
	sct = plt.scatter(x_vals, y_vals, s=sizes, c=color_ids, cmap='viridis', alpha=0.7)
	plt.xlabel('Pace (min/km)')
	plt.ylabel('Avg Heart Rate (bpm)')
	if activitytype == "running":
		plt.title("Activity: "+activitytype+" - Pace vs Avg Heart Rate")
	else:
		plt.title("Activity: "+activitytype+" - Speed vs Avg Heart Rate")
		
	if color_ids:
		valid_dates = [d for d in color_ids if d != 0]
		min_date, max_date = min(valid_dates), max(valid_dates)
		ticks = np.linspace(min_date, max_date, 6)
		cbar = plt.colorbar(sct, orientation='horizontal', pad=0.1, aspect=30)
		cbar.set_label('Date')
		cbar.set_ticks(ticks)
		cbar.set_ticklabels([datetime.fromordinal(int(t)).strftime('%Y-%m-%d') for t in ticks])
	
	# Legend for marker-sizes 
	# example marker sizes:
	sample_dists = [1000, 5000, 20000]
	legend_elements = [
		Line2D([0], [0], marker='o', color='w', label=f'{e} m',
			markerfacecolor='gray', markersize=np.sqrt(e * MARKERSCALE_DIST)) for e in sample_dists
	]
	plt.legend(handles=legend_elements, title='Distance(m)', loc='upper left', labelspacing=1)
	
	ax = plt.gca()
	ax.invert_xaxis()
	
	# ticks and axes labels
	x_min, x_max = min(x_vals), max(x_vals)
	y_min, y_max = min(y_vals), max(y_vals)
	x_ticks = np.arange(np.floor(x_min), np.ceil(x_max) + 0.25, 0.25)
	plt.xticks(x_ticks, [float_to_pace_str(t) for t in x_ticks], rotation=45)
	y_ticks = np.arange((y_min // 10) * 10, (y_max // 10 + 1) * 10, 10)
	plt.yticks(y_ticks)
	
	plt.grid(True, which='both', linestyle='--', alpha=0.5)
	plt.tight_layout()
	plt.show()

def visualize_split_data(datadir:str, minimum_heartrate:int=100, maximum_pace:int=12, min_date:str="01.01.2000", splitlength:int=1000, minelevation:int=0, activitytype:str="Unknown"):
	'''
	datadir: directory where parsed jsons with splitdata are located
	minimum_heartrate: splits with lower heartrate are ignored
	maximum_pace pace: splits with higher (i.e. slower) pace (min/km) are ignored
	min_date: earliest considered date, in format DD.MM.YYYY
	splitlength
	minelevation: minimum elevation gain, splits with less elevation are ignored
	activitytype
	'''
	if min_date is None:
		min_date = "01.01.2000"
	min_date_obj = parse_datestring(min_date)
	
	num_highlighted_ids = 1
	
	# compute total distance and total time
	totaldist = 0
	totaltime = 0
	
	# load data from jsons and find top ids (i.e. latest activities) that are to be highlighted in plot
	all_data = []
	highlighted_ids = []
	for filename in os.listdir(datadir):
		if filename.endswith('.json'):
			filepath = os.path.join(datadir, filename)
			data = load_json(filepath)
			all_data.append(data)
			splits = data.get('splits', [])
			date_str = data.get('date')
			
			activity_id = int(data.get('activityId'))
			if len(highlighted_ids) < num_highlighted_ids:
				highlighted_ids.append(activity_id)
				highlighted_ids.sort()
			elif num_highlighted_ids > 0 and activity_id > highlighted_ids[0]:
				highlighted_ids[0] = activity_id
				highlighted_ids.sort()
	#print (highlighted_ids)
	
	x_vals, y_vals, sizes, color_ids = [], [], [], []
	x_vals_hl, y_vals_hl, sizes_hl = [], [], []
	
	for data in all_data:
		splits = data.get('splits', [])
		date_str = data.get('date')
		activity_id = int(data.get('activityId'))
		# parse date from date-string:
		date_obj = parse_full_date(date_str)
		
		# check if date is after minimum date:
		if date_obj < min_date_obj:
			continue
		totaldist += data.get('totaldist')
		totaltime += data.get('totaltime')

		# get split data:
		for split in splits:
			pace_str = split.get('pace')
			heart_rate = split.get('avgHeartRate')
			elevation_gain = split.get('elevationGain', 0)

			if not pace_str or heart_rate is None:
				continue
				
			# ignore partial splits that are less then 50% of splitlength:
			if int(split.get('length')) < 0.5*splitlength:
				continue

			# ignore splits where heartrate is unrealistically low:
			if heart_rate < minimum_heartrate:
				continue

			pace_float = pace_to_float(pace_str)
			if pace_float is None:
				continue
				
			# ignore splits that are very slow (i.e. probably contain a break) to keep plot concise:
			if pace_float > maximum_pace:
				continue
			
			if elevation_gain < minelevation:
				continue

			x_vals.append(pace_float)
			y_vals.append(heart_rate)
			sizes.append(elevation_gain * MARKERSCALE)
			color_ids.append(date_obj.toordinal() if date_obj else 0)
			
			if activity_id in highlighted_ids:
				x_vals_hl.append(pace_float)
				y_vals_hl.append(heart_rate)
				sizes_hl.append(elevation_gain * MARKERSCALE+1)
				#color_ids_hl.append(date_obj.toordinal() if date_obj else 0)
			#	continue
	
	print ("Total distance: "+str(int(totaldist))+"m")
	t_hours = int(totaltime//(3600))
	t_minutes = int((totaltime%3600)//60)
	t_seconds = int(totaltime%60)
	print ("Total time: "+str(t_hours)+":"+str(t_minutes)+":"+str(t_seconds))
	
	plt.figure(figsize=(10, 6))
	plt.scatter(x_vals_hl, y_vals_hl, s=sizes_hl, c='red', alpha=1, marker='*')
	sct = plt.scatter(x_vals, y_vals, s=sizes, c=color_ids, cmap='viridis', alpha=0.7)
	plt.xlabel('Pace (min/km)')
	plt.ylabel('Avg Heart Rate (bpm)')
	plt.title("Activity: "+activitytype+" - "+str(splitlength/1000)+"km-Splits: Pace vs Avg Heart Rate")
	
	if color_ids:
		valid_dates = [d for d in color_ids if d != 0]
		min_date, max_date = min(valid_dates), max(valid_dates)
		ticks = np.linspace(min_date, max_date, 6)
		cbar = plt.colorbar(sct, orientation='horizontal', pad=0.1, aspect=30)
		cbar.set_label('Date')
		cbar.set_ticks(ticks)
		cbar.set_ticklabels([datetime.fromordinal(int(t)).strftime('%Y-%m-%d') for t in ticks])
	
	# Legend for marker-sizes 
	# example marker sizes:
	sample_elevations = [100, 50, 10]
	legend_elements = [
		Line2D([0], [0], marker='o', color='w', label=f'{e} m',
			markerfacecolor='gray', markersize=np.sqrt(e * MARKERSCALE)) for e in sample_elevations
	]
	plt.legend(handles=legend_elements, title='Altitude Inc. (m/split)', loc='upper left', labelspacing=1)
	
	ax = plt.gca()
	ax.invert_xaxis()
	
	# ticks and axes labels
	x_min, x_max = min(x_vals), max(x_vals)
	y_min, y_max = min(y_vals), max(y_vals)
	x_ticks = np.arange(np.floor(x_min), np.ceil(x_max) + 0.25, 0.25)
	plt.xticks(x_ticks, [float_to_pace_str(t) for t in x_ticks], rotation=45)
	y_ticks = np.arange((y_min // 10) * 10, (y_max // 10 + 1) * 10, 10)
	plt.yticks(y_ticks)
	
	plt.grid(True, which='both', linestyle='--', alpha=0.5)
	plt.tight_layout()
	plt.show()
