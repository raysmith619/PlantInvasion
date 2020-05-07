#GoogleMapImage.py
"""
Object From googlemapplot.py
Checking on scale
"""

from math import log, cos, sin, exp, sqrt, tan, atan, pi, ceil
import re
import os
import time
import datetime
import sys
from openpyxl.compat.strings import file
from PIL import Image, ImageDraw, ImageFont
import urllib.request, urllib.parse, urllib.error, io

from select_trace import SlTrace
from select_error import SelectError

from GeoDraw import GeoDraw, geoDistance, geoMove, gDistance, geoUnitLen
from GMIError import GMIError
from APIkey import APIKey
from graphviz.files import File


###from msilib.schema import File
###from matplotlib.pyplot import thetagrids
###from lib2to3.fixer_util import String

EARTH_RADIUS = 6378137
EQUATOR_CIRCUMFERENCE = 2 * pi * EARTH_RADIUS
INITIAL_RESOLUTION = EQUATOR_CIRCUMFERENCE / 256.0
ORIGIN_SHIFT = EQUATOR_CIRCUMFERENCE / 2.0

def geo_latlontopixels(lat, lon, zoom):
    mx = (lon * ORIGIN_SHIFT) / 180.0
    deg = (90 + lat) * pi/360.0
    tan_deg = tan(deg)
    min_tan = 1.0e-4
    if tan_deg < min_tan:
        tan_deg = min_tan
    my = log(tan_deg)/(pi/180.0)
    my = (my * ORIGIN_SHIFT) /180.0
    res = INITIAL_RESOLUTION / (2**zoom)
    px = (mx + ORIGIN_SHIFT) / res
    py = (my + ORIGIN_SHIFT) / res
    return px, py

def geo_pixelstolatlon(px, py, zoom):
    res = INITIAL_RESOLUTION / (2**zoom)
    mx = px * res - ORIGIN_SHIFT
    my = py * res - ORIGIN_SHIFT
    lat = (my / ORIGIN_SHIFT) * 180.0
    lat = 180 / pi * (2*atan(exp(lat*pi/180.0)) - pi/2.0)
    lon = (mx / ORIGIN_SHIFT) * 180.0
    return lat, lon

###upperleft =  '-29.44,-52.0'  
###lowerright = '-29.45,-51.98'


ul_lat = 42.38188      # 233 Common St
ul_long = -71.178746
lr_lat = 42.373827
lr_long = -71.173339

############################################
"""
Standalone utility functions
I failed to discover a way of making these class/static member functions
"""

def LoadImageFile(mapFileName=None, imageName=None, infoName=None):
    """
    Load image, info file pair
    either mapFileName or one or both of imageName and infoName
    
    If mapFileName is present determine which image file or info file
    
    If only imageName or infoName specifications, infer the other,
    
    If no file specification is present raise GMIError
    
    If either file type is not found return null in its place.
    :mapFileName - file name - infer type of file, the check
                 for other type file
    :imageName - image file name if present, else infer from info
    :infoName - info file name if present, else infer from image
    If neither is present, raise GMIError
    """
    if mapFileName is not None:
        if infoName is not None or imageName is not None:
            raise GMIError("Can't include infoName or imageName with mapFileName")
        if IsInfoName(mapFileName):
            imageName = MakeImageFromInfoName(mapFileName)
            infoName = mapFileName
        else:
            imageName = mapFileName
            infoName = MakeInfoName(mapFileName)
    else:        
        if infoName is None:
            infoName = MakeInfoName(imageName)
        elif imageName is None:
            imageName = MakeImageFromInfoName(infoName)
    SlTrace.lg("Loading image from image file %s" % imageName)
    try:
        image = Image.open(imageName)
    except IOError as e:
        SlTrace.lg("Error %s opening image file %s" % (repr(e), imageName))
        sys.exit(1)
    
    info = LoadImageInfo(infoName)
    return image, info



def LoadImageInfo(infoName):
    """
    Get info dictionary, if one, else return None
    :infoName - image info file name
    """
    # info types - default: str
    info_type_d = { 'mapType' : str,
                    'ulLat' : float,
                    'ulLong' : float,
                    'lrLat' : float,
                    'lrLong' : float,
                    'mapRotate' : float,
                    'isAugmented' : bool,
                    }
    info = {}
    SlTrace.lg("Loading info from info file %s" % infoName)
    # Set default values
    for key, type in info_type_d.items():
        if type is float:
            info[key] = 0
        elif type is bool:
            info[key] = False
        else:
            info[key] = None

    # Give defaults if not specified or not found    
    if infoName is None or not os.path.exists(infoName):
        info['isAugmented'] = True
        if infoName is None:
            SlTrace.lg("No info file = use defaults")
        else:
            SlTrace.lg("Info file %s not found - use defaults" % infoName)
        return info
        
    try:
        with open(infoName) as info_file:
            lines = info_file.readlines()
            for line in lines:
                line = line.strip()
                line = line.split('#')[0]       # Doesn't ignore # inside quoted string
                if re.match(r'^\s*$', line) is not None:
                    continue                    # Ignore blank lines
                m = re.match(r'(\S+)\s*=\s*(\S+)', line)
                if m is not None:
                    name = m.group(1)
                    if name in info_type_d:
                        info_type = info_type_d[name]
                    else:
                        info_type = str
                    value_str = m.group(2)
                    if info_type is str:
                        value = value_str
                    elif info_type is float:
                        if value_str is None or value_str == "None":
                            value_str = "0.0"
                        value = float(value_str)
                    elif info_type is int:
                        if value_str is None or value_str == "None":
                            value_str = "0"
                        value = int(value_str)
                    else:
                        raise GMIError("Unsupported type for image info%s" % infoName)
                    info[name] = value 
                
    except IOError as e:
        SlTrace.lg("Error %s in info file %s" % (repr(e), file))
        sys.exit(1)
    
    return info


def IsInfoName(fileName):
    """
    Test if valid image info name
    :fileName - candidate image info file name
    """
    m = re.match(r'^(.*)_([^.]+)\.imageinfo$', fileName)
    if m is None:
        return False         # Signal not an info name
    return True
    

def MakeImageFromInfoName(infoName):
    """
    make image file name from info filename
    Replaces _<image extension>.imageinfo with .<image extension>
    :infoName info file name
    :returns image file name if matches, else None
    """
    
    m = re.match(r'^(.*)_([^.]+)\.imageinfo$', infoName)
    if m is None:
        return None         # Signal not an info name
    
    image_name = m.group(1) + "." + m.group(2)
    return image_name


def MakeInfoName(imageName):
    """
    make info file name to pair with makeFileName file
    Replaces file extension (final r'.[^.]+' with "_" extension '.imageinfo'
    imageName
    """
    if imageName is None:
        raise GMIError("imageName is missing")
    
    m = re.match(r'^(.*)(\.)([^.]+)$', imageName)
    if m is None:
        raise GMIError("MakeInfoName: Invalid image file name '%s'" % imageName)
    info_name = m.group(1) + "_" + m.group(3) + ".imageinfo"
    return info_name


"""
End of utility functions
"""


class GoogleMapImage:
    def __init__(self,
                 ulLat=None, ulLong=None,
                 lrLat=None, lrLong=None,
                 displayRotateChange=False,         # True create displays before and after rotate
                 forceNew=False,                    # Force get of new image
                 mapRotate=None,
                 mapPoints=None,                    # Draw map to include all points, when rotated
                 mapBorderM=None,                    # extra space on edges
                 mapBorderD=None,
                 mapBorderP=None,
                 expandRotate=False,
                 maptype=None, zoom=None, scale=None,
                 compassRose=(.75, .25, .10),       # Place compass pointer, -1 ==> none
                                                    # x fraction, y fraction, length fraction
                 showSampleLL=True,                 # Show sample lat long
                 useOldFile=False,                  # Use existing image file even if code changed
                 xDim=None,                           # Dimension default, only if no lrLat
                 yDim=None,
                 xOffset=None,
                 yOffset=None,
                 xSize=None,
                 ySize=None,
                 maxSize = None,
                 file=None,
                 unit='m'):
        """ Generate map image, given latitute, longitude of upper left
        and lower right corners
        :ulLat, ulLong:  Upper left corner latitude, Longitude of image
        :lrLat, lrLong: Lower right corner latitude, longitude of image
        :displayRotateChange: True - create displays unrotated, rotated
                        default: False
        :forceNew: True - force obtaining new image
                default: use cached image file if present
        :mapRotate: Rotate image (degrees), if present
        :mapPoints: list of points added to display
                    if present - Draw map to include all points,
                     when rotated
        :mapBorderM: extra space on edges
                    ...X additional area added surrounding points
                        M - meters
                        D - degrees
                        P - pixels
                Default: 10 meters (e.g. mapBorderM=10)
        :expandRotate: adjust image so rotated image adjusts
                         to size of outputd
                         default: no change
        :maptype: Google Maps type
                    default: 'hybrid'
        :zoom: Google Maps zoom setting
                Default: 18
        :scale: Map scale
                Default: 1
        :compasRose: Place compas pointer
                    (x fraction, y fraction, length fraction)
                    default: (.75, .25, .10)
        :showSampleLL - include sample Longitude, Latitude
                    default: show
        :useOldFile: use pre-existing file even if code has changed
                    default: False
        :xDim:  picture x dimension in unit
        :yDim:  picture y dimension in unit
        :xOffset: picture offset, added to upper left corner (in unit) default: No offset
                ASSUMES North facing
        :yOffset: picture offset, added to upper left corner (in unit) default: No offset
                ASSUMES North facing
        :xSize: raw image x-size in pixels
                default: maxSize else 640
        :ySize: raw image y-size in pixels
                default: maxSize else 640
        :maxSize: maximum raw image x,y size in pixels
                INSTEAD of xSize,ySize
                default: use xSize, ySize
        :file: image file name
                default: construct name from image attributes
                        e.g.:
                            image: gmi_ulA-20_372547_O-80_297716
                                    _lRA-20_373936_O-80_294739
                                    _640x640_sc1z19
                                    _h_mr45.png
                            info:  gmi_uLA-20..._png.imageinfo
        :unit: distance unit m,y,f,s default: m(eter)
        """
        self.unit = unit
        self.displayRotateChange = displayRotateChange
        self.forceNew = forceNew
        self.useOldFile = useOldFile
        self.expandRotate = expandRotate
        self.mapRotate = mapRotate
        if (ulLat is not None or ulLong is not None
                or lrLat is not None or lrLong is not None) and mapPoints is not None:
            raise GMIError("Use only one of ullat... or mapPoints")
        self.mapPoints = mapPoints
        if compassRose is not None and compassRose[0] < 0:
            compassRose = None                      # -1 -- None
        self.compassRose = compassRose
        self.showSampleLL = showSampleLL
        if maptype is None:
            maptype = 'hybrid'
        self.maptype = maptype
        
        if zoom is None:
            zoom = 18
        self.zoom = zoom
        if xDim is None:
            xDim = 40.          # xDim=40 in params does not replace xDim=None in call!
        self.xDim = xDim        #Used in update... if present here
        if yDim is None:
            yDim = xDim
        self.yDim = yDim
        self.xOffset = xOffset
        self.yOffset = yOffset
        if file is not None and mapPoints is None and ulLat is None:
            image, info = LoadImageFile(file)
            SlTrace.lg(f"info:{info}")
            self.ulLat = info["ulLat"]
            self.ulLong = info["ulLong"]
            self.lrLat = info["lrLat"]
            self.lrLong = info["lrLong"]
            self.image = image
        else:
            if self.xOffset is not None or self.yOffset is not None:
                xOffset = 0. if self.xOffset is None else self.xOffset
                yOffset = 0. if self.yOffset is None else self.yOffset
                xOffset_m = xOffset/self.unitLen()
                yOffset_m = yOffset/self.unitLen()
                ulLat, ulLong = geoMove((ulLat,ulLong), latDist=-yOffset_m, longDist=xOffset_m)
                                
            if mapPoints is not None:
                ulLatLong, lrLatLong = GeoDraw.boundLatLong(points=mapPoints, mapRotate=mapRotate,
                                                       borderM=mapBorderM,
                                                       borderD=mapBorderD,
                                                       borderP=mapBorderP)
                ulLat = ulLatLong[0]
                ulLong = ulLatLong[1]
                lrLat = lrLatLong[0]
                lrLong = lrLatLong[1]
                SlTrace.lg(("points rotated %.0f deg bounds:" % mapRotate)
                      + "ulLat=%.6f ulLong=%.6f lrLat=%.6f lrLong=%.6f" %
                      (ulLat, ulLong,  lrLat, lrLong))
                
                height = gDistance((ulLat, ulLong), (lrLat, ulLong))*1000
                width = gDistance((ulLat, ulLong), (ulLat, lrLong))*1000
                diagonal = gDistance((ulLat, ulLong), (lrLat, lrLong))*1000
                SlTrace.lg("points rotated %.0f deg bounds(meters):" % (mapRotate)
                      + "height=%.6g width=%.6g diagonal=%.6g" %
                      (height, width, diagonal))
            else:
                if xDim is not None:
                    if yDim is None:
                        yDim = xDim
                    if lrLat is not None or lrLong is not None:
                        raise SelectError(f"xDim present - can't have lrLat({lrLat}, lrLong({lrLong})")
                unitLen = self.unitLen()
                latDist = -yDim/unitLen     # y increases downward, lat increases upward
                longDist = xDim/unitLen     # x increases rightward, longitude increases(less negative) rightward
                lrLat, lrLong = geoMove((ulLat,ulLong), latDist=latDist, longDist=longDist)
            self.ulLat = ulLat
            self.ulLong = ulLong
            self.lrLat = lrLat
            self.lrLong = lrLong
            SlTrace.lg("GogleMapImage: ulLat=%.5f ulLong=%.5f lrLat=%.5f lrLong=%.5f" %
                                (ulLat, ulLong, lrLat, lrLong))
            SlTrace.lg("             corner to corner:= %.2f meters" %
                                 geoDistance(latLong=(ulLat, ulLong), latLong2=(lrLat, lrLong)))
            
            if scale is None:
                scale = 1
            self.scale = scale
            
            if maxSize is not None:
                xSize = ySize = maxSize
            else:
                if xSize is None:
                    xSize = 640
                if ySize is None:
                    ySize = 640
            self.xSize = xSize
            self.ySize = ySize
            if file is None:
                file = self.makeFileName()
            self.file = file                # Save name, if specified
     
            self.image = self.getImage()
        self.geoDraw = GeoDraw(self.image,
                               ulLat=self.ulLat, ulLong=self.ulLong,
                               lrLat=self.lrLat, lrLong=self.lrLong,
                               mapRotate=self.mapRotate,
                               expandRotate=self.expandRotate,
                               unit=unit)

        if self.compassRose is not None:
            self.addCompassRose(self.compassRose)
            
    def makeFileName(self):
        """
        Create descriptive file name to facilitate previous generation to 
        facilitate reloading image instead of calling Google Map
        gmi_ula<latitude>_O<longitude>_lra<latitude>_<xpixel>x<ypixel>_sc<scale>_<maptype>
        Augmented image files will have "_AUG" before the extension
        maptype will be:
            s - satellite
            r - roadmap
            h - hybrid
        Returns absolute path name
        """
        base_name = "gmi_ulA%.6f_O%.6f_lRA%.6f_O%.6f_%dx%d_sc%dz%d_%s" % (
                    self.ulLat, self.ulLong,
                                self.lrLat, self.lrLong,
                                                self.xSize, self.ySize,
                                                        self.scale,
                                                        self.zoom,
                                                            self.maptype[0])
        if self.mapRotate is not None:
            base_name += "_mr%.0f" % self.mapRotate
        base_name = base_name.replace('.', "_")
        base_name += ".png"                     # Default image file extension
        rel_path = os.path.join("..", "out", base_name)
        full_path = os.path.abspath(rel_path)
        return full_path

    def get_ref_latLong(self):
        """ Get reference latitude, longitude generally uper left corner (corresponds to 0,0 on image
        :returns: (latitude, longitude pair)
        """
        return (self.ulLat, self.ulLong)

    def makeInfoName(self, imageName=None):
        """
        make info file name to pair with makeFileName file
        Replaces file extension (final r'.[^.]+' with "_" extension '.imageinfo'
        imageName, if present, else generate name
        """
        if imageName is None:
            imageName = self.makeFileName()
        return MakeInfoName(imageName)
    
            
    def haveImageFile(self):
        """
        Check if we already have the image file
        """
        image_name = self.makeFileName()
        if os.path.exists(image_name):
            code_name = __file__
            code_mod_time = os.path.getmtime(code_name)
            image_mod_time = os.path.getmtime(image_name)
            if code_mod_time < image_mod_time:
                return True
            SlTrace.lg("code changed (%s) more recently than image file (%s)" %
                            (time.ctime(code_mod_time), time.ctime(image_mod_time)))
            if self.useOldFile:
                SlTrace.lg("We are still going to use existing file")
                return True
        return False
        
            
    def loadImageFile(self):
        """
        load image file, and info file, and return image, info pair
        """
        image_name = self.makeFileName()
        return LoadImageFile(imageName=image_name)


    def addTitle(self, title, xY=None, size=None, color=None, **kwargs):
        self.geoDraw.addTitle(title, xY=xY, size=size, color=color, **kwargs)

    def getCenter(self, ctype='LL', unit=None, ref_latLong=None):
        """ Get center of plot
        :type: type of center 'll' - long,lat, 'pos' - physical location relative to ref,
                            'xY' - pixel
                            default: 'll'
        :returns: tuple of 'll', 'pos', 'xy'
        """
        if unit is None:
            unit = self.unit
        ctype = ctype.lower()
        if ref_latLong is None:
            ref_latLong = self.get_ref_latLong()
        ll_cent = (self.ulLat+self.lrLat)/2, (self.ulLong+self.lrLong)/2
        if ctype == 'll':
            return ll_cent

        if ctype == "pos":
            return self.getPos(latLong=ll_cent, unit=unit, ref_latLong=ref_latLong)
        
        if ctype == "xy":
            return self.getXY(latLong=ll_cent)        

    def getHeight(self):
        return self.geoDraw.getHeight()


    def getWidth(self):
        return self.geoDraw.getWidth()



    def getXY(self, latLong=None, pos=None, xY=None):
        """
        Get/Convert location pixel, longitude, physical location/specification
        to pixel location
        """
        return self.geoDraw.getXY(latLong=latLong, pos=pos, xY=xY)

    def getPos(self, latLong=None, pos=None, xY=None, unit=None, ref_latLong=None):
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
        if unit is None:
            unit = self.unit

        return self.geoDraw.getPos(latLong=latLong, pos=pos, xY=xY, unit=unit, ref_latLong=ref_latLong)

    
    def geoDist(self, latLong=None, latLong2=None, unit=None):
        """ Access to lat,long to distance
        :latLong: starting latitude,longitude pair
        :latLong2: ending latitude, longitued pair
        :unit: distance units name string feet, meter, yard
                default: self.unit, m(eter)
        """
        if unit is None:
            unit = self.unit
        return self.geoDraw.geoDist(latLong=latLong, latLong2=latLong2, unit=unit)

    
    def addToPoint(self, leng=None, xY=None, pos=None, latLong=None, theta=None, deg=None, unit=None):
        """
        Add to point, returning adjusted point in pixels
        Add requested rotation (curDeg if None) to map rotation, if
        mapRotation is not None
        :leng: length in unit
        :unit: unit default: self.unit, meter
        """
        if unit is None:
            unit = self.unit
        if not hasattr(self, "geoDraw"):
            geoDraw = GeoDraw(None,       # VERY limited 
                               ulLat=latLong[0], ulLong=latLong[1],
                               unit=unit)
        else:
            geoDraw = self.geoDraw
        return geoDraw.addToPoint(leng=leng, xY=xY, pos=pos, latLong=latLong,
                                       theta=theta, deg=deg, unit=unit)
    
    def addToPointLL(self, leng=None, xY=None, pos=None, latLong=None, theta=None, deg=None, unit=None):
        """
        Add to point, returning adjusted point in latLong
        """
        if unit is None:
            unit = self.unit
        if not hasattr(self, "geoDraw"):
            geoDraw = GeoDraw(None,       # VERY limited 
                               ulLat=latLong[0], ulLong=latLong[1],
                               unit=unit)
        else:
            geoDraw = self.geoDraw
        return geoDraw.addToPointLL(leng=leng, xY=xY, pos=pos, latLong=latLong,
                                       theta=theta, deg=deg, unit=unit)

        
    def getImage(self):
        """
        Get image, based on settings
        Note that the image may have been rotated and enlarged so as to fit in an image alligned with
        x-y coordinates.
        Enlarge scan to allow rotation and subsequent clipping to specified region.  This is necessary
        because the GoogleMap interface supports only north facing scans
        
        NOTE self.image and self.imageInfo are set here
        """
        if not self.forceNew and self.haveImageFile():
            self.image, self.imageInfo = self.loadImageFile()
            ulLat = self.imageInfo['ulLat']
            ulLong = self.imageInfo['ulLong']
            lrLat = self.imageInfo['lrLat']
            lrLong = self.imageInfo['lrLong']
            mapRotate = self.imageInfo['mapRotate']
            SlTrace.lg("File image: ulLat:%.6f ulLong %.6f lrLat:%.6f lrLong %.6f mapRotate %.0f" %
                        (ulLat, ulLong, lrLat, lrLong, mapRotate))
        else:                
            ulLat, ulLong = self.ulLat, self.ulLong
            lrLat, lrLong = self.lrLat, self.lrLong
            self.imageInfo = {}             # Startup info dictionary
            self.image = self.getRawImage(ulLatLong=(ulLat, ulLong), lrLatLong=(lrLat, lrLong))
            self.imageInfo['ulLat'] = ulLat
            self.imageInfo['ulLong'] = ulLong
            self.imageInfo['lrLat'] = lrLat
            self.imageInfo['lrLong'] = lrLong
            self.imageInfo['mapRotate'] = self.mapRotate
            SlTrace.lg("image width=%.2f height=%.2f" % (self.image.width, self.image.height))
            rotate = 0 if self.imageInfo['mapRotate'] is None else self.imageInfo['mapRotate']
            SlTrace.lg("File image: ulLat:%.6f ulLong %.6f lrLat:%.6f lrLong %.6f mapRotate %.0f" %
                        (self.imageInfo['ulLat'], self.imageInfo['ulLong'],
                         self.imageInfo['lrLat'], self.imageInfo['lrLong'],
                         rotate))
                   
            self.save()
        SlTrace.lg("image width=%.2f height=%.2f" % (self.image.width, self.image.height))
        
        # No need to change image
        if self.mapRotate is not None and self.mapRotate != 0:
            ###self.displayRotateChange = True     # TFD
            if self.displayRotateChange:
                self.dbShow("before rotate")
            self.image = self.image.rotate(self.mapRotate, expand=self.expandRotate)
            if self.displayRotateChange:
                self.image.load()
                SlTrace.lg("Rotated image(%.0f) width=%.2f height=%.2f expand=%s" %
                       (self.mapRotate, self.image.width, self.image.height, self.expandRotate))
                self.dbShow("after rotate")
                SlTrace.lg("after show")
            
            """
            Crop to points + border
            """
            """ Delay cropping --- 
            self.geoDraw = GeoDraw(self.image,
                               ulLat=self.ulLat, ulLong=self.ulLong,
                               lrLat=self.lrLat, lrLong=self.lrLong,
                               mapRotate=self.mapRotate)
            limitsXY, limitsXYpointh = self.geoDraw.limitsXY(self.mapPoints, self.mapRotate)
            x_min = limitsXY['min_x']
            y_min = limitsXY['min_y']
            x_max = limitsXY['max_x']
            y_max = limitsXY['max_y']
            self.crop(box=(x_min, y_min, x_max, y_max))
            --- """
        return self.image


    def crop(self, box=None):
        """
        Crop image, adjusting internal values appropriately
        Adjust bounds
        Adjusts GeoDraw member to reflect new dimensions
        """
        self.geoDraw.crop(box=box)
        
    def rotate(self, rotate=90.):
        """
        Rotate image by specified degrees
        """
        self.image = self.image.rotate(rotate)


    def save(self, name=None, hasInfo=True):
        """
        Save image to file
        If image file saved, then save as <filename_no_ext>_AUG.ext
        iff name is None - also save info fle
        """
        if name is None:
            name = self.makeFileName()
        ext_pat = re.compile(r'(.*)\.([^.]+)$')
        if ext_pat.search(name) is None:
            name += ".png"     # Default extension
        if not os.path.abspath(name):
            name = os.path.join("out", name)
                
        try:
            f = open(name, "wb")
        except (IOError) as e:
            SlTrace.lg("Can't open image save name %s %s" % (name, repr(e)))
            return
        
        try:
            self.image.save(f)
            
        except IOError as e:
            SlTrace.lg("Problem saving image name %s %s" % (name, e.get_message()))
            return
        
        SlTrace.lg("Image file saved in %s" % os.path.abspath(name))

        """
        Save info file
        Note Image.info structure does not seem to be preserved over all image operations
        """
        if hasInfo:        
            info_name = self.makeInfoName()
            try:
                f = open(info_name, "w")
            except (IOError) as e:
                SlTrace.lg("Can't open image info name %s %s" % (info_name, repr(e)))
                return
            
            try:
                now = datetime.datetime.now().strftime("%b %d %Y %H:%M:%S")
                line = "# %s\n# %s\n\n" % (info_name, now)
                f.write(line)
                for key in self.imageInfo:
                    value = self.imageInfo[key]
                    f.write("%s=%s\n" % (key, value))
                f.close()
                
            except IOError as e:
                SlTrace.lg("Problem saving image info name %s %s" % (name, e.get_message()))
                return
            
            SlTrace.lg("Info file saved in %s" % os.path.abspath(info_name))




    def getRawImage(self, ulLatLong=None, lrLatLong=None):
        """
        Get image from URL, covering square with North facing scans
        Store the ulLatLong, and lrLatLong in image.info
        """
        ullat, ullon = ulLatLong[0], ulLatLong[1]
        lrlat, lrlon = lrLatLong[0], lrLatLong[1]
                    
        zoom = self.zoom
        scale = self.scale
        ulx, uly = geo_latlontopixels(ullat, ullon, zoom)
        lrx, lry = geo_latlontopixels(lrlat, lrlon, zoom)
        dx, dy = abs(lrx - ulx), abs(uly - lry)
        cols, rows = int(ceil(dx/self.xSize)), int(ceil(dy/self.ySize))
        SlTrace.lg("cols=%d rows=%d" % (cols,rows))
        bottom = 120
        largura = int(ceil(dx/cols))
        altura = int(ceil(dy/rows))
        alturaplus = altura + bottom
        
        
        comp_image = Image.new("RGB", (int(dx), int(dy)))
        comp_image.info['ulLatLong'] = ulLatLong
        comp_image.info['lrLatLong'] = lrLatLong
        for x in range(cols):
            SlTrace.lg("x=%d" % x)
            for y in range(rows):
                SlTrace.lg("y=%d" % y)
                dxn = largura * (0.5 + x)
                dyn = altura * (0.5 + y)
                latn, lonn = geo_pixelstolatlon(ulx + dxn, uly - dyn - bottom/2, zoom)
                position = ','.join((str(latn), str(lonn)))
                SlTrace.lg(f"{x} {y} {position}")
                urlparams = urllib.parse.urlencode({'center': position,
                                              'zoom': str(zoom),
                                              'size': '%dx%d' % (largura, alturaplus),
                                              'maptype': self.maptype,
                                              'sensor': 'false',
                                              'scale': self.scale,
                                              'key' : APIKey(),
                                              })
                url = 'http://maps.google.com/maps/api/staticmap?' + urlparams
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
                
                fbytes  = f.read()
                tfname = "gmtmp.tmp"
                tf = open(tfname, "wb")
                tf.write(fbytes)
        
                tf.close()
                im=Image.open(tfname)
                comp_image.paste(im, (int(x*largura), int(y*altura)))
        return comp_image
    

    def saveAugmented(self, name=None):
        """
        Save augmented image file
        default name is <std name>_AUG.<std name ext>
        Returns augmented name
        """
        
        if name is None:
            name = self.makeFileName()
            SlTrace.lg("Saving augmented image for base = %s)" % name)
            ext_pat = re.compile(r'(.*)\.([^.]+)$')
            mat = ext_pat.match(name)       # Save as augmented image
            if mat is not None:
                base = mat.group(1)
                ext = mat.group(2)
                name = base + "." + ext
            else:
                SlTrace.lg("!!! No extension found in %s" % name)
                base = name
                ext = "png"
            name = base + "_AUG" + "." + ext    
            
        SlTrace.lg("Saving augmented image name %s" % name)
        self.save(name, hasInfo=False)
        return name
        
    def show(self):
        """
        Display image
        """
        self.image.show()

    def dbShow(self, *texts, image=None, **kwargs):
        """
        debug display, show image with annotations
        No change to image
        """
        if hasattr(self, 'geoDraw'):
            self.geoDraw.dbShow(*texts, image=image, **kwargs)
        else:
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
                SlTrace.lg("show: " + text)
                draw.text(xY, text, font=font, color=tcolor, **kwargs)
                xY = (xY[0], xY[1] + line_sp)
            id.show()

    def destroy(self):
        """ Release resources
            Present for uniformity
        """
        pass

    def text(self, text, xY=None,pos=None,latLong=None, **kwargs):
        """
        Draw text, at position, defaulting to current pen position
        """
        self.geoDraw.text(text, xY=xY, pos=pos, latLong=latLong, **kwargs)

    def unitLen(self, unit=None):
        if unit is None:
            unit = self.unit
        return geoUnitLen(unit)     # Use global function so we don't depend on GeoDraw

    def xMeterToPixel(self, dist):
        """
        Convert distance, in meters, to pixels
        Assumes latitude change over image is a fraction of circumferance
        
        """
        pix = dist/self.xPixSize() * float(self.image.width)
        return pix


    def yMeterToPixel(self, dist):
        """
        Convert distance, in meters, to pixels
        Assumes latitude change over image is a fraction of circumferance
        
        """
        pix = dist/self.yPixSize() * float(self.image.height)
        return pix


    def latSize(self):
        """
        Latitude size of plot == chg in latitude
        """
        lat_chg = abs(self.ulLat - self.lrLat)
        return lat_chg


    def longSize(self):
        """
        Longitude size of plot == chg in Longitude
        """
        long_chg = abs(self.ulLong - self.lrLong)
        return long_chg
    
    
        
    def xPixSize(self):
        """
        X side of plot size in meters
        """
        x_size = self.longSize()/360. * EQUATOR_CIRCUMFERENCE * cos(self.ulLat*pi/180.)
        return x_size


    def yPixSize(self):
        """
        Y side of plot size in meters
        """
        y_size = self.latSize()/360. * EQUATOR_CIRCUMFERENCE
        return y_size

    def fract2latlong(self, xy_fract):
        """ Convert x,y fraction pair to latitute,longitude pair
        :xy_fract: (x-fraction of span, y-fraction of span)
        :returns: (latitude, longitude)
            Note: we recognize x goes sideways, latitude goes up and down
                  but we generally talk x,y and lat, long or that's what we had heard
        """
        x_fract, y_fract = xy_fract
        ul_long = self.ulLong
        lr_long = self.lrLong
        ul_long2 = ul_long + x_fract*(ul_long-lr_long)
        
        ul_lat = self.ulLat
        lr_lat = self.lrLat
        ul_lat2 = ul_lat + y_fract*(ul_lat-lr_lat)
        return (ul_lat2, ul_long2)

    def latLonToImage(self, lat=None, long=None):
        """
        Convert latitude, longitude to pixel location on image
        Returning x,y pair
        """
        
        long_chg = abs(long - self.lrLong)
        long_size = self.longSize()
        x_size = self.image.width
        xpix = x_size - long_chg/long_size * x_size
        lat_chg = abs(lat - self.lrLat)
        lat_size = self.latSize()
        y_size = self.image.height
        ypix = y_size - lat_chg/lat_size * y_size    # yincreases down
        return xpix, ypix

    def latLonToXYm(self, lat=None, long=None, unit=None):
        """
        Convert latitude, longitude to xy offset in meters
        Returning x,y pair
        :lat: latitude in deg
        :long: longitude in deg
        :unit: output units 'm', 'y', 'f'
                default: self.unit, 'm' meters
        :returns: x,y in units
        """
        if unit is None:
            unit = self.unit
        xpix, ypix = self.latlonToImage(lat=lat, long=long)
        return xpix, ypix


    def imageTolatLon(self, x=None, y=None):
        """
        Convert pixel location on image to latitude, longitude
        Returning lat,long pair
        """
        
        x_size = self.image.width
        long_size = self.longSize()
        long = self.ulLong + long_size*x/x_size 
        
        y_size = self.image.height
        lat_size = self.latSize()
        lat = self.lrLat + (y_size-y)*lat_size/y_size
        return lat, long


    def imageChangeTolatLonChange(self, xchg=0, ychg=0):
        """
        Convert change in pixel location on image to latitude, longitude change
        Returning lat change,long change pair
        Used to facilitate oriented changes for figures such as compass 
        """
        p1_x = self.xPixSize()/2.
        p1_y = self.yPixSize()/2.
        p1_lat, p1_long = self.imageTolatLon(x=p1_x, y=p1_y)
        
        p2_x = p1_x + xchg
        p2_y = p1_y + ychg
        p2_lat, p2_long = self.imageTolatLon(x=p2_x, y=p2_y)
        lat_chg = p2_lat - p1_lat
        long_chg = p2_long - p1_long
        
        return lat_chg, long_chg


    def latLonDist(self, startLL=None, endLL=None ):
        """
        Convert change in pixel location on image to latitude, longitude change
        Returning lat change,long change pair
        Used to facilitate oriented changes for figures such as compass 
        """
        p1_x = self.xPixSize()/2.
        p1_y = self.yPixSize()/2.
        p1_lat, p1_long = self.imageTolatLon(x=p1_x, y=p1_y)
        
        p2_x = p1_x + xchg
        p2_y = p1_y + ychg
        p2_lat, p2_long = self.imageTolatLon(x=p2_x, y=p2_y)
        lat_chg = p2_lat - p1_lat
        long_chg = p2_long - p1_long
        
        return lat_chg, long_chg



    def pixelToLatLong(self, xY):
        """
        Convert  pixel x,y to latitude, longitude
        Assumes if map is rotated, then x,y is rotated before translation
        Returning x,y pair
        """
        return self.geoDraw.pixelToLatLong(xY)

    def addScale(self, **kwargs):
        """
        Add scale marker - see GeoDraw.addScale
        """
        self.geoDraw.addScale(**kwargs)
            
            
    def addCompassRose(self, compassRose):
        """
        Add orientation marker
        """
        self.geoDraw.addCompassRose(compassRose)

    
    def addSample(self, point):
        """
        Add sample to current image
        point:
            plot
            long
            lat    
    
        """
        self.geoDraw.addSample(point)


    def markPoint(self, point):
        """
        Mark point - mostly for debugging
        """
        plot = point['plot']
        plot_id = plot.replace("T", "")
        plot_id = plot_id.replace("P", "-")
        sr = self.yMeterToPixel(1.)         # radius, in pixels
        long = point['long']
        lat = point['lat']
        xY = self.getXY(latLong=(lat,long))
        color_plot = (127,127,0)
        self.geoDraw.circle(xY=xY, radius=.25, fill=color_plot)
        color_cent = (255,0,0)
        plot_radius = 10.
        plot_radius_pixel = self.geoDraw.meterToPixel(plot_radius)
        self.geoDraw.circle(xY=xY, radius=plot_radius_pixel, fill=color_plot)
        # get a font
        # use a truetype font
        font_label = ImageFont.truetype("arial.ttf", size=15)
        label_xy = self.geoDraw.addToPoint(xY=xY, leng=15, deg=75)
        self.geoDraw.text(plot_id, xY=label_xy,  font=font_label, fill=(255, 0, 0, 255))
        if False and self.showSampleLL:
            loc_string = "%.5f\n%.5f" % (long, lat)
            font_loc = ImageFont.truetype("arial.ttf", size=8)
            self.geoDraw.text(loc_string, xY=(label_xy[0]+25, label_xy[1]), font=font_loc, fill=(255,255,255,255))    


    def markPoints(self, points):
        for point in points:
            self.markPoint(point)
                


"""
Stanalone test / exercise:
"""
if __name__ == "__main__":
    import sys
    import argparse
    from GMIError import GMIError
    
    forceNew = False
    mapRotate = 45.
    maptype = "hybrid"
    testMarks = True
    useOldFile = False
    showSampleLL = True
    zoom = None
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--maprotate=', type=float, dest='mapRotate', default=mapRotate)
    parser.add_argument('--maptype', dest='maptype', default=maptype)
    parser.add_argument('--showsamplell', dest='showSampleLL', default=showSampleLL, action='store_true')
    parser.add_argument('--forcenew', dest='forceNew', default=forceNew, action='store_true')
    parser.add_argument('--testmarks', dest='testMarks', default=testMarks, action='store_true')
    parser.add_argument('--notestmarks', dest='testMarks', action='store_false')
    parser.add_argument('--useoldfile', dest='useOldFile', default=useOldFile, action='store_true')
    parser.add_argument('--zoom=', type=int, dest='zoom', default=zoom)
    
    args = parser.parse_args()             # or die "Illegal options"
    testMarks = args.testMarks
    mapRotate = args.mapRotate
    maptype = args.maptype
    showSampleLL = args.showSampleLL
    forceNew = args.forceNew
    zoom = args.zoom
    SlTrace.lg("%s %s\n" % (os.path.basename(sys.argv[0]), " ".join(sys.argv[1:])))
    SlTrace.lg("args: %s\n" % args)
    """
    max_lat  9-1  Longitude: -71.18546 latitude: 42.37449
    min_lat  2-5  Longitude: -71.18409 latitude: 42.37183
    max_long 1-1  Longitude: -71.18312 latitude: 42.37266
    min_long 9-2  Longitude: -71.18573 latitude: 42.37426
    
    """

    points = (
            {'limit' : 'max_lat',  'plot' : '9-1',  'long' : -71.18546, 'lat' : 42.37449},
            {'limit' : 'min_lat',  'plot' : '2-5',  'long' : -71.18409, 'lat' : 42.37183},
            {'limit' : 'max_long',  'plot' : '1-1',  'long' : -71.18312, 'lat' : 42.37266},
            {'limit' : 'min_long',  'plot' : '9-2',  'long' : -71.18573, 'lat' : 42.37426},
        )
    border = 10.
    ###border = 0
    gmi = GoogleMapImage(mapPoints=points,
                        mapBorderM=border,
                        compassRose=(.75, .25, .1),
                        mapRotate=mapRotate,
                        forceNew=forceNew,
                        maptype=maptype,
                        zoom=zoom)
    gmi.addScale()
    

    if testMarks:
        """
        Add samples to plot
        """
        test_point = 0
        for point in points:
            test_point += 1
            gmi.addSample(point)
            if test_point >= 4:
                pass

        red = (255, 0, 0)
        blue = (0, 0, 255)
        gmi.addScale(latLong=(gmi.ulLat, gmi.ulLong), latLongEnd=(gmi.lrLat, gmi.ulLong), color=red)   # vertical left edge
        gmi.addScale(latLong=(gmi.ulLat, gmi.ulLong), latLongEnd=(gmi.lrLat, gmi.lrLong))   # corner to corner
        gmi.addScale(latLong=(gmi.lrLat, gmi.ulLong), latLongEnd=(gmi.lrLat, gmi.lrLong), color=blue)   # horizontal botom
        """   
        A center point surrounded with N,E,S, and W markers
        """
        t_size = 20
        t_color = red
        t_font = ImageFont.truetype("arial.ttf", size=t_size)
        lat_len = abs((gmi.ulLat-gmi.lrLat)/8)
        long_len = abs((gmi.lrLong-gmi.ulLong)/8)
        SlTrace.lg("lat_len=%.6f long_len=%.6f" % (lat_len, long_len))
        c_latLong = ((gmi.ulLat+gmi.lrLat)/2, (gmi.ulLong+gmi.lrLong)/2)
        n_latLong = (c_latLong[0]+lat_len, c_latLong[1])
        e_latLong = (c_latLong[0], c_latLong[1]+long_len)
        s_latLong = (c_latLong[0]-lat_len, c_latLong[1])
        w_latLong = (c_latLong[0], c_latLong[1]-long_len)
        SlTrace.lg("North %.6f, %.6f" % (n_latLong[0], n_latLong[1]))
        SlTrace.lg("East %.6f, %.6f" % (e_latLong[0], e_latLong[1]))
        SlTrace.lg("South %.6f, %.6f" % (s_latLong[0], s_latLong[1]))
        SlTrace.lg("West %.6f, %.6f" % (w_latLong[0], w_latLong[1]))
        SlTrace.lg("Center %.6f, %.6f" % (c_latLong[0], c_latLong[1]))
        gmi.text("North %.6f, %.6f" % (n_latLong[0], n_latLong[1]), latLong=n_latLong, font=t_font, fill=t_color)
        gmi.text("East %.6f, %.6f" % (e_latLong[0], e_latLong[1]), latLong=e_latLong, font=t_font, fill=t_color)
        gmi.text("South %.6f, %.6f" % (s_latLong[0], s_latLong[1]), latLong=s_latLong, font=t_font, fill=t_color)
        gmi.text("West %.6f, %.6f" % (w_latLong[0], w_latLong[1]), latLong=w_latLong, font=t_font, fill=t_color)
        gmi.text("Center %.6f, %.6f" % (c_latLong[0], c_latLong[1]), latLong=c_latLong, font=t_font, fill=t_color)
        """
        Do box around orignial ul, lr
        """
        gd = gmi.geoDraw
        inset = 100
        box_line_width = 10
        gd.line([gd.addToPoint(latLong=(gmi.ulLat, gmi.ulLong), leng=inset, deg=-45),
                  gd.addToPoint(latLong=(gmi.ulLat, gmi.lrLong), leng=inset, deg=-180+45),
                gd.addToPoint(latLong=(gmi.lrLat, gmi.lrLong), leng=inset, deg=-180-45),
                 gd.addToPoint(latLong=(gmi.lrLat, gmi.ulLong), leng=inset, deg=45),
                gd.addToPoint(latLong=(gmi.ulLat, gmi.ulLong), leng=inset, deg=-45)],
                  fill=blue, width=box_line_width)
    
            
            ###break       # limit for debugging TFD
    if testMarks:
        ###gmi.addScale(latLong=(42.37350, -71.18318), leng=100, marks=10, unitName="f")
        ###gmi.addScale(latLong=(42.37365, -71.18304), deg=8, leng=100, marks=10, unitName="f", color=(0,0,255))
        ###gmi.addScale(latLong=(42.37365, -71.183060), deg=8.8, leng=500, marks=10, unitName="f", color=(0,0,255))
        gmi.addScale(latLong=(42.37357, -71.183000), deg=8.8, leng=500, marks=10, unitName="f", color=(0,0,255))
        gmi.addScale(latLong=(42.37555,-71.18677), latLongEnd=(42.37077,-71.18208)) # Diagonal ul to lr
        gmi.addScale(latLong=(42.37555,-71.18677), latLongEnd=(42.37077,-71.18677)) # Vertical left edge
        gmi.addScale(latLong=(42.37077,-71.18677), latLongEnd=(42.37077,-71.18208))
        gmi.addScale(xY=(10,10), deg=-90, leng=gmi.getHeight()*.9)
    if abs(mapRotate) >= 1:
        rot_str = "%.0f" % mapRotate
    else:
        rot_str = "%.3g" % mapRotate
    title = "%s rotate = %s" % (os.path.basename(__file__), rot_str)
    gmi.addTitle(title)
    gmi.show()
    gmi.saveAugmented()
    SlTrace.lg("End of Test")