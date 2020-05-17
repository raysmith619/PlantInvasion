# point_manager.py    27Apr2020  crs,
""" Point placement / manipulation management for surveying type operations
    The points are referenced in a GoogleMapImage

"""
import os
import sys
import re
from tkinter import *

from select_trace import SlTrace
from select_error import SelectError
from gpx_file import GPXFile

from point_place import PointPlace
from survey_point import SurveyPoint                
from tracking_control import TrackingControl
from canvas_coords import CanvasCoords
from GoogleMapImage import GoogleMapImage
import scrolled_canvas

class PointSelection:
    def __init__(self, point_list=None, name=None, title=None):
        self.point_list = point_list
        self.name = name
        self.title = title
        self.inside_points = None   # list of points inside region display, if known
        self.selected_points = []   # selected points if any
                    
class SurveyPointManager:
    """ Manipulate a list of points (SurveyPoint)
    """
    def __init__(self, scanvas,
                 label=None, label_size=None,
                 display_size=None, select_size=None,
                 point_type=None, center_color=None, color=None, label_no=None,
                 point_id=None,
                 trailfile=None,
                 track_sc=True):
        """ Setup point attributes
        :scanvas: canvas (ScrollableCanvas) on which points are positioned/displayed
        :display_size, select_size, point_type, center_color, color - default point attributes
                described in SurveyPoint
        :label_no: starting number for point labels <label><label_no>
                default: 1
        :track_sc:  track/display sc mouse motion
        :trailfile: trail file
        """
                       
        self.sc = scanvas
        self.trailfile = trailfile
        self.mapped_regions = []            # canvases of regions displayed
        self.mapped_regions.append(scanvas) # [0] base region
        if label is None:
            label = "P" 
        self.label = label
        if label_size is None:
            label_size = 12 
        self.label_size = label_size
        if display_size is None:
            display_size = 10
        self.display_size = display_size
        if select_size is None:
            select_size = display_size-1
        self.select_size = select_size
        if point_type is None:
            point_type = SurveyPoint.POINT_TYPE_CIRCLE
        self.point_type = point_type
        if center_color is None:
            center_color = "white"
        self.center_color = center_color
        if color is None:
            color = "blue"
        self.color = color
        if label_no is None:
            label_no = 1
        self.label_no = label_no
        if point_id is None:
            point_id = 0
        self.point_id = point_id
        self.reset_points()
        self.track_sc = False           # Set True if tracking
        if track_sc is not None:
            self.track_cursor()
        self.in_point = None            # Set to point we're in, if any
        self.in_point_start = None      # Set to starting x,y
        self.in_point_is_down = False   # Set True while mouse is down
        self.doing_mouse_motion = False # Suppress multiple concurrent moves
        self.tr_ctl = TrackingControl(self)
        self.point_lists = {}           # Dictionary of point list e.g. SampleFile, GPXFile
        
    def track_cursor(self):
        """ start/restart tracking cursor
        """
        if not self.track_sc:
            self.sc_point_place = PointPlace(self.sc, title="Curser Tracking")
            self.sc.set_mouse_down_call(self.mouse_down)
            self.sc.set_mouse_double_down_call(self.mouse_double_down)
            self.sc.set_mouse_up_call(self.mouse_up)
            self.sc.set_mouse_move_call(self.mouse_motion)
            self.track_sc = True
            
    def reset_points(self):
        self.points = []
        self.points_by_label = {}
        self.label_no = 1       # Reset point labeling
        self.point_id = 0

    def resize(self):
        self.sc.update()
        self.redisplay()
        
        
    def redisplay(self):
        """ Redisplay points, tracking connections
        everything that resize might change
        """
        for point in self.points:
            point.redisplay()
        self.tr_ctl.redisplay()

    def get_region(self): 
        """ Get currently selected(tracked) region
        :returns: region (SurveyRegion) None if not one
        """
        return self.tr_ctl.get_region()
    
    def map_region(self):
        """ Map most recently created region, if one
        """
        region = self.get_region()
        if region is None:
            SlTrace.report("No region selected")
            return False
        
        if not region.is_complete():
            SlTrace.report(f"Region is not complete")
            return False
        region_pts = region.get_points()
        min_lat, max_lat, min_long, max_long = region.min_max_ll()
        gmi_base = self.sc.gmi
        sc_base = self.sc
        zoom = min(gmi_base.zoom+2, 22)
        title = "Region bounded by " + ", ".join([pt.label for pt in region_pts])
        region_gmi = GoogleMapImage(ulLat=max_lat, ulLong=min_long,
                           lrLat=min_lat, lrLong=max_long,
                           zoom=zoom)
        region_sc = scrolled_canvas.ScrolledCanvas(title=title,
                            pt_mgr=self,          # All with common pt_mgr
                            map_ctl=sc_base.map_ctl,
                            gmi=region_gmi, 
                            width=sc_base.width, height=sc_base.height)
        self.mapped_regions.append(region_sc)
        sample_selection = self.get_point_list("samples")
        if sample_selection is not None:
            spx = sample_selection.point_list
            region_sc.gmi.addSamples(points=spx.get_points(), title="")

        trail_selection = self.get_point_list("trails")
        if trail_selection is not None:
            gpx = trail_selection.point_list
            title = trail_selection.title
            trail_points = gpx.get_points()
            inside_points = region.get_inside_points(trail_points)
            trail_selection.inside_points = inside_points
            region_sc.gmi.addTrail(points=trail_points, title=None)

        region_sc.set_size()
        region_sc.lower_image()        # Place map below points/lines

        region_sc.size_image_to_canvas()
        return True
                      
    def mouse_down(self, canvas_x, canvas_y):
        """ Capture/process mouse clicks in canvas
        :canvas_x: canvas x-coordinate
        :canvas_y: canvas y-coordinate
        """
        pc = CanvasCoords(self.sc, canvas_x=canvas_x, canvas_y=canvas_y)
        SlTrace.lg(f"mouse_down: canvas_x={canvas_x:.0f} canvas_y={canvas_y:.0f}", "mouse")
        point = self.get_in(lat=pc.lat, long=pc.long)
        if point is not None:
            self.in_point_is_down = True
            self.in_point = point
            self.in_point_start = (pc.lat, pc.long)  # ref for movement
        else:
            point = self.add_point(SurveyPoint(self, lat=pc.lat, long=pc.long))
            self.in_point_is_down = True
            self.in_point = point
            self.in_point_start = (pc.lat, pc.long)

    def mouse_double_down(self, canvas_x, canvas_y):
        """ Capture/process double click
        If we have a region of 3 or more points close region (connect end to beginning)
        :canvas_x:    x-coordinate
        :canvas_y:    y-coordinate
        """
        _ = canvas_x
        _ = canvas_y
        if self.tr_ctl.complete_region():
            return              # Region was completed
        

    def mouse_up(self, canvas_x, canvas_y):            
        """ Capture/process mouse up - Add new point if 
        :canvas_x: x-coordinate
        :canvas_y: y-coorcinate
        """
        _ = canvas_x            # uused
        _ = canvas_y            # unused
        self.in_point = None
        self.in_point_is_down = False
        
    def mouse_motion(self, canvas_x, canvas_y):
        """ Capture/process mouse move in canvas
        :canvas_x: canvas x-coordinate
        :canvas_y: canvas y-coordinate
        """
        ###if self.doing_mouse_motion:
        ###    return          # Block multiple calls
        pc = CanvasCoords(self.sc, canvas_x=canvas_x, canvas_y=canvas_y)
        pc_lat = pc.lat
        pc_long = pc.long
        self.doing_mouse_motion = True
        if self.in_point is not None and self.in_point_is_down:
            SlTrace.lg(f"mouse_motion(in_point): canvas_x,y={canvas_x:.0f}, {canvas_y:.0f}", "mouse_motion")
            point = self.in_point
            if self.in_point_start is not None:
                lat_start = self.in_point_start[0]
                long_start = self.in_point_start[1]
                lat_delta = pc_lat-lat_start
                long_delta = pc_long-long_start
                lat_new = lat_start + lat_delta
                long_new = long_start + long_delta
                SlTrace.lg(f"  lat,long_start: {lat_start:.6f}, {long_start:.6f}"
                           f" lat_delta:{lat_delta:.6f}, {long_delta:.6f} lat,long_new:{lat_new:.6f},{long_new:.6f}", "mouse_motion")
                point.move(lat=lat_new,  long=long_new)
        else:
            if self.track_sc:
                self.sc_track_update(canvas_x, canvas_y)
        ###self.doing_mouse_motion = False
        
    def sc_track_update(self, canvas_x, canvas_y):
        """ Update sc tracking display
        :canvas_x:  x-coordinate
        :canvas_y:  y-coordinate
        """
        self.sc_point_place.motion_update(canvas_x, canvas_y)

    def show_tracking_control(self):
        """ Bring or re-bring tracking control to view
        """
        self.track_cursor()
        self.tr_ctl = TrackingControl(self)
                
    def change_cursor_info(self, cursor_info):
        self.track_cursor()
        self.sc_point_place.change_cursor_info(cursor_info)
            
    def change_maptype(self, maptype):
        self.sc.change_maptype(maptype)
            
    def change_unit(self, unit):
        self.sc_point_place.change_unit(unit)
            
            
    def clear_points(self):
        """ remove points
        """
        self.tr_ctl.clear_tracking()       # First clear tracking
        for pt in self.points:
            pt.delete()
        self.reset_points()
                    
    def add_point(self, point, track=True):
        """ Add new point to list
        Checks for unique name - error if pre-existing named point
        :point: point to be env_added
        :track: track point, default: True
        :returns: added point
        """
        point_label = point.label.lower()
        if point_label in self.points_by_label:
            raise SelectError(f"duplicate point name {point_label} in points list")
        
        self.points.append(point)
        self.points_by_label[point_label] = point
        point.display()
        if track:
            self.tr_ctl.added_point()
        
        return point

    def add_point_list(self, point_list, name=None, title=None):
        """ Add point list for future access
        :point_list: point list object (SampleFile, GPXFile))
        :name: name (unique) of list (sample, trail)
        :title: title, often file name
        """
        self.point_lists[name] = PointSelection(point_list, name=name, title=title)

    def get_point_list(self, name):
        """ Get point list, if present
        :name: name of point list
        :returns: point list, if present else None
        """
        if name in self.point_lists:
            return self.point_lists[name]
        
        return None
    
    def add_trail_file(self, trailfile=None):
        """ Add trail file, asking if none
        :trailfile: trail file name
                default: ask for name
        """
        sc = self.sc
        if trailfile is None:
            point_selection = self.get_point_list("trails")
            if point_selection is not None:
                gpx = point_selection.point_list
            else:
                trailfile = filedialog.askopenfilename(
                    initialdir= "../data/trail_system_files",
                    title = "Open trail File",
                    filetypes= (("trail files", "*.gpx"),
                                ("all files", "*.*"))
                               )
                if trailfile is not None:
                    SlTrace.report(f"No file selected")
                    return False
        
        else:            
            if not os.path.isabs(trailfile):
                trailfile = os.path.join("..", "data", "trail_system_files", trailfile)
                if not os.path.isabs(trailfile):
                    trailfile = os.path.abspath(trailfile)
                    if re.match(r'.*\.[^.]+$', trailfile) is None:
                        trailfile += ".gpx"         # Add default extension
            if not os.path.exists(trailfile):
                SlTrace.report(f"File {trailfile} not found")
                return False
            gpx = GPXFile(trailfile)
        self.add_point_list(gpx, name="trails", title=trailfile)
        sc.gmi.addTrail(gpx, title=trailfile,
                        keep_outside=False)
        sc.set_size()
        sc.lower_image()        # Place map below points/lines
        return True

    def get_canvas(self):
        """ Get Canvas type object
        """
        return self.sc.get_canvas()
    
    def get_in(self, lat=None, long=None):
        """ Return point if onewithin selection area
        :lat: latitude 
        :long: longitude
        :returns: first if any, else None
        """
        for point in self.points:
            if point.is_in(lat=lat,long=long):
                return point
            
        return None
    
    def get_points(self):
        """ Get our points
        :returns: our point list
        """
        return self.points
    
    def get_point_labeled(self, label):
        """ Get point named (label)
        CASE INSENSITIVE COMPARE
        :name: name (label)
        :returns: point if found, else None
        """
        point_label = label.lower()
        if point_label in self.points_by_label:
            return self.points_by_label[point_label]
            
        return None
    
    def get_ins(self, x, y):
        """ Return points within selection area(s)
        :x: x-Coordinate 
        :y: y-Coordinate
        :returns: first if any, else None
        """
        points_in = []
        for point in self.points:
            if point.is_in(x,y):
                points_in.append(point)
                
        return points_in


    def remove_point(self, point):
        """ Remove point
        :point: point to remove
        """
        ids = [self.points[idx].point_id for idx in range(len(self.points))]
        for idx in ids:
            pt = self.points[idx]
            if pt.point_id == point.point_id:
                pt.delete()
                del self.points[idx]
                return pt
            
        return None