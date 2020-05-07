"""
Interface to Pillow Image facilitating map annotation 
"""
import re
from PIL import Image, ImageDraw, ImageFont
import urllib.request, urllib.parse, urllib.error, io
from math import log, cos, sin, exp, sqrt, tan, asin, atan, atan2, pi, ceil
from GMIError import GMIError
from builtins import staticmethod
from openpyxl.drawing.effect import Color
from idlelib.colorizer import color_config
from pandas._libs.tslibs.offsets import get_firstbday

from select_trace import SlTrace

EARTH_RADIUS = 6378137.
EQUATOR_CIRCUMFERENCE = 2 * pi * EARTH_RADIUS

def deg2rad(degree):
    return degree/180.*pi

def rad2deg(rad):
    return rad/pi*180.
    
trace_scale = False
    
def geoDistance(latLong=None, latLong2=None):
    """
    Compute distance(in meters) between two points given in latitude,longitude pairs
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
    phi1 = deg2rad(lat1)
    phi2 = deg2rad(lat2)
    delta_phi = deg2rad(lat2-lat1)
    delta_lambda = deg2rad(lon2-lon1)
    
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
    phi1 = deg2rad(lat1)
    delta_phi = latDist / R 
    phi2 = phi1 + delta_phi
    lat2 = rad2deg(phi2)
    
    lambda1 = deg2rad(long1)
    R2 = R * cos((phi1+phi2/2))     # Shortened by higher latitude
    delta_lambda = longDist / R2
    lambda2 = lambda1 + delta_lambda
    long2 = rad2deg(lambda2)
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
        raise GMIError(f"Unrecognized unit name '{unit}' choose f[oot],m[eter],y, or s")

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
        mapRot - Map's rotation (in degrees, counter clockwise) from North (up)
        mapPoints - points (latitude, longitude) included in map - minimum a perimeter
        :pos - drawing pen current position (x,y) in unit(meter)
        :latLong - drawing pen current location (latitude, longitude) in degrees
        :xY - drawing pen current location in floating pixels (x-left to right,y-top to bottom)
        :deg - drawing pen current direction in degrees (counter clockwise)
        :theta - drawing pen current direction in radians
        """
    
        self.showSampleLL = showSampleLL
            
        if image is None:
            image = Image.new("RGB", (400, 200))
        self.setImage(image)
        ulmx = 0.
        ulmy = 0.
        lrmx = ulmx  + self.getWidth()
        lrmy = ulmy + self.getHeight()
        self.ulmx = ulmx
        self.ulmy = ulmy
        self.lrmx = lrmx
        self.lrmy = lrmy
        self.mapRotate = mapRotate
        self.expandRotate = expandRotate
        
        if deg is not None and theta is not None:
            raise GMIError("Only deg or theta is allowed")
        if theta is not None:
            deg = theta/pi * 180
        self.deg = deg          #None - unrotated
        if ulLat is not None:
            self.ulLat = ulLat
            self.ulLong = ulLong
            self.lrLat = lrLat
            self.lrLong = lrLong
            
        if ulLat is not None and lrX is not None:
            raise GMIError("Only one of ulLat and lrX can be specified")
        if ulLong is not None and lrY is not None:
            raise GMIError("Only one of ulLong or lrY can be specified")

        if ulX is None: 
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
            lat_avg = (self.ulLat+self.lrLat)/2.
            lat_rad = lat_avg*pi/180.
            lrX = ulX + cos(lat_rad) * (self.lrLong-self.ulLong) / 360. * EQUATOR_CIRCUMFERENCE
            lrY = ulY + (self.ulLat-self.lrLat) / 360. * EQUATOR_CIRCUMFERENCE
        SlTrace.lg(f"Loaded Image: width:{self.getWidth()} height:{self.getHeight()}")
        SlTrace.lg(f"Distance coordinates(meters):"
              f"\n\tUpper Left x:{ulX:.1f} y:{ulY:.1f}"
              f"\n\tLower Right x: {lrX:.1f} y: {lrY:.1f}")
        self.ulX = ulX
        self.ulY = ulY
        self.lrX = lrX
        self.lrY = lrY
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
        

    @classmethod
    def boundLatLong(cls, points=None, mapRotate=None,
                    borderM=None, borderD=None, borderP=None):
        """
        Calculate a vertical bounding box containing the provided points on a rotated map,
        providing an optional surrounding border area, clear of points, such that
        given a north-pointing scan provided by Google-Maps will, when rotated and cropped
        verticaly and horizonally, give a rectangle. 
        :points a list of points(dictionaries), each having at least the entries
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
            
 ###TBD
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
            raise GMIError("Can't use more than one of borderM, borderD, borderP")
        
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
            if 'lat' in point:
                lat1 = point['lat']
            else:
                lat1 = point[0]
            if 'long' in point:
                long1 = point['long']
            else:
                long1 = point[1]
            
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
            theta = deg2rad(rotate)
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
            lat = point['lat']
            long = point['long']
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

            
    def addCompassRose(self, compassRose):
        """
        Add orientation marker
        """
        if compassRose is None:
            compassRose = (.5, .5, .25)
        xFraction = compassRose[0]
        yFraction = compassRose[1]
        lenFraction = compassRose[2]
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
        arrow_head_width = 2*arrow_width
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

    
    def addSample(self, point):
        """
        Add sample to current image
        point:
            plot
            long
            lat    
    
        """
        label_color = (255, 0, 0)
        label_size = 30
        label_font = ImageFont.truetype("arial.ttf", size=label_size)
        latlong_size = label_size/2
        plot = point['plot']
        pm = re.match("T(\d+)P(\d+)", plot)
        if pm is not None:
            plot_key = plot_key = f"{pm.group(1)}-{pm.group(2)}"
        else:
            plot_key = plot
        plot_id = plot_key
        long = point['long']
        lat = point['lat']
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
        if self.showSampleLL:
            latlong_size = int(latlong_size)
            loc_string = "%.5f\n%.5f" % (long, lat)
            font_loc = ImageFont.truetype("arial.ttf", size=latlong_size)
            latlong_xy = self.addToPoint(latLong=(lat,long),
                                         leng=latlong_size, deg=-self.mapRotate)
            self.text(loc_string, xY=latlong_xy, font=font_loc,
                       fill=(255,255,255,255))    


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
            raise GMIError("Atleast one of xY, pos, latLong must be present")
        if np1_spec > 1:
            raise GMIError("Only one of xY, pos, latLong is allowed")


        if np2_spec > 0 and leng is not None:
            raise GMIError("leng is not alowed when ending point is specified")
        if  np2_spec > 0 and deg is not None:
            raise GMIError("deg is not allowed when ending point is specified")
        
        if np2_spec == 0 and leng is None:
            leng = self.getWidth()*.8
        if np2_spec > 1:
            raise GMIError("Only one of xYEnd, posEnd, or latLongEnd may be specified")
            
        if np1_spec > 1:
            raise GMIError("Only one of xY, pos, latLong is allowed")
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
        scale_theta = deg2rad(scale_deg)
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
        self.text(title, xY=title_xy, font=title_font, fill=title_color)

    
    def addToPoint(self, leng=None, xY=None, pos=None, latLong=None, theta=None, deg=None, unit=None):
        """
        Add to point, returning adjusted point in pixels
        Add requested rotation (curDeg if None) to map rotation, if
        mapRotation is not None
        :leng: length in unit
        :unit: unit default: self.unit, meter
        """
        if leng is None:
            raise GMIError("leng is required")
        
        if unit is None:
            unit = self.unit
        leng /= self.unitLen(unit)
            
        if theta is not None and deg is not None:
            raise GMIError("Only specify theta or deg")
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
            raise GMIError("Only specify one of xY, pos or latLong")
        if npxl != 1:
            raise GMIError("Must specify one of xY, pos or latLong")
        if leng is None:
            raise GMIError("leng is required")
        
        xY = self.getXY(xY=xY, pos=pos, latLong=latLong)
            
        if deg is None:
            deg = 0
        if self.mapRotate is not None:
            deg += self.mapRotate
            
        theta = deg/180.*pi
        if theta != 0:
            delta_x = cos(theta)*leng
            delta_y = -sin(theta)*leng
        else:
            delta_x = leng
            delta_y = 0.
        return xY[0]+delta_x, xY[1]+delta_y


    def adjWidthBySize(self, lineWidth):
        """
        Adjust line widths to account for large images
        """
        mindim = min(self.getWidth(), self.getHeight())
        adj_lineWidth = lineWidth
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
            raise GMIError("crop: box is required")
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


    def getLatLong(self, latLong=None, pos=None, xY=None):
        """
        Get/Convert location pixel, longitude, physical location/specification
        to pixel location
        """
        xY = self.getXY(latLong=latLong, pos=pos, xY=xY)
        latLong = self.pixelToLatLong(xY)
        return latLong


    def getPos(self, latLong=None, pos=None, xY=None, unit='m', ref_latLong=None):
        """
        Get/Convert location pixel, longitude, physical location/specification
        to position in meters,yards, or feet
        :latLong: latitude,longitude pair
        :pos: x,y position pair in meters
        :xY: x,y position pair in pixels
        :unit: output distance units meter, yard, feet
            default: m(eter)
        :orig_latLong: if present, give position relative to reference
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
    

    def getXY(self, latLong=None, pos=None, xY=None):
        """
        Get/Convert location pixel, longitude, physical location/specification
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
        
        if nloc_spec > 1:
            raise GMIError("May specify, at most, one of latLong, pos, or xY")
        
        if latLong is not None:
            xY =  self.latLongToPixel(latLong)
        elif pos is not None:
            xY = self.posToPixel(pos)
        if xY is None:
            xY = self.curXY
        return xY



    def latLongToPixel(self, latLong):
        """
        Convert latitude, longitude to pixel location on image
        Assumes if map is rotated, then rectangular image rotated and expanded so map will fit
        Returning x,y pair
        """
        if latLong is None:
            raise GMIError("latlongToPixel: latLong required");
        lat = latLong[0]
        long = latLong[1]
        lat_offset = lat - self.ulLat         # from upper left corner - - increase down
        long_offset = long - self.ulLong      # increase left to right
        mx = long_offset/(self.lrLong-self.ulLong)*self.getWidth()      # increase left to right
        my = lat_offset/(self.lrLat-self.ulLat)*self.getHeight()        # increase ulLat: upper(less) to lrLat: lower(bigger)
        if self.mapRotate is not None:
            mapTheta = -deg2rad(self.mapRotate)
            # Translate to center of image
            mx_c = mx - self.getWidth()/2.
            my_c = my - self.getHeight()/2.
            mx2_c = mx_c * cos(mapTheta) - my_c * sin(mapTheta)
            my2_c = my_c * cos(mapTheta) + mx_c * sin(mapTheta)
            # Translate back to original coordinate system
            mx2 = mx2_c + self.getWidth()/2.
            my2 = my2_c + self.getHeight()/2.
            mx = mx2
            my = my2
            
        return mx, my


    def pixelToLatLong(self, xY):
        """
        Convert  pixel x,y to latitude, longitude
        Assumes if map is rotated, then x,y is rotated before translation
        Returning x,y pair
        """
        if xY is None:
            raise GMIError("pixelToLatLong: pixel required")
        mx = xY[0]        # from upper left corner
        my = xY[1]
        if self.mapRotate is not None:
            mapTheta = -deg2rad(self.mapRotate)
            # Translate to center of image
            mx_c = mx - self.getWidth()/2.
            my_c = my - self.getHeight()/2.
            mx2_c = mx_c * cos(mapTheta) - my_c * sin(mapTheta)
            my2_c = my_c * cos(mapTheta) + mx_c * sin(mapTheta)
            # Translate back to original coordinate system
            mx2 = mx2_c + self.getWidth()/2.
            my2 = my2_c + self.getHeight()/2.
           
            mx = mx2
            my = my2
        
        long_offset = mx * (self.lrLong-self.ulLong) / self.getWidth()
        lat_offset = my * (self.ulLat-self.lrLat) / self.getHeight()

        long = self.ulLong + long_offset
        lat = self.ulLat - lat_offset

        return lat, long
        
        
            
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


    def rotateMap(self, deg, expand=None):
        """
        Rotate map, updating image, and mapRotate
        """
        self.mapRotate = deg        # TFD
        im = self.image.rotate(deg, expand=expand)
        self.setImage(im)


    def rotatePoints(self, points, rotate=None):
        """
        Rotate points
        Return copy of points array, with lat, long, adjusted by map rotation
        """
        if rotate is None:
            rotate = self.mapRotate
        

    def setCurAngle(self,
        deg=0,
        theta=0):
        """
        Set current pen drawing direction
        
        :curDeg - drawing pen current direction in degrees
        :curTheta - drawing pen current direction in radians
        """
                
        if deg is not None and theta is not None:
            raise GMIError("Only one of deg or theta must be specified")
        if theta is not None:
            deg = theta / pi * 180
        if deg is None:
            deg = 0
            
        self.curDeg = deg


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
        

    def ellipse(self, elp_cent, **kwargs):
        self.draw.ellipse(elp_cent, **kwargs)

    def line(self, points, **kwargs):
        """
        Draw line segments one more points (pixelx, pixely)
        if only one point is given, the current pen location is used as the first point
        Current pen position is unchanged.
        Non used args are passed to Image.draw.line 
        """
        if len(points) == 1:
            pts = [self.curXY, points[0]]
        else:
            pts = points
        self.draw.line(pts, **kwargs)


    def text(self, text, xY=None,pos=None,latLong=None, **kwargs):
        """
        Draw text, at position, defaulting to current pen position
        """
        xY = self.getXY(xY=xY, pos=pos, latLong=latLong)
        self.draw.text(xY, text, **kwargs)
        
 
    def lineSeg(self, leng=10, xY=None, pos=None, latLong=None, theta=None, deg=None, **kwargs):
        """
        Draw line segment starting at current pen Position
        Extra named args are passed to Image.draw.line
        """
        xY = self.getXY(xY=xY, pos=pos, latLong=latLong)
        new_xY = self.addToPoint(leng=leng, xY=xY, theta=theta, deg=deg)
        self.line([xY, new_xY], **kwargs)



    def dbShow(self, *texts, image=None, **kwargs):
        """
        debug display, show image with annotations
        No change to image
        """
        if image is None:
            image = self.image
        id = image.copy()
        draw = ImageDraw.Draw(id)      # Setup ImageDraw access
        
        font_size = 58
        line_sp = font_size
        xY = (line_sp, line_sp)
        font = ImageFont.truetype("arial.ttf", size=font_size)
        tcolor = (255,0,255)

        for text in texts:
            print("show: " + text)
            draw.text(xY, text, font=font, color=tcolor, **kwargs)
            xY = (xY[0], xY[1] + line_sp)
        id.show()
        
        
        
if __name__ == "__main__":
    import os
    import sys
    print("%s %s\n" % (os.path.basename(sys.argv[0]), " ".join(sys.argv[1:])))
    # A small box
    im = Image.new("RGB", (400, 400))    
    fieldlen = 100            # Box side length in meters
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
    