"""
Interface to Pillow Image facilitating map annotation 
"""
import os
from PIL import Image, ImageDraw, ImageFont
from math import cos, sin, sqrt, asin, atan2, pi, ceil, radians, degrees
from geographiclib.geodesic import Geodesic

from select_error import SelectError
from builtins import staticmethod
###from openpyxl.drawing.effect import Color
###from idlelib.colorizer import color_config
###from pandas._libs.tslibs.offsets import get_firstbday
from GeoDrawMapState import GeoDrawMapState

from select_trace import SlTrace
from survey_trail import SurveyTrail
from compass_rose import CompassRose

def get_bearing(p1, p2):
    """ Get bearing p1 to p2, given two points p1, p2
    :p1,p2: points(latitude, longitude)
    From Stackoverflow.com Sterling Butters
    """
    lat1, long1 = p1.lat, p1.long
    lat2, long2 = p2.lat, p2.long

    brng = Geodesic.WGS84.Inverse(lat1, long1, lat2, long2)['azi1']
    return brng

EARTH_RADIUS = 6378137.
EQUATOR_CIRCUMFERENCE = 2 * pi * EARTH_RADIUS

def deg2rad(degree):
    return radians(degree)

def rad2deg(rad):
    return degrees(rad)
    
trace_scale = False

def minMaxLatLong(points):
    """
    Given point pairs lat,long, calculate max, min and
    dictionary of 'max_lat', 'min_lat, 'max_long', 'min_long' values
    followed by a dictionary of 'max_lat', 'min_lat, 'max_long', 'min_long' indexes into points
    Includes the maximum of initial and rotated points
    :points: list of SamplePoint
    :returns: minLat,minLog, maxLong, maxLong
    """
    max_lat = None
    min_lat = None
    max_long = None
    min_long = None
    for point in points:
        if isinstance(point, dict):
            lat, long = point["lat"], point["long"] # Dict 
        elif isinstance(point, tuple):       # Tuple
            lat, long = point
        else:
            lat, long = point.lat, point.long
        
        if max_lat is None or lat > max_lat:
            max_lat = lat
        if min_lat is None or lat < min_lat:
            min_lat = lat
        if max_long is None or long > max_long:
            max_long = long
        if min_long is None or long < min_long:
            min_long = long
    return min_lat, min_long, max_lat, max_long
    
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
    delta_lambda = longDist / R2
    lambda2 = lambda1 + delta_lambda
    long2 = degrees(lambda2)
    return lat2, long2

def geoUnitLen(unit="meter"):
    """ Unit length in meters
    :unit: unit name (only looks at first letter)
            feet, meeter, yard, smoot
            default: meter
    """
    uname = unit.lower()[0]
    if uname  == 'f':
        unitLen = .3048
    elif uname == 'm':
        unitLen = 1.
    elif uname == 'y':
        unitLen = .3048*3
    elif uname == "s":      # smoot
        unitLen = 1.7018
    else:
        raise SelectError(f"Unrecognized unit name '{unit}' choose f[oot],m[eter],y, or s")

    return unitLen


# Haversine formula example in Python
# Author: Wayne Dyck

import math

def gDistance(origin, destination):
    lat1, lon1 = origin
    lat2, lon2 = destination
    radius = 6371 # km

    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = radius * c

    return d


class GeoDraw:
    
    EAST_DEG = 0.
    NORTH_DEG = 90.
    WEST_DEG = 180.
    SOUTH_DEG = 270.
    
    
    def __init__(self,
        image,
        mapRotate=None,
        expandRotate=None,
        
        ulLat=None, ulLong=None,    # Bounding box
        lrLat=None, lrLong=None,
        ulX=None, ulY=None,         # Strict distance unit non long/lat specs
        lrX=None, lrY=None,
        forceSquare=True,
        
        pos=None,                   # Current pen location
        latLong=None,
        xY=None,
        
        deg=None,                      # Set Current pen direction
        theta=None,
        showSampleLL = True,        
        unit='meter',
        ):
        """ Setup geographic map annotation facility
        For simplicity, internal locations are kept as floating point xy pixels
        Physical locations are kept as Latitude, Logitude pairs but can be converted
            to image x,y pixels
        
        :image - PIL compatible image
        :ulLat - Map's Upper left corner latitude
        :ulLong - Map's Upper left corner longitude
        :lrLat - Map's Lower right corner latitude
        :lrLong - Map's lower right corner longitude
        :mapRotate: - Map's rotation (in degrees, counter clockwise) from North (up)
        :forceSquare: - Force new image dimensions to be square
        mapPoints - points (latitude, longitude) included in map - minimum a perimeter
        :pos - drawing pen current position (x,y) in unit(meter)
        :latLong - drawing pen current location (latitude, longitude) in degrees
        :xY - drawing pen current location in floating pixels (x-left to right,y-top to bottom)
        :deg - drawing pen current direction in degrees (counter clockwise)
        :theta - drawing pen current direction in radians
        """
        self.in_pixelToLatLong = 0      # Debugging level count
        self.in_latLongToPixel = 0
        self.showSampleLL = showSampleLL
        self.forceSquare = forceSquare
        self.compass_rose = CompassRose().live_obj()    
        if image is None:
            image = Image.new("RGB", (100, 100))
        self.imageOriginal = image
        self.setImage(image)
        self.mapRotate = mapRotate              # Current rotation
        self.mapRotateOriginal = mapRotate      # record original
        self.expandRotate = expandRotate
        
        if deg is not None and theta is not None:
            raise SelectError("Only deg or theta is allowed")
        if theta is not None:
            deg = theta/pi * 180
        self.deg = deg          #None - unrotated
        if ulLat is None:
            ulLat = ulLong = lrLat = lrLong = 0
        else:
            if lrX is not None:
                raise SelectError("Only one of ulLat and lrX can be specified")
            if ulLong is not None and lrY is not None:
                raise SelectError("Only one of ulLong or lrY can be specified")

        self.setLatLong(ulLat=ulLat, ulLong=ulLong,
                        lrLat=lrLat, lrLong=lrLong,
                        setXY=(ulX is None)) 
        self.setCurLoc(pos=pos, latLong=latLong, xY=xY)
        self.setCurAngle(deg=deg, theta=theta)
        self.unit = unit

    def setImage(self, image):
        """
        Setup image and associated data
        This should be called when ever the image is
        created.
        """
        self.image = image
        self.draw = ImageDraw.Draw(self.image)      # Setup ImageDraw access
        

    def setLatLong(self, ulLat=None, ulLong=None,
                    lrLat=None, lrLong=None,
                    setXY=True):
        """ Setup latitude, Longitude and distance, if requested
        :ulLat, ulLong, lrLat, lrLong: set corners lat, long
                    default: use current values
        :setXY: set distance, iff True
            default: True
        """
        if ulLat is not None:
            self.ulLat = ulLat
         
        if ulLong is not None:
            self.ulLong = ulLong
        
        if lrLat is not None:
            self.lrLat = lrLat
        
        if lrLong is not None:
            self.lrLong = lrLong
        SlTrace.lg(f"\n setLatLong: ulLat:{self.ulLat} ulLong:{self.ulLong}"
                   f" lrLat:{self.lrLat} lrLong:{self.lrLong} ")

        ulmx = 0.
        ulmy = 0.
        lrmx = ulmx  + self.getWidth()
        lrmy = ulmy + self.getHeight()
        self.ulmx = ulmx
        self.ulmy = ulmy
        self.lrmx = lrmx
        self.lrmy = lrmy
        SlTrace.lg(f"setLatLong: getWidth:{self.getWidth()} getHeight:{self.getHeight()}")
        SlTrace.lg(f"setLatLong: ulmx:{self.ulmx} ulmy:{self.ulmy}"
                   f" lrmx:{self.lrmx} lrmy:{self.lrmy} ")

            
        self.long_width = self.lrLong-self.ulLong    # increase left to right
        self.lat_height = self.ulLat-self.lrLat      # increase ulLat: upper(more) to lrLat: lower(less)
        
        if setXY:
            """
            The normal case - set distance square
            with 0,0 in upper left corner
            and unit distance in x and  y to
            lower right corner
            lat increases (positive North) upwards
            Longitude (negative for West) increases (less negative) to right
            x increases to right
            y increases downward   
            """
            ulX = 0.        # Upper left corner is origin
            ulY = 0.
            '''
            lat_avg = (self.ulLat+self.lrLat)/2.
            lat_rad = lat_avg*pi/180.
            lrX = ulX + cos(lat_rad) * (self.lrLong-self.ulLong) / 360. * EQUATOR_CIRCUMFERENCE
            lrY = ulY + (self.ulLat-self.lrLat) / 360. * EQUATOR_CIRCUMFERENCE
            '''
            lrX = self.geoDist((self.ulLat, self.ulLong), (self.ulLat, self.lrLong), 'm')
            lrY = self.geoDist((self.ulLat, self.lrLong), (self.lrLat, self.lrLong), 'm')
            SlTrace.lg(f"Loaded Image: width:{self.getWidth()} height:{self.getHeight()}")
            SlTrace.lg(f"Distance coordinates(meters):"
                  f"\n\tUpper Left x:{ulX:.1f} y:{ulY:.1f}"
                  f"\n\tLower Right x: {lrX:.1f} y: {lrY:.1f}")
            self.ulX = ulX
            self.ulY = ulY
            self.lrX = lrX
            self.lrY = lrY
        SlTrace.lg(f"setLatLong: ulX:{self.ulX:.1f} ulY:{self.ulY}"
                   f" lrX:{self.lrX} lrmy:{self.lrY} meters")

    @classmethod
    def boundLatLong(cls, points=None, mapRotate=None,
                    borderM=None, borderD=None, borderP=None):
        """
        Calculate a vertical bounding box containing the provided points on a rotated map,
        providing an optional surrounding border area, clear of points, such that
        given a north-pointing scan provided by Google-Maps will, when rotated and cropped
        verticaly and horizonally, give a rectangle. 
        :points a list of points(SamplePoint), each having at least the entries
                'lat' or 0 - latitude (float) degree
                'long' or 1 - longitude (float) degree
        :mapRotate - map rotation (degree counter clockwise), from horizontal
        :borderX additional area added surrounding points
            borderM - meters
            borderD - degrees
            borderP - pixels
                Default: 10 meters
        :returns: ulLatLong, lrLatLong
        """
        
        
        
        """
        Use GeoDraw to to the arithmetic lat,Long - x,y
        """
        
        limits_lat_long, _ = GeoDraw.limitsLatLong(points=points, rotate=mapRotate)
        ulLat = limits_lat_long['max_lat']
        ulLong = limits_lat_long['min_long']
        lrLat = limits_lat_long['min_lat']
        lrLong =  limits_lat_long['max_long']
        print("limits(rotate=%.0f): ulLat:%.6f ulLong: %.6f  lrLat:%.6f lrLong: %.6f" %
                            (mapRotate, ulLat, ulLong,        lrLat, lrLong))
        gd_image = Image.new("RGB", (100, 100))
        gd = GeoDraw(gd_image, ulLat=ulLat, ulLong=ulLong, lrLat=lrLat, lrLong=lrLong,
                      mapRotate=mapRotate)     # simple strait up
        #HACK because our stuf doesn't work
        if borderM is not None:
            deg_chg = borderM*.3/(70*5280.)
            ulLat -= deg_chg
            ulLong -= deg_chg
            lrLat -= deg_chg
            lrLong += deg_chg
            return (ulLat,ulLong), (lrLat,lrLong)
            
        nb_spec = 0
        if borderM is not None:
            nb_spec += 1
            border = gd.meterToPixel(borderM)
        if borderD is not None:
            nb_spec += 1
            border = gd.latLongToPixel(latLong=(borderD,borderD))[0]
        if borderP is not None:
            nb_spec += 1
            border = borderP
        if nb_spec == 0:
            border = gd.meterToPixel(100.)
        if nb_spec > 1:
            raise SelectError("Can't use more than one of borderM, borderD, borderP")
        
        ulLatLong1 = (ulLat, ulLong)
        lrLatLong1 = (lrLat, lrLong)
        if border is not None and border > 0:
            ulXY2 = gd.addToPoint(latLong=ulLatLong1, leng=border, deg=-180)
            ulXY2 = gd.addToPoint(xY=ulXY2, leng=border, deg=90)
            ulLatLong1 = gd.getLatLong(xY=ulXY2)
            
            lrXY2 = gd.addToPoint(latLong=lrLatLong1, leng=border, deg=0)
            lrXY2 = gd.addToPoint(xY=lrXY2, leng=border, deg=-90)
            lrLatLong1 = gd.getLatLong(xY=lrXY2)
            print("After border of %f pixels added" % border)
            print("ulLatLong=%s  lrLatLong=%s" % (ulLatLong1, lrLatLong1))

            print("latLong border changes: ulLat chg=%.6f  ulLong chg=%.6f  lrLat chg=%.6f  lrLong chg=%.6f " %
                                    (ulLatLong1[0]-ulLat,
                                    ulLatLong1[1]-ulLong,
                                    lrLatLong1[0]-lrLat,
                                    lrLatLong1[1]-lrLong)
                                    )
        return ulLatLong1, lrLatLong1


    @staticmethod    
    def limitsLatLong(points, rotate):
        """
        Given point pairs lat,long, calculate max, min and
        dictionary of 'max_lat', 'min_lat, 'max_long', 'min_long' values
        followed by a dictionary of 'max_lat', 'min_lat, 'max_long', 'min_long' indexes into points
        Includes the maximum of initial and rotated points
        :points: list of SamplePoint
        """
        limit_pointh = {}       # Hash by limit
        limit_point_roth = {}   # hash of rotated points by limit
        pointh = {}             # Hash by limit into points
                                # Find range
        max_lat1 = None
        min_lat1 = None
        max_long1 = None
        min_long1 = None
        trace_ck = False
        for index, point in enumerate(points):
            if isinstance(point, dict):
                lat1, long1 = point["lat"], point["long"]
            elif isinstance(point, tuple):
                lat1, long1 = point
            else:
                lat1, long1 = point
            
            if max_lat1 is None or lat1 > max_lat1:
                max_lat1 = lat1
                if trace_ck:
                    print("[%d]max_lat1=%.7f" % (index, max_lat1))
            if min_lat1 is None or lat1 < min_lat1:
                min_lat1 = lat1
            if max_long1 is None or long1 > max_long1:
                max_long1 = long1
                if trace_ck:
                    print("[%d]max_long1=%.7f" % (index, max_long1))
            if min_long1 is None or long1 < min_long1:
                min_long1 = long1
                if trace_ck:
                    print("[%d]min_long1=%.7f" % (index, min_long1))
        lat_len = max_lat1 - min_lat1
        long_len = max_long1 - min_long1

        print(("limitsLatLong points     NO rotation bounds:")
              + "max_lat=%.6f min_long=%.6f min_lat=%.6f max_long=%.6f" %
                  (max_lat1, min_long1,  min_lat1, max_long1)
                  + "\nlat_len=%.6f long_len=%.6f" % (lat_len, long_len))

        max_lat2 = max_lat1
        min_lat2 = min_lat1
        max_long2 = max_long1
        min_long2 = min_long1
        if rotate != 0:
            rotfact = 1.2
            theta = radians(rotate)
            lat_radius = (max_lat1-min_lat1)/2
            lat_chg = rotfact*lat_radius * sin(theta)
            max_lat2 += lat_chg
            min_lat2 -= lat_chg

            long_radius = (max_long1-min_long1)/2
            long_chg = rotfact*long_radius * sin(theta)
            max_long2 += long_chg
            min_long2 -= long_chg
            

        print(("limitsLatLong points rotated %.0f deg bounds:" % rotate)
              + "max_lat=%.6f min_long=%.6f min_lat=%.6f max_long=%.6f" %
                  (max_lat2, min_long2,  min_lat2, max_long2))

        print(("limitsLat chg points rotated %.0f deg bounds:" % rotate)
              + "max_lat=%.6f min_long=%.6f min_lat=%.6f max_long=%.6f" %
                  (max_lat2-max_lat1, min_long2-min_long1,  min_lat2-min_lat1, max_long2-max_long1))
        lat_fudge = 1e-9 
        long_fudge = 1e-9 
        return {'max_lat' : max_lat2 + lat_fudge,
                'min_lat' : min_lat2 - lat_fudge,
                'max_long' : max_long2 + long_fudge,
                'min_long' : min_long2 - long_fudge}, limit_pointh

        
    def limitsXY(self, points, rotate):
        """
        Given point pairs lat,long in rotated map image, calculate max, min x,y pixels
        dictionary of 'max_x', 'min_x, 'max_y', 'min_y' values
        followed by a dictionary of 'max_x', 'min_x, 'max_y', 'min_y' indexes into points
     :points: list of SamplePoint
        """
        limit_pointh = {}       # Hash by limit
        limit_point_roth = {}   # hash of rotated points by limit
        pointh = {}             # Hash by limit into points
                                # Find range
        max_x = None
        min_x = None
        max_y = None
        min_y = None
        for index, point in enumerate(points):
            lat, long = point.latLong()
            x,y = self.getXY(latLong=(lat, long))
            
            if max_x is None or x > max_x:
                max_x = x
                print("[%d]max_x=%.7f" % (index, max_x))
            if min_x is None or x < min_x:
                min_x = x
            if max_y is None or y > max_y:
                max_y = y
                print("[%d]max_y=%.7f" % (index, max_y))
            if min_y is None or y < min_y:
                min_y = y
                print("[%d]min_y=%.7f" % (index, min_y))
        y_len = max_y - min_y
        x_len = max_x - min_x
        return {'max_x' : max_x,
                'min_x' : min_x,
                'max_y' : max_y,
                'min_y' : min_y}, limit_pointh

            
    def addCompassRose(self, compassRose=None):
        """
        Add orientation marker
        """
        SlTrace.lg("addCompassRose")
        self.compass_rose = CompassRose(placement=compassRose).live_obj()
        if self.compass_rose is None:
            return
        
        xFraction = self.compass_rose.x_fract
        yFraction = self.compass_rose.y_fract
        lenFraction = self.compass_rose.len_fract
        mx = self.getWidth() * xFraction
        my = self.getHeight() * yFraction
        arrow_len = sqrt(self.getWidth()**2 + self.getHeight()**2) * lenFraction
        cent_color = (255,0,0)
        xY = (mx,my)
        self.circle(xY=xY, radius=5, fill=cent_color)
        north_deg = 90.     # Default map north
        arrow_color = (100,255,100, 126)
        arrow_width = self.adjWidthBySize(4)
        self.lineSeg(xY=xY, leng=arrow_len, deg=north_deg, fill=arrow_color, width=arrow_width)
        arrow_point_xy = self.addToPoint(xY=xY, leng=arrow_len, deg=north_deg)
        arrow_head_width = int(1.2*arrow_width)
        head_len = arrow_len/5.
        left_edge_deg = north_deg-20. - 180.
        self.lineSeg(xY=arrow_point_xy, leng=head_len, deg=left_edge_deg,
                      fill=arrow_color, width=arrow_head_width)
        right_edge_deg = north_deg+20. - 180.
        self.lineSeg(xY=arrow_point_xy, leng=head_len, deg=right_edge_deg,
                      fill=arrow_color, width=arrow_head_width)
        # North Label
        label_size=38
        north_label_font = ImageFont.truetype("NIAGSOL.TTF", size=label_size)
        label_pt = self.addToPoint(xY=arrow_point_xy, leng=label_size+10, deg=north_deg)

        self.text("North", xY=label_pt, font=north_label_font, fill=arrow_color)


    def addTrail(self, trail_in, title=None, color_code=False,color="orange",
                 keep_outside=True,
                 width=3.):
        """
        :trail_in: trail input trail info
        :title: title (may be point file full path)
        :color: trail color
        :width: trail width in meters
        :color_code: color code longer point distances
        :keep_outside: Keep points even if outside region
                further back than self.max_dist_allowed,
                False: skip points outside region
                default: keep
        """
        if title is not None:
            self.title = os.path.basename(title)
            title_xy = (self.getWidth()*.5, self.getHeight()*.05)
            self.addTitle(self.title, xY=title_xy)
        self.max_dist_allowed = 150.
        trail = self.cleanTrail(trail_in, keep_outside=keep_outside)
        for track in trail.get_segments():
            points = track.get_points()
            if color_code:
                return self.addTrail_color_code(points)
            
            line_width = int(self.meterToPixel(width))
            line_points = []
            for point in points:
                latLong = (point.lat, point.long)
                xY = self.getXY(latLong=latLong)
                line_points.append(xY)
            self.line(line_points, width=line_width,
                        fill=color)
        return True
            
    def addTrail_color_code(self, points):
        """ Do map with color coded line segments
        :points:
        :title:
        """
        prev_point = None
        for i, point in enumerate(points):
            if prev_point is not None:
                line_len = abs(self.geoDist(prev_point.latLong(), point.latLong()))
                line_color = None
                if line_len > 100:
                    line_color = "red"
                    SlTrace.lg(f"point {i+1}: {point} is at a distance {line_len:.1f}m")
                elif line_len > 20:
                    line_color = "blue"
                elif line_len > 10:
                    line_color = "green"
                elif line_len > 5:
                    line_color = "yellow"
                if line_len > self.max_dist_allowed:
                    SlTrace.lg(f"Ignoring Suspicious line {i+1}:"
                               f" {prev_point} to {point} as being too long: {line_len:.1f}m")
                    line_color = "red"
                else:
                    self.addTrailLine(prev_point, point, color=line_color)
            prev_point = point
        return True

    
    def addSample(self, point, color="red",
                  show_LL=True):
        """
        Add sample to current image
        :point: SamplePoint
        :color: sample label color
        :show_LL: show Latitude, Longitude
                default: True - show LL
    
        """
        label_color = (255,0,0)
        label_size = 30
        label_font = ImageFont.truetype("arial.ttf", size=label_size)
        latlong_size = label_size/2
        if isinstance(point, dict):
            plot_key = point["plot"]                    # Older
            lat, long = point["lat"], point["long"]
        else:
            plot_key = point.get_plot_key()
            lat, long = point.latLong()
        plot_id = plot_key
        xY = self.getXY(latLong=(lat,long))
        plot_color = (0,255,0, 128)
        plot_radius = 10.
        plot_radius_pixel = self.meterToPixel(plot_radius)
        if plot_key == "TBM":
            radius_pixel = self.meterToPixel(plot_radius*.25)
            self.circle(xY=xY, radius=radius_pixel, fill="#adf0f5")
            latlong_size *= 2
            label_xy = self.addToPoint(xY=xY, leng=1.5*label_size, deg=75)
            self.text(plot_id, xY=label_xy,  font=label_font, fill=label_color)
        else:    
            self.circle(xY=xY, radius=plot_radius_pixel, fill=plot_color)
            label_xy = self.addToPoint(xY=xY, leng=1.5*label_size, deg=75)
            self.text(plot_id, xY=label_xy,  font=label_font, fill=label_color)
        
        cent_color = (255,0,0)
        cent_radius = 1
        cent_radius_pixel = self.meterToPixel(cent_radius)
        self.circle(xY=xY, radius=cent_radius_pixel, fill=cent_color)
        # get a font
        # use a truetype font
        if show_LL:
            latlong_size = int(latlong_size)
            loc_string = "%.5f\n%.5f" % (long, lat)
            font_loc = ImageFont.truetype("arial.ttf", size=latlong_size)
            latlong_xy = self.addToPoint(latLong=(lat,long),
                                         leng=latlong_size, deg=-self.get_mapRotate())
            self.text(loc_string, xY=latlong_xy, font=font_loc,
                       fill=(255,255,255,255))    


    def addSamples(self, points, title=None, color=None,
                   show_LL=True):
        """ Add trail, given ll points
        First try just add line segments connecting thepoints
        :points: sample points (SamplePoint)
        :title: title (may be point file full path)
        :color: color for sample
        :show_LL: show Latitude, longitude
        """
        if title is not None:
            self.title = os.path.basename(title)
            title_xy = (self.getWidth()*.5, self.getHeight()*.1)
            self.addTitle(self.title, xY=title_xy)
        for point in points:
            self.addSample(point, color=color, show_LL=show_LL)
        return True

            
    def addTrailLine(self, p1, p2, color=None):
        """ Do trail segment from p1, 2p
        :p1: First point GPXPoint
        :p2: Second point GPXPoint    
        """
        if color is None:
            color = "orange"
        line_width = self.meterToPixel(self.trail_width)
        self.lineSeg(latLong=(p1.lat,p1.long), latLong2=(p2.lat,p2.long), width=int(line_width),
                     fill=color)

    def cleanTrail(self, trail_in, keep_outside=True):
        """ Adjust initial points to most likely to be valid measurements
            Assemble trail stats
            1. Throw any points outside border
            :trail_in: raw trail info (SurveyTrail)
            :keep_outside: Keep points even if outside region
                or further back than self.max_dist_allowed
                False: skip points outside region
                default: keep
        """
        return trail_in  # For now - no changes
        '''
        trail = SurveyTrail()
        n_diff = 0              # Number of distances (n good pts - 1)
        n_outside = 0
        dist_sum = 0.
        max_dist = None
        min_dist = None
        points_len = len(points_in)
        for i, point in enumerate(points_in):
            if not self.is_inside(latLong=point.latLong()):
                n_outside += 1
                SlTrace.lg(f"Questioning point {i+1}: {point} as outside border", "clean_trail")
                if not keep_outside:
                    continue    # Skip point outside border
            if i == 0 and len(points_in) > 1:
                p1_ll = points_in[i].latLong()
                p2_ll = points_in[i+1].latLong()
                dist = abs(self.geoDist(p1_ll, p2_ll))
                if dist > self.max_dist_allowed:
                    n_outside += 1
                    SlTrace.lg(f"Questioning point {i+1}: {point} as too far")
                    if not keep_outside:
                        continue
            point_prev = points[-1] if len(points) > 0 else None
            check_prev = True if point_prev is not None else False
            if i >= points_len-1:
                check_next = False
            else:
                check_next = True
                point_next = points_in[i+1]
            if check_prev:
                dist_prev = abs(self.geoDist(point_prev.latLong(), point.latLong()))
                dist = dist_prev
            if check_next:
                dist_next = abs(self.geoDist(point.latLong(), point_next.latLong()))
                dist = dist_next
            if check_prev and check_next:
                dist = max(dist_prev, dist_next)
            points.append(point)
            if check_prev:
                n_diff += 1
            if min_dist is None or dist < min_dist:
                min_dist = dist
            if max_dist is None or dist > max_dist:
                max_dist = dist
            dist_sum += dist            
        SlTrace.lg("Trail Statistics")
        SlTrace.lg(f"Number of points: {len(points_in)}")
        SlTrace.lg(f"Number of displayed points: {len(points)}")
        avg_dist = 0 if n_diff == 0 else dist_sum/n_diff
        if len(points) > 0:
            SlTrace.lg(f"minimum distance: {min_dist:.1f}m maximum distance: {max_dist:.1f}m average: {avg_dist:.2f}m")
            SlTrace.lg(f"Total path distance: {dist_sum:.1f}m") 

        return trail
        '''
   
    def addScale(self,
                xY=None, pos=None, latLong=None,
                xYEnd=None, posEnd=None, latLongEnd=None,
                
                deg=None,
                leng=None,
                
                unitName="m",
                tic_dir=1,
                marks=10,
                bigMarks=10, 
                color=None):
        """
        Add scale marker
            One of ending specification
                :xY - starting x,y pixels
                :pos - starting x,y meters            
                :latLong - starting latitude,longitude
            
            OR One of starting specification
                :xYEnd - starting
                :posEnd - endin
                :latLongEnd - ending latitude, longitude
        
            OR One of the above AND   
                :leng - Length in pixels
                AND
                :deg - direction of scale line in degrees from image horizontal
                         (0 - horizontal to right)
            
            :marks - ticks every marks unit
            :bigMarks - big marks every bigMarks mark
            :tic_dir: tic direction 1: axis + 90 deg, -1: axix -90 deg
                        default: 1
            :unitName - text for unit - m - meter, f - foot
            :color - scale color
        :returns: NA
        Raises: NA
        """
        np1_spec = 0
        if xY is not None:
            np1_spec += 1
        if pos is not None:
            np1_spec += 1
        if latLong is not None:
            np1_spec += 1

        np2_spec = 0
        if xYEnd is not None:
            np2_spec += 1
        if posEnd is not None:
            np2_spec += 1
        if latLongEnd is not None:
            np2_spec += 1

        if np1_spec == 0 and np2_spec == 0:
            xY = (self.getWidth()*.1, self.getHeight()*.9)
            np1_spec = 1
            if leng is None:
                leng = self.getWidth()*.8
            if deg is None:
                deg = 0.
            
        if np1_spec == 0:
            raise SelectError("Atleast one of xY, pos, latLong must be present")
        if np1_spec > 1:
            raise SelectError("Only one of xY, pos, latLong is allowed")


        if np2_spec > 0 and leng is not None:
            raise SelectError("leng is not alowed when ending point is specified")
        if  np2_spec > 0 and deg is not None:
            raise SelectError("deg is not allowed when ending point is specified")
        
        if np2_spec == 0 and leng is None:
            leng = self.getWidth()*.8
        if np2_spec > 1:
            raise SelectError("Only one of xYEnd, posEnd, or latLongEnd may be specified")
            
        if np1_spec > 1:
            raise SelectError("Only one of xY, pos, latLong is allowed")
        unitLen = self.unitLen(unitName)
        
        if bigMarks is None:
            bigMarks = 5
        if tic_dir is None:
            tic_dir = 1
        scale_color = (255,255,255)
        if color is not None:
            scale_color = color
                
        xY = self.getXY(xY=xY, pos=pos, latLong=latLong)
        if np2_spec > 0:
            xYEnd = self.getXY(xY=xYEnd, pos=posEnd, latLong=latLongEnd)
            chg_x = xYEnd[0]-xY[0]
            chg_y = xYEnd[1]-xY[1]
            leng = sqrt(chg_x**2+chg_y**2)
            theta = -asin(chg_y/leng)
            deg = rad2deg(theta)
        else:
            if deg is None:
                deg = 0
            xyEnd = self.addToPoint(xY=xY, leng=leng, deg=deg)
            
        scale_len = leng
        scale_deg = deg
        scale_theta = radians(scale_deg)
        tic_deg = scale_deg+tic_dir*90
        scale_width = self.adjWidthBySize(4)
        self.lineSeg(xY=xY, leng=scale_len, deg=scale_deg, fill=scale_color, width=scale_width)

        tic_len = 20        # tic mark length in pixels
        tic_space = marks*unitLen      # distance, in distance units (e.g., meters), between tics
        tic_space_pixel = self.meterToPixel(tic_space)     # Assume symetric
        tic_width = self.adjWidthBySize(2)
        tic_big_len = tic_len + 5
        tic_big_width = tic_width + self.adjWidthBySize(3)
        mark_n = 0          # nth marker
        scale_font = ImageFont.truetype("arial.ttf", size=28)
        nthmark = 0     # Heavy tics
        """
        Move in a straight line in direction of scale line
        between xY and xY end
        """
        scale_xY = xY
        scale_pos = 0           # position relative to length
        scale_end = self.pixelToMeter(scale_len)
        while scale_pos <= scale_end:
            mark_n += 1
            if mark_n % bigMarks == 1:
                nthmark += 1
                self.lineSeg(xY=scale_xY, deg=tic_deg, leng=tic_big_len,
                                      fill=scale_color, width=tic_big_width)
                if nthmark % 2 == 1:
                    label = "%d%s" % (round(scale_pos/unitLen), unitName)
                else:
                    label = "%d" % round(scale_pos/unitLen)
                tic_top = self.addToPoint(xY=scale_xY, leng=2.5*tic_big_len, deg=tic_deg)
                self.text(label, xY=tic_top,
                           font=scale_font, fill=scale_color)

            else:
                self.lineSeg(xY=scale_xY, deg=tic_deg, leng=tic_len,
                                      fill=scale_color, width=tic_width)
            """
            Update position to next tic mark
            """
            if trace_scale:
                print("mark_n: %d scale_pos: %.2f scale_xY: %s" %
                      (mark_n, scale_pos, scale_xY))
            
            scale_pos = mark_n * tic_space
                
            scale_xY = self.addToPoint(xY=scale_xY, leng=tic_space_pixel, deg=scale_deg)
        pass


    def addTitle(self, title, xY=None, size=None, color=None, **kwargs):
        if xY is None:
            title_xy = (self.getWidth()*.1, self.getHeight()*.05)
        if size is None:
            size = 32
        if color is None:
            color = (255, 255, 255, 255)
        title_font = ImageFont.truetype("arial.ttf", size=size)
        title_color = color        
        title_xy = xY
        self.text(title, xY=title_xy, font=title_font, fill=title_color, **kwargs)

    
    def addToPoint(self, leng=None, lengPix=None, xY=None, pos=None, latLong=None, theta=None, deg=None, unit=None):
        """
        Add to point (in unrotated image), returning adjusted point in pixels
        Add requested rotation (curDeg if None) to map rotation, if
        mapRotation is not None
        :leng: length in unit
        :lengPix: length in pixels
        :unit: unit default: self.unit, meter
        """
        if leng is None and lengPix is None:
            raise SelectError("leng/LengPix is required")
        if leng is not None and lengPix is not None:
            raise SelectError("Only one of leng/LengPix is allowed")
        
        if lengPix is not None:
            leng = self.pixelToMeter(lengPix)
            
        if leng is not None and not isinstance(leng, float) and not isinstance(leng, int):
            raise SelectError(f"leng({leng} {type(leng)}) must be a float or int")
        
        if unit is None:
            unit = self.unit
        leng /= self.unitLen(unit)
            
        if theta is not None and deg is not None:
            raise SelectError("Only specify theta or deg")
        
        if theta is not None:
            deg = theta / pi * 180
        if deg is None:
            deg = self.curDeg
            
        npxl = 0
        if pos is not None:
            npxl += 1
        if xY is not None:
            npxl += 1
        if latLong is not None:
            npxl += 1
        if npxl > 1:
            raise SelectError("Only specify one of xY, pos or latLong")
        if npxl != 1:
            raise SelectError("Must specify one of xY, pos or latLong")
        if leng is None:
            raise SelectError("leng is required")
        
        xY = self.getXY(xY=xY, pos=pos, latLong=latLong)
            
        if deg is None:
            deg = 0
        deg += self.get_mapRotate()
            
        theta = deg/180.*pi
        if theta != 0:
            delta_x = cos(theta)*leng
            delta_y = -sin(theta)*leng
        else:
            delta_x = leng
            delta_y = 0.
        return xY[0]+self.meterToMx(delta_x), xY[1]+self.meterToMy(delta_y)


    def adjWidthBySize(self, lineWidth):
        """
        Adjust line widths to account for large images
        """
        mindim = min(self.getWidth(), self.getHeight())
        adj_lineWidth = lineWidth
        if mindim == 0:
            mindim = 1
        line_fract = lineWidth/mindim
        min_line_fract = .001
        if line_fract < min_line_fract * adj_lineWidth:
            adj_lineWidth = ceil(min_line_fract * mindim * lineWidth)
        if lineWidth < 1:
            adj_lineWidth = 1
        if adj_lineWidth > lineWidth:
            return lineWidth            # Leave alone
        
        return adj_lineWidth




    def crop(self, box=None):
        """
        Crop image, adjusting internal values appropriately
        Adjust bounds
        Adjusts GeoDraw member to reflect new dimensions
        """
    
        if box is None:
            raise SelectError("crop: box is required")
        print("before crop")
        i_width, i_height = self.image.size
        print("x width=%.2f y height=%.2f" %
              (i_width, i_height))
        """
        ulLatLong = self.getLatLong(xY=(x_min, y_min))
        lrLatLong = self.getLatLong(xY=(x_max, y_max))
        ulLat = ulLatLong[0] 
        ulLong = ulLatLong[1]
        lrLat = lrLatLong[0]
        lrLong = lrLatLong[1]
        print("cropping bounds: ulLatLong=%s, lrLatLong=%s" % (ulLatLong, lrLatLong))

        self.line([(x_min, y_min), (x_max, y_min),
                           (x_max,y_max), (x_min, y_max),
                           (x_min, y_min)])
        """
        ### if self.mapPoints is not None:
        ###    self.markPoints(self.mapPoints)
        crop_image = self.image.crop(box=box)
        crop_image.load()
        self.dbShow("after crop", 
                    "image width=%d height=%d" % (crop_image.width, crop_image.height),
                    image=crop_image)
        self.setImage(crop_image)               # break connection with image
    
    def addToPointLL(self, leng=None, xY=None, pos=None, latLong=None, theta=None, deg=None, unit=None):
        """
        Add to point, returning adjusted point in latLong
        """
        xY = self.addToPoint(leng=leng, xY=xY, pos=pos, latLong=latLong,
                              theta=theta, deg=deg, unit=unit)

        return self.getLatLong(xY=xY)
    
    def geoDist(self, latLong=None, latLong2=None, unit='m'):
        """ Access to lat,long to distance
        :latLong: starting latitude,longitude pair
        :latLong2: ending latitude, longitued pair
        :unit: distance units name string feet, meter, yard, smoot
                default: m(eter)
        """
        unitLen = self.unitLen(unit)
        gdist = geoDistance(latLong=latLong, latLong2=latLong2)

        return gdist/unitLen



    def getHeight(self):
        """
        Get image height in pixels
        """
        return self.image.height


    def getWidth(self):
        """
        Get image width in pixels
        """
        return self.image.width

    def getXFract(self, x_image):
        """ fraction of width
        :x_image: x pixels
        """
        return x_image/self.getWidth()

    def getYFract(self, y_image):
        """ fraction of image height
        y_image: x pixels
        """
        return y_image/self.getHeight()

    def getLatFract(self, lat):
        """ fraction of latitude width
        :latitude: latitude
        """
        lat_height = self.ulLat - self.lrLat
        lat_offset = self.ulLat - lat
        return lat_offset/lat_height

    def getLongFract(self, long):
        """ fraction of latitude width
        :latitude: latitude
        """
        long_height = self.ulLong - self.lrLong
        long_offset = self.ulLong - long
        return long_offset/long_height

    def getLatLong(self, latLong=None, pos=None, xY=None, unit=None):
        """
        Get/Convert location pixel, longitude, physical location/specification
        to lat/long
        """
        xY = self.getXY(latLong=latLong, pos=pos, xY=xY, unit=unit)
        latLong = self.pixelToLatLong(xY)
        return latLong

    def get_mapRotate(self):
        """ Get current map rotation 0<= deg < 360
        """
        rotate = 0 if self.mapRotate is None else self.mapRotate % 360
            
        return rotate


    def getPos(self, latLong=None, pos=None, xY=None, unit='m', ref_latLong=None):
        """
        Get/Convert location pixel, longitude, physical location/specification
        to position in meters,yards, or feet
        :latLong: latitude,longitude pair
        :pos: x,y position pair in meters
        :xY: x,y position pair in pixels
        :unit: output distance units meter, yard, feet
            default: m(eter)
        :ref_latLong: if present, give position relative to reference
                    latitude, longitude
        :returns: x,y position in unit
        """
        unitLen = self.unitLen(unit)
        xY = self.getXY(latLong=latLong, pos=pos, xY=xY)
        x_meter = self.mxToMeter(xY[0])
        y_meter = self.myToMeter(xY[1])
        if ref_latLong is not None:
            ref_xY = self.getXY(latLong=ref_latLong)
            ref_x_meter = self.mxToMeter(ref_xY[0])
            ref_y_meter = self.myToMeter(ref_xY[1])
            x_meter -= ref_x_meter
            y_meter -= ref_y_meter
        x_out = x_meter/unitLen
        y_out = y_meter/unitLen
        return x_out, y_out 
    

    def getXY(self, latLong=None, pos=None, xY=None, xYFract=None, unit=None):
        """
        Get/Convert location pixel, map fraction, longitude, physical location/specification
        to pixel location
        """
        nloc_spec = 0
        if latLong is not None:
            nloc_spec += 1
        if pos is not None:
            nloc_spec += 1
            latLong = self.posToLatLong(pos)
        if xY is not None:
            nloc_spec += 1
        if xYFract is not None:
            nloc_spec += 1
        
        if nloc_spec > 1:
            raise SelectError("May specify, at most, one of latLong, pos, or xY or xYFract")
        
        if latLong is not None:
            xY =  self.latLongToPixel(latLong)
        elif pos is not None:
            xY = self.posToPixel(pos, unit=unit)
        elif xYFract is not None:
            xY = (xYFract[0]*self.getWidth(), xYFract[1]*self.getHeight())
        if xY is None:
            xY = self.curXY
        return xY


    def has_compass_rose(self):
        """ Check if map has been augmented by Compass Rose
        """
        return self.compass_rose.present


    def is_inside(self, latLong=None, pos=None, xY=None):
        """ Test if point is within map borders
        :latLong, pos, xY: location as in getXY,
        :returns: True if inside
        """
        xY = self.getXY(latLong=latLong, pos=pos, xY=xY)
        if (xY[0] < 0 or xY[1] < 0
                 or xY[0] > self.getWidth() or xY[1] > self.getHeight()):
            return False
        
        return True 


    def latLongToPixel(self, latLong):
        """
        Convert latitude, longitude to pixel location on image (unrotated)
        1. NO Need to Rotate from mapRotate to North Facing,
             since already image already alligned with North
        2. Scale from longLat to x,y pixel
        3. Rotate back to mapRotate
        :returns: x,y pixels
        """
        if latLong is None:
            raise SelectError("latlongToPixel: latLong required");
        
        self.in_latLongToPixel += 1
        lat = latLong[0]
        long = latLong[1]
        lat_offset = self.ulLat - lat         # from upper left corner - latitude decreases down, offset increases down
        long_offset = long - self.ulLong      # increase left to right
        '''
        long_offset, lat_offset = self.rotate_xy(       # Returns: x-offset(longitude),
                                                        #          y-offset(latitude)
                    x=long_offset, y=lat_offset,
                    width=self.long_width, height=self.lat_height,
                    deg=-self.get_mapRotate())
        '''
        mx = long_offset/self.long_width*self.getWidth()
        my = lat_offset/self.lat_height*self.getHeight()
        '''
        mx, my = self.rotate_xy(x=mx, y=my,
                            width=self.getWidth(), height=self.getHeight(),
                            deg=self.get_mapRotate())
        '''
        if self.in_pixelToLatLong == 0:
            latLong2 = self.pixelToLatLong((mx,my))
            latchg = latLong2[0]-latLong[0]
            longchg = latLong2[1]-latLong[1]
            max_diff = 5e-3
            if abs(latchg) > max_diff or abs(longchg) > max_diff:
                if SlTrace.trace("reversable_report"):
                    SlTrace.lg(f"latLongToPixel rot({self.get_mapRotate()}) not reversable: latchg:{latchg:.7} longchg:{longchg:.7}")
                    SlTrace.lg(f"    latLong:{latLong} latLong2:{latLong2}")


        self.in_latLongToPixel -= 1            
        return mx, my


    def pixelToLatLong(self, xY):
        """
        Convert  (unrotated image) pixel x,y  to latitude, longitude
        1. Rotate from mapRotate to North Facing
        2. Scale from x,y pixel to latLong
        3. Rotate back to mapRotate
        Returning lat,Long pair
        """
        self.in_pixelToLatLong += 1
        xY1 = xY
        if xY is None:
            raise SelectError("pixelToLatLong: pixel required")
        
        mx, my = self.rotate_xy(x=xY[0], y=xY[1],
                            width=self.getWidth(), height=self.getHeight(),
                            deg=-self.get_imageRotate())
        long_offset = mx * self.long_width / self.getWidth()
        lat_offset = my * self.lat_height / self.getHeight()
        '''
        long_offset, lat_offset = self.rotate_xy(       # Returns: x (longitude offset) right
                                                        #          y (latitude offset) downwards
                                    x=long_offset, y=lat_offset,
                                    width=self.long_width, height=self.lat_height,
                                    deg=self.get_mapRotate())
        '''
        lat = self.ulLat - lat_offset           # Offset down from upper left corner
        long = self.ulLong + long_offset
        if self.in_latLongToPixel == 0:
            xY2 = self.latLongToPixel((lat,long))
            xchg = xY2[0]-xY1[0]
            ychg = xY2[1]-xY1[1]
            if abs(xchg) > 1e-7 or abs(ychg) > 1e-7:
                if SlTrace.trace("reversable_report"):
                    SlTrace.lg(f"pixelToLat rot({self.get_mapRotate()}) not reversable: xchg:{xchg:.7} ychg:{ychg:.7}")
                    SlTrace.lg(f"    xY1:{xY1} xY2:{xY2}")

        self.in_pixelToLatLong -= 1
        return lat, long
        
    def rotate_xy(self, x=None, y=None, width=None,
                   height=None, deg=None):
        """ Rotate point x,y deg degrees(counter clockwise
         about the center (Width/2, Hight/2)
        :x: x value horizontal increasing to right
        :y: y value, vertical increasing to down
        :width: x width default: image width
        :height:  y height    default: image height
        :deg: rotation, in degrees,
                default: self.get_mapRotate()
        :returns: x,y updated by rotation
        """
        if deg is None:
            deg = self.get_mapRotate()
            if deg is None:
                deg = 0
        angle = -radians(deg)           # Adjust for downward going y
        if width is None:
            width=self.getWidth()
        if height is None:
            height=self.getHeight()

        ox, oy = width/2, height/2
        px, py = x, y
        qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
        qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
        return qx, qy

    """ Culled from an unsuccessful attempt at rotation in rotate_xy
            '''
        ### Don't know where I went wrong with this
        ### but I gave up and used a slick version from Stackoverflow
        ### with a modification for downward increasing y
        if deg is None:
            deg = self.get_mapRotate()
        effective_zero = 1e-7
        if deg is not None and deg > effective_zero:
            theta = radians(deg)         # Rotate to North Facing
            # Translate to center of image
            x_c = x - width/2.
            y_c = y - height/2.
            x2_c = x_c * cos(theta) - y_c * sin(theta)
            y2_c = y_c * cos(theta) + x_c * sin(theta)
            x2 = x2_c + width /2.
            y2 = y2_c + height/2.
           
            x = x2
            y = y2
            
        return x,y
    """

            
    def posToPixel(self, pos):
        """
        Convert position in distance to pixels
        """
        x_meter = float(pos[0])
        y_meter = float(pos[1])
        mx = self.meterToMx(x_meter - self.ulX)
        my = self.meterToMy(y_meter - self.ulY)
        return mx, my

    def unitLen(self, unit):
        """ Unit length in meters
        :unit: unit name (only looks at first letter)
                feet, meeter, yard, smoot
                default: self.unit, meter
        """
        if unit is None:
            unit = self.unit
        return geoUnitLen(unit)

        
            
    def posToLatLong(self, pos):
        """
        Convert position in distance to latitude, longitude
        """
        xY = self.posToPixel(pos)
        latLong = self.pixelToLatLong(xY)
        return latLong


    
    def meterToPixel(self, meter):
        """
        meter to pixel assumes symetric conversion
        we take average here
        """
        
        return (self.meterToMx(meter) + self.meterToMy(meter))/2.

    
    def meterToMx(self, meter):
        """
        Convert horizontal position, in meters, to location in xpixels
        """
        return (meter-self.ulX)/(self.lrX-self.ulX)*self.getWidth()
    
    def meterToMy(self, meter):
        return (meter-self.ulY)/(self.lrY-self.ulY)*self.getHeight()

    
    def mxToMeter(self, mx):
        """
        Convert horizontal location in pixels to horizontal location in meters
        """
        return mx/self.getWidth()*(self.lrX-self.ulX) + self.ulX
    
    def myToMeter(self, my):
        """
        Convert vertical location in pixels(y down) to location in meters
        """
        return my/self.getHeight()*(self.lrY-self.ulY) + self.ulY


    
    def pixelToMeter(self, pixel):
        return pixel/self.meterToPixel(1)
    
            
    def setCurLoc(self,
         pos=None,
         latLong=None,
         xY=None,
         unit='meter'):
        """
        Set current drawing location
        
        :curPos - drawing pen current position (x,y) in unit(meter)
        :curLatLong - drawing pen current location (latitude, longitude) in degrees
        :curXY - drawing pen current location in floating pixels (x-left to right,y-top to bottom)
        """

        if pos is not None:
            assert(latLong is None)
            assert(xY is None)
            xY = self.posToPixel(pos);
        elif latLong is not None:
            assert(xY is None)
            xY = self.latLonToPixel(latLong)
        elif xY is None:
            xY = (0., 0.)
        self.curXY = xY

    def get_imageRotate(self):
        """ get current map rotate from original orientation
        """
        mapRotate = self.get_mapRotate()
        mapRotateOriginal = 0 if self.mapRotateOriginal is None else self.mapRotateOriginal
        imageRotate = mapRotate - mapRotateOriginal
        return imageRotate
        

    def expandRegion(self, ul_xy=None, lr_xy=None, 
                     aspect=True):
        """
        Expand region to fill map
        :ul_xy: upper left corner xy
        :lr_xy: lower right corner xy
        :aspect: True keep x,y aspect unchanged TBD
                default: True
        """
        ul_x, ul_y = ul_xy
        lr_x, lr_y = lr_xy
        ulLat, ulLong = self.pixelToLatLong(ul_xy)
        lrLat, lrLong = self.pixelToLatLong(lr_xy)
        self.prev_image = self.image
        new_im = self.image.crop(box=(ul_x, ul_y, lr_x, lr_y))
        SlTrace.lg(f"expandRegion: ul_x={ul_x} ul_y={ul_y} lr_x={lr_x} lr_y={lr_y}")
        SlTrace.lg(f"new_im: {new_im}")
        self.setImage(new_im)
        
        self.setLatLong(ulLat=ulLat, ulLong=ulLong,
                        lrLat=lrLat, lrLong=lrLong)
        return new_im           # Just for immediate use, already stored

    def popMapState(self):
        """ pop (restore) previous map state
        """
        if len(self.mapStates) <= 0:
            return
        
        map_state = self.mapStates.pop()
        self.setMapState(map_state)
            
    def pushMapState(self):
        """ push current map state, recovered via popMap
        """
        map_state = self.collectMapState()
        self.mapStates.append(map_state)

    def collectMapState(self):
        """ save map state and return it
        :returns: map_state able to be reset via call to restoreMap
        """
        map_state = GeoDrawMapState(self)
        return map_state
        
    def setMapState(self, state):
        state.setState()
        
    def expandRegion_xy(self, min_x=None, min_y=None, max_x=None, max_y=None,
                     aspect=True):
        """
        Expand region to fill map
        :min_x,min_y,...: image box
        :aspect: True keep x,y aspect unchanged TBD
                default: True
        """

        self.prev_image = self.image
        new_im = self.image.crop(box=(min_x, min_y, max_x, max_y))
        SlTrace.lg(f"expandRegion: min_x={min_x} min_y={min_y} max_x={max_x} max_y={max_y}")
        SlTrace.lg(f"new_im: {new_im}")
        self.setImage(new_im)
        ulLat, ulLong = self.pixelToLatLong((min_x,min_y))
        lrLat, lrLong = self.pixelToLatLong((max_x,max_y))
        self.setLatLong(ulLat=ulLat, ulLong=ulLong,
                        lrLat=lrLat, lrLong=lrLong)
        return new_im           # Just for immediate use, already stored

    def rotateMap(self, deg, incr=True, expand=None):
        """
        Rotate map, updating image, and mapRotate
        Using original image to avoid pixel loss
        :deg: number of degrees to rotate
        :incr: incremental rotation False = absolute
            default: True - rotate from current
        :expand: expand image (defined) by PIL image
        """
        map_current = mapRotate = self.get_mapRotate()
        if incr:
            to_deg = mapRotate + deg
        else:
            to_deg = deg
        self.mapRotate = to_deg
        to_deg = self.get_mapRotate()   # Normalize
        self.mapRotate = to_deg         # Store normaized
        from_current_deg = to_deg - map_current
        im = self.image.rotate(from_current_deg, expand=expand)
        self.setImage(im)
        return im           # Just for immediate use, already stored

    def mark_image(self):
        """ Mark image for diagnostics
            with a temporary overlay (not in image)
        """
        if SlTrace.trace("mark_image"):
            if hasattr(self, "mki_tags"):
                if self.mki_tags:
                    for tag in self.mki_tags:
                        pass
            mi_color = "red"
            mi_width=4
            w = self.getWidth()
            h = self.getHeight()
            pt1 = (w/2, 0)
            pt2 = (w/2, h)
            self.line([pt1, pt2], fill=mi_color, width=mi_width)
            pt3 = (0, h/2)
            pt4 = (w, h/2)
            self.line([pt3, pt4], fill=mi_color, width=4)
            pts = [(0,0), (w,0), (w,h/2), (w,h), (0,h), (0,0)]
            self.line(pts, fill=mi_color, width=mi_width+2)
        
    def rotatePoints(self, points, rotate=None):
        """
        Rotate points
        Return copy of points array, with lat, long, adjusted by map rotation
        """
        if rotate is None:
            rotate = self.get_mapRotate()
        

    def setCurAngle(self,
        deg=0,
        theta=0):
        """
        Set current pen drawing direction
        
        :curDeg - drawing pen current direction in degrees
        :curTheta - drawing pen current direction in radians
        """
                
        if deg is not None and theta is not None:
            raise SelectError("Only one of deg or theta must be specified")
        if theta is not None:
            deg = theta / pi * 180
        if deg is None:
            deg = 0
            
        self.curDeg = deg


    def drawCircle(self, xY=None, radius=None, color=None, **kwargs):
        """
        Draw circle at current location with radius, in pixels
        """
        if radius is None:
            radius = 2
        if color is not None:
            kwargs['fill'] = color
        for key in ['activeoutline', 'activefill', 'activewidth']:
            if key in kwargs:
                SlTrace.lg(f"geoDraw.drawCircle param {key} not supported - ignored")
                del kwargs[key]
        
        x, y = xY
        x0 = x - radius
        y0 = y - radius
        x1 = x0 + radius 
        y1 = y0 + radius 
        elp_cent = (x0, y0, x1, y1)
        self.ellipse(elp_cent, **kwargs)


    def circle(self, xY=None, pos=None, latLong=None, radius=None, **kwargs):
        """
        Draw circle at current location with radius, in pixels
        """
        xY = self.getXY(xY=xY, pos=pos, latLong=latLong)
        if radius is None:
            radius = 2
        mx = xY[0]
        my = xY[1]
        elp_cent = (mx-radius, my-radius, mx+radius, my+radius)
        self.ellipse(elp_cent, **kwargs)
        

    def points_to_image(self, *pts_list, rotation=None):
        """ Rotate points to, possibly, rotated image
        :*pts: comma-separated point or list of points in unrotated image
        :rotation: image rotation
                default: current image rotation (deg) from map original
        :returns: list of points in rotated image
        """
        pts = []
        for pt_list in pts_list:
            if isinstance(pt_list, list):
                pts.extend(pt_list)     # add list
            else:
                pts.append(pt_list)     # add pt
        if rotation is None:
            rotation = self.get_imageRotate()
        rot_pts = []
        for pt in pts:
            pt_x, pt_y = self.rotate_xy(x=pt[0], y=pt[1],
                                        deg=rotation)
            rot_pts.append((pt_x,pt_y))
        return rot_pts
                
    def ellipse(self, elp_cent, **kwargs):
        ###elp_cent = self.points_to_image(elp_cent)[0]
        self.draw.ellipse(elp_cent, **kwargs)

    def line(self, points, **kwargs):
        """
        Draw line segments one more points (pixelx, pixely) on to rotated image
        if only one point is given, the current pen location is used as the first point
        Current pen position is unchanged.
        Non used args are passed to Image.draw.line 
        """
        if len(points) == 1:
            pts = [self.curXY, points[0]]
        else:
            pts = points
        pts = self.points_to_image(pts)
        self.draw.line(pts, **kwargs)

        
    def drawLine(self, *points, color=None, width=None, **kwargs):
        """ drawText (ImageOverDraw image part
        """
        if color is not None:
            kwargs['fill'] = color
        if width is not None:
            kwargs['width'] = int(width)
        if 'arrow' in kwargs:
            del kwargs['arrow']
        if 'arrowshape' in kwargs:
            del kwargs['arrowshape']
        pts = []
        for point in points:
            pt = (int(point[0]), int(point[1]))
            pts.append(pt)
        self.draw.line(pts, **kwargs)


        
    def drawPolygon(self, *points, color=None, width=None, **kwargs):
        """ drawText (ImageOverDraw image part
        """
        if color is not None:
            kwargs['fill'] = color
        if width is not None:
            kwargs['width'] = int(width)
        pts = []
        for point in points:
            pt = (int(point[0]), int(point[1]))
            pts.append(pt)
        self.draw.polygon(pts, **kwargs)

        
    def drawText(self, xY, text, color=None, font=None, **kwargs):
        """ drawText (ImageOverDraw image part)
        :text: text string
        :xY: x,y pixel location
        :**kwargs: unused args passed on
        """
        if color is not None:
            kwargs['fill'] = color
        if font is not None:
            SlTrace.lg(f"GeoDraw:drawText need font({font}) work in {kwargs}")
        self.draw.text(xY, text, font=font, **kwargs)

    def text(self, text, xY=None,pos=None,latLong=None, **kwargs):
        """
        Draw text, at position, defaulting to current pen position
        """
        xY = self.getXY(xY=xY, pos=pos, latLong=latLong)
        xY = self.points_to_image(xY)[0]
        self.draw.text(xY, text, **kwargs)
        
 
    def lineSeg(self, xY=None, pos=None, latLong=None,
                xY2=None, pos2=None, latLong2=None,
                 leng=10, theta=None, deg=None, **kwargs):
        """
        Draw line segment starting at given point
        position(xY or pos or latLong) and going to 
            2nd point:
                (xY2 or pos2 or latLong2)
                    or
                point 2 plus length leng at angle (theta radians or deg degrees)
            
        Extra named args are passed to Image.draw.line
        """
        xY = self.getXY(xY=xY, pos=pos, latLong=latLong)
        if xY2 is not None or pos2 is not None or latLong2 is not None:
            new_xY = self.getXY(xY=xY2, pos=pos2, latLong=latLong2)
        else:
            new_xY = self.addToPoint(leng=leng, xY=xY, theta=theta, deg=deg)
        pts = self.points_to_image(xY, new_xY)
        self.line(pts, **kwargs)



    def dbShow(self, *texts, image=None, **kwargs):
        """
        debug display, show image with annotations
        No change to image
        """
        if image is None:
            image = self.image
        im = image.copy()
        draw = ImageDraw.Draw(im)      # Setup ImageDraw access
        
        font_size = 58
        line_sp = font_size
        xY = (line_sp, line_sp)
        font = ImageFont.truetype("arial.ttf", size=font_size)
        tcolor = (255,0,255)

        for text in texts:
            print("show: " + text)
            draw.text(xY, text, font=font, color=tcolor, **kwargs)
            xY = (xY[0], xY[1] + line_sp)
        im.show()
        
        
        
if __name__ == "__main__":
    from select_trace import SlTrace
    
    def lines_test():
        # A small box
        im = Image.new("RGB", (400, 400))    
        fieldlen = 100            # Box side length in meters
        """
        p1        p2
        
        
        
        p4        p3
        """
        box_lrLatLong = (42., -71.000)
        p1 = box_lrLatLong
        p2 = geoMove(latLong=p1, latDist=0,       longDist=fieldlen)
        p3 = geoMove(latLong=p1, latDist=-fieldlen, longDist=fieldlen)
        p4 = geoMove(latLong=p1, latDist=-fieldlen, longDist=0)
        print("Testing placement against geoDistance")
        print("p2-p1=%.3f p3-p2=%.3f p4-p3=%.3f p4-p1=%.3f" %
              (geoDistance(latLong=p2, latLong2=p1),
                geoDistance(latLong=p3, latLong2=p2),
                geoDistance(latLong=p4, latLong2=p3),
                geoDistance(latLong=p1, latLong2=p4)))
        gd = GeoDraw(im, ulLat=p1[0], ulLong=p1[1], lrLat=p3[0], lrLong=p3[1])
        print("image width=%d height=%d" % (gd.getWidth(), gd.getHeight()))
        borderP = 0
        boxlen = fieldlen/4.
        p5_offset = boxlen + 5
        p5 = geoMove(latLong=p1, latDist=p5_offset,      longDist=p5_offset)
        p6 = geoMove(latLong=p5, latDist=boxlen,       longDist=boxlen)
        p7 = geoMove(latLong=p5, latDist=-boxlen, longDist=boxlen)
        p8 = geoMove(latLong=p5, latDist=-boxlen, longDist=0)
        print("boxlen=%.3f meters, ul:%s lr:%s" % (boxlen, gd.getXY(latLong=p5), gd.getXY(latLong=p7)))
        
        points = [p5, p6, p7, p8, p5]
        print("points: %s" % repr(points))
        
        blue = (0,0,255)
        for n, point in enumerate(points, 1):
            radius = gd.meterToMx(boxlen/10.)
            px, py = gd.getXY(latLong=point)
            dx, dy = gd.getPos(latLong=point)
            gd.circle(latLong=point, radius=radius, fill=blue)
            print("%d: circle at:x,y(%s), longLat(%s), dx,dy(%s) radius=%f" %
                   (n, (px,py), point, (dx,dy), radius))
            
        im.show()
        
        rotate = 0
        print("\n\nboundLatLong for rotate=%.0f" % rotate)
        bd = GeoDraw.boundLatLong(points, mapRotate=rotate, borderP=borderP)
        print("rotate %.0f: bound: %s" % (rotate, bd))
        rotate = 1
        print("\n\nboundLatLong for rotate=%.0f" % rotate)
        bd = GeoDraw.boundLatLong(points, mapRotate=rotate, borderP=borderP)
        print("rotate %.0f: bound: %s" % (rotate, bd))
        rotate = 45
        print("\n\nboundLatLong for rotate=%.0f" % rotate)
        bd = GeoDraw.boundLatLong(points, mapRotate=rotate, borderP=borderP)
        print("rotate %.0f: bound: %s" % (rotate, bd))
        rotate = 90
        print("\n\nboundLatLong for rotate=%.0f" % rotate)
        bd = GeoDraw.boundLatLong(points, mapRotate=rotate, borderP=borderP)
        print("rotate %.0f: bound: %s" % (rotate, bd))
        rotate = 180
        print("\n\nboundLatLong for rotate=%.0f" % rotate)
        bd = GeoDraw.boundLatLong(points, mapRotate=rotate, borderP=borderP)
        print("rotate %.0f: bound: %s" % (rotate, bd))
        
        width = gd.getWidth()
        height = gd.getHeight() 
        gd.setCurLoc(xY=(width/3., height/2))
        gd.lineSeg(leng=width/2, fill=(255,0,0))
        gd.lineSeg(leng=width/2, deg= -22.5, fill=(0,255,0))
        gd.lineSeg(leng=width/2, deg= -45, width=5, fill=(0,0,255))
        gd.lineSeg(pos=(0, 0), leng=width/2, deg= -77.5, width=10, fill=(255,255,0))
        gd.setCurLoc(xY=(width*.75, height*.25))
        gd.line([(width*.8, height*.40),
                 (width*.9, height*.50),
                 (width*.95, height*.60)
                ],
                fill=(0,255,255))
        gd.image.show()
    
    def close(p1,p2, dist=1.E-15):
        """ Check if point close
        :p1,p2: points (x,y)
        :dist: distance for close

        """
        dp2 = (p1[0]-p2[0])**2 + (p1[1]-p2[1])**2
        if dp2 < dist**2:
            return True
        
        return False
    
    def rotate_xy_test():
        npass = 0
        nfail = 0
        ntest = 0
        mapRotate = 0.
        w = 886.
        h = 773.
        im = Image.new("RGB", (int(w), int(h)))    
        gd = GeoDraw(im, mapRotate=mapRotate,
                ulLat=None, ulLong=None,    # Bounding box
                lrLat=None, lrLong=None,
                      ulX=0, ulY=0, lrX=w, lrY=h)
        f_fmt = "10.6f"
        ndiv = 100
        x_min = 100
        x_max = 200
        x_inc = (x_max-x_min)/ndiv
        y_min = 500
        y_max = 600
        y_inc = (y_max-y_min)/ndiv
        ndeg = 3
        for x in range(x_min, x_max):
            x1 = x
            x += x_inc
            for y in range(y_min, y_max):
                y1 = y
                y += y_inc
                for k in range(0, ndeg+1):
                    deg = k*45.
                    x2, y2 = gd.rotate_xy(x=x1, y=y1,
                                           width=gd.getWidth(),
                                           height=gd.getHeight(), deg=deg)
                    SlTrace.lg(f"{deg:5.1f}"
                               f" x1: {x1:{f_fmt}} y1: {y1:{f_fmt}}"
                               f"  x2: {x2:{f_fmt}} y2: {y2:{f_fmt}}")
                    if (x1,y1) == (w/2, 0):
                        if deg == 45.:
                            ntest += 1
                            theta = radians(deg)
                            x_shrink = h/2/sqrt(2)
                            y_shrink = h/2/sqrt(2)
                            x2_expect = w/2 - x_shrink
                            y2_expect = h/2 - y_shrink
                            if not close((x2,y2), (x2_expect, y2_expect)):
                                nfail += 1
                                SlTrace.lg(f" FAIL: (x2: {x2:{f_fmt}}, y2: {y2:{f_fmt}})"
                                           f" != (x2_expect: {x2_expect:{f_fmt}},"
                                           f" y2_expect: {y2_expect:{f_fmt}})")
                            else:
                                npass += 1
                                SlTrace.lg(f" PASS: (x2: {x2}, y2: {y2})"
                                           f" == (x2_expect: {x2_expect}, y2_expect: {y2_expect})")
                        if deg == 90.:
                            ntest += 1
                            if not close((x2,y2), ((w-h)/2, h/2)):
                                nfail += 1
                                SlTrace.lg(f" FAIL: (x2: {x2}, y2: {y2})"
                                           f" != ((w-h)/2: {(w-h)/2}, h/2: {h/2})")
                            else:
                                npass += 1
                                SlTrace.lg(f" PASS: (x2: {x2}, y2: {y2})"
                                           f" == ((w-h)/2: {(w-h)/2}, h/2: {h/2})")
        SlTrace.lg(f"{ntest:4d} tests  {npass:4d} pass  {nfail:4d} fail")
    
    def rotate_lat_long_test():
        npass = 0
        nfail = 0
        ntest = 0
        mapRotate = 0.
        fieldlen = 100            # Box side length in meters
        """
        p1        p2
        
        
        
        p4        p3
        """
        box_lrLatLong = (42., -71.000)
        p1 = box_lrLatLong
        p2 = geoMove(latLong=p1, latDist=0,       longDist=fieldlen)
        p3 = geoMove(latLong=p1, latDist=-fieldlen, longDist=fieldlen)
        p4 = geoMove(latLong=p1, latDist=-fieldlen, longDist=0)
        w = fieldlen
        h = fieldlen
        ll_fmt = ".7f"
        f_fmt = "6.3f"
        px_fmt = "4.0f"

        ck_reverse = False                  # True to ck reverse
        ck_reverse = True 
        
        im = Image.new("RGB", (int(w), int(h)))    
        gd = GeoDraw(im, mapRotate=mapRotate,
                      ulLat=p1[0], ulLong=p1[1],
                      lrLat=p3[0], lrLong=p3[1])
        SlTrace.lg(f"mapRotate: {gd.get_mapRotate():.1f} degrees")
        for n, pt in enumerate([p1,p2,p3,p4], 1):
            lat, long = pt
            x, y = gd.latLongToPixel((lat, long))
            stat_line = str(f"p{n}: lat: {lat:{ll_fmt}} long: {long:{ll_fmt}}"
                       f"    x: {x:{px_fmt}} y: {y:{px_fmt}} ")
            if ck_reverse:
                lat2, long2 = gd.pixelToLatLong((x,y))
                
                stat_line += f"  lat2: {lat2:{ll_fmt}} long2: {long2:{ll_fmt}}"
                ntest += 1
                if close((lat,long), (lat2,long2)):
                    stat_line += " Pass"
                    npass += 1
                else:
                    stat_line += " Fail"
                    nfail += 1

            SlTrace.lg(stat_line)
        lat_height = gd.lrLat - gd.ulLat
        long_width = gd.lrLong - gd.ulLong
        lat_base = p1[0]
        long_base = p1[1]
        lat_mid = (lat_base-lat_height/2)
        long_mid = long_base + long_width/2
        for i in range(0, 6+1):
            for j in range(0, 4+1):         # Moving down, decreasing latitude
                lat1, long1 = geoMove(p1, latDist=-j*fieldlen/4, longDist=i*fieldlen/6)
                for k in range(0, 8+1):
                    ###for k in range(1):
                    deg = k*45.
                    x2, y2 = gd.latLongToPixel((lat1, long1))
                    stat_line = str(f"{deg:5.1f}"
                               f" lat1: {lat1:{ll_fmt}}  long1: {long1:{ll_fmt}}"
                               f"  x2: {x2:{px_fmt}}     y2: {y2:{px_fmt}}")
                    if ck_reverse:
                        lat2, long2 = gd.pixelToLatLong((x2,y2))
                        stat_line += f"  lat2: {lat2:{ll_fmt}} long2: {long2:{ll_fmt}}"
                        ntest += 1
                        if close((lat1,long1), (lat2,long2)):
                            stat_line += " Pass"
                            npass += 1
                        else:
                            stat_line += " Fail"
                            nfail += 1
                    SlTrace.lg(stat_line)
        SlTrace.lg(f"{ntest:4d} tests  {npass:4d} pass  {nfail:4d} fail")
        
    do_lines_test = False
    if do_lines_test:
        lines_test()
    
    do_rotate_xy_test = True
    ###do_rotate_xy_test = False
    if do_rotate_xy_test:
        rotate_xy_test()

    do_rotate_lat_long_test = False
    ###do_rotate_lat_long_test = True
    if do_rotate_lat_long_test:
        rotate_lat_long_test()
    
