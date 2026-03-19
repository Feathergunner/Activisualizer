#!usr/bin/python
# -*- coding: utf-8 -*-import string

import os
import json
import datetime
from getpass import getpass

from garminconnect import Garmin,GarminConnectAuthenticationError,GarminConnectConnectionError,GarminConnectTooManyRequestsError

from misc import save_json, ensure_dir_exists, load_json, parse_isodatestring, parse_full_date
from org import DIR_DOWNLOAD, VALID_ACTIVITY_TYPES

class GarminDataDownloader():
	'''
	class to simplify download of activity data from garmin server
	'''
	def __init__(self):
		# Set january first, 2010 as default start date
		self.default_start_date = datetime.date(2010,1,1)
		self.download_dir = None

	def get_activity_data(self, activity_type:str="running", min_date:str="2020-01-01", force_download:bool=False):
		'''
		Downloads all activities of specified type with ids that don't exists as jsonfile in DIR_DOWNLOAD/[activity_type]

		options for activity_type are (see org.py/VALID_ACTIVITY_TYPES):
		cycling, running, swimming, multi_sport, fitness_equipment, hiking, walking, other

		If force_download is True, re-downloads existing files.
		'''
		if activity_type not in VALID_ACTIVITY_TYPES:
			raise ValueError("Unknown activity_type:",activity_type)

		# init download directory and check for existing files:
		self.download_dir = os.path.join(DIR_DOWNLOAD, activity_type)
		ensure_dir_exists(self.download_dir)
		start_date = self._get_latest_downloaded_date(activity_type)
		min_date_as_date = parse_isodatestring(min_date)
		
		if start_date is None or (min_date_as_date is not None and start_date < min_date_as_date):
			start_date = min_date_as_date
		if start_date is None or force_download:
			# use very early startdate, download everything since then:
			start_date = self.default_start_date
		
		print ("Download activities of type "+activity_type+" starting from "+str(start_date))

		# login:
		email, password = self._ask_user_login_data()
		client = self._connect_with_garmin(email, password)
		# get data:
		self._download_data_from_garmin(client, start_date, activity_type, force_download)

	def _ask_user_login_data(self):
		print ("Login credentials for Garmin Connect are required")
		email = input("Enter email address: ")
		password = getpass("Enter password: ")
		return email, password

	def _connect_with_garmin(self, email, password):
		client = None
		try:
			client = Garmin(email, password)
			client.login()
			print("Login erfolgreich")
		except Exception as e:
			print("Login fehlgeschlagen:", e)
			exit()
		return client
	
	#def _get_relative_startdate(self,num_days_backwards:int=365):
	#	# by default 1 year before today
	#	return datetime.date.today() - datetime.timedelta(days=365)

	def _get_latest_downloaded_date(self, activity_type) -> datetime.date:
		# iterates through downloaded data and returns latest date
		latest_date = None
		dir_downloaded = os.path.join(DIR_DOWNLOAD, activity_type)
		for filename in os.listdir(dir_downloaded):
			if filename.endswith(".json"):
				data = load_json(os.path.join(dir_downloaded,filename))
				datetimestring = data["summaryDTO"]["startTimeLocal"]
				datetimeobject = parse_full_date(datetimestring)
				if latest_date is None or latest_date < datetimeobject:
					latest_date = datetimeobject
		return latest_date

	def _download_data_from_garmin(self,client, startdate, activity_type:str, force_download:bool):
		'''		
		checks for each activity-id if a file for this activity already exists. Data is only downloaded if no local data exists or if
		force_download = True
		'''
		#print ("Get all activities of type "+activity_type+" starting from "+str(startdate))

		# get basic activity data:
		activities = client.get_activities_by_date(startdate.isoformat(), datetime.date.today().isoformat(), activity_type)
		dl_counter = 0
		# for each activity, request detailed data:
		for act in activities:
			# double-check that activity_type is correct:
			if act.get("activityType", {}).get("typeKey") == activity_type:
				# get metadata: id, name and date of activity
				act_id = act.get("activityId")
				act_name = act.get("activityName")
				act_date = parse_isodatestring(act.get("startTimeLocal")[:10])
				# construct outputfilename based on activitiy-id:
				filepath = os.path.join(self.download_dir, str(act_id)+".json")
				if  act_date < startdate or (os.path.isfile(filepath) and not force_download):
					# data earlier then startdate or data already exists
					continue
				else:
					# download data:
					dl_counter += 1
					print ("Download activity",act_id)
					data_base = client.get_activity(act_id)
					data_detailed = client.get_activity_details(act_id)
					# store base data and detailed data in single json-file:
					data = {**data_base, **data_detailed}
					save_json(data, filepath)
		print ("Downloaded "+str(dl_counter)+ "activities. Data are saved at: "+self.download_dir)+"."

if __name__ == '__main__':
	gdd = GarminDataDownloader()
	gdd.get_activity_data("running")