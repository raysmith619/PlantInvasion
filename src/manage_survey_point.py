# manage_survey_point.py    27Apr2020  crs,
""" Point placement / manipulation management for surveying type operations
    The points are referenced in a GoogleMapImage

"""
import os
import sys
import re
from math import sqrt
from tkinter import font

from tkinter.filedialog import asksaveasfilename

from select_trace import SlTrace
from select_error import SelectError
from survey_trail import SurveyTrail
from survey_scale import SurveyMapScale
from point_place import PointPlace
from survey_point import SurveyPoint                
from tracking_control import TrackingControl
from canvas_coords import CanvasCoords
from GoogleMapImage import GoogleMapImage
from image_over_draw import ImageOverDraw
import scrolled_canvas
from compass_rose import CompassRose


class PointSelection:
    def __init__(self, point_list=None, name=None, title=None):
        self.point_list = point_list    # External object e.g. GPXFile, SampleFile
        self.name = name
        self.title = title
        self.inside_points = None   # list of points inside region display, if known
        self.selected_points = []   # selected points if any
    
class SurveyPointManager:
    """ Manipulate a list of points (SurveyPoint)
    """
    def __init__(self, scanvas,
                 compass_rose=None,
                 label=None, label_size=None,
                 display_size=None, select_size=None,
                 point_type=None, center_color=None, color=None, label_no=None,
                 point_id=None,
                 trailfile=None,
                 track_sc=True,
                 unit="m"):
        """ Setup point attributes
        :scanvas: canvas (ScrollableCanvas) on which points are positioned/displayed
        :compassRose: North indicator (location x-fract, y-fract, size-fract)
                    -1 => no compassRose
                    defalult: standard size/placement
        :display_size, select_size, point_type, center_color, color - default point attributes
                described in SurveyPoint
        :label_no: starting number for point labels <label><label_no>
                default: 1
        :track_sc:  track/display sc mouse motion
        :trailfile: trail file
        :unit: distance units default: "m"
        """
                       
        self.sc = scanvas
        self.compass_rose = CompassRose(compass_rose).live_obj()
        self.trailfile = trailfile
        self.trail = None                   # Currently loaded trail
        self.trail_title_tag = None         # canvas trail title display object, if one
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
        self.scales = []
        
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
        Only redisplay points that don't belong to 
        something else, being redisplayed, e.g. trail
        """
        other_points = {}
        if self.trail is not None:
            for tp in self.trail.get_points():
                other_points[tp.label] = tp
        gd = self.get_gmi().geoDraw
        gd.mark_image()
        for point in self.points:
            '''
            if point.label in other_points:
                continue
            '''
            point.redisplay()
        if self.compass_rose is not None:
            self.overlayCompassRose()
        if self.trail is not None:
            self.overlayTrail()
        if len(self.scales) > 0:
            for scale in self.scales:
                scale.redisplay()
        self.tr_ctl.redisplay()

    def get_region(self): 
        """ Get currently selected(tracked) region
        :returns: region (SurveyRegion) None if not one
        """
        return self.tr_ctl.get_region()

    def get_sc(self):
        return self.sc
        
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
        region_bearing = region.get_bearing()
        SlTrace.lg(f"Region bearing: {region_bearing}")
        region_gmi = GoogleMapImage(ulLat=max_lat, ulLong=min_long,
                           lrLat=min_lat, lrLong=max_long,
                           mapRotate=region_bearing,
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
            region_sc.gmi.addTrail(gpx, title=None)
        SlTrace.lg(f"Region bearing: {region_bearing:.2f}")

        region_sc.set_size()
        region_sc.lower_image()        # Place map below points/lines

        region_sc.size_image_to_canvas()
        return True

    def rotate_map(self, deg=None, incr=False, expand=None):
        """ Interactively rotate map in main display
        """
        gmi = self.get_gmi()
        image = gmi.rotateMap(deg=deg, incr=incr, expand=expand)
        self.sc.update_image(image)
        self.sc.size_image_to_canvas()
        self.sc.mark_canvas()
        self.redisplay()

    def previous_map(self):
        """ Put up previous map state
        """
        gD = self.get_geoDraw()
        gD.popMap()
                    
    def expand_region(self):
        """ expand most recently created region, if one, to
        fill display area, keeping aspect ration the same
        """
        gD = self.get_geoDraw()
        region = self.get_region()
        if region is None:
            SlTrace.report("No region selected")
            return False
        region_points = region.get_points()
        SlTrace.lg("\n Region Points")
        for point in region_points:
            point.snapshot()
        if not region.is_complete():
            SlTrace.report(f"Region is not complete")
            return False
        
        (ulLat, ulLong), (lrLat, lrLong) = region.ullr_ll()
        if SlTrace.trace("expand_points"):
            erp_color = "white"
            self.add_point(SurveyPoint(self, label="ER_ul", lat=ulLat,
                                       long=ulLong,
                                       color=erp_color))
            self.add_point(SurveyPoint(self, label="ER_lr", lat=lrLat,
                                       long=lrLong,
                                       color=erp_color))
        cc_dist = gD.geoDist((ulLat, ulLong), (lrLat, lrLong),  unit="m")
        SlTrace.lg(f"ul to lr dist: {cc_dist:.1f} meters")
        self.remove_points(region.get_points()) # Of no use and clutter drawing
        self.tr_ctl.restart_region()
        new_image = gD.expandRegion(ulLat, ulLong, lrLat, lrLong)
        self.sc.update_image(new_image)
        self.sc.size_image_to_canvas()
        self.sc.mark_canvas()
        ###gD.setLatLong()
        self.redisplay()
        return True
            
    def select_region(self):
        """ select most recently created region, if one
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
        title = "Region bounded by " + ", ".join([pt.label for pt in region_pts])
        region_bearing = region.get_bearing()
        SlTrace.lg(f"Region bearing: {region_bearing}")
        region_gmi = GoogleMapImage(gmi=gmi_base,
                            ulLat=max_lat, ulLong=min_long,
                            lrLat=min_lat, lrLong=max_long,
                            mapRotate=region_bearing)
        region_sc = scrolled_canvas.ScrolledCanvas(title=title,
                            pt_mgr=self,          # All with common pt_mgr
                            map_ctl=sc_base.map_ctl,
                            gmi=region_gmi, 
                            width=sc_base.width, height=sc_base.height)
        if not gmi_base.has_compass_rose():
            region_gmi.addCompassRose()       # Paste in to its image
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
            region_sc.gmi.addTrail(gpx, title=None)
        SlTrace.lg(f"Region bearing: {region_bearing:.2f}")

        region_sc.set_size()
        region_sc.lower_image()        # Place map below points/lines

        region_sc.size_image_to_canvas()
        return True

    def use_region(self):
        """ Use the selected region(viewed) as the main map
        """
        if len(self.mapped_regions) < 1:
            return self.sc              # No change
        
        SlTrace.lg("Using most recently selected/mapped region")        
        region_sc = self.mapped_regions[-1]
        self.sc.gmi = region_sc.gmi
        self.sc.pt_mgr = region_sc.pt_mgr
        self.sc.pt_mgr.redisplay()
                              
    def mouse_down(self, canvas_x, canvas_y):
        """ Capture/process mouse clicks in canvas
        :canvas_x: canvas x-coordinate
        :canvas_y: canvas y-coordinate
        """
        pc_lat, pc_long = self.sc.canvas_to_ll(canvas_x=canvas_x, canvas_y=canvas_y)
        SlTrace.lg(f"mouse_down: canvas_x={canvas_x:.0f} canvas_y={canvas_y:.0f}", "mouse")
        point = self.get_in(lat=pc_lat, long=pc_long)
        if point is not None:
            self.in_point_is_down = True
            self.in_point = point
            self.in_point_start = (pc_lat, pc_long)  # ref for movement
        else:
            point = self.make_point(lat=pc_lat, long=pc_long)
 
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

    def canvas_create_circle(self, xY, radius=None, **kwargs):
        """ create circle on canvas
        :xY: x,y center in pixels
        :radius: radius in pixels
        :fill: color
                default: "red"
        :returns: canvas object tag
        """
        canvas = self.get_canvas()
        if canvas is None:
            return
        
        if radius is None:
            radius = 2
            
        x, y = xY[0], xY[1]
        x1, y1 = x-radius, y-radius
        x2, y2 = x+radius, y+radius
        tag = canvas.create_oval(x1, y1, x2, y2, **kwargs)
        return tag
        
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
            
    def save_map_file(self, mapfile=None):
        """ Save updated map file
        :mapfile: trail file name
                default: ask for name
        """
        self.set_image()    # Set image updated  with overlays
        gmi = self.get_gmi()
        if gmi is None:
            return
        map_name = gmi.get_filename()
        
        initialfile = os.path.basename(map_name)
        if mapfile is None:
            mapfile = asksaveasfilename(
                initialdir= "../new_data",
                initialfile=initialfile,
                title = "New Map File",
                filetypes= (("Map files", "*.png"),
                            ("all files", "*.*"))
                           )
            if mapfile is None:
                SlTrace.report(f"No file selected")
                return False
            if re.match(r'.*\.[^.]+$', mapfile) is None:
                mapfile += ".png"         # Add default extension

        SlTrace.lg(f"Saving mapfile: {mapfile}")
        
        gmi.save(name=mapfile)
        
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

        ###Already announced in asksaveasfilename            
        ###if os.path.exists(trailfile):
        ###    SlTrace.report(f"File {trailfile} already exists")
        
        trail.save_file(trailfile)   

    def set_image(self):
        """ Set image, in preparation to save completed graphics file
        In genera, copy objects like trails which are canvas based objects to
        the image
        """
        self.iodraw.set_to_image(True)
        
        self.redisplay()
        self.get_sc().raise_image()
        
        self.iodraw.set_to_image(False)
        
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

    def get_mapRotate(self):
        """ Get current map rotation 0<= deg < 360
        """
        gmi = self.get_gmi()
        if gmi is None:
            return 0
        
        return gmi.get_mapRotate()
    
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

    def get_iodraw(self):
        """ Get ImageOverDraw instance, or create it
        """
        if hasattr(self, "iodraw") and self.iodraw is not None:
            return self.iodraw 
        
        
        sc = self.get_sc()
        if sc is None:
            raise SelectError("sc not ready")
        
        gD = self.get_geoDraw()
        if gD is None:
            raise SelectError("geoDraw not ready")
        
        self.iodraw = ImageOverDraw(sc=sc, geoDraw=gD)
        return self.iodraw

    def add_scale(self):
        """ Add scales to map
        """
        self.create_scales()
            
    def overlayCompassRose(self, compassRose=None):
        """
        Add orientation marker
        Like GeoDraw.add..., but overlay, to allow modification
        Stores canvas tags in self.compass_rose_tags
        :returns: list of tags created
        :compassRose: (x_fract, y_fract, len_fract) of x,y, length(smallest)
        :to_image: True --> place figure in image (permanent for saving)
                    False(default) --> place figure in canvas
        """
        SlTrace.lg("overlayCompassRose", "compass_rose")
        canvas = self.get_canvas()
        if canvas is None:
            return
        if compassRose is not None:
            self.compass_rose = CompassRose(compassRose).live_obj()
        if self.compass_rose is None:
            return
        
        iodraw = self.get_iodraw()
        iodraw.drawCompassRose(compassRose=self.compass_rose)
        
    def create_circle(self, xy, to_image=False,
                      radius=None,
                      fill=None,
                      **kwargs):
        """ Create a circle (on canvas or image)
        :xy: xy point
        :to_image: True -> place in image
        :radius: radius in pixels
        :fill: fill color
        :**kwargs: passed to create_circle or geoDraw.circle
        :returns: canvas tag only used if canvas
        """
        if not to_image:
            return self.canvas_create_circle((ap_canvas_x,ap_canvas_y),
                                       to_image=to_image,
                                       radius=5, fill=cent_color)

    def create_scales(self):
        """ Add new scale
        """
        scale =  SurveyMapScale(self, xYFract=(.2,.85), lengFract=.43, deg=0, unit="Feet")
        scale.display()
        self.scales.append(scale)
        scale = SurveyMapScale(self, xYFract=(.2,.9), lengFract=.5, deg=0, unit="Meters")
        scale.display()
        self.scales.append(scale)

    def add_scale_markers(self):
        """ Create special scales for scaling/positioning verification
        """
        tennis_court = False        
        ###tennis_court = True        
        ###third_to_home = False
        third_to_home = True
        football_sideline = False
        ###football_sideline = True
        iodraw = self.get_iodraw()
        
        if tennis_court:
            ptc = iodraw.getXY(latLong=(42.37332, -71.18349))
            th_deg = -iodraw.get_mapRotate()+8.0
            nw_corner_1 = iodraw.addToPoint(xY=ptc, leng=iodraw.meterToPixel(110), deg=th_deg)
            nw_corner = iodraw.addToPoint(xY=nw_corner_1, leng=iodraw.meterToPixel(54), deg=th_deg+90)
            ###pthird = iodraw.addToPoint(xY=pthird, leng=iodraw.meterToPixel(0.182), deg=th_deg)
            scale = SurveyMapScale(self,xY=nw_corner, deg=th_deg, unit='f',
                                    leng=iodraw.meterToPixel(100), tic_dir=-1, mapRelative=False)
            scale.display()
            self.scales.append(scale)
        
        if third_to_home:
            iodraw = self.get_iodraw()
            phome_ll = (42.3733323, -71.1827931)
            pthird_ll = (42.3734756, -71.1830477)
            scale = SurveyMapScale(self, latLong=pthird_ll, latLongEnd=phome_ll, unit='f',
                                    tic_dir=-1)
            scale.display()
            self.scales.append(scale)
            
        
        if football_sideline:
            goal_p = iodraw.getXY(latLong=(42.3736665, -71.18350))
            th_deg = -iodraw.get_mapRotate()+9.5+90
            goal_left_p = iodraw.addToPoint(xY=goal_p, leng=iodraw.meterToPixel(56.5), deg=th_deg)
            goal_left_p = iodraw.addToPoint(xY=goal_left_p, leng=iodraw.meterToPixel(-6.6), deg=th_deg+90)
            scale = SurveyMapScale(self, xY=goal_left_p, deg=th_deg, unit='y', leng=iodraw.meterToPixel(100))
            scale.display()
            self.scales.append(scale)

        
        
    def text(self, text, xY=None,pos=None,latLong=None, **kwargs):
        """
        Draw text, at position, defaulting to current pen position
        like GeoDraw, but overlay
        :returns: list of canvas tags
        """
        canvas = self.get_canvas()
        gmi = self.get_gmi()
        xY = gmi.getXY(xY=xY, pos=pos, latLong=latLong)
        x_image, y_image = xY
        p1c = self.get_canvas_coords(x_image=x_image, y_image=y_image)
        tag = canvas.create_text(p1c.canvas_x, p1c.canvas_y,
                                 text=text, **kwargs)
        return tag
 
    def lineSeg(self, xY=None, pos=None, latLong=None,
                xY2=None, pos2=None, latLong2=None,
                 leng=10, theta=None, deg=None, **kwargs):
        """
        Like GeoDraw but overlay
        :xY: x_image, y_image
        Draw line segment starting at given point
        position(xY or pos or latLong) and going to 
            2nd point:
                (xY2 or pos2 or latLong2)
                    or
                point 2 plus length leng at angle (theta radians or deg degrees)
            
        Extra named args are passed to Image.draw.line
        :returns: list of canvas tags
        """
        canvas = self.get_canvas()
        xY = self.getXY(xY=xY, pos=pos, latLong=latLong)
        if xY2 is not None or pos2 is not None or latLong2 is not None:
            new_xY = self.getXY(xY=xY2, pos=pos2, latLong=latLong2)
        else:
            new_xY = self.addToPoint(leng=leng, xY=xY, theta=theta, deg=deg)
        x_image, y_image = xY
        p1c = self.get_canvas_coords(x_image=x_image, y_image=y_image)
        x_image2, y_image2 = new_xY
        p2c = self.get_canvas_coords(x_image=x_image2, y_image=y_image2)
        tag = canvas.create_line(
                p1c.canvas_x, p1c.canvas_y, p2c.canvas_x, p2c.canvas_y,
                **kwargs)
        return tag
    
    def overlayTitle(self, title, xY=None, size=None, color=None, **kwargs):
        """ Like GeoDraw.addTitle, but overlay, to allow modification
        """
        canvas = self.get_canvas()
        self.remove_trail_title_display()
        if xY is None:
            xY = (self.getWidth()*.1, self.getHeight()*.05)
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
            if title is None:
                title = trail.title
        self.trail_width = 2.       # Trail width in meters
        self.max_dist_allowed = 150.
        trail_width = max(self.meterToPixel(self.trail_width), 2)
        trail = self.iodraw.drawTrail(trail=trail, title=title, color=color,
                                      color_points=color_points,
                                      line_width=trail_width,
                                      show_points=show_points)
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

    def get_geoDraw(self):
        return self.get_gmi().get_geoDraw()
    
    def get_canvas_coords(self, **kwargs):
        """ Shorthand to get CanvasCoords
        """
        return CanvasCoords(self.sc, **kwargs)

    def leave(self):
        """ Process cursor leaving canvas
        """
        if self.sc_point_place is not None:
            self.sc_point_place.remove_show_point()
            
    
    def ll_to_canvas(self, lat=None, long=None, trace=False):
        """ Convert Lat/Long to canvas x,y
        Transformation:
            1. Scale lat/Long offsets to unrotated canvas x,y Note that image has been
            resized to canvas.
            2. Rotate x,y to mapRotate
            
        Part of single purpose functions, replacing CanvasCoords
        
        :lat: latitude
        :long: Longitude
        :trace: trace operation - Debugging
        """
        return self.sc.ll_to_canvas(lat=lat, long=long, trace=trace)
    

    def get_canvas_height(self):
        """ Get our canvas width in pixels
        :returns: width in pixelst
        """
        return self.sc.get_canvas_height()

    def get_canvas_width(self):
        """ Get our canvas width in pixels
        :returns: width in pixelst
        """
        return self.sc.get_canvas_width()
    
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
        return self.sc.meterToPixel(meter)

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

    def show_point_tracking(self, *points):
        """ Display/redisplay tracking items/lines
        for points given.
        :ponts: zero or more args, each of which is a point or list of points
        """
        self.tr_ctl.show_point_tracking(*points)

    def hide_point_tracking(self, *points):
        """ Hide  tracking items/lines
        for points given.
        :ponts: zero or more args, each of which is a point or list of points
        """
        self.tr_ctl.hide_point_tracking(*points)

    def remove_point_tracking(self, point):
        """ Remove tracking from this point
        :point: point of interest
        """
        self.tr_ctl.remove_point_tracking(point)
        
    def remove_point(self, point):
        """ Remove point, and any associated tracking
        :point: point to remove
        """
        if point.label.lower() in self.points_by_label:
            for idx, pt in enumerate(self.points):
                if pt.point_id == point.point_id:
                    self.remove_point_tracking(pt)
                    del self.points[idx]
                    pt.delete()
                    break
            return pt
            
        return None
    
    def remove_points(self, points):
        """ Remove given points
        :points: list of points
        """
        for point in points:
            self.remove_point(point)