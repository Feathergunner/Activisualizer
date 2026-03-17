#!usr/bin/python
# -*- coding: utf-8 -*-import string

import os
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.lines import Line2D
from PIL import Image

from misc import load_json
from parsing import extract_data
import OSMMapDownloader as osmmd

def get_gps_stats(data, zoom:int=osmmd.MAP_DEFAULT_ZOOM):
	'''
	data: dictionary of activity-data as constructed by misc.extract_data

	returns dictionary containing:
		min, max, range of longitude and latitude of datapoints,
		min, max of longitude and latitude of area covered by map,
		and range of map tiles (in x,y-coordinates)

	parses the data to compute bounds of latitude, longitude and of maptile-(x,y)-coords
	to get the correct map and plot a route on top of the map.
	'''

	min_lat = -1
	max_lat = -1
	min_lon = -1
	max_lon = -1
	#print(extracted_data)
	for datapoint in data:
		#print (datapoint)
		lat = datapoint["directLatitude"]
		lon = datapoint["directLongitude"]
		#print (lat, lon)
		if lat is not None and lon is not None:
			if min_lat < 0 or lat < min_lat:
				min_lat = lat
			if lat > max_lat:
				max_lat = lat
			if min_lon < 0 or lon < min_lon:
				min_lon = lon
			if lon > max_lon:
				max_lon = lon
	min_x, min_y = osmmd.latlong_to_merccoords(min_lat, min_lon,zoom)
	max_x, max_y = osmmd.latlong_to_merccoords(max_lat, max_lon,zoom)
	(min_lat_tiles, min_lon_tiles) = osmmd.tile_xy_to_latlon(min_x, min_y,zoom)
	(max_lat_tiles, max_lon_tiles) = osmmd.tile_xy_to_latlon(max_x, max_y,zoom)
	lat_range = max_lat_tiles-min_lat_tiles
	lon_range = max_lon_tiles-min_lon_tiles

	x_range = max_x-min_x+1
	y_range = min_y-max_y+1

	return {
		"lon_min" : min_lon,
		"lon_max" : max_lon,
		"lat_min" : min_lat,
		"lat_max" : max_lat,
		"lon_mintile" : min_lon_tiles,
		"lon_maxtile" : max_lon_tiles,
		"lon_tile_range" : lon_range,
		"lat_mintile" : min_lat_tiles,
		"lat_maxtile" : max_lat_tiles,
		"lat_tile_range" : lat_range,
		"x_range" : x_range,
		"y_range" : y_range
	}

def get_route_xy_coords(data, gps_stats):
	'''
	data: dictionary of activity-data as constructed by misc.extract_data
	gps_stats: disctionary of gps-stats as constructed by get_gps_stats

	constructs lists of x- and of y- coords from gps-data, ready for lineplot
	'''
	xs = []
	ys = []
	for datapoint in data:
		lat = datapoint["directLatitude"]
		lon = datapoint["directLongitude"]
		if lat is not None and lon is not None:
			# compute pixel offsets:
			# compute relative distance from (0,0) on image:
			relx = (datapoint["directLongitude"]-gps_stats["lon_mintile"])/gps_stats["lon_tile_range"]
			rely = 1-(datapoint["directLatitude"]-gps_stats["lat_mintile"])/gps_stats["lat_tile_range"]
			# compute absolute pixel distances, consider 1-tile-border:
			px = relx*osmmd.MAP_DIM_TILE*(gps_stats["x_range"]-1)
			py = rely*(osmmd.MAP_DIM_TILE*(gps_stats["y_range"]-1))
			# add 1-tile-border offset:
			px += osmmd.MAP_DIM_TILE
			py += osmmd.MAP_DIM_TILE
			# add to list of coordinates:
			xs.append(px)
			ys.append(py)
	return (xs, ys)

def plot_route_on_map(filename):
	'''
	filename: name of json-file containing the raw downloaded data (not the parsed one)
	'''

	# get data:
	jsondata = load_json(filename)
	extracted_data = extract_data(jsondata)
	gps_stats = get_gps_stats(extracted_data)

	# get map:
	mapdownloader = osmmd.OSMMapDownloader(gps_stats["lat_min"], gps_stats["lat_max"], gps_stats["lon_min"], gps_stats["lon_max"], add_border=True)
	mapdownloader.get_map()

	# plot map:
	mapimage = Image.open(mapdownloader.filepath)
	plt.imshow(mapimage)

	# plot route:
	(xs, ys) = get_route_xy_coords(extracted_data, gps_stats)
	plt.plot(xs, ys)
	plt.show()

def plot_multiple_routes(activity_ids:list, activity_type:str="running", filename:str=None, zoom:int=osmmd.MAP_DEFAULT_ZOOM):
	'''
	plots multiple routes on a map.

	If filename is not None, the resulting plotted map will be saved under specified filename
	'''	
	gps_stats = {}
	extracted_data = {}
	for aid in activity_ids:
		filepath = os.path.join("full_activity_data", activity_type, str(aid)+".json")
		jsondata = load_json(filepath)
		extracted_data[aid] = extract_data(jsondata)
		gps_stats[aid] = get_gps_stats(extracted_data[aid])

	# get global statistics:
	global_gps_stats = {}
	global_gps_stats["lon_min"] = min(gps_stats[aid]["lon_min"] for aid in gps_stats)
	global_gps_stats["lon_max"] = max(gps_stats[aid]["lon_max"] for aid in gps_stats)
	global_gps_stats["lat_min"] = min(gps_stats[aid]["lat_min"] for aid in gps_stats)
	global_gps_stats["lat_max"] = max(gps_stats[aid]["lat_max"] for aid in gps_stats)
	global_gps_stats["lon_mintile"] = min(gps_stats[aid]["lon_mintile"] for aid in gps_stats)
	global_gps_stats["lon_maxtile"] = max(gps_stats[aid]["lon_maxtile"] for aid in gps_stats)


	min_x, min_y = osmmd.latlong_to_merccoords(global_gps_stats["lat_min"], global_gps_stats["lon_min"],zoom)
	max_x, max_y = osmmd.latlong_to_merccoords(global_gps_stats["lat_max"], global_gps_stats["lon_max"],zoom)
	(global_gps_stats["lat_mintile"], global_gps_stats["lon_mintile"]) = osmmd.tile_xy_to_latlon(min_x, min_y,zoom)
	(global_gps_stats["lat_maxtile"], global_gps_stats["lon_maxtile"]) = osmmd.tile_xy_to_latlon(max_x, max_y,zoom)
	global_gps_stats["lat_tile_range"] = global_gps_stats["lat_maxtile"]-global_gps_stats["lat_mintile"]
	global_gps_stats["lon_tile_range"] = global_gps_stats["lon_maxtile"]-global_gps_stats["lon_mintile"]

	global_gps_stats["x_range"] = max_x-min_x+1
	global_gps_stats["y_range"] = min_y-max_y+1

	#for key in global_gps_stats:
	#	print (key, ":", [gps_stats[aid][key] for aid in gps_stats], " -- ", global_gps_stats[key])

	# get map:
	mapdownloader = osmmd.OSMMapDownloader(global_gps_stats["lat_min"], global_gps_stats["lat_max"], global_gps_stats["lon_min"], global_gps_stats["lon_max"], add_border=True)
	mapdownloader.get_map()

	# plot map:
	mapimage = Image.open(mapdownloader.filepath)
	plt.imshow(mapimage)

	# plot routes:
	for aid in activity_ids:
		(xs, ys) = get_route_xy_coords(extracted_data[aid], global_gps_stats)
		plt.plot(xs, ys, c='red')

	plt.tight_layout()
	plt.show()

def plot_all_routes_in_area(lat:float, lon:float, delta:float=0.05, activity_type:str="running"):
	'''
	lat: latitude of start position
	lon: longitude of start position
	delta: maximum difference for lat/lon position of startposition of activities

	plots all routes that start within 
		latitude: [lat - delta, lat + delta]
		longitude: [lon - delta, lon + delta]
	'''

	activities_to_plot = []

	# parse downloaded files:
	datadir = os.path.join("full_activity_data", activity_type)
	for filename in os.listdir(datadir):
		if filename.lower().endswith(".json"):
			print (" checking file",filename,"...")
			filepath = os.path.join("full_activity_data", activity_type, filename)
			jsondata = load_json(filepath)
			#data = extract_data(jsondata)

			act_lat = jsondata["summaryDTO"]["startLatitude"]
			act_lon = jsondata["summaryDTO"]["startLongitude"]
			if act_lat >= lat-delta and act_lat <= lat+delta and act_lon >= lon-delta and act_lon <= lon+delta:
				activities_to_plot.append(jsondata["activityId"])
				print ("  ... added!")
			else:
				print ("  ... to far away")

	print ("Found "+str(len(activities_to_plot))+" activities to plot.")
	plot_multiple_routes(activities_to_plot, activity_type)


def test(type="running"):
	plot_all_routes_in_area(50.9, 11.6)
	#plot_all_routes_in_area(53.2, 8.8)

if __name__ == "__main__":
	test()
	