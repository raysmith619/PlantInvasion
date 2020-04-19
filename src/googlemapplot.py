import sys
from PIL import Image
import urllib.request, urllib.parse, urllib.error, io
from math import log, exp, tan, atan, pi, ceil

EARTH_RADIUS = 6378137
EQUATOR_CIRCUMFERENCE = 2 * pi * EARTH_RADIUS
INITIAL_RESOLUTION = EQUATOR_CIRCUMFERENCE / 256.0
ORIGIN_SHIFT = EQUATOR_CIRCUMFERENCE / 2.0

def latlontopixels(lat, lon, zoom):
    mx = (lon * ORIGIN_SHIFT) / 180.0
    my = log(tan((90 + lat) * pi/360.0))/(pi/180.0)
    my = (my * ORIGIN_SHIFT) /180.0
    res = INITIAL_RESOLUTION / (2**zoom)
    px = (mx + ORIGIN_SHIFT) / res
    py = (my + ORIGIN_SHIFT) / res
    return px, py

def pixelstolatlon(px, py, zoom):
    res = INITIAL_RESOLUTION / (2**zoom)
    mx = px * res - ORIGIN_SHIFT
    my = py * res - ORIGIN_SHIFT
    lat = (my / ORIGIN_SHIFT) * 180.0
    lat = 180 / pi * (2*atan(exp(lat*pi/180.0)) - pi/2.0)
    lon = (mx / ORIGIN_SHIFT) * 180.0
    return lat, lon

############################################

###upperleft =  '-29.44,-52.0'  
###lowerright = '-29.45,-51.98'

upperleft =  '42.38188,-71.178746'     # 233 Common St 
lowerright = '42.373827,-71.173339'

zoom = 18   # be careful not to get too many images!

ullat, ullon = list(map(float, upperleft.split(',')))
lrlat, lrlon = list(map(float, lowerright.split(',')))
scale = 1
maxsize = 640
ulx, uly = latlontopixels(ullat, ullon, zoom)
lrx, lry = latlontopixels(lrlat, lrlon, zoom)
dx, dy = lrx - ulx, uly - lry
cols, rows = int(ceil(dx/maxsize)), int(ceil(dy/maxsize))
print("cols=%d rows=%d" % (cols,rows))
bottom = 120
largura = int(ceil(dx/cols))
altura = int(ceil(dy/rows))
alturaplus = altura + bottom


final = Image.new("RGB", (int(dx), int(dy)))
for x in range(cols):
    print("x=%d" % x)
    for y in range(rows):
        print("y=%d" % y)
        dxn = largura * (0.5 + x)
        dyn = altura * (0.5 + y)
        latn, lonn = pixelstolatlon(ulx + dxn, uly - dyn - bottom/2, zoom)
        position = ','.join((str(latn), str(lonn)))
        print(x, y, position)
        urlparams = urllib.parse.urlencode({'center': position,
                                      'zoom': str(zoom),
                                      'size': '%dx%d' % (largura, alturaplus),
                                      'maptype': 'satellite',
                                      'sensor': 'false',
                                      'scale': scale})
        url = 'http://maps.google.com/maps/api/staticmap?' + urlparams
        print("url=%s" % url)
        max_try = 5
        ntry = 0
        while True:
            ntry += 1
            if ntry > max_try:
                print("ntry = %d, exceeding max:%d" % (ntry, max_try))
                sys.exit(1)
            try:
                print("ntry: %d" % ntry)
                f=urllib.request.urlopen(url)
                break
            except:
                continue
        
        fbytes  = f.read()
        tfname = "gmtmp.tmp"
        tf = open(tfname, "wb")
        tf.write(fbytes)

        tf.close()
        im=Image.open(tfname)
        final.paste(im, (int(x*largura), int(y*altura)))
final.show()
print("End of Test")