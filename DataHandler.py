#!usr/bin/python
# -*- coding: utf-8 -*-import string

import os
import datetime

from misc import load_json, save_json, ensure_dir_exists, parse_full_date, parse_isodatestring, check_datestr_format, check_daterange
from org import DIR_DOWNLOAD, DIR_PARSED, METRICS_OF_INTEREST, VALID_ACTIVITY_TYPES

class SplitData():
	'''
	Organizes the aggregated data for a single split.
	'''
	def __init__(self, activity_id:int, split_id:int, datapoints, previous_distance:float, previous_elevation:float, is_incomplete:bool=False):
		self.activity_id:int = activity_id
		self.split_id:int = split_id
		self.elapsed_time:int = None
		self.elapsed_time_str:str = None
		self.length:float = None
		self.pace_seconds:float = None
		self.pace_str:str = None
		self.elevation_gain:float = None
		self.avg_heartrate:float = None
		self.previous_distance:float = previous_distance
		self.previous_elapsed_time:float = None
		self.previous_elevation:float = previous_elevation
		self.is_incomplete:bool = is_incomplete

		# aggregate data:
		data_start = datapoints[0]
		data_end = datapoints[-1]

		# Split-length in meter
		self.length = round(data_end["sumDistance"] - data_start["sumDistance"],1)

		# elapsed time in seconds:
		self.elapsed_time = data_end["sumDuration"] - data_start["sumDuration"]
		#self.elapsed_time_str = format_time(self.elapsed_time)
		self.previous_elapsed_time = data_start["sumDuration"]

		# compute pace (seconds/km)
		if self.length > 0 and self.elapsed_time > 0:
			self.pace_seconds = self.elapsed_time / (self.length / 1000)
			#self.pace_str = format_time(self.pace_seconds)

		# aggregated elevation gain:
		self.elevation_gain = round(int(sum(
			max(0, datapoints[i + 1]["directElevation"] - datapoints[i]["directElevation"])
			for i in range(len(datapoints) - 1)
		)),2)

		# average heartrate:
		hr_values = [data["directHeartRate"] for data in datapoints if data["directHeartRate"] is not None]
		self.avg_heartrate = round(int(sum(hr_values) / len(hr_values)),2) if hr_values else None

	def export_to_dict(self):
		datadict = {
			"activity_id" : self.activity_id,
			"id" : self.split_id,
			"elapsed_time" : self.elapsed_time,
			"length" : self.length,
			"pace" : self.pace_seconds,
			"elevation_gain" : self.elevation_gain,
			"avg_heartrate" : self.avg_heartrate,
			"previous_distance" : self.previous_distance,
			"previous_elapsed_time" : self.previous_elapsed_time,
			"previous_elevation" : self.previous_elevation,
			"is_incomplete" : self.is_incomplete
		}
		return datadict

class ActivityData():
	def __init__(self,
			activity_type:str,
			activity_id:int,
			date:datetime.date,
			name:str,
			totaldist:float,
			totaltime:float,
			totalelevation:float,
			avg_heartrate:float,
			splitlength:int = None,
			datapoints = None,
			splits = None):
		# input format check:
		if activity_type not in VALID_ACTIVITY_TYPES:
			raise ValueError("Unknown activity_type:",activity_type)
		self.activity_type = activity_type
		self.activity_id = activity_id
		self.date = date
		self.name = name
		self.totaldist = totaldist
		self.totaltime = totaltime
		self.totalelevation = totalelevation
		self.avg_heartrate = avg_heartrate
		self.splitlength = splitlength
		self.datapoints = datapoints
		self.add_splitdata(splits)

	def add_splitdata(self, splits):
		if splits is None:
			self.splits = None
		else:
			self.splits = []
			for split in splits:
				if isinstance(split, SplitData):
					self.splits.append(split.export_to_dict())
				else:
					# assume split is already a dict:
					self.splits.append(split)
		#self.splits = [split.export_to_dict() for split in splits] if splits is not None else None

	def save_to_json(self):
		ensure_dir_exists(self._get_output_dir())
		output_path = self._get_output_filename()
		save_json(self._export_to_dict(), output_path)
		print(f"Parsed data stored in {output_path}")

	def _get_output_dir(self):
		return os.path.join(DIR_PARSED, self.activity_type)

	def _get_output_filename(self):
		return os.path.join(self._get_output_dir(), str(self.activity_id)+".json")

	def _export_to_dict(self):
		datadict = {
			"id" : self.activity_id,
			"type" : self.activity_type,
			"name" : self.name,
			"date" : self.date.isoformat(),
			"totaldist" : self.totaldist,
			"totaltime" : self.totaltime,
			"totalelevation" : self.totalelevation,
			"avgHR" : self.avg_heartrate,
			"splitlength" : self.splitlength,
			#"datapoints" : self.datapoints,
			"splits" : self.splits
		}
		return datadict

class DataHandler():
	def __init__(self, force_compute_splits=False):
		self.force_compute_splits = force_compute_splits

	def get_data(self,
			activity_type:str,
			min_date:str=None,
			max_date:str=None,
			latitude_min:float=None,
			latitude_max:float=None,
			longitude_min:float=None,
			longitude_max:float=None,
			require_fulldata:bool=True,
			splitlength:int=None,
			verbose=False):
		'''
		Returns a list of ActivityData that contains all activities
			of specified activity_type and
			within [min_data, max_date] (if these are not None) and
			within specified region of latitude/longitude (if these are not None)
		If require_fulldata, it is ensured that the ActivityData 
			also contains parsed datapoints
			and aggregated splitdata with respect to the specified splitlength.
		'''
		print ("Loading data for activity_type", activity_type, "in date-range",min_date,"-",max_date)
		# check if activity_type is valied:
		if not activity_type in VALID_ACTIVITY_TYPES:
			raise ValueError("Unknown activity_type:", activity_type)
		# check if dates are correct:
		if not check_datestr_format(min_date):
			raise ValueError("min_date has to be in isoformat YYYY-MM-DD.")
		if not check_datestr_format(max_date):
			raise ValueError("max_date has to be in isoformat YYYY-MM-DD.")
		# check if splitlength makes sense:
		if splitlength is not None and splitlength <= 0:
			raise ValueError("splitlength has to be a positive number.")
		#if require_fulldata and splitlength is None:
		#	raise Exception("Splitlength has to be specified!")

		# load data:
		activities = []
		datadir = os.path.join(DIR_DOWNLOAD, activity_type)
		ensure_dir_exists(datadir)
		if verbose:
			print ("check files in directory",datadir)
		for filename in os.listdir(datadir):
			if filename.endswith(".json"):
				if verbose:
					print (". checking file",filename)
				jsondata = load_json(os.path.join(datadir, filename))
				data_is_in_range = True
				if not check_daterange(parse_full_date(jsondata["summaryDTO"]["startTimeLocal"]), parse_isodatestring(min_date), parse_isodatestring(max_date)):
					data_is_in_range = False
				if latitude_min is not None and jsondata["summaryDTO"]["startLatitude"] < latitude_min:
					data_is_in_range = False
				if latitude_max is not None and jsondata["summaryDTO"]["startLatitude"] > latitude_max:
					data_is_in_range = False
				if longitude_min is not None and jsondata["summaryDTO"]["startLongitude"] < longitude_min:
					data_is_in_range = False
				if longitude_max is not None and jsondata["summaryDTO"]["startLongitude"] > longitude_max:
					data_is_in_range = False
				if data_is_in_range:
					if verbose:
						print (".. adding to dataset")
					if require_fulldata:
						activities.append(self._get_activity_fulldata(activity_type, jsondata, splitlength))
					else:
						activities.append(self._get_activity_metadata(activity_type, jsondata))
				else:
					if verbose:
						print (".. data not within specified range")

		print ("Loaded "+str(len(activities))+" activities.")
		if len(activities) == 0:
			print ("NO ACTIVITIES FOUND! Make sure you specified a correct range of dates and parameters and have your activity data downloaded.")
		return activities

	def _get_activity_metadata(self, activity_type:str, fulldata:dict, splitlength:int=None) -> ActivityData:
		'''
		Returns an instance of ActivityData, but without datapoints and splits

		fulldata: a dict loaded from a json file constructed by GarminDataDownloader
		'''
		summarydata = fulldata.get("summaryDTO")

		return ActivityData(
			activity_type = activity_type,
			activity_id = fulldata.get("activityId"),
			date = parse_full_date(summarydata.get("startTimeLocal")),
			name = fulldata.get("activityName"),
			totaldist = summarydata.get("distance"),
			totaltime = summarydata.get("movingDuration"),
			totalelevation = summarydata.get("elevationGain"),
			avg_heartrate = summarydata.get("averageHR"),
			splitlength = splitlength)

	def _get_activity_fulldata(self, activity_type, fulldata:dict, splitlength:int=1000) -> ActivityData:
		'''
		Returns an instance of ActivityData, including splits and simplified datapoints

		fulldata: a dict loaded from a json file constructed by GarminDataDownloader
		'''
		activity_data = self._get_activity_metadata(activity_type, fulldata, splitlength)
		activity_data.datapoints = self._extract_data(fulldata)

		# check if file with parsed splitdata exists:
		splitdata = None
		parseddatafile = os.path.join(DIR_PARSED, activity_type, str(activity_data.activity_id)+".json")
		require_compute_splits = False
		if splitlength is not None:
			if self.force_compute_splits:
				require_compute_splits = True
			elif not os.path.isfile(parseddatafile):
				# splitdata does not exist:
				require_compute_splits = True
			else:
				parseddata = load_json(parseddatafile)
				if parseddata.get("splitlength") != splitlength:
					# wrong splitlength
					require_compute_splits = True
					splitdata = None
		if require_compute_splits:
			# compute splits:
			print ("compute splits for activity", activity_data.activity_id)
			splitdata = self._construct_splits(activity_data.activity_id, activity_data.datapoints, splitlength)
		elif splitlength is not None:
			splitdata = parseddata.get("splits")
		if splitlength is not None:
			activity_data.add_splitdata(splitdata)
		if require_compute_splits:
			# save newly computed splitdata for future use:
			activity_data.save_to_json()
		return activity_data

	def _construct_splits(self, activity_id, datapoints, splitlength:int=1000):
		print ("... Compute splits...")
		# init data structure:
		splits = []
		# distance at which the next split is completed:
		current_target_distance = splitlength
		# keep track of elevation gain:
		previous_elevation = 0.0
		# keep track of distance:
		previous_distance = 0.0
		# keep track of elapsed time:
		elapsed_time = 0.0
		# keep track of current split:
		current_split_datapoints = []

		# iterate through activity data:
		i = 0
		while i < len(datapoints) - 1:
			current_split_datapoints.append(datapoints[i])
			# check if split is completed:
			# that is, if at point i, the total distance has not reached the target distance,
			#	but at point i+1, total distance is at least the target distance,
			# that is, split is completed somewhere between i and i+1
			if datapoints[i]["sumDistance"] < current_target_distance <= datapoints[i+1]["sumDistance"]:
				# compute the interpolated point where split is exactly completed:
				interpolated_point = self._interpolate_point(datapoints[i], datapoints[i+1], current_target_distance)
				current_split_datapoints.append(interpolated_point)
				# computed the aggregated split data:
				new_split = SplitData(activity_id, len(splits), current_split_datapoints, previous_distance, previous_elevation)
				splits.append(new_split)
				# init temp data for next split:
				previous_distance += splitlength
				previous_elevation += new_split.elevation_gain
				current_target_distance += splitlength
				current_split_datapoints = [interpolated_point]
			i += 1

		# aggregate remaining datapoints into a final inclomplete split:
		if len(current_split_datapoints) > 1:
			current_split_datapoints.append(datapoints[-1])
			final_split = SplitData(activity_id, len(splits), current_split_datapoints, previous_distance, previous_elevation, is_incomplete=True)
			splits.append(final_split)
		return splits


	# Get correct numerical ids for the wanted string-keys:
	def _get_metric_indices(self, metric_descriptors, wanted_keys):
		key_to_index = {}
		for descriptor in metric_descriptors:
			key = descriptor.get("key")
			idx = descriptor.get("metricsIndex")
			if key in wanted_keys:
				key_to_index[key] = idx
		return key_to_index
	
	# extract wanted data by numerical keys from detail_metrics:
	def _extract_metrics(self, detail_metrics, key_to_index):
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

	def _extract_data(self, jsondata:dict):
		# parse raw data:
		metric_descriptors = jsondata["metricDescriptors"]
		detail_metrics = jsondata["activityDetailMetrics"]
	
		# get metrics and compute splits:
		key_to_index = self._get_metric_indices(metric_descriptors, METRICS_OF_INTEREST)
		extracted_data = self._extract_metrics(detail_metrics, key_to_index)
		return extracted_data

	# interpolate point, needed to compute exakt 1km-splits
	def _interpolate_point(self, point_a, point_b, target_distance:int):
		'''
		point_a, point_b: data points from detail_metrics
		target_distance: distance at which an interpolated point is required
		'''
		d1 = point_a["sumDistance"]
		d2 = point_b["sumDistance"]
		if target_distance < d1 or target_distance > d2:
			print ("Error! Target distance is outside of [a,b]")
			return None
		factor = (target_distance - d1) / (d2 - d1) if d2 != d1 else 0
		def interp(key):
			v1 = point_a[key]
			v2 = point_b[key]
			if v1 is None or v2 is None:
				return None
			return v1 + (v2 - v1) * factor
	
		return {
			key: interp(key) for key in point_a.keys()
		}
