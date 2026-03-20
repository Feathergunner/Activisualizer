#!usr/bin/python
# -*- coding: utf-8 -*-import string

import math
from matplotlib import pyplot as plt
import networkx as nx

from DataHandler import DataHandler
from misc import check_datestr_format
from org import VALID_ACTIVITY_TYPES

# approximation of meters per gpx-degree.
# We only need a rough approximation, the values are only used to bound the order of magnitude of error when rounding lat/lon data
# value for latitude holds everywhere:
METER_PER_DEG_LAT = 110000
# value for longitude holds at approx 51 degree,
# maybe adjust for approx 1500m per degree if longitude is +/- 10 degrees,
# further away approximation might become to rough
# formula: meters = earth_radius*cos(lon)/360 (with earth_radius approx. 40.000.000m)
METER_PER_DEG_LON = 70000

def round_gpx(lat:float, lon:float, precision:int=7):
	'''
	Rounds (lat,lon)-coordinates
	precision: precision of rounded coordinates in meter
	'''
	decimal_prec_lat = int(math.log(METER_PER_DEG_LAT/precision)/math.log(10))
	decimal_prec_lon = int(math.log(METER_PER_DEG_LON/precision)/math.log(10))
	rounded_lat = round(round(METER_PER_DEG_LAT/precision*lat)/(METER_PER_DEG_LAT/precision), decimal_prec_lat)
	rounded_lon = round(round(METER_PER_DEG_LON/precision*lon)/(METER_PER_DEG_LON/precision), decimal_prec_lon)
	return (rounded_lat, rounded_lon)

class RouteGraphNode():
	'''
	Class to represent nodes data with geographic metadata:
		latitude, longitude, elevation
	'''
	n = 0
	def __init__(self, lat:float, lon:float, elevation:float=0):
		self.id = RouteGraphNode.n
		RouteGraphNode.n += 1
		self.latitude = lat
		self.longitude = lon
		self.elevation = elevation
		(self.rounded_lat, self.rounded_lon) = round_gpx(lat, lon)

	def get_label(self):
		return (self.rounded_lat, self.rounded_lon)

	def get_position(self):
		return (self.latitude, self.longitude)

class RouteGraphEdge():
	'''
	Class to represent graph edge with metadata
	'''
	def __init__(self, node_a:RouteGraphNode, node_b:RouteGraphNode, count:int=1):
		if node_a.id < node_b.id:
			self.id_min = node_a.id
			self.id_max = node_b.id
		else:
			self.id_min = node_b.id
			self.id_max = node_a.id
		self.count = 1

	def get_node_list(self):
		return [self.id_min, self.id_max]

	def get_key(self):
		return (self.id_min, self.id_max)

class RouteGraph():

	def __init__(self):
		#self.activities = []
		self.nodes = {}
		self.edges = {}

	def _add_subgraph_from_activity(self, activity_data):
		previous_node = None
		for datapoint in activity_data.datapoints:
			#print (datapoint)
			# construct node:
			lat = datapoint["directLatitude"]
			lon = datapoint["directLongitude"]
			if lat is None or lon is None:
				continue
			(node_pos_lat, node_pos_lon) = round_gpx(lat, lon)
			if (node_pos_lat, node_pos_lon) not in self.nodes:
				new_node = RouteGraphNode(lat, lon, datapoint["directElevation"])
				self.nodes[new_node.get_label()] = new_node
			else:
				new_node = self.nodes[(node_pos_lat, node_pos_lon)]
			
			if previous_node is not None:
				# check if new node is different from the previous node:
				if not previous_node.get_label() == (node_pos_lat, node_pos_lon):
					# construct edge:
					new_edge = RouteGraphEdge(previous_node, new_node)
					edge_key = new_edge.get_key()
					# if edge does not yet exist, add it:
					if edge_key not in self.edges:
						self.edges[edge_key] = new_edge
					else:
						self.edges[edge_key].count += 1
			previous_node = new_node

	def construct_activity_routes_graph(self, activity_type:str, lat:float, lon:float, delta:float=0.05, min_date:str=None, max_date:str=None):#, zoom:int=osmmd.MAP_DEFAULT_ZOOM, filename:str=""):
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

		for activity_data in activities:
			self._add_subgraph_from_activity(activity_data)

	def get_networkx_graph(self):
		g = nx.Graph()
		#print ("rg.nodes:")
		#for key in self.edges:
		#	print (self.edges[key].get_node_list())

		g.add_nodes_from([self.nodes[key].id for key in self.nodes])
		#print (self.edges)
		g.add_edges_from([self.edges[ekey].get_node_list() for ekey in self.edges])
		return g

def test():
	min_date = "2026-03-01"
	max_date = None #"2026-03-20"

	rg = RouteGraph()
	rg.construct_activity_routes_graph("running", 50.9, 11.6, min_date=min_date, max_date=max_date)
	g = rg.get_networkx_graph()
	#print (g.nodes)
	print ("number of nodes:", g.number_of_nodes())
	print ("number of edges:",g.number_of_edges())
	
	pos = [None for _ in range(RouteGraphNode.n)]
	for node in rg.nodes:
		pos[rg.nodes[node].id] = rg.nodes[node].get_position()
	nx.draw(g, pos, node_size=2)
	plt.show()


if __name__ == '__main__':
	test()