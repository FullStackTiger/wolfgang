# Save pickle file with territorial water info:

import time
start_time = time.time()

import shapefile as shp
from shapely.geometry.polygon import Polygon
from shapely.geometry import shape, Point

keep_countries = ('ESP', 'FRA', 'MCO', 'ITA', 'HRV', 'SVN', 'MNE', 'ALB', 'GRC', 'CYP', 'MLT', 'TUR', 'SYR', 'LBN', 'ISR', 'PSE', 'JOR', 'EGY', 'LBY', 'TUN', 'DZA', 'MAR', 'GIB')

f = '/Users/dave/Downloads/World_Internal_Waters_v2_20180221/eez_internal_waters_v2.shp'
sf = shp.Reader(f)
polygons_iw = {}
for i, a_shape in enumerate(sf.shapes()):
    country = sf.records()[i][7]
    if country not in keep_countries:
        continue
    polygons_iw[country] = shape(a_shape)

f = '/Users/dave/Downloads/World_12NM_v2_20180221/eez_12NM_v2.shp'
sf = shp.Reader(f)
polygons_12n = {}
for i, a_shape in enumerate(sf.shapes()):
    country = sf.records()[i][7]
    if country not in keep_countries:
        continue
    polygons_12n[country] = shape(a_shape)


polygons = {name:(polygons_12n[name].union(polygons_iw[name]) if name in polygons_iw else polygons_12n[name]) for name in polygons_12n.keys()}


from shapely.wkb import dumps
import pickle
serialized = {name:dumps(poly) for name,poly in polygons.items()}
with open('scripts/international_water.pickle', 'wb') as fp:
    pickle.dump(serialized, fp, protocol=pickle.HIGHEST_PROTOCOL)


from shapely.wkb import loads
import pickle


with open('scripts/international_water.pickle', 'rb') as handle:
    serialized = pickle.load(handle)

polygons = {name:loads(poly) for name,poly in serialized.items()}

def locate_point(pt):
    for zone, poly in polygons.items():
        if Point(pt).within(poly): # check inside polygon
            return(zone)

print(locate_point((7.007194, 43.547634))) # internal water
print(locate_point((6.982897, 43.471150))) # internal water

print(locate_point((7.015924, 43.538662))) # coast
print(locate_point((7.016239, 43.544192))) # coast
print(locate_point((7.015011, 43.548699))) # port

print(locate_point((5.883238, 41.301252))) # high seas

print(locate_point((15.883238, 44.301252))) # high seas

print("--- %s seconds ---" % (time.time() - start_time))
