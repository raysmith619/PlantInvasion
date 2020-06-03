# track_points.py    29Apr2020  crs
"""
Facilitate tracking single point, using PointPlace
Facilitate tracking point pairs using PointPlaceTwo

Keeps a list of tracked points
Keeps a list of tracked point-pairs
"""
import os

from tkinter import *

from select_trace import SlTrace
from select_control_window import SelectControlWindow
from point_place import PointPlace
from point_place_two import PointPlaceTwo
from select_list import SelectList        # TEMP - select_list will be extended
from survey_point import SurveyPoint
from survey_region import SurveyRegion

class TrackingControl(SelectControlWindow):
    """ Collection of point selection controls
    """
    CONTROL_NAME_PREFIX = "tracking_control"
    DEF_WIN_X = 500
    DEF_WIN_Y = 300
    
        
            
    def __init__(self, mgr,
                 title=None, control_prefix=None, 
                 central_control=None,
                 tracking_update=None,
                 unit='f',
                 auto_tracking="adjacent_pairs",
                 connection_line="line",
                 connection_line_color="red",
                 connection_line_width = 2,
                 cursor_info = "lat_long",
                 **kwargs):
        """ Initialize subclassed SelectControlWindow
             Setup score /undo/redo window
             :mgr: tracking point manager
             :mw: main window if one
        """
        self.mgr = mgr
        if title is None:
            title = "Tracking Control"
        if control_prefix is None:
            control_prefix = TrackingControl.CONTROL_NAME_PREFIX
        self.central_control = central_control
        self.tracking_update = tracking_update
        self.connection_line = connection_line
        self.connection_line_color = connection_line_color
        self.connection_line_width = connection_line_width
        self.cursor_info = cursor_info
        self.unit = unit
        self.auto_tracking = auto_tracking
        self.trail = None
        self.trail_segment = None
        self.tracked_items = []
        self.current_region = None  # list of points in order, else None
        self.regions = []       # list of completed regions, each a list of points
        self.px_fmt = ".0f"             # pixel format
        self.ll_fmt = ".7f"             # longitude/latitude format
        self.dis_fmt = ".1f"             # linear format
        super().__init__(title=title, control_prefix=control_prefix,
                       **kwargs)
        self.control_display()

    def set(self):
        self.set_vals()
        if self.set_cmd is not None:
            self.set_cmd(self)

    def set_set_cmd(self, cmd):
        """ Setup / clear Set button command
        """
        self.set_cmd = cmd
            
    def set_play_control(self, play_control):
        """ Link ourselves to the display
        """
        self.play_control = play_control
        
            
    def control_display(self):
        """ display /redisplay controls to enable
        entry / modification
        """


        super().control_display()       # Do base work        
        
        controls_frame = self.top_frame
        controls_frame.pack(side="top", fill="x", expand=True)
        self.controls_frame = controls_frame

        progressive_connection_frame = Frame(controls_frame)
        self.set_fields(progressive_connection_frame, "auto_tracking", "Auto-Track")
        self.set_radio_button(field="auto_track", label="none", command=self.change_auto_tracking,
                              value="none", set_value=self.auto_tracking)
        self.set_radio_button(field="auto_track", label="adjacent_pairs::1-2,2-3", value="adjacent_pairs",
                              command=self.change_auto_tracking)
        self.set_radio_button(field="auto_track", label="separate pairs: 1-2,3-4", value="separate_pairs",
                              command=self.change_auto_tracking)
        self.set_radio_button(field="auto_track", label="every point: 1,2,3,4", value="every_point",
                              command=self.change_auto_tracking)
        self.set_radio_button(field="auto_track", label="add to trail", value="add_to_trail",
                              command=self.change_auto_tracking)
        
        trail_control_frame = Frame(controls_frame)
        self.set_fields(trail_control_frame, "trail_control", "Trail")
        self.set_button(trail_control_frame, "show_trail_points", "Show Points",
                         command=self.show_trail_points)
        self.set_button(trail_control_frame, "hide_trail_points", "Hide Points",
                         command=self.hide_trail_points)
        self.set_button(trail_control_frame, "delete_trail_points", "Delete Trail Points",
                         command=self.delete_trail_points_chosen)
        self.set_button(trail_control_frame, "add_start_trail", "Add/Start Trail Section",
                         command=self.add_start_trail_segment)
        self.set_entry(field="trail_number", label="Trail Number", value="", width=3)
        
        region_control_frame = Frame(controls_frame)
        self.set_fields(region_control_frame, "region_control", "Region")
        self.set_button(region_control_frame, "complete_region", "Complete Region",
                         command=self.complete_region)
        self.set_button(region_control_frame, "show_trail_points", "Show Trail Points",
                         command=self.show_region_trail_points)
        self.set_button(region_control_frame, "restart_region", "Restart Region",
                         command=self.restart_region)
        self.set_button(region_control_frame, "clear_tracking", "Clear Tracking",
                         command=self.clear_tracking)
        self.set_button(region_control_frame, "clear_all_points", "Clear ALL Points",
                         command=self.clear_points)
        
        single_point_frame = Frame(controls_frame)
        self.set_fields(single_point_frame, "single_point", title="Single Point")
        self.set_button(field="track_one_point", label="Track", command=self.track_one_point_chosen)
        self.set_entry(field="single_point_name", label="name", value="P1", width=4)
        self.set_sep()
        self.set_button(field="untrack_point", label="Un-track", command=self.untrack_one_point)

        two_point_frame = Frame(controls_frame)
        self.set_fields(two_point_frame, "two_points", title="Two points")
        self.set_button(field="track_two_points", label="Track", command=self.track_two_points_chosen)
        self.set_entry(field="first_point_name", label="first point", value="P1", width=4)
        self.set_entry(field="second_point_name", label="second point", value="P2", width=4)
        self.set_sep()
        self.set_button(field="untrack_points", label="Un-track", command=self.untrack_two_points)

        point_file_frame = Frame(controls_frame)
        self.set_fields(point_file_frame, "point_lists", title="Point Lists")
        self.set_button(field="samples", label="Samples", command=self.track_samples)
        self.set_button(field="trails", label="Trails", command=self.track_trails)

        connection_frame = Frame(controls_frame)
        self.set_fields(connection_frame, "connection", title="Connection Line")
        self.set_radio_button(field="line", label="none", command=self.change_connection_line,
                              set_value=self.connection_line)
        self.set_radio_button(field="line", label="line", command=self.change_connection_line)
        self.set_radio_button(field="line", label="i_bar", command=self.change_connection_line)
        self.set_fields(connection_frame, "line_attributes")
        self.set_entry(field="width", label="Width", value=self.connection_line_width, width=2)
        self.set_entry(field="color", label="Color", value=self.connection_line_color, width=10)

        unit_frame = Frame(controls_frame)
        self.set_fields(unit_frame, "distance_units", title="distance units")   # Value should match self.unit
        self.set_radio_button(frame=unit_frame, field="unit", label="meter", value= "m", command=self.change_unit,
                               set_value=self.unit)
        self.set_radio_button(frame=unit_frame, field="unit", label="yard", value= "y", command=self.change_unit)
        self.set_radio_button(frame=unit_frame, field="unit", label="foot", value= "f", command=self.change_unit)
        self.set_radio_button(frame=unit_frame, field="unit", label="Smoot", value= "s", command=self.change_unit)

        cursor_track_frame = Frame(controls_frame)
        self.set_fields(cursor_track_frame, "cursor", title="Cursor")
        self.set_radio_button(field="info", label="None", value="none", command=self.change_cursor_info,
                              set_value=self.cursor_info)
        self.set_radio_button(field="info", label="Latitude/longitude", value="lat_long", command=self.change_cursor_info)
        self.set_radio_button(field="info", label="Distance", value="dist", command=self.change_cursor_info)
        self.set_radio_button(field="info", label="Image", value="image", command=self.change_cursor_info)
        self.set_radio_button(field="info", label="Canvas", value="canvas", command=self.change_cursor_info)
        
        self.arrange_windows()
        if not self.display:
            self.hide_window()
            
    def clear_points(self):
        """ remove points
        """
        self.clear_tracking()       # First clear tracking
        self.mgr.clear_points()
            
    def clear_tracking(self):
        """ Clear tracking items
        """
        for tracked in self.tracked_items:
            tracked.destroy()
        self.tracked_items = []
            
    def redisplay(self):
        """ Clear tracking items
        """
        for tracked in self.tracked_items:
            tracked.redisplay()

    def meterToPixel(self, meter):
        """ via GoogleMapImage
        """
        return self.mgr.meterToPixel(meter)

    
    def add_trail_file(self, trailfile=None, show_points=False):
        """ Add trail file, asking if none
        :trailfile: trail file name
                default: ask for name
        :show_points: mark trail points
                        default: False - don't show points
        :returns: trail (SurveyTrail) if OK, else None
        """
        self.trail = self.mgr.add_trail_file(trailfile=trailfile, show_points=show_points)
        return self.trail

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
        self.trail = self.mgr.overlayTrail(trail=trail, title=title, color=color,
                     color_points=color_points,
                     show_points=show_points)
        return self.trail
    
    def add_start_trail_segment(self):
        """ Add to the end of a named trail or start a new trail with mouse clicks
        Short cut for setting auto-tracking
        """
        trail_number = self.get_val_from_ctl("trail_control.trail_number")
        trail = self.overlayTrail(show_points=True)
        if trail_number == "":
            segment = trail.add_new_segment()
        else:
            try:
                trail_number = int(trail_number)
            except:
                self.report(f"trail_Number {trail_number} is not a valid number")
                return
            segment = trail.get_segment(trail_number)
            if segment is None:
                self.report(f"No trail segment number {trail_number}")
                return
            
        self.trail_segment = segment
        new_auto_track = "add_to_trail"
        self.set_ctl_val("auto_tracking.auto_track", new_auto_track)
        self.change_auto_tracking(new_auto_track)

    def add_point_to_trail(self, point):
        """ Add point to current trail segment
        :point:  point to be added to trail
        """
        trail = self.trail
        segment = self.trail_segment
        if segment is None:
            if self.trail is None:
                trail = self.mgr.overlayTrail(show_points=True)
            segment = trail.add_new_segment()
        prev_point = segment.get_end_point()    
        if prev_point is not None:
            self.track_two_points(prev_point, point,
                color=trail.color, width=trail.line_width, display_monitor=False,
                line_type="line")
            prev_point.display(displayed=True, color=trail.color_points)        # Place on top of line segments
            point.display(displayed=True, color=trail.color)
        else:
            point.display(displayed=True, color=trail.color)            
        segment.add_points(point)

    def make_point(self, lat=None, long=None):
        """ Create appropriate point for mouse click with current tracking state
        :lat: latitude
        :long: longitude
        :returns: point (SurveyPoint)
        """
        if (self.auto_tracking == "add_to_trail"
            and self.trail is not None
             and self.trail_segment is not None):
            trail = self.trail
            color_points = "black"
            segment = self.trail_segment
            seg_no = segment.segment_no
            pt_no = len(segment.points)+1
            label = self.trail.label_pattern % (seg_no, pt_no)
            point = SurveyPoint(self.mgr, label=label, color=color_points,
                                lat=lat, long=long)
            point.snapshot(title=f"\n make_point on trail")
            segment.add_points(point)
            self.mgr.add_point(point, track=False)
            seg_points = segment.get_points()
            if len(seg_points) > 1:
                self.track_two_points(seg_points[-2], seg_points[-1],
                         color=trail.color, width=trail.line_width,
                         line_type=trail.line_type,
                         display_monitor=trail.display_monitor)
        else:
            point = SurveyPoint(self.mgr, lat=lat, long=long)
            point.snapshot(title=f"\n make_point")
            self.mgr.in_point_is_down = True                        # Standard continuation for regualar new points
            self.mgr.in_point = point
            self.mgr.in_point_start = (lat, long)
            self.mgr.add_point(point)
        return point    
            

    def added_point(self, point):
        """ Make tracking adjustments given most recently added point
        :point: point just added
        """
        if self.auto_tracking == "none":
            return              # No auto tracking
        
        if self.auto_tracking == "add_to_trail":
            return self.add_point_to_trail(point)
        
        if self.current_region is None:
            self.current_region = SurveyRegion(self.mgr)
            SlTrace.lg(f"Starting region with {point}")
        self.current_region.add_points(point)     # Add most recent point
        if self.auto_tracking == "adjacent_pairs":
            """ Track (connect) points in current region """
            self.augment_region()
            
    def augment_region(self, point1=None, point2=None):
        if point1 is None and len(self.current_region.points) > 1:
            point1 = self.current_region.points[-2]
        if point2 is None and len(self.current_region.points) > 0:
            point2 = self.current_region.points[-1]
        
        if point1 is not None and point2 is not None:
            SlTrace.lg(f"Adding to region with {point2}")
            connection_line = self.get_val("connection.line", self.connection_line)
            connection_line_color=self.get_val("line_attributes.color", self.connection_line_color)
            connection_line_width=self.get_val("line_attributes.width", self.connection_line_width)
            self.track_two_points(point1, point2,
                              line_type=connection_line,
                              color=connection_line_color,
                              width=connection_line_width)
                
    def change_connection_line(self, connection_line):
        if connection_line is None:
            connection_line = self.connection_line
        else:
            self.connection_line = connection_line
        for tracked_item in self.tracked_items:
            tracked_item.change_connection_line(connection_line)
                
    def change_cursor_info(self, cursor_info):
        if cursor_info is not None:
            self.cursor_info = cursor_info
        self.mgr.change_cursor_info(self.cursor_info)
        
    def change_auto_tracking(self, tracking):
        self.auto_tracking = tracking

    def change_unit(self, unit=None):
        if unit is not None:
            self.unit = unit
        self.mgr.change_unit(self.unit)
        for tracked_item in self.tracked_items:
            tracked_item.change_unit(self.unit)

    def complete_region(self):
        """ Complete region
        For now, just connect last(most recent) and first point (after last completed region)
        :returns: True iff a region was completed
        """
        if self.current_region is None:
            return False
        
        if not self.current_region.complete_region():
            return False
        
        # Track completion edge
        self.augment_region(point1=self.current_region.points[-1], point2=self.current_region.points[0])
        self.current_region.completed = True
        self.regions.append(self.current_region)
        self.current_region = None
        return True


    def get_region(self, index=-1): 
        """ Get region
        :index:  region index default: -1 => most recently created
        :returns: region (SurveyRegion) None if not one
        """
        return None if len(self.regions) == 0 else self.regions[index]

    def restart_region(self):
        """ Restart region collection (with next point)
        """
        self.current_region = None
        
    def select_region_trail_points(self):
        """ select region trail points
        If no region, show all trail points
        """
        (t_points, t_show_list) = self.get_region_trail_points()
        x0 = 300
        y0 = 400
        width = 200
        height = 400
        SlTrace.lg(f"x0={x0}, y0={y0}, width={width}, height={height}", "select_list")                    
        app = SelectList(title="Select Trail Points",
                         ckbox=True,
                         items=t_show_list,
                         position=(x0, y0), size=(width, height))
        selecteds = app.get_selected()

        
    def get_region_trail_points(self):
        """ Get region trail points
        If no region, show all trail points
        :returns: (points, list of selection display items)
        """
        region = self.get_region()
        if region is None:
            SlTrace.lg("No region - show all points")
        
        trail_selection = self.mgr.get_point_list("trails")
        if trail_selection is None:
            SlTrace.lg("Trail added")
            self.mgr.add_trail_file(self.mgr.trailfile)
            trail_selection = self.mgr.get_point_list("trails")
            
        
        gpx = trail_selection.point_list
        trail_segments = gpx.get_segments()
        if region is not None:
            list_segments = []
            for seg in trail_segments:      # Add segment if any point is inside
                for pt in seg.get_points():
                    if region.is_inside(pt):
                        list_segments.append(seg)
                        break 
        else:
            list_segments = trail_segments
        
        unit = self.unit
        points = []
        show_list = []
        for iseg, seg in enumerate(list_segments):
            seg_points = seg.get_points()
            seg_no = iseg + 1
            for i, seg_point in enumerate(seg_points):
                if i == 0:
                    prev_point = seg_point
                else:
                    prev_point = points[i-1]
                prev_latLong = (prev_point.lat,prev_point.long)
                latLong = (seg_point.lat, seg_point.long)
                delta = self.mgr.sc.gmi.geoDist(prev_latLong, latLong)
                x_d, y_d = self.mgr.sc.gmi.getPos(latLong=latLong)
                label = f"t{seg_no}.{i+1}"
                show_list.append(f"{label}:   x:{x_d:.1f}{unit} y:{y_d:.1f}{unit}"
                                 f"   delta: {delta:.1f}{unit}"
                                 f"   lat:{seg_point.lat} Long:{seg_point.long}")
                track_point = self.mgr.get_point_labeled(label) # Don't duplicate
                if track_point is None:
                    track_point = SurveyPoint(self.mgr, label=label,
                                    lat=seg_point.lat, long=seg_point.long,
                                    display_size=8,
                                    color="black")
                    self.mgr.add_point(track_point, track=False)
                points.append(track_point)
        return (points, show_list)

    def delete_region_trail_points(self):
        """ Show region trail points, provide selection list,
        delete selected points from view
        If no region, show all trail points
        """
        (points, t_show_list) = self.get_region_trail_points()
        points_by_show = {}
        for i, pt in enumerate(points):
            points_by_show[t_show_list[i]] = pt
        x0 = 300
        y0 = 400
        width = 200
        height = 400
        app = SelectList(title="Delete Points", ckbox=True,
                         items=t_show_list,
                         position=(x0, y0), size=(width, height))
        delete_list = app.get_checked()
        for delete_label in delete_list:
            self.mgr.remove_point(points_by_show[delete_label])

    def delete_trail_points(self):
        """ Show region trail points, provide selection list,
        delete selected points from view
        If no region, show all trail points
        """
        trail = self.mgr.overlayTrail(show_points=True)
        seg_sep = "====="
        points_by_show = trail.get_points_by_show()
        show_items = trail.get_show_items(seg_sep=seg_sep)
        x0 = 300
        y0 = 400
        width = 200
        height = 400
        app = SelectList(title="Delete Points", ckbox=True,
                         items=show_items,
                         item_sep=seg_sep,
                         position=(x0, y0), size=(width, height))
        delete_list = app.get_checked()
        for delete_label in delete_list:
            del_point = points_by_show[delete_label]
            SlTrace.lg(f"delete point: {del_point}")
            trail.delete_points(del_point)
            self.mgr.remove_point(del_point)

    def delete_trail_points_chosen(self):
        region = self.get_region()
        if region is not None:
            self.delete_region_trail_points()
        else:
            self.delete_trail_points()

    def hide_trail_points_chosen(self):
        region = self.get_region()
        if region is not None:
            self.hide_region_trail_points()
        else:
            self.hide_trail_points()

    def show_point_tracking(self, *points):
        """ Display/redisplay tracking items/lines
        for points given.
        :ponts: zero or more args, each of which is a point or list of points
        """
        tracked_items = self.get_point_tracking(*points)
        for item in tracked_items:
            item.show()

    def hide_point_tracking(self, *points):
        """ Hide  tracking items/lines
        for points given.
        :ponts: zero or more args, each of which is a point or list of points
        """
        tracked_items = self.get_point_tracking(*points)
        for item in tracked_items:
            item.hide()
    
    def get_point_tracking(self, *points):
        """ Get all tracking connected to points
        :points: zero or more args, each of which is a point or list of points
        :returns: list of tracking items associated with these points
        """
        for pts in points:
            if not isinstance(pts, list):
                pts = [pts]         # Make list of one
            tracked_items = {}      # Dictionary of tracked items
            for point in pts:
                for tracked_item in self.tracked_items:
                    if isinstance(tracked_item, PointPlace):
                        pt = tracked_item.point
                        if pt.point_id == point:
                            tracked_items[tracked_item.tracking_id] = tracked_item
                    elif isinstance(tracked_item, PointPlaceTwo):
                        tpt = tracked_item.point1
                        if tpt.point_id == point.point_id:
                            tracked_items[tracked_item.tracking_id] = tracked_item
                        else:
                            tpt = tracked_item.point2
                            if tpt.point_id == point.point_id:
                                tracked_items[tracked_item.tracking_id] = tracked_item
        return tracked_items.values()
    
    def remove_point_tracking(self, *points):
        """ Remove all tracking connected to points
        :points: zero or more args, each of which is a point or list of points
        """
        for pts in points:
            if not isinstance(pts, list):
                pts = [pts]     # Make list of one
            for point in pts:
                kept_tracked = []        # tracked to be kept
                for tracked_item in self.tracked_items:
                    is_kept = True          # Cleared if removing tracked_item
                    if isinstance(tracked_item, PointPlace):
                        pt = tracked_item.point
                        if pt.point_id == point:
                            tracked_item.destroy()
                            is_kept = False
                    elif isinstance(tracked_item, PointPlaceTwo):
                        tpt = tracked_item.point1
                        if tpt.point_id == point.point_id:
                            tracked_item.destroy()
                            is_kept = False
                        else:
                            tpt = tracked_item.point2
                            if tpt.point_id == point.point_id:
                                tracked_item.destroy()
                                is_kept = False
                    if is_kept:
                        kept_tracked.append(tracked_item)    
                self.tracked_items = kept_tracked    
                            
    def show_region_trail_points(self):
        """ Show region trail points
        If no region, show all trail points
        """
        (_, t_show_list) = self.get_region_trail_points()
        x0 = 300
        y0 = 400
        width = 200
        height = 400
        SlTrace.lg(f"x0={x0}, y0={y0}, width={width}, height={height}", "select_list")                    
        app = SelectList(title="Trail Points",
                         items=t_show_list,
                         position=(x0, y0), size=(width, height))
        app.get_selected()
        
                            
    def track_one_point(self, name=None):
        """ Track one point
        :name: point's label
        :returns: True if OK, else False
        """
        point = self.mgr.get_point_labeled(name)
        if point is None:
            self.report("first point named {p1} is not on the map")
            return False
        SlTrace.lg(f"tracking point: {name}")
        pp1 = PointPlace(self.mgr.sc, title=f"Tracking:{name}", point=point,
                            unit=self.unit)
        self.tracked_items.append(pp1)
        return True

    def show_trail_points(self):
        """ Show trail with points visible
        """
        if self.trail is not None:
            self.mgr.overlayTrail(show_points=True)
    
    def hide_trail_points(self):
        """ Hide trail points
        """
        if self.trail is not None:
            self.trail.hide_points()
            
    def track_one_point_chosen(self):
        p1 = self.get_val_from_ctl("single_point.single_point_name")
        if p1 == "":
            self.report("single_point_name is empty")
            return
        
        self.track_one_point(p1)

    def untrack_one_point(self):
        self.report("untrack_one_point TBD")

    def track_two_points_chosen(self):
        p1 = self.get_val_from_ctl("two_points.first_point_name")
        if p1 == "":
            self.report("first_point is empty")
            return
        
        point1 = self.mgr.get_point_labeled(p1)
        if point1 is None:
            self.report("first point named {p1} is not on the map")
            return
        
        p2 = self.get_val_from_ctl("two_points.second_point_name")
        if p2 == "":
            self.report("second_point is empty")
            return
        
        point2 = self.mgr.get_point_labeled(p2)
        if point2 is None:
            self.report("Second point named {p2} is not on the map")
            return
        self.set_vals()     # Read form
        connection_line = self.get_val("connection.line", self.connection_line)
        connection_line_color=self.get_val("line_attributes.color", self.connection_line_color)
        connection_line_width=self.get_val("line_attributes.width", self.connection_line_width)
                  
        self.track_two_points(point1, point2,
            color=connection_line_color,
            width=connection_line_width,
            line_type=connection_line,
            display_monitor=True)
        
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
        p1 = point1.label
        p2 = point2.label
        SlTrace.lg(f"track_two_points: {p1}-{p2}", "tracking")
        pp2 = PointPlaceTwo(self.mgr.sc, title=f"Tracking:{p1}-{p2}", point1=point1, point2=point2,
                            connection_line=line_type,
                            connection_line_color=color,
                            connection_line_width=width,
                            display_monitor=display_monitor,
                            unit=self.unit)
        self.tracked_items.append(pp2)
        

    def untrack_two_points(self):
        self.report("untrack_two_points")

    def track_samples(self):
        point_selection = self.mgr.get_point_list("samples")
        if point_selection is None:
            SlTrace.report("No samples list loaded")
            return
        
        point_labels = []
        spx = point_selection.point_list
        points = spx.get_points()
        for point in points:
            label = point.get_plot_key()
            point_labels.append(label)
        x0 = 300
        y0 = 400
        width = 200
        height = 400
        SlTrace.lg(f"x0={x0}, y0={y0}, width={width}, height={height}", "select_list")
        title = os.path.basename(point_selection.title)                    
        app = SelectList(title=f"Track on of {title}",
                         items=point_labels,
                         position=(x0, y0), size=(width, height))
        point_label = app.get_selected()
        if point_label is None:
            self.report("NO point selected")
            return
        
        point1 = self.mgr.get_point_labeled(point_label)
        if point1 is not None:
            self.report(f"Point {point_label} is already in the map")
            return
        point = spx.get_point(point_label)
        if point is None:
            self.report(f"Point label {point_label} not found in list")
            return
        
        new_point = self.mgr.add_point(SurveyPoint(self.mgr, label=point_label, lat=point.lat,
                                                    long=point.long))
        if new_point is not None:
            self.track_one_point(point_label)
        
    def track_trails(self):
        gpx = self.mgr.get_point_list("trails")
        if gpx is None:
            SlTrace.report("No trails list loaded")
            return

    def destroy(self):
        """ Destroy window resources
        """
        if self.mw is not None:
            self.mw.destroy()
        self.mw = None

    
if __name__ == '__main__':
    from select_trace import SlTrace

    def set_cmd(ctl):
        SlTrace.lg("Set Button")
                
    root = Tk()
    root.withdraw()       # Hide main window

    SlTrace.setProps()
    loop = True
    ###loop = False
    ###tc = TrackingControl(None, mw=root, title="TrackingControl Testing", display=True, set_cmd=set_cmd)
    tc = TrackingControl(None, mw=None, title="TrackingControl Testing",
                         win_x=200, win_y=300, win_width=400, win_height=150,
                         display=True, set_cmd=set_cmd)
    ###tc.control_display()

    root.mainloop()