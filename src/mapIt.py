"""
mapIt.py
Map a selected Location

Whitney Hill Park
Type:  park
Location:  Massachusetts, New England, United States, North America
Latitude:  42 22' 21.4" (42.3726) north
Longitude:  71 11' 5.2" (71.1848) west
Elevation:  154 feet (47 meters)


"""
import argparse
from GoogleMap import GoogleMap
###from wx import Height

file = "mapIt.png"
latitude=42.3726
longitude=-71.1848
latitude += .0015
longitude += -.0010
width=1500                      # meters
height=500
iwidth=500
iheight=iwidth
maptype='satellite'
maptype='hybrid'
maptype='road'
scale=1
zoom=None
markCenter=False
useCenter=False

parser = argparse.ArgumentParser()
parser.add_argument('--file', dest='file', default=file)
parser.add_argument('--latitude=', type=float, dest='latitude', default=latitude)
parser.add_argument('--longitude=', type=float, dest='longitude', default=longitude)
parser.add_argument('--width=', type=float, dest='width', default=width)
parser.add_argument('--height=', type=float, dest='height', default=height)
parser.add_argument('--iwidth=', type=int, dest='iwidth', default=iwidth)
parser.add_argument('--iheight=', type=int, dest='iheight', default=iheight)
parser.add_argument('--maptype=', dest='maptype', default=maptype)
parser.add_argument('--markcenter=', action='store_true', dest='markCenter', default=markCenter)
parser.add_argument('--scale=', type=int, dest='scale', default=scale)
parser.add_argument('--zoom=', type=int, dest='zoom', default=zoom)
parser.add_argument('--usecenter=', action='store_true', dest='useCenter', default=useCenter)


args = parser.parse_args()             # or die "Illegal options"
file = args.file
latitude = args.latitude
longitutde = args.longitude
width = args.width
height = args.height
iwidth = args.iwidth
iheight = args.iheight
maptype = args.maptype
markCenter = args.markCenter
useCenter = args.useCenter
scale = args.scale
zoom = args.zoom

gm = GoogleMap(file=file,
               latitude=latitude,
               longitude=longitude,
               maptype=maptype,
               width=width,
               height=height,
               iwidth=iwidth,
               iheight=iheight,
               scale=scale,
               markCenter=markCenter)
gm.show()
gm.save(file)
print("End of Test")