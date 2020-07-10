#testdeg2meter.py
"""
Test/display degree to Meter conversion
"""
from math import radians, degrees, cos, sin, atan2, sqrt
from select_trace import SlTrace

from GeoDraw import geoDistance, geoMove

'''    
def geoDistance(latLong=None, latLong2=None):
    """
    Compute signed distance(in meters) between two points given in latitude,longitude pairs
    From: https://www.movable-type.co.uk/scripts/latlong.html
        JavaScript:    

    var R = 6371e3; // metres
    var phi_1 = lat1.toRadians();
    var phi_2 = lat2.toRadians();
    var delta_phi = (lat2-lat1).toRadians();
    var delta_lambda = (lon2-lon1).toRadians();
    
    var a = Math.sin(delta_phi/2) * Math.sin(delta_phi/2) +
           Math.cos(phi_1) * Math.cos(phi_2) *
           Math.sin(delta_lambda/2) * Math.sin(delta_lambda/2);
    var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    
    var d = R * c

    """
    lat1 = latLong[0]
    lon1 = latLong[1]
    lat2 = latLong2[0]
    lon2 = latLong2[1]
    R = 6371e3          # meters
    phi1 = radians(lat1)
    phi2 = radians(lat2)
    delta_phi = radians(lat2-lat1)
    delta_lambda = radians(lon2-lon1)
    
    a = (
        sin(delta_phi/2) * sin(delta_phi/2) +
            cos(phi1) * cos(phi2) *
            sin(delta_lambda/2) * sin(delta_lambda/2)
        )

    c = 2 * atan2(sqrt(a), sqrt(1-a));
    
    d = R * c;        
    return d
    
def geoMove(latLong=None, latDist=0, longDist=0):
    """
    Compute new latatitude, longitude location given
    original latatitude, longitude plus distance in lat(south), long(east) directions in meters
    Developed from geoDistance
    :returns latitude, longitude   pair
    """
    lat1 = latLong[0]
    long1 = latLong[1]
    
    R = 6371e3          # meters
    phi1 = radians(lat1)
    delta_phi = latDist / R 
    phi2 = phi1 + delta_phi
    lat2 = degrees(phi2)
    
    lambda1 = radians(long1)
    
    R2 = R * cos((phi1+phi2)/2)     # Shortened by higher latitude
    SlTrace.lg(f"phi1: {phi1} phi2: {phi2} (phi1+phi2)/2:{(phi1+phi2)/2:7.3g}"
               f"  cos((phi1+phi2/2): {cos((phi1+phi2/2)):7.2g}")
    SlTrace.lg(f"longDist:{longDist:15.5g}    R2:{R2:15.5g}"
               f" cos((phi1+phi2/2): {cos((phi1+phi2/2)):7.2g}")
    delta_lambda = longDist / R2
    lambda2 = lambda1 + delta_lambda
    SlTrace.lg(f"lambda2:{lambda2:15.5g}")
    long2 = degrees(lambda2)
    return lat2, long2
'''

deg_long = -71      # Near here
deg_start = 0
deg_end = 90
deg_inc = 1
SlTrace.lg(f"{'deg':>5s} {'dist_x':>10s} {'dist_y':>10s}"
                        f" {'x_d_chg':>10s} {'y_d_chg':>10s}"
                        f" {'x_deg':>15s} {'long_deg':>15s}"
                        )
for deg in range(deg_start, deg_end+deg_inc, deg_inc):
    deg_lat = deg
    deg_lat2 = deg_lat + deg_inc
    deg_long2 = deg_long + deg_inc
    dist_x = geoDistance((deg_lat, deg_long), (deg_lat, deg_long2))
    if abs(dist_x) > 112e3:
        SlTrace.lg(f"\ndist_x: {dist_x: 15.5g}") 
    dist_y = geoDistance((deg_lat, deg_long), (deg_lat2, deg_long))
    move_x_latLong = geoMove((deg_lat,deg_long), longDist=dist_x)
    move_long = move_x_latLong[1]
    move_x_deg_chg = move_long-deg_long
    move_y_latLong = geoMove((deg_lat, deg_long), latDist=dist_y)
    move_y_deg_chg =  move_y_latLong[0]-deg_lat
    if abs(move_long) > 100:
        SlTrace.lg(f"\n\n large long:{move_long}")
    SlTrace.lg(f"{deg_lat:5d} {dist_x:10.1f} {dist_y:10.1f}"
               f" {move_x_deg_chg:10.5g} {move_y_deg_chg:10.5g}"
               f" {move_x_latLong[1]:15.5g} {deg_long:15.5g}"
               )
        
    
    