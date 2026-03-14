#!usr/bin/python
# -*- coding: utf-8 -*-import string

import os
import argparse
import json

from misc import ensure_dir_exists, parse_full_date, parse_datestring
from downloading import get_data_from_garmin
from parsing import process_activity
from visualizing import visualize_split_data, visualize_activity_data

# directories where data is stored:
DIRNAME_FULL_DATA = "full_activity_data"
DIRNAME_PARSED_DATA = "parsed_activity_data"

if __name__ == '__main__':
	# parse arguments
	parser = argparse.ArgumentParser(description="Download, parse and plot activity data from garmin connect.")
	parser.add_argument("-f", "--force", action="store_true", help="Force redownload of existing data.")
	parser.add_argument("--test", action="store_true", help="Test download and parsing, force redownload, only parse one file, no visualization.")
	parser.add_argument("-t", "--type", action="store", help="Set activity type, choose one from 'cycling', 'running', 'swimming', 'multi_sport', 'fitness_equipment', 'hiking', 'walking', 'other'", default="running")
	parser.add_argument("-V", "--visualize_only", action="store_true", help="Only visualize existing data, don't download or parse.", default=False)
	parser.add_argument("-D", "--download_only", action="store_true", help="Only download data, don't parse or visualize.", default=False)
	parser.add_argument("-P", "--parse_only", action="store_true", help="Only parse existing data, don't download or visualize.", default=False)
	parser.add_argument("-pv", "--parse_and_visualize", action="store_true", help="Don't download data, only parse and visualize.", default=False)
	parser.add_argument("--minheart", action="store", help="minimum heart rate in bpm; ignore splits with lower heart rate in visualization.", default=None)
	parser.add_argument("--maxpace", action="store", help="maximum pace in min/km; ignore splits with slower pace in visualization.", default=None)
	parser.add_argument("--minelevation", action="store", help="minimum elevation gain in meter; ignore splits with less elevation.", default=None)
	parser.add_argument("--splitlength", action="store", help="Set split length in meter.", default=1000)
	parser.add_argument("--mindate", action="store", help="Set earliest date in format DD.MM.YYYY", default=None)
	args = parser.parse_args()
	
	activitytype = args.type
	if activitytype not in ["cycling", "running", "swimming", "multi_sport", "fitness_equipment", "hiking", "walking", "other"]:
		print ("Error! Unknown activitytype: "+activitytype)
		
	if args.minheart != None:
		minimum_heartrate = int(args.minheart)
	else:
		if activitytype in ["running", "cycling"]:
			minimum_heartrate = 100
		else:
			minimum_heartrate = 50
	if args.maxpace != None:
		maximum_pace = int(args.maxpace)
	else:
		# somewhat usefull upper (i.e. slower) bounds on pace depending on sport, to remove outliers and keep plot concise:
		if activitytype == "hiking":
			maximum_pace = 20
		elif activitytype == "running":
			maximum_pace = 12
		elif activitytype == "cycling":
			maximum_pace = 5
		else:
			maximum_pace = 30
	if args.minelevation != None:
		minelevation = int(args.minelevation)
	else:
		minelevation = 0
			
	if args.mindate != None:
		start_date = parse_datestring(args.mindate)
	else:
		start_date = None
	
	# construct directories for data:
	# ensure output directory exists:
	dir_downloaded = DIRNAME_FULL_DATA+"\\"+activitytype
	ensure_dir_exists(dir_downloaded)
	dir_parsed = DIRNAME_PARSED_DATA+"\\"+activitytype
	ensure_dir_exists(dir_parsed)
	
	# download data and store locally in json-files:
	if not args.visualize_only and not args.parse_only and not args.parse_and_visualize:
		get_data_from_garmin(outputdir=dir_downloaded, activitytype=activitytype, startdate=start_date)
	
	if (not args.visualize_only and not args.download_only) or args.parse_and_visualize:
		# get list of files in target directory
		input_files = [
			f for f in os.listdir(dir_downloaded)
			if f.lower().endswith(".json")
		]
	
		if not input_files:
			print(f"Did not find any JSON-Files in '{dir_downloaded}'.")
			exit()

		# parse data: only keep interesting fields, compute splitwise aggregated data:
		for filename in input_files:
			input_path = os.path.join(dir_downloaded, filename)

			try:
				with open(input_path, "r", encoding="utf-8") as f:
					raw_data = json.load(f)

				activity_id = raw_data.get("activityId")
				if not activity_id:
					print(f"No 'activityId' in file: {filename}")
					continue
				
				date = parse_full_date(raw_data.get("summaryDTO")["startTimeLocal"])
				if not start_date is None and date < start_date:
					#print ("skip parsing for activity "+str(activity_id)+": before start_date")
					continue

				output_path = os.path.join(dir_parsed, f"{activity_id}.json")
	
				# we do not want to skip parsing, since a custom splitlength always requires re-parsing
				#if os.path.exists(output_path) and not args.force and not args.test:
				#	print(f"Skipped file: {activity_id}.json (parsed data already exists)")
				#	continue
	
				process_activity(input_path, output_path, int(args.splitlength))
				#print(f"Parsed: {filename} → {activity_id}.json")
	
			except Exception as e:
				print(f"Error while parsing '{filename}': {e}")
				
			if args.test:
				# if testing, stop after one file
				break
	
	# visualize data:
	if (not args.download_only and not args.parse_only) or args.parse_and_visualize:
		splitlength = int(args.splitlength)
		if splitlength > 0:
			visualize_split_data(dir_parsed, minimum_heartrate, maximum_pace, args.mindate, int(args.splitlength), minelevation, activitytype)
		else:
			visualize_activity_data(dir_parsed, args.mindate, activitytype)