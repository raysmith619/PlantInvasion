# point_manager.py    27Apr2020  crs,
""" Point placement / manipulation management for surveying type operations
    The points are referenced in a GoogleMapImage

"""
import os
import sys
import re
from tkinter import *
from tkinter.filedialog import asksaveasfilename

from select_trace import SlTrace
from select_error import SelectError
from survey_trail import SurveyTrail

from point_place import PointPlace
from survey_point import SurveyPoint                
from tracking_control import TrackingControl
from canvas_coords import CanvasCoords
from GoogleMapImage import GoogleMapImage
import scrolled_canvas

class PointSelection:
    def __init__(self, point_list=None, name=None, title=None):
        self.point_list = point_list    # External object e.g. GPXFile, SampleFile
        self.name = name
        self.title = title
        self.inside_points = None   # list of points inside region display, if known
        self.selected_points = []   # selected points if any

class SelectTrail:
    """ Trail information
    to support loading, saving, manipulation of trails
    """
    def __init__(self, point_selection, segments=None):
        """ Setup trail info
        :point_selection: base info (PointSelection)
        :trail_segments: internal segments (SurveySegment)
        """
        self.point_selection = point_selection
        if segments is None:
            segments = []
        self.segments = segments
    
    
    def add_points(self, *points):
        """ Add point(s) to segment
        :pts: zero or more args, each of which is a point or list of points
         (GPXPoint) to add
        """
        for pts in points: 
            if not isinstance(pts, list):
                pts = [pts]         # Make list of one
            self.points.extend(pts)
            
    def get_points(self):
        return self.points
    
class SurveyPointManager:
    """ Manipulate a list of points (SurveyPoint)
    """
    def __init__(self, scanvas,
                 label=None, label_size=None,
                 display_size=None, select_size=None,
                 point_type=None, center_color=None, color=None, label_no=None,
                 point_id=None,
                 trailfile=None,
                 track_sc=True,
                 unit="m"):
        """ Setup point attributes
        :scanvas: canvas (ScrollableCanvas) on which points are positioned/displayed
        :display_size, select_size, point_type, center_color, color - default point attributes
                described in SurveyPoint
        :label_no: starting number for point labels <label><label_no>
                default: 1
        :track_sc:  track/display sc mouse motion
        :trailfile: trail file
        :unit: distance units default: "m"
        """
                       
        self.sc = scanvas
        self.trailfile = trailfile
        self.trail = None                   # Currently loaded trail
        self.trail_segment = None           # Currently processed trail segment
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
        if track_sc:
            self.track_cursor()
        self.in_point = None            # Set to point we're in, if any
        self.in_point_start = None      # Set to starting x,y
        self.in_point_is_down = False   # Set True while mouse is down
        self.doing_mouse_motion = False # Suppress multiple concurrent moves
        self.unit = unit
        self.tr_ctl = TrackingControl(self)
        self.point_lists = {}           # Dictionary of point list e.g. SampleFile, GPXFile
        
    def track_cursor(self):
        """ start/restart tracking cursor
        """
        if not self.track_sc:
            self.sc_point_place = PointPlace(self.sc, title="Cursor Tracking")
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

    def restart_region(self):
        """ Restart region collection (with next point)
        """
        self.tr_ctl.restart_region()
        
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
            point = self.make_point(lat=pc.lat, long=pc.long)
 
    def make_point(self, lat=None, long=None):
        """ Create appropriate point for mouse click with current tracking state
        :lat: latitude
        :long: longitude
        :returns: point (SurveyPoint)
        """
        return self.tr_ctl.make_point(lat=lat, long=long)
    
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
            self.tr_ctl.added_point(point)
        
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
    
    def add_trail_file(self, trailfile=None, show_points=False):
        """ Add trail file, asking if none
        :trailfile: trail file name
                default: ask for name
        :show_points: mark trail points
                        default: False - don't show points
        :returns: trail if OK, else None
                sets self.trail
        """
        self.delete_trail()
        trail = SurveyTrail(self, file_name=trailfile, show_points=show_points)
        self.add_point_list(trail, name="trails", title=trailfile)
        self.overlayTrail(trail, title=trailfile)
        self.tr_ctl.trail = self.trail = trail      # synchronize tracking control
        return trail

    def delete_trail(self):
        """ Remove trail, clearing display
        """
        if self.trail is not None:    
            self.trail.delete()
            self.trail = None
            self.trail_segment = None
            self.tr_ctl.trail = None        # Synchronize with tracking
            self.tr_ctl.trail_segment = None
            
    def save_trail_file(self, trailfile=None):
        """ Save updated trail file (From get_point_list("trails")
        :trailfile: trail file name
                default: ask for name
        """
        trail = self.trail
        if trail is None:
            return
        
        initialfile = os.path.basename(trail.file_name)
        if trailfile is None:
            trailfile = asksaveasfilename(
                initialdir= "../new_data",
                initialfile=initialfile,
                title = "New Trail File",
                filetypes= (("trail files", "*.gpx"),
                            ("all files", "*.*"))
                           )
            if trailfile is None:
                SlTrace.report(f"No file selected")
                return False
            
        if os.path.exists(trailfile):
            SlTrace.report(f"File {trailfile} already exists")
        
        trail.save_file(trailfile)   
        

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


    def overlayTitle(self, title, xY=None, size=None, color=None, **kwargs):
        """ Like GeoDraw.addTitle, but overlay, to allow modification
        """
        canvas = self.get_canvas()
        if xY is None:
            title_xy = (self.getWidth()*.1, self.getHeight()*.05)
        if size is None:
            size = 16
        if color is None:
            color = "white"
        title_font = ("tahoma", size)
        title_xy = xY
        self.trail_title_tag = canvas.create_text(title_xy,
                                    font=title_font,
                                     text=title, fill=color)

    def overlayTrail(self, trail=None, title=None, color=None,
                     color_points=None,
                     show_points=False):
        """ Display trail in the same manor as mgr.sc.addTrail()
        but as an overlay, not changing the image, so that the
        points and links can be dynamicly changed
        :trail: trail info (SurveyTrail)
        :title: title (may be point file full path)
        :color: trail color default: orange
        :show_points: Show points, default: False - points not shown
        "color_points" points color default: same as color
        :keep_outside: Keep points even if outside region
                further back than self.max_dist_allowed,
                False: skip points outside region
                default: keep
        :returns: trail (SurveyTrail) overlaid
        """
        if color is None:
            color = "orange"
        if color_points is None:
            color_points = "black"
            
        if trail is None:
            trail_selection = self.get_point_list("trails")
            if trail_selection is None:
                SlTrace.lg("Trail added")
                self.add_trail_file(self.trailfile)
                trail_selection = self.get_point_list("trails")
            trail = trail_selection.point_list
        if title is not None:
            self.trail_title = os.path.basename(title)
            title_xy = (self.getWidth()*.5, self.getHeight()*.05)
            self.overlayTitle(self.trail_title, xY=title_xy)
        self.trail_width = 2.       # Trail width in meters
        self.max_dist_allowed = 150.
        line_width = int(self.meterToPixel(self.trail_width))
        prev_point = None
        for track in trail.get_segments():
            track_points = track.get_points()
            for point_no, point in enumerate(track_points, start=1):
                if point_no > 1:
                    self.track_two_points(prev_point, point,
                        color=color, width=line_width, display_monitor=False,
                        line_type="line")
                    if show_points:
                        prev_point.display(displayed=True, color=color_points)        # Place on top of line segments
                        point.display(displayed=True, color=color_points)
                    else:
                        # Use as "rounding at segment joining
                        ###prev_point.display(displayed=True, color=color)        # Place on top of line segments
                        ###point.display(displayed=True, color=color)
                        pass                        
                prev_point = point
        sc = self.sc
        sc.set_size()
        sc.lower_image()        # Place map below points/lines
        return trail
    
    def track_two_points(self, point1, point2,
                         color=None, width=None,
                         line_type=None,
                         display_monitor=None):
        """ Track (join) two points might be considered an edge
        in crs_points
        :point1: first point
        :point2: second point
        :color: color of connecting line
        :line_type: type of connection line
        :width: with of line in pixels
        :display_monitor: show connection attributes in monitor
            default: display
        """
        self.tr_ctl.track_two_points(point1, point2, color=color,
                                     width=width, line_type=line_type,
                                     display_monitor=display_monitor)

    def get_gmi(self):
        return self.sc.gmi
    
    def getHeight(self):
        """ via GoogleMapImage
        """
        gmi = self.get_gmi()
        return gmi.getHeight()

    def getWidth(self):
        """ via GoogleMapImage
        """
        gmi = self.get_gmi()
        return gmi.getWidth()

    def meterToPixel(self, meter):
        """ via GoogleMapImage
        """
        gmi = self.get_gmi()
        return gmi.meterToPixel(meter)

    def hide_point(self, point):
        """ Make point invisible, if not already
        :point: point to see
        """
        point.display(displayed=False)
        self.tr_ctl.show_point_tracking(point)


    def show_point(self, point):
        """ Make point visible, if not already
        :point: point to see
        """
        self.tr_ctl.show_point_tracking(point)  # In case changed
        point.display(displayed=True)

    def remove_point(self, point):
        """ Remove point, and any associated tracking
        :point: point to remove
        """
        if point.label.lower() in self.points_by_label:
            for idx, pt in enumerate(self.points):
                if pt.point_id == point.point_id:
                    self.tr_ctl.remove_point_tracking(pt)
                    del self.points[idx]
                    pt.delete()
                    break
            return pt
            
        return None