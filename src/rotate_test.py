# rotate_test.py
""" Test mapRotate in GeoDraw
Verify line deg interoperates properly
"""
import os
import sys
from math import log, cos, sin, exp, sqrt, tan, asin, atan, atan2, pi, ceil
from PIL import Image, ImageDraw, ImageFont
import argparse

from GMIError import GMIError
from GeoDraw import GeoDraw, geoDistance, gDistance, deg2rad

# A small box
side_len = 1000         # Image side in pixels
ngrid = 10              # Number of grid spaces
mapRotate = 45.         # Map rotation in degrees

parser = argparse.ArgumentParser()
parser.add_argument('--maprotate=', type=float, dest='mapRotate', default=mapRotate)
parser.add_argument('--side_len=', type=float, dest='side_len', default=side_len)
parser.add_argument('--ngrid=', type=float, dest='ngrid', default=ngrid)

args = parser.parse_args()             # or die "Illegal options"

mapRotate = args.mapRotate
side_len = args.side_len
ngrid = args.ngrid

print("%s %s\n" % (os.path.basename(sys.argv[0]), " ".join(sys.argv[1:])))
print("args: %s\n" % args)


im = Image.new("RGB", (int(side_len), int(side_len)))
ulX=0
ulY=0
lrX=side_len
lrY=side_len

# Create map North facing
gd = GeoDraw(im, ulX=ulX, ulY=ulY, lrX=lrX, lrY=lrY, mapRotate=0)
print("image width=%d height=%d" % (gd.getWidth(), gd.getHeight()))
# Ad grid t immage to simulate map
grid_space = side_len/ngrid
line_color = (240, 240, 240)
line_width = 2
point_size = 5
db_color = (0, 0, 256)
db_color2 = (256, 0, 256)
db_color_point = (0, 256, 50)
db_width = 4
font_size = 20
db_font = ImageFont.truetype("arial.ttf", size=font_size)

for n in range(ngrid+1):       # Vertical lines
    x = n * grid_space
    y = 0
    if n == ngrid:
        x -= line_width         # Move in on last line to fit inside edge
    gd.lineSeg(xY=(x,y), leng=side_len, deg=-90, fill=line_color, width=line_width)

for n in range(ngrid+1):       # Horizontal lines
    x = 0
    y = n * grid_space
    if n == ngrid:
        y -= line_width         # Move in on last line to fit inside edge
    gd.lineSeg(xY=(x,y), leng=side_len, deg=0, fill=line_color, width=line_width)


# Rotate map
gd.lineSeg(xY=(side_len*.1, side_len*.1), leng=side_len, deg=0, fill=db_color, width=db_width)
gd.rotateMap(mapRotate)        
gd.lineSeg(xY=(side_len*.2, side_len*.2), leng=side_len, deg=0, fill=db_color, width=db_width)
compassRose = (.7, .3, .1)
gd.addCompassRose(compassRose)
gd.lineSeg(xY=(side_len*.3, side_len*.3), leng=side_len, deg=0, fill=db_color, width=db_width)
gd.lineSeg(xY=(side_len*.4, side_len*.4), leng=side_len, deg=-mapRotate, fill=db_color, width=db_width)
gd.lineSeg(xY=(2*line_width, side_len-2*line_width), leng=side_len, deg=-mapRotate, fill=db_color, width=db_width)
p1 = (side_len*.3, side_len*.6)
plen = side_len*.3
gd.text(" p1:(%.2f, %.2f)" % (p1[0], p1[1]), xY=p1, fill=db_color2, font=db_font)
gd.circle(xY=p1, radius=point_size, fill=db_color_point) 

p2 = gd.addToPoint(xY=p1, leng=plen, deg=0)
gd.text(" p2:(%.1f, %.1f)" % (p2[0], p2[1]), xY=p2, fill=db_color2, font=db_font)
gd.circle(xY=p2, radius=point_size, fill=db_color_point) 

p3 = gd.addToPoint(xY=p2, leng=plen, deg=90)
gd.text(" p3:(%.1f, %.1f)" % (p3[0], p3[1]), xY=p3, fill=db_color2, font=db_font)
gd.circle(xY=p3, radius=point_size, fill=db_color_point) 

p4 = gd.addToPoint(xY=p3, leng=plen, deg=180)
gd.text(" p4:(%.1f, %.1f)" % (p4[0], p4[1]), xY=p4, fill=db_color2, font=db_font)
gd.circle(xY=p4, radius=point_size, fill=db_color_point) 

gd.dbShow("testing mapRotate=%.2g" % (mapRotate))
    
 