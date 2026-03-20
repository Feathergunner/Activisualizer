#!usr/bin/python
# -*- coding: utf-8 -*-import string

from matplotlib import pyplot as plt
from PIL import Image

import OSMMapDownloader as osmmd
from DataHandler import DataHandler
from misc import check_datestr_format
from org import METRICS_OF_INTEREST, VALID_ACTIVITY_TYPES


class RoutePlotter():
	'''
	Class that handles plotting multiple routes from activities onto a map.
	'''
	def __init__(self, add_border:bool=True):
		self.add_border = add_border

	def plot_routes_in_area(self, activity_type:str, lat:float, lon:float, delta:float=0.05, min_date:str=None, max_date:str=None, zoom:int=osmmd.MAP_DEFAULT_ZOOM, filename:str=""):
		'''
		lat: latitude of start position
		lon: longitude of start position
		delta: maximum difference for lat/lon position of startposition of activities
	
		plots all routes that start within 
			latitude: [lat - delta, lat + delta]
			longitude: [lon - delta, lon + delta]
	
		If result_filename is not None, the resulting plotted map will be saved under specified filename
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

		dh = DataHandler()
		activities = dh.get_data(self.activity_type,
			self.min_date,
			self.max_date,
			latitude_min=lat-delta,
			latitude_max=lat+delta,
			longitude_min=lon-delta,
			longitude_max=lon+delta,
			require_fulldata=True)

		if len(activities) == 0:
			# no data, abort
			return

		result_filename = filename+"_"+activity_type
		self._plot_multiple_routes(activities, activity_type, result_filename=result_filename, zoom=zoom)
		
	def _plot_multiple_routes(self, activities, activity_type:str, result_filename:str, zoom:int):
		'''
		plots multiple routes on a map.
	
		If result_filename is not None, the resulting plotted map will be saved under specified filename
		'''	
		gps_stats = {}
		for activity in activities:
			gps_stats[activity.activity_id] = self._get_gps_stats(activity)
	
		# get global statistics:
		global_gps_stats = {}
		global_gps_stats["lon_min"] = min(gps_stats[aid]["lon_min"] for aid in gps_stats)
		global_gps_stats["lon_max"] = max(gps_stats[aid]["lon_max"] for aid in gps_stats)
		global_gps_stats["lat_min"] = min(gps_stats[aid]["lat_min"] for aid in gps_stats)
		global_gps_stats["lat_max"] = max(gps_stats[aid]["lat_max"] for aid in gps_stats)
		global_gps_stats["lon_mintile"] = min(gps_stats[aid]["lon_mintile"] for aid in gps_stats)
		global_gps_stats["lon_maxtile"] = max(gps_stats[aid]["lon_maxtile"] for aid in gps_stats)
		
		# compute the remaining statistics:
		min_x, min_y = osmmd.latlong_to_merccoords(global_gps_stats["lat_min"], global_gps_stats["lon_min"],zoom)
		max_x, max_y = osmmd.latlong_to_merccoords(global_gps_stats["lat_max"], global_gps_stats["lon_max"],zoom)
		max_x += 1
		min_y += 1
		if self.add_border:
			min_x -= 1
			max_x += 1
			min_y += 1
			max_y -= 1
		(global_gps_stats["lat_mintile"], global_gps_stats["lon_mintile"]) = osmmd.tile_xy_to_latlon(min_x, min_y,zoom)
		(global_gps_stats["lat_maxtile"], global_gps_stats["lon_maxtile"]) = osmmd.tile_xy_to_latlon(max_x, max_y,zoom)
		global_gps_stats["lat_tile_range"] = global_gps_stats["lat_maxtile"]-global_gps_stats["lat_mintile"]
		global_gps_stats["lon_tile_range"] = global_gps_stats["lon_maxtile"]-global_gps_stats["lon_mintile"]
	
		global_gps_stats["x_range"] = max_x-min_x
		global_gps_stats["y_range"] = min_y-max_y
	
		#for key in global_gps_stats:
		#	print (key, ":", [gps_stats[aid][key] for aid in gps_stats], " -- ", global_gps_stats[key])

		# get map:
		mapdownloader = osmmd.OSMMapDownloader(global_gps_stats["lat_min"], global_gps_stats["lat_max"], global_gps_stats["lon_min"], global_gps_stats["lon_max"], zoom=zoom, add_border=self.add_border)
		mapdownloader.get_map()
		mapimage = Image.open(mapdownloader.filepath)
	
		# set up figure:
		dpi = 200
		im_x, im_y = mapimage.size
		width_inches = im_x / (dpi)
		height_inches = im_y / (dpi)
		plt.figure(figsize=(width_inches, height_inches))
	
		# plot map:
		plt.imshow(mapimage)
	
		# plot routes:
		#for aid in global_gps_stats:
		for activity in activities:
			(xs, ys) = self._get_route_xy_coords(activity.datapoints, global_gps_stats)
			plt.plot(xs, ys, c='red')
	
		plt.tight_layout()
		plt.axis('off')
	
		if result_filename is None:
			plt.show()
		else:
			# ensure filename ends with ".png"
			if not result_filename.endswith(".png"):
				result_filename = result_filename.split(".")[0]+".png"
			# save plot
			plt.savefig(result_filename, bbox_inches='tight', pad_inches=0, dpi=dpi)
			print ("Saved map image with routes in: "+result_filename)
			plt.close('all')

	def _get_gps_stats(self, activity_data, zoom:int=osmmd.MAP_DEFAULT_ZOOM):
		'''
		activity_data: full instance of ActivityData, in particular containing the datapoints
	
		returns dictionary containing:
			min, max, range of longitude and latitude of datapoints,
			min, max of longitude and latitude of area covered by map,
			and range of map tiles (in x,y-coordinates)
	
		parses the data to compute bounds of latitude, longitude and of maptile-(x,y)-coords
		to get the correct map and plot a route on top of the map.
		'''
		if activity_data.datapoints is None:
			raise ValueError("activity_data is missing the datapoints!")
	
		min_lat = -1
		max_lat = -1
		min_lon = -1
		max_lon = -1
		#print(extracted_data)
		for datapoint in activity_data.datapoints:
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
		# get x/y-coordinates of tile that covers minimum lat/lon-coordinates
		# note that y is related inverse to lateitude, 
		# therefore max_y <= min_y
		min_x, min_y = osmmd.latlong_to_merccoords(min_lat, min_lon,zoom)
		max_x, max_y = osmmd.latlong_to_merccoords(max_lat, max_lon,zoom)
		# adjust so that tile coordinates refer to MAP BOUNDARIES
		max_x += 1
		min_y += 1
		if self.add_border:
			# add one tile in each direction:
			min_x -= 1
			max_x += 1
			min_y += 1
			max_y -= 1
		(min_lat_tiles, min_lon_tiles) = osmmd.tile_xy_to_latlon(min_x, min_y, zoom)
		(max_lat_tiles, max_lon_tiles) = osmmd.tile_xy_to_latlon(max_x, max_y, zoom)
		lat_range = max_lat_tiles-min_lat_tiles
		lon_range = max_lon_tiles-min_lon_tiles
	
		x_range = max_x-min_x
		y_range = min_y-max_y
	
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

	def _get_route_xy_coords(self, data, gps_stats):
		'''
		activity_data: full instance of ActivityData, in particular containing the datapoints
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
				# compute distance in full tiles from (0,0) on image:
				relx = (datapoint["directLongitude"]-gps_stats["lon_mintile"])/gps_stats["lon_tile_range"]
				rely = 1-((datapoint["directLatitude"]-gps_stats["lat_mintile"])/gps_stats["lat_tile_range"])
				# compute absolute pixel distances, consider 1-tile-border:
				px = relx*(osmmd.MAP_DIM_TILE*(gps_stats["x_range"]))
				py = rely*(osmmd.MAP_DIM_TILE*(gps_stats["y_range"]))
				# add to list of coordinates:
				xs.append(px)
				ys.append(py)
		return (xs, ys)

if __name__ == '__main__':
	min_date = "2026-03-15"
	max_date = None
	
	rp = RoutePlotter(False)
	rp.plot_routes_in_area("running", 50.9, 11.6, min_date=min_date, max_date=max_date, zoom=14, filename="test_RP")
