# -*- coding: utf-8 -*-
"""Find if WPs are in country's territorial waters."""

import shapefile as shp
from shapely.geometry.polygon import Polygon
from shapely.geometry import shape, Point
from shapely.wkb import loads
import pickle

import os

with open('wolfgang/geo/territorial_water.pickle', 'rb') as handle:
    serialized = pickle.load(handle)
polygons = {name:loads(poly) for name,poly in serialized.items()}

def locate_water_point(pt):
    for zone, poly in polygons.items():
        if Point(pt).within(poly): # check inside polygon
            return(zone)
    return None
# print(locate_point((7.007194, 43.547634))) # internal water
# print(locate_point((6.982897, 43.471150))) # internal water
#
# print(locate_point((7.015924, 43.538662))) # coast
# print(locate_point((7.016239, 43.544192))) # coast
# print(locate_point((7.015011, 43.548699))) # port
#
# print(locate_point((5.883238, 41.301252))) # high seas
#
# print(locate_point((15.883238, 44.301252))) # high seas
