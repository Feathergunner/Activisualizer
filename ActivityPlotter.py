#!usr/bin/python
# -*- coding: utf-8 -*-import string

from matplotlib import pyplot as plt
import matplotlib as mpl

from DataHandler import DataHandler
from misc import check_datestr_format
from org import METRICS_OF_INTEREST, VALID_ACTIVITY_TYPES

class ActivityPlotter:
	'''
	Plots activity progress as a single lineplot, not aggregated into splits.

	For example: elevation profiles or cumulative elevation
	'''
	valid_axis_keys = METRICS_OF_INTEREST+["deltaElevation", "cumulativeElevation"]

	def __init__(self):
		self.activity_type = None
		self.min_date = None
		self.max_date = None
		self.delta_x = False
		self.delta_y = False
		self.sum_x = False
		self.sum_y = False
		self.plotdata = None

	def plot_activities(self, activity_type:str="running", min_date:str=None, max_date:str=None, axis_x_key:str="sumDistance", axis_y_key:str="directElevation"):
		'''
		
		'''

		# check if inputs are correct:
		if activity_type not in VALID_ACTIVITY_TYPES:
			raise ValueError("Unknown activity_type:", activity_type)
		self.activity_type = activity_type
		# check if dates are correct:
		if not check_datestr_format(min_date):
			raise ValueError("min_date has to be in isoformat YYYY-MM-DD")
		self.min_date = min_date
		if not check_datestr_format(max_date):
			raise ValueError("max_date has to be in isoformat YYYY-MM-DD")
		self.max_date = max_date
		# check axis keys:
		if axis_x_key not in ActivityPlotter.valid_axis_keys:
			raise ValueError("Unknown axis_x_key:",axis_x_key)
		if axis_x_key == "cumulativeElevation":
			self.axis_x_key = "directElevation"
			self.delta_x = True
			self.sum_x = True
		elif axis_x_key == "deltaElevation":
			self.axis_x_key = "directElevation"
			self.delta_x = True
			self.sum_x = False
		else:
			self.axis_x_key = axis_x_key
			self.delta_x = False
			self.sum_x = False
		if axis_y_key not in ActivityPlotter.valid_axis_keys:
			raise ValueError("Unknown axis_y_key:",axis_y_key)
		if axis_y_key == "cumulativeElevation":
			self.axis_y_key = "directElevation"
			self.delta_y = True
			self.sum_y = True
		elif axis_y_key == "deltaElevation":
			self.axis_y_key = "directElevation"
			self.delta_y = True
			self.sum_y = False
		else:
			self.axis_y_key = axis_y_key
			self.delta_y = False
			self.sum_y = False

		# load data:
		dh = DataHandler()
		activity_data = dh.get_data(self.activity_type, self.min_date, self.max_date, require_fulldata=True)
		if len(activity_data) == 0:
			# no data, abort
			return

		# construct plot:
		self.plotdata = []
		for data in activity_data:
			self.plotdata.append(self._get_activity_plotline(data))

		# normalize color-values:
		min_colorval = min(linedata["color"] for linedata in self.plotdata)
		max_colorval = max(linedata["color"] for linedata in self.plotdata)
		for data in self.plotdata:
			data["color"] = (data["color"]-min_colorval)/(max_colorval-min_colorval+1)

		# plot
		for linedata in self.plotdata:
			plt.plot(linedata["x"], linedata["y"], c=mpl.colormaps["viridis"](linedata["color"]))
			#c=color_values, cmap='viridis'
			#plt.plot(linedata["x"], linedata["y"])#, c=linedata["color"], cmap='viridis')

		plt.xlabel(axis_x_key)
		plt.ylabel(axis_y_key)
		plt.show()

	def _get_activity_plotline(self, activity_data):
		'''
		constructs line data for a single activity
		'''
		
		x = [datapoint[self.axis_x_key] for datapoint in activity_data.datapoints]
		if self.delta_x:
			for i in range(len(x)-1, 0, -1):
				x[i] = x[i]-x[i-1]
			x[0] = 0
		if self.sum_x:
			for i in range(1,len(x)):
				x[i] = max(0, x[i]) + x[i-1]
		y = [datapoint[self.axis_y_key] for datapoint in activity_data.datapoints]
		if self.delta_y:
			for i in range(len(y)-1, 0, -1):
				y[i] = y[i]-y[i-1]
			y[0] = 0
		if self.sum_y:
			for i in range(1, len(y)):
				y[i] = max(0, y[i]) + y[i-1]
		plotdata = {
			"x" : x,
			"y" : y,
			"color" : activity_data.date.toordinal()
		}
		return plotdata

if __name__ == '__main__':
	mind = None#"2026-01-01"
	maxd = None#"2026-03-17"
	type = "running"

	ap = ActivityPlotter()
	# "sumDistance", "sumDuration", "directElevation", "directHeartRate", "directLongitude", "directLatitude", cumulativeElevation, deltaElevation
	ap.plot_activities(type, mind, maxd, axis_x_key="sumDistance", axis_y_key="cumulativeElevation")