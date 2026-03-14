#!usr/bin/python
# -*- coding: utf-8 -*-import string

import os
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.lines import Line2D
import numpy as np
from datetime import datetime, timedelta

from misc import load_json, pace_to_float, float_to_pace_str, parse_full_date, parse_datestring, METRICS_OF_INTEREST
from parsing import get_metric_indices, extract_metrics, extract_data


def generate_elevation_profile_single(filename):
	jsondata = load_json(filename)
	extracted_data = extract_data(jsondata)
	
	dist = [datapoint["sumDistance"] for datapoint in extracted_data]
	elevation = [datapoint["directElevation"] for datapoint in extracted_data]
	plotdata = {
		"date" : parse_full_date(jsondata["summaryDTO"].get("startTimeLocal")),
		"x" : dist,
		"y" : elevation
	}
	return plotdata

def generate_cumelevation_profile_single(filename):
	jsondata = load_json(filename)
	extracted_data = extract_data(jsondata)
	
	dist = [datapoint["sumDistance"] for datapoint in extracted_data]
	elevation = [datapoint["directElevation"] for datapoint in extracted_data]
	n = len(elevation)
	cumelevation = [0]*n
	for i in range(n-1):
		cumelevation[i+1] = cumelevation[i]+max(0, elevation[i+1]-elevation[i])
	plotdata = {
		"date" : parse_full_date(jsondata["summaryDTO"].get("startTimeLocal")),
		"x" : dist,
		"y" : cumelevation
	}
	return plotdata

def plot_elevation_profiles(filenames, cumulative=False):
	color_ord = {}
	data_by_date = {}
	for filename in filenames:
		if cumulative:
			plotdata = generate_cumelevation_profile_single(filename)
		else:
			plotdata = generate_elevation_profile_single(filename)
		data_by_date[plotdata["date"]] = {"x": plotdata["x"], "y" : plotdata["y"]}
		color_ord[plotdata["date"]] = plotdata["date"].toordinal()
	min_dataord = min(color_ord[d] for d in color_ord)
	max_dataord = max(color_ord[d] for d in color_ord)
	dataord_diff = max_dataord-min_dataord
	for date in data_by_date:
		datapoint = data_by_date[date]
		plt.plot(datapoint["x"],datapoint["y"], c=mpl.colormaps["viridis"]((date.toordinal()-min_dataord)/dataord_diff))
	plt.xlabel("Distance")
	if cumulative:
		plt.ylabel("Cumulative elevation gained (m)")
		plt.title("Cumulative Elevation Gain (m)")
	else:
		plt.ylabel("Elevation (m above sea level)")
		plt.title("Height Profiles")

	ticks = np.linspace(0.0, 1.0, 6)
	cbar = plt.colorbar(plt.cm.ScalarMappable(cmap="viridis"), ax=plt.gca(), orientation='horizontal', pad=0.1, aspect=30)
	cbar.set_label('Date')
	cbar.set_ticks(ticks)
	cbar.set_ticklabels([datetime.fromordinal(int(t*dataord_diff+min_dataord)).strftime('%Y-%m-%d') for t in ticks])

	plt.tight_layout()
	plt.show()

	
def test(type="running"):
	dir_downloaded = "full_activity_data/"+type
	input_files = [
			"full_activity_data/"+type+"/"+f for f in os.listdir(dir_downloaded)
			if f.lower().endswith(".json")
		]
	#print (input_files)
	plot_elevation_profiles(input_files, True)

if __name__ == "__main__":
	test("running")
	