'''
User-defined functions for GIS distance measurement

Prepared by Thomas W. Miller
Revised May 18, 2023

begin with conversion function of degrees to radians
needed for lat_long_distance function
example also shows how to convert lon/lat to UTM
UTM units are in meters

UTM work requires installation of the pyproj package
    pip install pyproj

See README.md for Markdown file explaining UTMs
Or view README.html in a browser.
'''
import math
from math import pi, pow, sin, cos, asin, sqrt, floor
from scipy import stats
import numpy as np
from pyproj import Proj

def degrees_to_radians(x):
     return((pi/180)*x)
     
def lon_lat_distance_miles(lon_a,lat_a,lon_b,lat_b):
    radius_of_earth = 24872/(2*pi)
    c = sin((degrees_to_radians(lat_a) - \
    degrees_to_radians(lat_b))/2)**2 + \
    cos(degrees_to_radians(lat_a)) * \
    cos(degrees_to_radians(lat_b)) * \
    sin((degrees_to_radians(lon_a) - \
    degrees_to_radians(lon_b))/2)**2
    return(2 * radius_of_earth * (asin(sqrt(c))))    

def lon_lat_distance_meters (lon_a,lat_a,lon_b,lat_b):
    return(lon_lat_distance_miles(lon_a,lat_a,lon_b,lat_b) * 1609.34) 
    
# UTM zone may be computed directly from the list of longitude values
def findZone(listOfLon):
    zones = [ ((floor((long + 180)/6) ) % 60) + 1 for long in listOfLon]
    zone = stats.mode(zones, keepdims = False)[0].astype(int)
    return(zone.item())    
    
# Glendale, CA, latitude 34.142509, and longitude is -118.255074  
# Pasadena latitude and longitude coordinates are: 34.156113, -118.131943
print() 
print("Glendale to Pasadena distances computed directly from lon/lat:")
print("miles: ",lon_lat_distance_miles(-118.255074 ,34.142509,-118.131943,34.156113))
print("meters: ",lon_lat_distance_meters(-118.255074 ,34.142509,-118.131943,34.156113))

# UTM zones are obtained from longitude measures only
zoneSetting = str(findZone([-118.255074,-118.131943]))

# apLocation data defined by UTM apx and apy and elevation apz coordinates
# apx and apy come from projection of coord_longitude and coord_latitude
myProj = Proj("+proj=utm +zone=" + zoneSetting + " +north +ellps=WGS84 +datum=WGS84 +units=m +no_defs")

GlendaleUTMx, GlendaleUTMy = myProj(-118.255074 ,34.142509)
PasadenaUTMx, PasadenaUTMy = myProj(-118.131943, 34.156113)
UTMdistance = sqrt((GlendaleUTMx - PasadenaUTMx)**2 + (GlendaleUTMy - PasadenaUTMy)**2)
print() 
print("Glendale to Pasadena distances computed from UTM projection:") 
print("meters: ",UTMdistance)

'''
Glendale to Pasadena distances computed directly from lon/lat:
miles:  7.102649835652347
meters:  11430.578486508748

Glendale to Pasadena distances computed from UTM projection:
meters:  11452.445557847373

Note accuracy of the UTM conversion... less than 22 meters
difference between lon/lat and UTMx/UTMy calculations
for distance between two cities 7 miles apart
'''