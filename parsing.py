#!usr/bin/python
# -*- coding: utf-8 -*-import string

from misc import load_json, save_json

# metrics of interest:
from misc import METRICS_OF_INTEREST


# Get correct numerical ids for the wanted string-keys:
def get_metric_indices(metric_descriptors, wanted_keys):
	key_to_index = {}
	for descriptor in metric_descriptors:
		key = descriptor.get("key")
		idx = descriptor.get("metricsIndex")
		if key in wanted_keys:
			key_to_index[key] = idx
	return key_to_index


# extract wanted data by numerical keys from detail_metrics:
def extract_metrics(detail_metrics, key_to_index):
	extracted = []
	for entry in detail_metrics:
		metrics = entry["metrics"]
		data_point = {}
		for key, idx in key_to_index.items():
			try:
				data_point[key] = metrics[idx]
			except IndexError:
				data_point[key] = None  # optional: handle missing values
		extracted.append(data_point)
	return extracted
	

def extract_data(jsondata:dict):
	# parse raw data:
	metric_descriptors = jsondata["metricDescriptors"]
	detail_metrics = jsondata["activityDetailMetrics"]

	# get metrics and compute splits:
	key_to_index = get_metric_indices(metric_descriptors, METRICS_OF_INTEREST)
	extracted_data = extract_metrics(detail_metrics, key_to_index)
	return extracted_data


# interpolate point, needed to compute exakt 1km-splits
def interpolate_point(a, b, target_distance:int):
	'''
	a,b: data points from detail_metrics
	target_distance: distance at which an interpolated point is required
	'''
	d1 = a["sumDistance"]
	d2 = b["sumDistance"]
	if target_distance < d1 or target_distance > d2:
		print ("Error! Target distance is outside of [a,b]")
		return None
	
	factor = (target_distance - d1) / (d2 - d1) if d2 != d1 else 0
	def interp(key):
		v1 = a[key]
		v2 = b[key]
		if v1 is None or v2 is None:
			return None
		return v1 + (v2 - v1) * factor

	return {
		key: interp(key) for key in a.keys()
	}


def calculate_splits(data_points, split_size:int=1000):
	'''
	aggregates data points into splits of fixed size.
	split_size: split length in meter
	
	returns list of splits, i.e. aggregated data
	'''
	splits = []
	target_distance = split_size
	previous_elevation = 0.0
	current_split = []
	i = 0

	while i < len(data_points) - 1:
		a = data_points[i]
		b = data_points[i + 1]
		current_split.append(a)

		d1 = a["sumDistance"]
		d2 = b["sumDistance"]

		# interpolate if next point is beyond wanted splitlength:
		if d1 < target_distance <= d2:
			interpolated = interpolate_point(a, b, target_distance)
			current_split.append(interpolated)
			
			# get aggregated data:
			split = compute_split(current_split, len(splits), previous_elevation)
			previous_elevation += split["elevationGain"]
			splits.append(split)

			# new split starts at interpolated point:
			current_split = [interpolated]
			# increase target distance for next split:
			target_distance += split_size

		i += 1

	# aggregate remaining datapoints into final inclomplete split:
	if len(current_split) > 1:
		current_split.append(data_points[-1])
		split = compute_split(current_split, len(splits), previous_elevation, is_final=True)
		splits.append(split)

	return splits


def compute_split(block, km_index, previous_elevation, is_final:bool=False):
	'''
	computes aggregated data for a single split:
	'''
	if len(block) < 2:
		return {
			"km": km_index,
			"elapsedTime": None,
			"pace": None,
			"length": None,
			"elevationGain": 0.0,
			"avgHeartRate": None,
			"previousElevation": previous_elevation,
			"isIncomplete": True
		}

	start = block[0]
	end = block[-1]

	# Split-length in meter
	length = end["sumDistance"] - start["sumDistance"]

	# duration in seconds:
	duration = end["sumDuration"] - start["sumDuration"]
	elapsed_time_str = format_pace(duration)

	# compute pace (seconds/km)
	if length > 0 and duration > 0:
		pace_seconds = duration / (length / 1000)
		pace_str = format_pace(pace_seconds)
	else:
		pace_str = None

	# aggregated elevation gain:
	elevation_gain = int(sum(
		max(0, block[i + 1]["directElevation"] - block[i]["directElevation"])
		for i in range(len(block) - 1)
	))

	# average heartrate:
	hr_values = [p["directHeartRate"] for p in block if p["directHeartRate"] is not None]
	avg_hr = int(sum(hr_values) / len(hr_values)) if hr_values else None

	return {
		"km": km_index,
		"elapsedTime": elapsed_time_str,
		"pace": pace_str,
		"length": round(length, 1),
		"elevationGain": round(elevation_gain, 2),
		"avgHeartRate": round(avg_hr, 1) if avg_hr is not None else None,
		"previousElevation": round(previous_elevation, 2),
		"isIncomplete": is_final and (length < 1000)
	}


def format_pace(seconds):
	'''
	format pace into min:sec
	'''
	if seconds <= 0 or seconds is None:
		return None
	minutes = int(seconds // 60)
	secs = int(seconds % 60)
	return f"{minutes}:{secs:02}"


def process_activity(input_path:str, output_path:str, splitlength:int=1000):
	data = load_json(input_path)
	metadata = data["summaryDTO"]
	extracted_data = extract_data(data)
	splits = calculate_splits(extracted_data, splitlength)

	result = {
		"activityId": data.get("activityId"),
		"date": metadata.get("startTimeLocal"),
		"name": data.get("activityName"),
		"totaldist": metadata.get("distance"),
		"totaltime": metadata.get("movingDuration"),
		"totalelevation": metadata.get("elevationGain"),
		"avgHR": metadata.get("averageHR"),
		"splits": splits
	}

	save_json(result, output_path)
	print(f"Parsed data stored in {output_path}")