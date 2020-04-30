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
"""
"""
Created on October 30, 2018

@author: Charles Raymond Smith
"""
import os
from tkinter import *    
from tkinter.filedialog import askopenfilename
import argparse

from survey_point_manager import SurveyPointManager
from point_place import PointPlace

###gc.set_debug(gc.DEBUG_LEAK)
mw = Tk()       # MUST preceed users of SelectControl for tkinter vars ...Var()
                # e.g. SelectPlay -> ScoreWindow -> SelectControl
from crs_funs import str2bool
from select_error import SelectError
from select_trace import SlTrace

from select_control import SelectControl
from select_window import SelectWindow
from GoogleMapImage import GoogleMapImage
from scrolled_canvas import ScrolledCanvas
from tracking_control import TrackingControl

def pgm_exit():
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
profile_running = False

test_mapFile = '../out/gmi_ulA42_376371_O-71_187576_lRA42_369949_O-71_181274_640x640_sc1z19_h_mr45_AUG.png'
mapFile = r"C:\Users\raysm\workspace\python\PlantInvasion\out\gmi_ulA42_376000_O-71_177315_lRA42_375640_O-71_176507_640x640_sc1z22_h.png"
mapInfo = r"C:\Users\raysm\workspace\python\PlantInvasion\out\gmi_ulA42_376000_O-71_177315_lRA42_375640_O-71_176507_640x640_sc1z22_h_png.imageinfo" 
infoFile = None


def askopenfilename(**options):
    "Ask for a filename to open"

    return Open(**options).show()


parser = argparse.ArgumentParser()

parser.add_argument('-m', '--mapfile=', dest='mapFile', default=mapFile)
parser.add_argument('-i', '--infofile=', dest='infoFile', default=infoFile)
parser.add_argument('-f', '--image_file_name', '--file', dest='image_file_name', default=image_file_name)
parser.add_argument('--profile_running', type=str2bool, dest='profile_running', default=profile_running)
parser.add_argument('--trace', dest='trace', default=trace)
parser.add_argument('--undo_len', type=int, dest='undo_len', default=undo_len)
parser.add_argument('-w', '--width=', type=int, dest='width', default=width)
parser.add_argument('-e', '--height=', type=int, dest='height', default=height)
args = parser.parse_args()             # or die "Illegal options"
SlTrace.lg("args: {}\n".format(args))
image_file_name = args.image_file_name
profile_running = args.profile_running
trace = args.trace
if trace:
    SlTrace.setFlags(trace)
undo_len = args.undo_len
width = args.width
height = args.height

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
    
def image_file():
    """ Get new image file
    """
    SlTrace.report("image_file - TBD")
    
def adjust_view():
    """ Adjust view
    """
    SlTrace.report("Adjust View - TBD")

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

def tracking_update(changes):
    """ Tracking update processor
    :changes: list of changed items
    """
    pass        # TBD    
    
def track_points():
    global new_points    
    """ Add point next down click
    """
    if pt_mgr is None:
        return
    
    TrackingControl(pt_mgr, tracking_update=tracking_update)
    
    
app.add_menu_command("ImageFile", image_file)
app.add_menu_separator()
app.add_menu_command("Adjust View", adjust_view)
app.add_menu_command("Track Points", track_points)

if mapFile is None:
    mapFile = askopenfilename() # show an "Open" dialog box and return the path to the selected file
SlTrace.lg(f"mapfile: {mapFile}")
mapFile = args.mapFile
if mapFile == "TEST":
    mapFile = test_mapFile      # Use test file
infoFile = args.infoFile
width = args.width
height = args.height

###Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
if mapFile is None:
    mapFile = askopenfilename() # show an "Open" dialog box and return the path to the selected file
SlTrace.lg(f"mapfile: {mapFile}")
###width = 100
###height = 100
SlTrace.lg(f"canvas: width={width} height={height}")
sc = ScrolledCanvas(mapFile, width=width, height=height)
pt_mgr = SurveyPointManager(sc)
mainloop()
SlTrace.lg("After mainloop()")