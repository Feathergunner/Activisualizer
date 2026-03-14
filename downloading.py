#!usr/bin/python
# -*- coding: utf-8 -*-import string

import os
import json
import datetime
from getpass import getpass

from garminconnect import Garmin,GarminConnectAuthenticationError,GarminConnectConnectionError,GarminConnectTooManyRequestsError

from misc import save_json, ensure_dir_exists

def get_login_data():
	print ("Login credentials for Garmin Connect are required")
	email = input("Enter email address: ")
	password = getpass("Enter password: ")
	return email, password

def connect_with_garmin(email, password):
	client = None
	try:
		client = Garmin(email, password)
		client.login()
		print("Login erfolgreich")
	except Exception as e:
		print("Login fehlgeschlagen:", e)
		exit()
	return client

def get_relative_startdate(num_days_backwards:int=365):
	# by default 1 year before today
	return datetime.date.today() - datetime.timedelta(days=365)

def get_data_starting_from_date(client, startdate, outputdir:str, activitytype:str, force_download:bool):
	'''
	options for activitytype are:
	cycling, running, swimming, multi_sport, fitness_equipment, hiking, walking, other
	
	checks for each activity-id if a file for this activity already exists. Data is only downloaded if no local data exists or if
	force_download = True
	'''
	print ("Get all activities of type "+activitytype+" starting from "+str(startdate))
	
	# get basic activity data:
	if activitytype not in ["cycling", "running", "swimming", "multi_sport", "fitness_equipment", "hiking", "walking", "other"]:
		print("Error! Activitytype \""+activitytype+"\" unknown!")
		exit()
	activities = client.get_activities_by_date(startdate.isoformat(), datetime.date.today().isoformat(), activitytype)
	
	# for each activity, request detailed data:
	for act in activities:
		# double-check that activitytype is correct:
		if act.get("activityType", {}).get("typeKey") == activitytype:
			# get metadata: id, name and date of activity
			id = act.get("activityId")
			act_name = act.get("activityName")
			act_date = act.get("startTimeLocal")[:10]
			# construct outputfilename based on activitiy-id:
			rawfilename = outputdir+"/"+str(id)+".json"
			if os.path.isfile(rawfilename) and not force_download:
				# data already exists
				continue
			else:
				# download data:
				data_base = client.get_activity(id)
				data_detailed = client.get_activity_details(id)
				# store base data and detailed data in single json-file:
				data = {**data_base, **data_detailed}
				save_json(data, rawfilename)


def get_data_from_garmin(outputdir:str, activitytype:str="running", force_download:bool=False, startdate=None):
	email, password = get_login_data()
	client = connect_with_garmin(email, password)
	if startdate is None:
		startdate = get_relative_startdate()
	get_data_starting_from_date(client, startdate, outputdir, activitytype, force_download)