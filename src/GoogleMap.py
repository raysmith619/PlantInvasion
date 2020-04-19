from PIL import Image
import urllib
import urllib.request, urllib.parse, urllib.error, io
from math import log, cos, exp, tan, atan, pi, ceil
import re
import os
import sys

from select_trace import SlTrace
from APIkey import APIKey
"""
Notes:
A Maps Static API URL must be of the following form:

https://maps.googleapis.com/maps/api/staticmap?parameters

"""

EARTH_RADIUS = 6378137
EQUATOR_CIRCUMFERENCE = 2 * pi * EARTH_RADIUS
DEG_PER_METER = 360./EQUATOR_CIRCUMFERENCE
INITIAL_RESOLUTION = EQUATOR_CIRCUMFERENCE / 256.0
ORIGIN_SHIFT = EQUATOR_CIRCUMFERENCE / 2.0

class GoogleMap:
    """
    Create a map of area at given location and size
    with the requested pizel dimensions.  Multiple sub maps
    will be stiched together when necessary
        logitude    degrees
        latitude    degrees
        width        meters
        height       meters
        iwidth        pixels
        iheight       pixels
        maptype        string: stellite, roadmap, hybrid
    returning  a PIL.Image
    """
    def __init__(self,
            file=None,
            latitude=None,
            longitude=None,
            width=None,
            height=None,
            iwidth=None,
            iheight=None,
            maptype='satellite',
            markCenter=True,
            scale=1,
            zoom=None
            ):
        if file is None:
            file = "GoogleMapImage"
        self.file = file
        self.maptype = maptype
        self.markCenter = markCenter
        self.scale = scale
        if zoom is None:
            zoom = 19
        self.zoom = zoom
        if latitude is None and longitude is None:
            latitude = longitude = 0.
        if latitude is None:
            latitude = longitude
        if longitude is None:
            longitude = latitude
        self.latitude = latitude
        self.longitude = longitude
            
        if height is None and width is None:
            height = width = 100.
        if height is None:
            height = width
        if width is None:
            width = height
        self.height = height
        self.width = width
        
        if iwidth is None and iheight is None:
            iwidth = iheight = 640
        if iwidth is None:
            iwidth = iheight
        if iheight is None:
            iheight = iwidth    
            iwidth = iheight
        self.iwidth = iwidth
        self.iheight = iheight
        
        self.image = self.getImage()


    def newLatLon(self, latdist, longdist):
        """
        Return new (lat, long) based on x,y change in meters
        along surface, x-parallel equator, y-vertical to equator
        Short distances
        circle shrinks : cos 
        """
        lat = self.latitude
        lon = self.longitude
        rad_lat = lat*pi/180.
        cos_lat = cos(rad_lat)
        delta_lat_equator = 360.*latdist/EQUATOR_CIRCUMFERENCE
        new_lat = lat + delta_lat_equator
        
        delta_long_equator = 360.*longdist/EQUATOR_CIRCUMFERENCE
        delta_long = delta_long_equator*cos_lat
        new_lon = lon + delta_long
        
        return (new_lat, new_lon)
    
            
    def latlontoDistanceChange(self, lat, lon):
        """
        Convert new latitude, longitude to lat, long distance change in meters
        """
        if lat is None:
            lat = self.latitude
        if lon is None:
            lon = self.longitude
        if zoom is None:
            zoom = self.zoom
        lat_chg = lat - self.latitude
        lon_chg = lon - self.longitude
        lat_chg_dist = lat_chg/360.*EQUATOR_CIRCUMFERENCE
        lat_rad = lat*pi/180.
        lon_chg_dist = lon_chg/360.*cos(lat_rad)*EQUATOR_CIRCUMFERENCE
        return lat_chg_dist, lon_chg_dist
    
        
    def latlontopixels(self, lat, lon):
        lat_chg_dist, lon_chg_dist = self.latlontoDistanceChange(lat, lon)
        px = self.widthToPixel(lon_chg_dist)
        py = self.heightToPixel(lat_chg_dist)
        return px, py
    
    def pixelstolatlon(px, py, zoom):
        if zoom is None:
            zoom = self.zoom
                
        res = INITIAL_RESOLUTION / (2**zoom)
        mx = px * res - ORIGIN_SHIFT
        my = py * res - ORIGIN_SHIFT
        lat = (my / ORIGIN_SHIFT) * 180.0
        lat = 180 / pi * (2*atan(exp(lat*pi/180.0)) - pi/2.0)
        lon = (mx / ORIGIN_SHIFT) * 180.0
        return lat, lon
        
    
    def makeRelMarker(self, latdistoff, londistoff):
        """
        Make marker with distance off of latitude, longitude
        """
        new_lat, new_lon = self.newLatLon(latdistoff, londistoff)
        mkstr = "%.6f,%.6f" % (new_lat, new_lon)
        SlTrace.lg("latdistof=%d, longdistoff=%d newlat=%.6f newlong=%.6f" %
              (latdistoff, londistoff, new_lat, new_lon))
        return mkstr
    

    def widthToPixel(self, x):
        """
        Width(meters) to pixels
        """
        return x * self.iwidth/self.width


    def hightToPixel(self, y):
        """
        Height(meters) to pixels
        """
        return y * self.iheight/self.height
    
    
        
    def getImage(self):
        """
        Get image for __init__
        """
        SlTrace.lg("map=%s" % self)
        for key in self.__dict__.keys():
            SlTrace.lg("    ", key, self.__dict__[key])
        param_dict = {'size': '%dx%d' % (self.iwidth, self.iheight),
                        'maptype': self.maptype,
                        'sensor': 'false',
                        'scale': self.scale,
                        'key' : APIKey()}
        if self.zoom is not None:
            param_dict['zoom'] = str(self.zoom)
        param_dict['center'] = "%f,%f" % (self.latitude, self.longitude)
                
        url = 'http://maps.google.com/maps/api/staticmap?'
        if self.markCenter:
            markers_center_str = (
                "size=small|color=blue|label=C"
                 + "|%.6f,%.6f" % (self.latitude, self.longitude)
                 )            
            url += "markers="+ urllib.request.pathname2url(markers_center_str)
            url += "&"
        urlparams = urllib.parse.urlencode(param_dict)
        url +=  urlparams
        SlTrace.lg("url=%s" % url)
        max_try = 5
        ntry = 0
        while True:
            ntry += 1
            if ntry > max_try:
                SlTrace.lg("ntry = %d, exceeding max:%d" % (ntry, max_try))
                sys.exit(1)
            try:
                SlTrace.lg("ntry: %d" % ntry)
                f=urllib.request.urlopen(url)
                break
            except:
                raise
                continue
        self.im=Image.open(f)
        self.im.load()


    def save(self, *args):
        """
        Save image to file
        """
        file = self.file
        if len(args) > 0:
            file = args[0]
            
            
        ext_pat = re.compile(r'\.\w+$')
        if ext_pat.search(file) is None:
            file += ".png"     # Default extension
        try:
            f = open(file, "wb")
        except:
            SlTrace.lg("Can't open image save file %s", file)
            return
        
        try:
            self.im.save(f)
            
        except:
            SlTrace.lg("Problem saving image file %s", file)
            return
        
        SlTrace.lg("Image file saved in %s", os.path.abspath(file))
        
        
    def show(self):
        """
        Display image
        """
        self.im.show()
        
        
"""
Stanalone test / exercise:
"""
if __name__ == "__main__":
    lat = 42.376
    lon = -71.177058
    maptype = "hybrid"
    zoom = 18
    maptype = "roadmap"
    file_name = "test_GoogleMap"
    file = os.path.join("..", "out", file_name)
    gm = GoogleMap(latitude=lat, longitude=lon, maptype=maptype, file=file,
                   height=50, width=50)
    gm.show()
    gm.save()
    SlTrace.lg("End of Test")