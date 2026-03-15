#!usr/bin/python
# -*- coding: utf-8 -*-import string

import os
import math
import urllib.request
from PIL import Image

from misc import ensure_dir_exists

DEFAULT_ZOOM = 14
EXAMPLE_LATITUDE = 52.5
EXAMPLE_LONGITUDE = 13.4
MAPSERVER = "https://a.tile.openstreetmap.org/"
MAP_DIR = "maps"

def get_maptile_filename(x:int,y:int,z:int)-> str:
	tiles_dir = os.path.join(MAP_DIR, "tiles")
	ensure_dir_exists(tiles_dir)
	return os.path.join(tiles_dir, str(z)+"-"+str(x)+"-"+str(y)+".png")


def latlong_to_merccoords(lat:float, lon:float, zoom:int=DEFAULT_ZOOM):
	'''
	computes the (x,y)-coordinates from (latitude, longitude) data, to fetch map tiles from mercerator projected online map service

	maths from https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Derivation_of_tile_names
	'''

	x = int((lon+180)/360 * 2**zoom)
	y = int((1-(math.log(math.tan(lat*(math.pi/180))+(1/(math.cos(lat*(math.pi/180))))))/math.pi)*2**(zoom-1))
	return (x,y)

def download_maptiles(maptile_coords, zoom:int):
	'''
	maptile_coords: array of tupels (x:int,y:int) that specify maptile positions
	zoom: required to construct filenames
	'''
	for coords in maptile_coords:
		x = coords[0]
		y = coords[1]
		filename = get_maptile_filename(x,y,zoom)
		fullurl = MAPSERVER+str(zoom)+"/"+str(x)+"/"+str(y)+".png"
		#print ("download tile: ",fullurl)
		webopener = urllib.request.URLopener()
		webopener.addheader('User-Agent', 'Magic Browser')
		filename, headers = webopener.retrieve(fullurl, filename)

def construct_maptile_coords(lat_min:int, lat_max:int, lon_min:int, lon_max:int, zoom:int=DEFAULT_ZOOM, add_border:bool=True):
	'''
	lat_min: minimum latitude from a set of coordinates
	lat_max: maximum latitude from a set of coordinates
	lon_min: minimum longitude from a set of coordinates
	lon_min: maximum longitude from a set of coordinates
	zoom
	add_border: if True, the area covered by the constructed coords will include one tile width of border

	constructs an rray of (x:int, y:int)-tuples that defines a set of maptiles to cover the area defined by the parameters.
	'''
	mincoords = latlong_to_merccoords(lat_min, lon_min, zoom)
	maxcoords = latlong_to_merccoords(lat_max, lon_max, zoom)
	x_1 = mincoords[0]
	y_1 = mincoords[1]
	x_2 = maxcoords[0]
	y_2 = maxcoords[1]
	x_min = min(x_1, x_2)
	x_max = max(x_1, x_2)
	y_min = min(y_1, y_2)
	y_max = max(y_1, y_2)
	if add_border:
		x_min -= 1
		y_min -= 1
		x_max += 1
		y_max += 1

	maptile_coords = []
	for ix in range(x_min, x_max+1):
		for iy in range(y_min, y_max+1):
			maptile_coords.append((ix, iy))
	return maptile_coords

def combine_maptiles(maptile_coords, zoom:int=DEFAULT_ZOOM, filename:str="map", dim:int=256):
	'''
	maptile_coords: a list of (x:int, y:int)-tuples, as constructed by construct_maptile_coords
	zoom: required for getting filenames of tiles
	filename: name of generate map image file
	dim: dimension of tile-images

	combines the tiles into a single image, based on their position in the 2D-Array:
		tiles[0][0] is top-left, tiles[-1][-1] is bottom-right

	code assumes that the tile coordinates in maptile_coords fully cover a rectangular area.
	otherwise the resulting map image might have empty rectangles.
	'''
	# get coordinate ranges:
	x_min = -1
	x_max = -1
	y_min = -1
	y_max = -1
	for coords in maptile_coords:
		(x,y) = coords
		if x_min < 0 or x < x_min:
			x_min = x
		if x > x_max:
			x_max = x
		if y_min < 0 or y < y_min:
			y_min = y
		if y > y_max:
			y_max = y

	n_x = x_max-x_min+1
	n_y = y_max-y_min+1
	total_width = n_x * dim
	total_height = n_y * dim

	combined_map = Image.new('RGB', (total_width, total_height))
	for ix in range(n_x):
		for iy in range(n_y):
			tile = Image.open(get_maptile_filename(ix+x_min,iy+y_min, zoom))
			combined_map.paste(tile, (ix*dim, iy*dim))

	ensure_dir_exists(MAP_DIR)
	full_filename = filename+"_"+str(zoom)+".png"
	filepath = os.path.join(MAP_DIR, filename+"_"+str(zoom)+".png")
	combined_map.save(filepath)
	print ("Generated map saved in: "+filepath)

def test(test_coords=False, test_maptile=True, test_download=True, test_combine=True):
	zoom = 15
	if test_coords:
		print ("Test computation of x-y-coordinates:")
		coords = latlong_to_merccoords(EXAMPLE_LATITUDE, EXAMPLE_LONGITUDE, zoom)
		x = coords[0]
		y = coords[1]
		print (x,y)
		print (MAPSERVER+str(zoom)+"/"+str(x)+"/"+str(y)+".png")
	
	if test_maptile:
		print ("Test construct list of maptile-coordinates:")
		maptile_coords = construct_maptile_coords(EXAMPLE_LATITUDE-0.01, EXAMPLE_LATITUDE+0.01, EXAMPLE_LONGITUDE-0.01, EXAMPLE_LONGITUDE+0.01, zoom)
		print (maptile_coords)

	if test_download:
		print ("Test download map tiles:")
		download_maptiles(maptile_coords, zoom=zoom)
		print ("download complete!")

	if test_combine:
		print ("Test combine tiles to map:")
		#tiles = get_tiles(maptile_coords)
		combine_maptiles(maptile_coords, zoom, "testmap")
	
	print ("Finish!")

if __name__ =="__main__":
	test(False, True, True, True)