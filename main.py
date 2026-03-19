#!usr/bin/python
# -*- coding: utf-8 -*-import string

import re

from GarminDataDownloader import GarminDataDownloader
from SplitPlotter import SplitPlotter
from ActivityPlotter import ActivityPlotter
from RoutePlotter import RoutePlotter

from org import VALID_ACTIVITY_TYPES
from misc import check_datestr_format

sc_axis_param = {
	"t" : "elapsed_time",
	"p" : "pace",
	"e" : "elevation_gain",
	"r" : "avg_heartrate",
	"l" : "previous_distance",
	"h" : "previous_elevation",
	"d" : "date",
	"n" : None
}

lp_axis_param = {
	"d" : "sumDistance",
	"t" : "sumDuration",
	"e" : "directElevation",
	"h" : "directHeartRate",
	"g" : "cumulativeElevation"
}

class UserHandler():
	def __init__(self):
		# level 0:
		self.activity_type = "running"
		# level 1:
		self.min_date = None
		self.max_date = None
		# level 2:
		self.splitlength = 1000

		# scatterplotsettings:
		self.sc_axis_keys = {
			"x" : "pace",
			"y" : "avg_heartrate",
			"s" : "elevation_gain", # point size
			"c" : "date" # point color
		}

		# lineplotsettings:
		self.lp_axis_keys = {
			"x" : "sumDistance",
			"y" : "directElevation",
			"c" : "date" # line color
		}

		# routplotsettings:
		# set lat/lon near Jena, Germany:
		self.home_latitude = 50.9
		self.home_longitude = 11.6
		# default zoom level
		self.zoom_level = 14
		self.map_file_name = ""


	def _update_type(self, new_activity_type:str) -> bool:
		if not new_activity_type in VALID_ACTIVITY_TYPES:
			print ("Unknown activity_type: "+new_activity_type+". Has to be one of: "+VALID_ACTIVITY_TYPES+".")
			return False
		self.activity_type = new_activity_type
		return True

	def _reset_min_date(self):
		self.min_date = None

	def _reset_max_date(self):
		self.max_date = None

	def _update_min_date(self, new_min_date:str) -> bool:
		if not check_datestr_format(new_min_date):
			print ("Date format not recognized: "+new_min_date+". Has to be in format YYYY-MM-DD.")
			return False
		self.min_date = new_min_date
		return True

	def _update_max_date(self, new_max_date:str) -> bool:
		if not check_datestr_format(new_max_date):
			print ("Date format not recognized: "+new_max_date+". Has to be in format YYYY-MM-DD.")
			return False
		self.max_date = new_max_date
		return True

	def _update_splitlength(self, new_splitlength:int) -> bool:
		if not new_splitlength.isdigit() or new_splitlength == "0":
			print ("Entered value is not a valid splitlength: "+new_splitlength+". Has to be positive integer.")
			return False
		self.splitlength = int(new_splitlength)
		return True

	def show_scatterplot_settings(self):
		while True:
			print ("Set up scatterplot of aggregated spit data:")
			print ("*********************************************************************")
			print (" * x-Axis: "+self.sc_axis_keys["x"])
			print (" * y-Axis: "+self.sc_axis_keys["y"])
			print (" * point size: "+str(self.sc_axis_keys["s"]))
			print (" * point color: "+str(self.sc_axis_keys["c"]))
			print ("*********************************************************************")
			print ()
			print ("Do you want to change some settings?")
			options = {
				"y" : "Yes",
				"n" : "No, proceed."
			}
			userchoice = menu(options)
			if userchoice == "y":
				self._change_scatterplot_settings()
			if userchoice == "n":
				return

	def _change_scatterplot_settings(self):
		while True:
			print ("Which axis do you want to change?")
			options_axes = {
				"q" : "abort (continue with plotting)",
				"x" : "x-axis",
				"y" : "y-axis",
				"s" : "point size",
				"c" : "point color"
			}
			userchoice_axis = menu(options_axes)

			if userchoice_axis == "q":
				return
			else:
				print ("Which parameter do you want to use for the "+options_axes[userchoice_axis]+"?")
				options_parameters = {
					"t" : "elapsed time before split",
					"p" : "pace during split",
					"e" : "elevation gain during split",
					"r" : "average heart rate during split",
					"l" : "previous distance before split",
					"h" : "cumulative elevation gain before split",
					"d" : "date of activity"
				}
				if userchoice_axis in ["s","c"]:
					options_parameters = options_parameters | {
						"n" : "none ("+options_axes[userchoice_axis]+" will be uniform for all splits)"
					}
				userchoice_param = menu(options_parameters)
				self.sc_axis_keys[userchoice_axis] = sc_axis_param[userchoice_param]

	def show_lineplot_settings(self):
		while True:
			print ("Set up lineplot of activity data:")
			print ("*********************************************************************")
			print (" * x-Axis: "+self.lp_axis_keys["x"])
			print (" * y-Axis: "+self.lp_axis_keys["y"])
			print ("*********************************************************************")
			print ()
			print ("Do you want to change some settings?")
			options = {
				"y" : "Yes",
				"n" : "No, proceed."
			}
			userchoice = menu(options)
			if userchoice == "y":
				self._change_lineplot_settings()
			if userchoice == "n":
				return
			return

	def _change_lineplot_settings(self):
		while True:
			print ("Which axis do you want to change?")
			options_axes = {
				"q" : "abort (continue with plotting)",
				"x" : "x-axis",
				"y" : "y-axis",
			}
			userchoice_axis = menu(options_axes)

			if userchoice_axis == "q":
				return
			else:
				print ("Which parameter do you want to use for the "+options_axes[userchoice_axis]+"?")
				options_parameters = {
					"d" : "distance",
					"t" : "duration",
					"e" : "absolute elevation",
					"h" : "heart rate",
					"g" : "elevation gain so far"
				}
				userchoice_param = menu(options_parameters)
				self.lp_axis_keys[userchoice_axis] = lp_axis_param[userchoice_param]
		return

	def show_routeplot_settings(self):
		while True:
			print ("Set up route plot:")
			print ("*********************************************************************")
			print (" * home latitude: "+str(self.home_latitude))
			print (" * home latitude: "+str(self.home_longitude))
			print ("     (Only activities that START within +/- 0.5 lat/lon will be used.)")
			print ("     (This covers an area of several km^2.)")
			print (" * zoom level: "+str(self.zoom_level))
			print ("     (The larger, the more detailed the map,")
			print ("       but image size is exponential in zoom level.)")
			print ("     (Consider using a lower zoom level for biking.)")
			print ("*********************************************************************")
			print ()
			print ("Do you want to change some settings?")
			options = {
				"y" : "Yes",
				"n" : "No, proceed."
			}
			userchoice = menu(options)
			if userchoice == "y":
				self._change_routeplot_settings()
			if userchoice == "n":
				return
			return

	def _change_routeplot_settings(self):
		while True:
			print ("Which axis do you want to change?")
			options_axes = {
				"q" : "abort (continue with plotting)",
				"a" : "latitude",
				"o" : "longitude",
				"z" : "zoom level"
			}
			userchoice_axis = menu(options_axes)

			if userchoice_axis == "q":
				return
			else:
				if userchoice_axis in ["a", "o"]:
					print ("Enter new coordinate:")
					new_val = input()
					# check if values are valid:
					# regex for float that contains 1 to 3 digits before the point, and optionally up to 2 digits after the point
					latlon_format = r"-*\d{1,3}(\.\d{1,2})*"
					latlon_regex = re.compile(latlon_format)
					if latlon_regex.match(new_val) is None:
						print ("Wrong format: value has to be an (optionally negative) integer or float with at most three digits before the decimal point and at most two digits behind the decimal point.")
					else:
						try:
							floatval = float(new_val)
						except ValueError:
							print("Something went wrong while casting the value "+new_val+" to float.")
							continue
						if userchoice_axis == "a":
							if floatval < -90 or floatval > 90:
								print ("Latitude has to be within (-90, 90).")
							else:
								self.home_latitude = floatval
						if userchoice_axis == "o":
							if floatval < 0 or floatval > 360:
								print ("Longitude has to be within (0, 360).")
							else:
								self.home_longitude = floatval

				if userchoice_axis == "z":
					print ("Enter zoom level:")
					new_val = input()
					if new_val.isdigit():
						new_zoom = int(new_val)
						if new_zoom > 0 and new_zoom < 19:
							self.zoom_level = new_zoom
						else:
							print ("Zoom level has to be an integer within {1, ... , 18}")
					else:
						print ("Zoom level has to be an integer within {1, ... , 18}")
		return

	def show_global_settings(self, level=0):
		while True:
			print ("Your current settings are:")
			print ("*********************************************************************")
			print (" * Activity Type: "+self.activity_type)
			print ("     (Activities of other types will be ignored)")
			if level > 0:
				if self.min_date is None:
					print (" * Minimum Date: None")
				else:
					print (" * Minimum Date: "+self.min_date)
				print ("     (Earlier activities (if date is specified) will be ignored)")
				if self.max_date is None:
					print (" * Maxmum Date: None")
				else:
					print (" * Maximum Date: "+self.max_date)
				print ("     (Later activities (if date is specified) will be ignored)")
			if level > 1:
				print (" * Splitlength: "+str(self.splitlength))
			print ("*********************************************************************")
			print ()
			print ("Do you want to change some settings?")
			options = {
				"y" : "Yes",
				"n" : "No, proceed."
			}
			userchoice = menu(options)
			if userchoice == "y":
				self.change_settings(level)
			if userchoice == "n":
				return

	def change_settings(self, level=0):
		while True:
			print ("== Change Activity Settings ==")
			options = {
				"q" : "[Quit menu]",
				"t" : "Change activity type"
			}
			if level > 0:
				options = options | {
				"l" : "Set new minimum date",
				"u" : "Set new maximum date",
				"x" : "Reset minimum date",
				"y" : "Reset maximum date"
				}
			if level > 1:
				options = options | {
				"s" : "Change splitlength"
				}

			userchoice = menu(options)
	
			if userchoice == "t":
				# change activity type:
				print ("== Change Activity Type ==")
				options_activity = {
					"r" : "running",
					"h" : "hiking",
					"c" : "cycling",
					#"s" : "swimming",
					#"w" : "walking",
					"q" : "[Quit menu]"
				}
				userchoice_activity = menu(options_activity)
				if not userchoice_activity == "q":
					self._update_type(options_activity[userchoice_activity])
					return

			if userchoice in ["l", "u"]:
				print ("Enter new date [YYYY-MM-DD]:")
				new_date = input()
				if userchoice == "l":
					success = self._update_min_date(new_date)
				if userchoice == "u":
					success = self._update_max_date(new_date)
				if success:
					print ("Date changed!")
				return
			if userchoice == "x":
				self._reset_min_date()
				return
			if userchoice == "y":
				self._reset_max_date()
				return
			if userchoice == "s":
				print ("Enter new splitlength (in meter: a positive integer)")
				new_splitlength = input()
				if self._update_splitlength(new_splitlength):
					print ("Splitlength changed!")
			if userchoice == "q":
				return

def menu(options):
	# check if options are valid:
	for key in options.keys():
		if len(key) != 1:
			raise ValueError("Invalid key in menu options: "+key)
		elif not key[0].isalpha() and not key[0].isdigit():
				raise ValueError("Invalid key in menu options: "+key)

	# print options:
	for key in options: 
		print (" [ "+str(key)+" ] : "+options[key])
	print ("")
	#print     ("[ enter ]  : abort\n")
	# get user input
	while True:
		print("Please choose your action:")
		choice = input()
		if len(choice) != 1 or choice not in options.keys():
			print ("Invalid option:",choice)
		else:
			return choice

def download_data(uh):
	print ("=== Download Data ===")
	uh.show_global_settings(level=0)
	gdd = GarminDataDownloader()
	gdd.get_activity_data(uh.activity_type, uh.min_date)

def scatterplot(uh):
	print ("=== Plot Split Data ===")
	uh.show_global_settings(level=2)
	uh.show_scatterplot_settings()
	sp = SplitPlotter(activity_type=uh.activity_type, splitlength=uh.splitlength, min_date=uh.min_date, max_date=uh.max_date)
	sp.plot_scatter(axis_x_key=uh.sc_axis_keys["x"], axis_y_key=uh.sc_axis_keys["y"], axis_color_key=uh.sc_axis_keys["c"], axis_size_key=uh.sc_axis_keys["s"])


def lineplot(uh):
	print ("=== Plot Activity Data ===")
	uh.show_global_settings(level=1)
	uh.show_lineplot_settings()
	ap = ActivityPlotter()
	ap.plot_activities(activity_type=uh.activity_type, min_date=uh.min_date, max_date=uh.max_date, axis_x_key=uh.lp_axis_keys["x"], axis_y_key=uh.lp_axis_keys["y"])

def routeplot(uh):
	print ("=== Map Activity GPX ===")
	uh.show_global_settings(level=1)
	uh.show_routeplot_settings()
	rp = RoutePlotter()
	rp.plot_routes_in_area(activity_type=uh.activity_type, lat=uh.home_latitude, lon=uh.home_longitude, min_date=uh.min_date, max_date=uh.max_date, zoom=uh.zoom_level, filename=uh.map_file_name)

if __name__ == '__main__':
	uh = UserHandler()
	while True:
		print ("\n=== Activity Visualizer Main Menu ===\n")
		mainoptions = {
			"d" : "Download data from garmin",
			"s" : "Create Scatterplot of aggregated split data",
			"l" : "Create lineplot of activity data",
			"m" : "Map gpx data from activities",
			"q" : "Quit"
		}
		userchoice = menu(mainoptions)
		if userchoice == "d":
			download_data(uh)
		elif userchoice == "s":
			scatterplot(uh)
		elif userchoice == "l":
			lineplot(uh)
		elif userchoice == "m":
			routeplot(uh)
		elif userchoice == "q":
			quit()
