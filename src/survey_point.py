# survey_point.py    28Apr2020  crs
"""
Handling point display aspect for points in SurveyPointManager
"""
from select_trace import SlTrace

from select_trace import SelectError

class SurveyPoint:
    """ Point objects used for doing surveying type operations
    .e.g. distance, direction, area, circumferance measurements
    """
    
    POINT_TYPE_NONE = 1
    POINT_TYPE_CIRCLE = 2
    POINT_TYPE_SQUARE = 3
    POINT_TYPE_CROSS = 4
    point_id = 0                # Unique id
            
    def __init__(self, mgr, lat=None, long=None,
                 label=None, label_size=None,
                 label_displayed = True,
                 show_item=None,
                 displayed=True,
                 display_size=None, select_size=None,
                 point_type=None,
                 center_color=None, color=None,
                 point_id=None):
        """ Setup point attributes
        :lat: latitude        # To insulate against scaling/shifting
        :long: longitude
        :label: Point label (str) Point label prefix e.f. P1, P2,...
        :label_size: Point label vertical size in pixels
                must be CASE INSENSITIVE unique
        :label_displayed: label is displayed if the point is displayed
                default: True - displayed
        :show_item: unique display item for selection lists
                default: label: lat=... long=...
         :displayed: display point if present, else don't display point
                default: display
                    
        :display_size: point display circle size in pixels
                    default: 10
        :select_size: point selection circle size 
                    default: display_size-2
        :point_type: Point display type/shape: default
                        CIRCLE - circle with dot in middle
                        SQUARE - square with dot in middle
                        CROSS - cross
        :center_color: center color
        :color: point color default
        :point_id: unique point identifier
                    default: generator
        :track_sc:  display sc mouse movement
        """
        
        self.mgr = mgr
        self.lat = lat
        self.long = long
        if label is None:
            label = f"{mgr.label}{self.mgr.label_no}" 
            self.mgr.label_no += 1
        self.label = label
        self.label_displayed = label_displayed
        self.displayed = displayed
        if show_item is None:
            show_item = f"{label}:  lat={lat} long={long}"
        self.show_item = show_item
        if lat is None:
            raise SelectError(f"SurveyPoing {label} lat is missing")
        
        if long is None:
            raise SelectError(f"SurveyPoing {label} long is missing")
        
        if label_size is None:
            label_size = mgr.label_size 
        self.label_size = label_size
        if display_size is None:
            display_size = mgr.display_size
        self.display_size = display_size
        if select_size is None:
            select_size = mgr.select_size
        self.select_size = select_size
        if point_type is None:
            point_type = mgr.point_type
        self.point_type = point_type
        if center_color is None:
            center_color = mgr.center_color
        self.center_color = center_color
        if color is None:
            color = mgr.color
        self.color = color
        if point_id is None:
            mgr.point_id += 1
            point_id = mgr.point_id
        self.point_id = point_id
        
        self.point_tag = None       # point iodraw tag
        self.center_tag = None      # point center tag
        self.label_tag = None       # point label tag
        self.trackers = []          # list of trackers if any

    def __str__(self):
        """ Point diagnostic representation
        """
        tr_ctl = self.mgr.tr_ctl
        string = str(f"SurveyPoint {self.label}:"
                     f" lat: {self.lat:{tr_ctl.ll_fmt}}"
                     f" Long: {self.long:{tr_ctl.ll_fmt}}")
        return string
            
    def delete(self):
        """ Delete point (stop display)
        """
        iodraw = self.get_iodraw()
        if iodraw is None:
            return
        
        if self.point_tag is not None:
            iodraw.delete_tag(self.point_tag)
            self.point_tag = None
        if self.center_tag is not None:
            iodraw.delete_tag(self.center_tag)
            self.point_tag = None
        if self.label_tag is not None:
            iodraw.delete_tag(self.label_tag)
            self.label_tag = None

    def destroy(self):
        self.delete()
                    
    def display(self, displayed=None, color=None):
        """ Display point + label
        Adjusting / deleting / replacing iodraw tags as appropriate
        :displayed: changing displayed, if present
        :color: changing color if present
        """
        if displayed is not None:
            self.displayed = displayed  # Update point, to make redisplay keep color
        if color is not None:
            self.color = color
        self.display_point()
        self.display_label()

    def redisplay(self):
        """ Redisplay point
        Should be the same as display because the internal state (long,lat)
        does not change
        """
        self.display()
        
    def display_point(self):
        """ Display point part
        """
        iodraw = self.get_iodraw()
        if iodraw is None:
            return
        
        if self.point_tag is not None:
            iodraw.delete_tag(self.point_tag)
            self.point_tag = None
        if self.center_tag is not None:
            iodraw.delete_tag(self.center_tag)
            self.center_tag = None
        if not self.displayed:          # Do after in case state changed
            return
        
        if self.point_type == SurveyPoint.POINT_TYPE_CIRCLE:
            w = h = self.display_size
            x, y = self.ll_to_canvas(trace=SlTrace.trace("ll_to_canvas"))
            hw = w/2.
            hh = h/2.
            x0 = x - hw
            y0 = y - hh
            x1 = x0 + w 
            y1 = y0 + h 
            self.point_tag = iodraw.drawCircle((x,y), radius=w/2, color=self.color,
                                    outline=self.color,
                                    activeoutline="red", activefill="red", activewidth=4)
            self.center_tag = iodraw.drawCircle((x,y), radius=1, color=self.center_color)
        elif self.point_type == SurveyPoint.POINT_TYPE_NONE:
            pass    

    def get_canvas_coords(self, **kwargs):
        """ Shorthand to get CanvasCoords
        """
        if not kwargs:
            kwargs['lat'] = self.lat
            kwargs['long'] = self.long
        return self.mgr.get_canvas_coords(**kwargs)
    
    def ll_to_canvas(self, lat=None, long=None, trace=False):
        """ Convert Lat/Long to iodraw x,y
        :lat: latitude
        :long: Longitude
        :trace: trace operation - Debugging
        """
        if lat is None:
            lat = self.lat
        if long is None:
            long = self.long
        if trace and SlTrace.trace("ll_to_canvas"):
            SlTrace.lg(f"\n{self.label} rot: {self.mgr.get_mapRotate()}")
        return self.mgr.ll_to_canvas(lat=lat, long=long, trace=trace)
            
    def display_label(self):
        """ Display label part
        """
        iodraw = self.get_iodraw()
        if iodraw is None:
            return
        
        if self.label_tag is not None:
            iodraw.delete_tag(self.label_tag)
            self.label_tag = None
        if not self.displayed or not self.label_displayed:        # Do here, in case state changed
            return
        
        text = self.label
        char_size = self.label_size
        text_color = "white"
        x_pixel, y_pixel = self.ll_to_canvas()
        text_push_v = char_size*2
        text_push = char_size*(len(text)/2.+1)   
        text_x_off = self.display_size
        text_y_off = text_x_off
        if x_pixel < text_push:
            text_x_off = text_push
        elif x_pixel > iodraw.getWidth() - text_push:
            text_x_off = - text_push
        if y_pixel > iodraw.getHeight() - text_push_v:
            text_y_off = -1*text_push_v
        text_pos = (x_pixel+text_x_off, y_pixel+text_y_off)
        over_laps = self.over_lapping()
        if len(over_laps) > 0:
            our_idx = 0
            for pt in over_laps:
                if pt.point_id == self.point_id:
                    break
                our_idx += 1
            
            text_pos = (text_pos[0]+our_idx*char_size, text_pos[1]+our_idx*char_size)
            prefix = "+"*our_idx
            text = f"{prefix}{text}"    
        self.label_tag = iodraw.drawText(text_pos, text=text, color=text_color)

    def get_iodraw(self):
        """ Get overlay/image object
        """
        return self.mgr.get_iodraw()

    def get_gmi(self):
        return self.get_sc().gmi

    def get_sc(self):
        """ Get ScrollableCanvas
        """
        return self.mgr.sc
    
    def move(self, canvas_x=None, canvas_y=None, lat=None, long=None):
        """ Move point
        :x,y: to new iodraw point
        :lat,long: to new latitude, longitude
        FUTURE: use iodraw move
        """
        nc = 0
        if canvas_x is not None or canvas_y is not None: nc += 1
        if lat is not None or long is not None: nc += 1
        if nc == 0:
            raise SelectError("At least one of iodraw, or lat/long")
        
        if nc > 1:
            raise SelectError("No more than one of iodraw, lat/long")
        
        pc = self.get_canvas_coords(canvas_x=canvas_x, canvas_y=canvas_y,
                          lat=lat, long=long)
        self.lat = pc.lat 
        self.long = pc.long 
        self.display()
        for tracker in self.trackers:            
            tracker(self)

    def add_tracker(self, tracker):
        """ Add tracking function
        :tracker: tracking function to be called with self
        """
        self.trackers.append(tracker)
        
    def is_in(self, lat=None, long=None):
        """ Check if lat,long is within point selection
        :lat: latitude - checking coordinate
        :long: longitude - checking coordinate
        :returns: True iff lat,long is within point selection
        """
        canvas_x1, canvas_y1 = self.ll_to_canvas()
        canvas_x2, canvas_y2 = self.ll_to_canvas(lat=lat, long=long)
        if ((canvas_x1-canvas_x2)**2 + (canvas_y1-canvas_y2)**2
             <= self.select_size**2):
            return True
        
        return False

    def over_lapping(self):
        """ Return all overlapping points - those whose displays 
        overlap ours.  To allow display mitigations
        :returns: list of all overlapping points, including this one, in
                the order of appearance. [] if none
        """
        pts = self.mgr.get_points()
        over_laps = []
        for pt in pts:
            if self.is_in(lat=pt.lat, long=pt.long):
                over_laps.append(pt)
        if len(over_laps) > 1:
            return over_laps
        
        return []

    def snapshot(self, title=None):
        """ Snapshot current point stats
        """
        if title is None:
            title = ""
        else:
            title = f"{title}: "
        tr_ctl = self.mgr.tr_ctl
        px_fmt = tr_ctl.px_fmt
        dis_fmt = tr_ctl.dis_fmt
        unit = tr_ctl.unit
        pc_lat, pc_long = self.lat, self.long
        pc_x, pc_y = self.ll_to_canvas()
        pc = self.get_canvas_coords()       # To do others which we have not ported
        sc = self.get_sc()
        gmi = self.get_gmi()
        ll_fmt = tr_ctl.ll_fmt
        SlTrace.lg(f"{title}Point {self.label}: {self}")
        SlTrace.lg(f"    Latitude: {pc_lat:{ll_fmt}} Longitude: {pc_long:{ll_fmt}}")
        SlTrace.lg(f"    x({unit}): {pc.x_dist:{dis_fmt}}  y({unit}): {pc.y_dist:{dis_fmt}}")
        SlTrace.lg(f"    x(image pix): {pc.x_image:{px_fmt}}  y(image pix): {pc.y_image:{px_fmt}}")
        SlTrace.lg(f"    x(iodraw pix): {pc_x:{px_fmt}}  y(canvas pix): {pc_y:{px_fmt}}")
        rotate = gmi.get_mapRotate()
        SlTrace.lg(f"    rot({rotate})")
        SlTrace.lg(f"    ulLat: {gmi.ulLat:{ll_fmt}} ulLong: {gmi.ulLong:{ll_fmt}}")
        SlTrace.lg(f"    lrLat: {gmi.lrLat:{ll_fmt}} lrLong: {gmi.lrLong:{ll_fmt}}")
        SlTrace.lg(f"    Image: Width: {gmi.getWidth():{px_fmt}} Height: {gmi.getHeight():{px_fmt}}")
        SlTrace.lg(f"    Canvas: Width: {sc.get_canvas_width():{px_fmt}} Height: {sc.get_canvas_height():{px_fmt}}")