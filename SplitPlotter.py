#!usr/bin/python
# -*- coding: utf-8 -*-import string

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.lines import Line2D
import datetime

from DataHandler import DataHandler
from misc import check_datestr_format
from org import VALID_AXIS_KEYS, MARKERSCALE, VALID_ACTIVITY_TYPES


class SplitPlotter():
	def __init__(self, activity_type:str="running", splitlength:int=1000, min_date:str=None, max_date:str=None):
		if activity_type not in VALID_ACTIVITY_TYPES:
			raise ValueError("activity_type has to be one of \"cycling\", \"running\", \"swimming\", \"multi_sport\", \"fitness_equipment\", \"hiking\", \"walking\", \"other\"")
		self.activity_type = activity_type
		if splitlength <= 0:
			raise ValueError("splitlength hast to be a positive number.")
		self.splitlength = splitlength

		# check if dates are correct:
		if not check_datestr_format(min_date):
			raise ValueError("min_date has to be in isoformat YYYY-MM-DD")
		self.min_date = min_date
		if not check_datestr_format(max_date):
			raise ValueError("max_date has to be in isoformat YYYY-MM-DD")
		self.max_date = max_date

		dh = DataHandler()
		self.activity_data = dh.get_data(self.activity_type, self.min_date, self.max_date, require_fulldata=True, splitlength=self.splitlength)

	def plot_scatter(self, axis_x_key:str="pace", axis_y_key:str="avg_heartrate", axis_size_key:str="elevation_gain", axis_color_key:str="date"):
		'''
		generates a scatter plot of split data

		splits: a list of SplitData
		axis_x_key, axis_y_key, axis_size_key, axis_color_key: each have to be one of
			"elapsed_time", "pace", "elevation_gain", "avg_heartrate", "previous_distance", "previous_elevation", "date"
		axis_size_key and axis_color_key can be None, optionally
		'''
		if axis_x_key not in VALID_AXIS_KEYS:
			raise ValueError("Invalid axis_x_key:",axis_x_key)
		if axis_y_key not in VALID_AXIS_KEYS:
			raise ValueError("Invalid axis_x_key:",axis_y_key)
		if axis_size_key is not None and axis_size_key not in VALID_AXIS_KEYS:
			raise ValueError("Invalid axis_x_key:",axis_size_key)
		if axis_color_key is not None and axis_color_key not in VALID_AXIS_KEYS:
			raise ValueError("Invalid axis_x_key:",axis_color_key)

		if len(self.activity_data) == 0:
			# no data, abort
			return

		x_values = []
		y_values = []
		color_values = []
		size_values = []
		for activity in self.activity_data:
			print ("add splits from activity", activity.activity_id)
			for split in activity.splits:
				if "date" in [axis_x_key, axis_y_key, axis_size_key, axis_color_key]:
					# if required, add date to splitdata to simplify data collection:
					split["date"] = activity.date
				x_values.append(split[axis_x_key])
				y_values.append(split[axis_y_key])
				if axis_color_key is not None:
					color_values.append(split[axis_color_key])
				if axis_size_key is not None:
					size_values.append(split[axis_size_key])

		# some values need processing to be plotted:
		# turn date-strings into ordinals:
		if axis_x_key == "date":
			x_values = [x.toordinal() for x in x_values]
		if axis_y_key == "date":
			y_values = [y.toordinal() for y in y_values]
		if axis_color_key is not None and axis_color_key == "date":
			color_values = [c.toordinal() for c in color_values]
		if axis_size_key is not None and axis_size_key == "date":
			size_values = [s.toordinal() for s in size_values]

		# normalize size:
		if axis_size_key is not None:
			min_size = min(size_values)
			max_size = max(size_values)
			diff_size = max_size-min_size
			size_values = [(0.1+(s-min_size)/diff_size)*MARKERSCALE for s in size_values]

		# plotting:
		plt.figure(figsize=(10, 6))
		#plt.scatter(x_vals_hl, y_vals_hl, s=sizes_hl, c='red', alpha=1, marker='*')
		if axis_size_key is None and axis_color_key is None:
			sct = plt.scatter(x_values, y_values, alpha=0.7)
		elif axis_size_key is None:
			sct = plt.scatter(x_values, y_values, c=color_values, cmap='viridis', alpha=0.7)
		elif axis_color_key is None:
			sct = plt.scatter(x_values, y_values, s=size_values, alpha=0.7)
		else:
			sct = plt.scatter(x_values, y_values, s=size_values, c=color_values, cmap='viridis', alpha=0.7)
		
		ax = plt.gca()
		# invert axis of pace (so it reads from slower to faster:)
		if axis_x_key == "pace":
			ax.invert_xaxis()
		if axis_y_key == "pace":
			ax.invert_yaxis()
	
		# ticks and axes labels
		x_ticks, x_ticklabels, x_unit = self._construct_ticks(x_values, axis_x_key)
		plt.xticks(x_ticks, x_ticklabels, rotation=45)
		plt.xlabel(axis_x_key+x_unit)
		y_ticks, y_ticklabels, y_unit = self._construct_ticks(y_values, axis_y_key)
		plt.yticks(y_ticks, y_ticklabels, rotation=45)
		plt.ylabel(axis_y_key+y_unit)

		# colorbar:
		if axis_color_key is not None:
			all_col_ticks, all_col_ticklabels, col_unit = self._construct_ticks(color_values, axis_color_key)
			# thin out ticks if too many:
			n_ticks = len(all_col_ticks)
			if n_ticks > 5:
				col_ticks = [all_col_ticks[i] for i in range(n_ticks) if i%(n_ticks//5)==0]
				col_ticklabels = [all_col_ticklabels[i] for i in range(n_ticks) if i%(n_ticks//5)==0]
			else:
				col_ticks = all_col_ticks
				col_ticklabels = all_col_ticklabels
			cbar = plt.colorbar(sct, orientation='horizontal', pad=0.1, aspect=30)
			cbar.set_label(axis_color_key+col_unit)
			cbar.set_ticks(col_ticks)
			cbar.set_ticklabels(col_ticklabels)

		# point size legend:
		if axis_size_key is not None:
			size_ticks, size_ticklabels, size_unit = self._construct_ticks(size_values, axis_size_key)
			min_val = min(size_ticks)
			max_val = max(size_ticks)
			sample_values = [min_val, (min_val+max_val)//2, max_val]
			legend_elements = [
				Line2D([0], [0], marker='o', color='w', label=f'{s} m',
					markerfacecolor='gray', markersize=np.sqrt((0.1+(s-min_size)/diff_size)*MARKERSCALE)) for s in sample_values
				]
			plt.legend(handles=legend_elements, title=axis_size_key+size_unit, labelspacing=1)# loc='upper left', 
	
		plt.grid(True, which='both', linestyle='--', alpha=0.5)
		plot_title = "Activity: "+self.activity_type+" - "+str(self.splitlength/1000)+"km-Splits"
		if self.min_date is None and self.max_date is not None:
			plot_title += " - before "+self.max_date
		elif self.min_date is not None and self.max_date is None:
			plot_title += " - since "+self.min_date
		elif self.min_date is not None and self.max_date is not None:
			plot_title +=  "- between "+self.min_date+" and "+self.max_date
		plt.title(plot_title)
		plt.show()

	def _construct_ticks(self, values, axis_key):
		minval, maxval = min(values), max(values)
		if axis_key == "pace":
			# 1 tick = 15sec/km
			ticks = np.arange(15*np.floor(minval/15), np.ceil(maxval) + 15, 15)
			ticklabels = [self._parse_pacefloat(t) for t in ticks]
			unit = "min/km"
		elif axis_key == "elevation_gain":
			# 1 tick = 50m
			ticks = np.arange(0, maxval + 50, 50)
			ticklabels = [int(t) for t in ticks]
			unit = "m"
		elif axis_key == "avg_heartrate":
			# 1 tick = 10 bpm
			ticks = np.arange((minval//10)*10, maxval + 10, 10)
			ticklabels = [int(t) for t in ticks]
			unit = "bpm"
		elif axis_key == "elapsed_time":
			# 1 tick = 1minute
			ticks = np.arange(0, np.ceil(maxval) + 60, 60)
			ticklabels = [str(int(t/60))+":"+str(int(t%60)) for t in ticks]
			unit = "min:sec"
		elif axis_key == "previous_elapsed_time":
			# 1 tick = 15 minutes
			ticks = np.arange(0, np.ceil(maxval) + 300, 900)
			ticklabels = [str(int(t/3600))+":"+str(int(t/60)) for t in ticks]
			unit = "h:min"
		elif axis_key == "previous_distance":
			# 1 tick = 5 km
			ticks = np.arange(0, np.ceil(maxval) + 1000, 5000)
			ticklabels = [int(t/1000) for t in ticks]
			unit = "km"
		elif axis_key == "previous_elevation":
			# 1 tick = 100m
			ticks = np.arange(0, np.ceil(maxval) + 100, 100)
			ticklabels = [int(t) for t in ticks]
			unit = "m"
		elif axis_key == "date":
			# todo: 1tick = 1 month ?
			# currently: 1 tick = 1/10 of range
			ticks = np.arange(minval, maxval, (maxval-minval)/10)
			ticklabels = [datetime.date.fromordinal(int(t)) for t in ticks]
			unit = ""
		if not unit == "":
			unit = " ("+unit+")"
		return ticks, ticklabels, unit

	def _parse_pacefloat(self, pace:float) -> str:
		return str(int(pace//60))+":"+str(int(pace%60))

if __name__ == '__main__':
	#ap = ActivityParser("running", min_date="01.01.2026", max_date="01.02.2026")
	mind = "2024-01-01"
	maxd = None#"2026-03-01"
	sl = 5000

	sp = SplitPlotter(splitlength=sl, min_date=mind, max_date=maxd)
	#"elapsed_time", "pace", "elevation_gain", "avg_heartrate", "previous_distance", "previous_elevation", "date"
	sp.plot_scatter(axis_x_key="date", axis_y_key="avg_heartrate", axis_color_key="pace", axis_size_key="elevation_gain")