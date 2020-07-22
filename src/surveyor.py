#surveyor.py
"""
Small program which allows the operator to specify a location e.g. longitude/Latitude
and displays a composite map and facilitates the placement of markers within the display.
The program facilitates display of information on the placement of the markers to provide
information about the relative location of those markers.
Display of the following will be provided:
    Compass direction between two markersd
    Distance between two markers
    Area of the area surrounded by a number of markers
    Interactive rotation of display
Home: https://www.google.com/maps/place/233+Common+St,+Watertown,+MA+02472
            /@42.3760002,-71.1773149,51m/data=!3m1!1e3!4m5
            !3m4!1s0x89e377f6fcdb5fe3:0x4f5a8d756f440867!8m2!3d42.3760597!4d-71.1772921

Created on October 30, 2018

@author: Charles Raymond Smith
"""
import os
import sys
import re
from tkinter import filedialog,Tk, mainloop    
###from tkinter.filedialog import askopenfilename
import argparse

from manage_survey_point import SurveyPointManager
from geo_address import GeoAddress
from sample_file import SampleFile

###gc.set_debug(gc.DEBUG_LEAK)
mw = Tk()       # MUST preceed users of SelectControl for tkinter vars ...Var()
                # e.g. SelectPlay -> ScoreWindow -> SelectControl
from crs_funs import str2bool
from select_trace import SlTrace

from select_control import SelectControl
from select_window import SelectWindow
from GoogleMapImage import GoogleMapImage
from scrolled_canvas import ScrolledCanvas
from mapping_control import MappingControl

def pgm_exit():
    if pt_mgr is not None:
        pt_mgr.save_favorite()
    SlTrace.lg("Properties File: %s"% SlTrace.getPropPath())
    SlTrace.lg("Log File: %s"% SlTrace.getLogPath())
    sys.exit(0)

###sys.setrecursionlimit(500)
cF = SelectControl(control_prefix="surveyor")       # Late comer for this pgm
image_file_name = None
width = 600         # Window width
height = width      # Window height
base_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
pgm_info = "%s %s\n" % (os.path.basename(sys.argv[0]), " ".join(sys.argv[1:]))
SlTrace.lg(pgm_info)
###SlTrace.setTraceFlag("get_next_val", 1)
trace = ""
undo_len=200           # Undo length (Note: includes message mcd
enlargeForRotate = True
mapRotate = 45.
profile_running = False
lat = 42.34718
long = -71.07317
lat_long = None
show_samples_lat_lon = False    # No lat/long for samples
test_lat_long = (lat,long)
address = None
test_address = "24 Chapman St., Watertown, MA, US"
map_file = None
test_map_file = '../out/gmi_ulA42_376371_O-71_187576_lRA42_369949_O-71_181274_640x640_sc1z19_h_mr45_AUG.png'
test_map_file = "C:/Users/raysm/workspace/python/PlantInvasion/out/gmi_ulA42_376000_O-71_177315_lRA42_375640_O-71_176507_640x640_sc1z22_h.png"
test_map_info = "C:/Users/raysm/workspace/python/PlantInvasion/out/gmi_ulA42_376000_O-71_177315_lRA42_375640_O-71_176507_640x640_sc1z22_h_png.imageinfo" 
trailfile = "C:/Users/raysm/workspace/python/PlantInvasion/new_data/trails_from_averaged_waypoints_CORRECTED_9nov2018_adj_20may2020.gpx"
infoFile = None

'''
def askopenfilename(**options):
    "Ask for a filename to open"

    return Open(**options).show()
'''


parser = argparse.ArgumentParser()

parser.add_argument('-a', '--address=', dest='address', default=address)
parser.add_argument('-g', '--enlargeforrotate', dest='enlargeForRotate', default=enlargeForRotate, action='store_true')
parser.add_argument('-m', '--mapfile=', dest='map_file', default=map_file)
parser.add_argument('-r', '--maprotate=', type=float, dest='mapRotate', default=mapRotate)
parser.add_argument('-i', '--infofile=', dest='infoFile', default=infoFile)
parser.add_argument('-f', '--image_file_name', '--file', dest='image_file_name', default=image_file_name)
parser.add_argument('-l', '--lat_long', dest='lat_long', default=lat_long)
parser.add_argument('--profile_running', type=str2bool, dest='profile_running', default=profile_running)
parser.add_argument('-s', '--show_ll', dest='show_samples_lat_lon',
                      default=show_samples_lat_lon)
parser.add_argument('--trace', dest='trace', default=trace)
parser.add_argument('--trailfile', dest='trailfile', default=trailfile)
parser.add_argument('--undo_len', type=int, dest='undo_len', default=undo_len)
parser.add_argument('-w', '--width=', type=int, dest='width', default=width)
parser.add_argument('-e', '--height=', type=int, dest='height', default=height)
args = parser.parse_args()             # or die "Illegal options"
SlTrace.lg("args: {}\n".format(args))
address = args.address
enlargeForRotate = args.enlargeForRotate
lat_long = args.lat_long
image_file_name = args.image_file_name
profile_running = args.profile_running
show_samples_lat_lon = args.show_samples_lat_lon
trace = args.trace
if trace:
    SlTrace.setFlags(trace)
undo_len = args.undo_len
width = args.width
height = args.height
map_file = args.map_file
if map_file == "TEST":
    map_file = test_map_file      # Use test file
mapRotate = args.mapRotate
trailfile = args.trailfile
infoFile = args.infoFile
width = args.width
height = args.height
if lat_long == "TEST":       # Set to test_...
    lat_long = test_lat_long
if address == "TEST":
    address = test_address
if image_file_name == "TEST":
    image_file_name = test_map_file
memory_trace = False    # Set true when tracing
        
mw.lift()
mw.attributes("-topmost", True)

def file_open():
    """
    Open image file
    """
    SlTrace.report("file_open - TBD")
    
def file_save():
    """ Save updated image file
    """
    
def map_place():
    """ Map a place
    """
    SlTrace.report("image_file - TBD")
    
def save_trail_file():
    """ Save Trail (GPX) File
    """
    if pt_mgr is not None:
        pt_mgr.save_trail_file()

gmi = None
sc = None
pt_mgr = None           # Point manager, set when ready

new_points = []
ulLat = 42.3760002
ulLong = -71.1773149
uLatLong = (ulLat, ulLong)

app = SelectWindow(mw,
                title="Surveyor",
                pgmExit=pgm_exit,
                cmd_proc=True,
                cmd_file=None,
                file_open=file_open,
                file_save=file_save,
                arrange_selection=False,
                )

samplefile = "../data/2018 05 12 Revised GPS coordinates of 32 sample plot centers.xlsx"
def add_sample_file():
    """ add trail file to display
    """
    global samplefile
    
    if sc is None or sc.gmi is None:
        return
    
    if samplefile is None:
        samplefile = filedialog.askopenfilename(
            initialdir= "../data",
            title = "Open Sample File",
            filetypes= (("sample files", "*.xlsx"),
                        ("all files", "*.*"))
                       )
        if samplefile is not None:
            SlTrace.report(f"No file selected")
            sys.exit(1)

    if not os.path.isabs(samplefile):
        samplefile = os.path.join("..", "data", samplefile)
        if not os.path.isabs(samplefile):
            samplefile = os.path.abspath(samplefile)
            if re.match(r'.*\.[^.]+$', samplefile) is None:
                samplefile += ".xlsx"         # Add default extension
    if not os.path.exists(samplefile):
        SlTrace.report(f"File {samplefile} not found")
        sys.exit(1)
        
    spx = SampleFile(samplefile)
    sc.gmi.addSamples(points=spx.get_points(), title=samplefile,
                      show_LL=show_samples_lat_lon)
    sc.set_size()
    sc.lower_image()        # Place map below points/lines
    if pt_mgr is not None:
        pt_mgr.add_point_list(spx, name="samples", title=samplefile)

def favorites():
    """ Shortcut to Mapping Control Favorites button
    """
    global map_ctl
    global pt_mgr
    
    if sc is None:
        return
    
    if pt_mgr is None:
        pt_mgr = SurveyPointManager(sc)
    if sc.pt_mgr is None:
        sc.set_pt_mgr(pt_mgr)
        
    if sc.map_ctl is None:
        sc.map_ctl = MappingControl(mgr=pt_mgr, address=test_address, enlargeForRotate=enlargeForRotate)
        
    sc.map_ctl.get_favorites()

def save_favorite():
    if pt_mgr is None:
        return
    
    pt_mgr.save_favorite()

def save_map_file():
    if pt_mgr is None:
        return
    
    pt_mgr.save_map_file()
    
def add_trail_file():
    """ add trail file to display
    """
    global trailfile
    
    if pt_mgr is not None:
        if pt_mgr.get_gmi() is None:
            return
        
    if trailfile is None or trailfile == "ASK":
        trailfile = filedialog.askopenfilename(
            initialdir= "../new_data",
            title = "Add Trail File",
            filetypes= (("Trail files", "*.gpx"),
                        ("all files", "*.*"))
                       )
    if trailfile is None:
        SlTrace.report(f"No file selected")
        sys.exit(1)
        
    if not os.path.exists(trailfile):
        SlTrace.report(f"File {trailfile} not found")
        sys.exit(1)
            
    pt_mgr.add_trail_file(trailfile)

def add_scale():
    """ Add Compass Rose to map
    """
    if pt_mgr is None:
        return
    
    pt_mgr.add_scale()

def add_scale_markers():
    """ Add Compass Rose to map
    """
    if pt_mgr is None:
        return
    
    pt_mgr.add_scale_markers()
    
def map_region():
    if pt_mgr is not None:
        if not pt_mgr.map_region():
            SlTrace.report("No region created")

def expand_region():
    if pt_mgr is not None:
        if not pt_mgr.expand_region():
            SlTrace.report("No region to expand")

def select_region():
    if pt_mgr is not None:
        if not pt_mgr.select_region():
            SlTrace.report("No region created")

def use_region():
    global sc
    
    if  pt_mgr is None:
        return
    
    pt_mgr.use_region()
    
def set_image():
    if sc is not None:
        sc.set_image()

def previous_map():
    if pt_mgr is None:
        return
    
    pt_mgr.previous_map()

def rotate_map():
    if pt_mgr is None:
        return
    
    pt_mgr.rotate_map()

def drag_map():
    pass

def use_map():
    pass
        
def tracking_update(changes):
    """ Tracking update processor
    :changes: list of changed items
    """
    pass        # TBD    
    
def track_points():
    global new_points    
    """ Add point next down click
    """
    if pt_mgr is not None:
        pt_mgr.show_tracking_control()

def do_map_file(file_name):
    SlTrace.lg(f"mapfile: {map_file}")
    ###width = 100
    ###height = 100
    SlTrace.lg(f"canvas: width={width} height={height}")
    sc = ScrolledCanvas(fileName=file_name, width=width, height=height, parent=app,
                        enlargeForRotate=enlargeForRotate)
    pt_mgr = SurveyPointManager(sc)

def do_lat_long(lat_long, xDim=40,  zoom=22, unit='m'):
    """ Get/create map file from latitude longitude pair
    :lat_long: (latitude,longitude) pair
    :xDim: x dimentsions in meters
    :zoom" Google maps precision 18 - coarse, 22 - high
    :unit: linear dimension default: meters
    :returns: map file name
    """
    global gmi
    
    ulLat, ulLong = lat_long
    gmi = GoogleMapImage(ulLat=ulLat, ulLong=ulLong, xDim=xDim, zoom=zoom, unit=unit,
                         enlargeForRotate=enlargeForRotate,
                         mapRotate=mapRotate)
    gmi.saveAugmented()             # Save file for reuse
    return  gmi.makeFileName()

    
def do_address(address):
    """ Get long latitude from address
    :address: string of address
    """
    if address == "ASK":
        map_ctl = MappingControl(mgr=pt_mgr, address=test_address, enlargeForRotate=enlargeForRotate)
        lat_long = map_ctl.get_location()
        if lat_long is None:
            loc_str = map_ctl.get_location_str()
            SlTrace.report(f"We can't find location:{loc_str}")
            return None
    else:    
        ga = GeoAddress()
        lat_long = ga.get_lat_long(address)
        if lat_long is None:
            SlTrace.report(f"Can't find address: {address}")
            return None
    
    return do_lat_long(lat_long)


menubar, filemenu = app.add_menu()
filemenu.add_command(label="Favorites", command=favorites)
filemenu.add_separator()
filemenu.add_command(label="Save Map", command=save_map_file)
filemenu.add_separator()
filemenu.add_command(label="Save Favorite", command=save_favorite)
menubar.add_cascade(label="Places/Maps", menu=filemenu)

menubar, filemenu = app.add_menu()
filemenu.add_command(label="Add Trail File", command=add_trail_file)
filemenu.add_command(label="Add Sample File", command=add_sample_file)
filemenu.add_separator()
filemenu.add_command(label="Add Scale", command=add_scale)
filemenu.add_separator()
filemenu.add_command(label="ADD MARKERS", command=add_scale_markers)
menubar.add_cascade(label="Add to Map", menu=filemenu)

menubar, filemenu = app.add_menu()
filemenu.add_command(label="Set Image", command=set_image)
filemenu.add_command(label="Save Trail File", command=save_trail_file)
filemenu.add_separator()
filemenu.add_command(label="Track Points", command=track_points)
menubar.add_cascade(label="Trail Operation", menu=filemenu)

menubar, filemenu = app.add_menu()
filemenu.add_command(label="Expand Region", command=expand_region)
filemenu.add_separator()
filemenu.add_command(label="Select Region", command=select_region)
filemenu.add_separator()
filemenu.add_command(label="Map Region", command=map_region)
filemenu.add_separator()
filemenu.add_command(label="USE Region", command=use_region)
menubar.add_cascade(label="Region Operation", menu=filemenu)

menubar, filemenu = app.add_menu()
filemenu.add_command(label="Previous Map", command=previous_map)
filemenu.add_separator()
filemenu.add_command(label="Rotate Map", command=rotate_map)
filemenu.add_separator()
filemenu.add_command(label="Drag Map", command=drag_map)
filemenu.add_separator()
filemenu.add_command(label="USE Map", command=use_map)
menubar.add_cascade(label="Arrange Map", menu=filemenu)


if map_file == "TEST":
    map_file = test_map_file
    
sc = ScrolledCanvas(fileName=map_file, width=width, height=height, parent=app,
                    enlargeForRotate=enlargeForRotate,
                    trailfile=trailfile)
pt_mgr = sc.get_pt_mgr()
map_ctl = sc.get_map_ctl()
if address is not None:
    if address == "ASK":
        address = None
    map_ctl.get_address(address)
elif lat_long is not None:
    map_ctl.get_address_ll(lat_long)
elif map_file is not None:
    if map_file == "ASK":
        map_file = filedialog.askopenfilename(
            initialdir= "../out",
            title = "Open Map File",
            filetypes= (("map files", "*.png"),
                        ("info files", "*.map_info"),
                        ("all files", "*.*"))
                       )
    if map_file is not None:
        do_map_file(map_file)
        
mainloop()
SlTrace.lg("After mainloop()")