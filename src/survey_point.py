# survey_point.py    28Apr2020  crs
"""
Handling point display aspect for points in SurveyPointManager
"""
from select_trace import SelectError
from canvas_coords import CanvasCoords
from wx.lib.plot.utils import DisplaySide
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
                 display_size=None, select_size=None,
                 point_type=None,
                 center_color=None, color=None,
                 point_id=None):
        """ Setup point attributes
        :lat: latitude        # To insulate against scaling/shifting
        :long: longitude
        :label: Point label (str) Point label prefix e.f. P1, P2,...
                must be CASE INSENSITIVE unique
        :label_size: Point label vertical size in pixels
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
        
        self.point_tag = None       # point canvas tag
        self.center_tag = None      # point center tag
        self.label_tag = None       # point label tag
        self.trackers = []          # list of trackers if any

    def __str__(self):
        """ Point diagnostic representation
        """
        string = f"SurveyPoint {self.label}: lat: {self.lat} Long: {self.long}"
        return string
            
    def delete(self):
        """ Delete point (stop display)
        """
        canvas = self.get_canvas()
        if canvas is None:
            return
        
        if self.point_tag is not None:
            canvas.delete(self.point_tag)
            self.point_tag = None
        if self.center_tag is not None:
            canvas.delete(self.center_tag)
            self.point_tag = None
        if self.label_tag is not None:
            canvas.delete(self.label_tag)
            self.label_tag = None

    def destroy(self):
        self.delete()
                    
    def display(self):
        """ Display point + label
        Adjusting / deleting / replacing canvas tags as appropriate
        """
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
        canvas = self.get_canvas()
        if canvas is None:
            return
        
        if self.point_tag is not None:
            canvas.delete(self.point_tag)
            self.point_tag = None
        if self.center_tag is not None:
            canvas.delete(self.center_tag)
            self.center_tag = None
        pc = self.get_canvas_coords()
        if self.point_type == SurveyPoint.POINT_TYPE_CIRCLE:
            w = h = self.display_size
            x = pc.canvas_x
            y = pc.canvas_y
            hw = w/2.
            hh = h/2.
            x0 = x - hw
            y0 = y - hh
            x1 = x0 + w 
            y1 = y0 + h 
            self.point_tag = canvas.create_oval(x0, y0, x1, y1, fill=self.color)
            self.center_tag = canvas.create_oval(x-1, y-1, x+1, y+1, fill=self.center_color)
            

    def get_canvas_coords(self, **kwargs):
        """ Shorthand to get CanvasCoords
        """
        if not kwargs:
            kwargs['lat'] = self.lat
            kwargs['long'] = self.long
        return CanvasCoords(self.mgr.sc, **kwargs)
    
            
    def display_label(self):
        """ Display label part
        """
        canvas = self.get_canvas()
        if canvas is None:
            return
        
        if self.label_tag is not None:
            canvas.delete(self.label_tag)
            self.label_tag = None
        if self.label == "":
            return              # No label
        
        text = self.label
        char_size = self.label_size
        text_fill = "white"
        pc = self.get_canvas_coords()
        x_pixel = pc.canvas_x
        y_pixel = pc.canvas_y
        text_push_v = char_size*2
        text_push = char_size*(len(text)/2.+1)   
        text_x_off = self.display_size
        text_y_off = text_x_off
        if x_pixel < text_push:
            text_x_off = text_push
        elif x_pixel > canvas.winfo_width() - text_push:
            text_x_off = - text_push
        if y_pixel > canvas.winfo_height() - text_push_v:
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
        self.label_tag = canvas.create_text(text_pos, text=text, fill=text_fill)

    def get_canvas(self):
        """ Get canvas directly
        """
        return self.mgr.get_canvas()
        

    def move(self, canvas_x=None, canvas_y=None, lat=None, long=None):
        """ Move point
        :x,y: to new canvas point
        :lat,long: to new latitude, longitude
        FUTURE: use canvas move
        """
        nc = 0
        if canvas_x is not None or canvas_y is not None: nc += 1
        if lat is not None or long is not None: nc += 1
        if nc == 0:
            raise SelectError("At least one of canvas, or lat/long")
        
        if nc > 1:
            raise SelectError("No more than one of canvas, lat/long")
        
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
        p1c = self.get_canvas_coords()
        p2c = self.get_canvas_coords(lat=lat, long=long)
        
        if ((p1c.canvas_x-p2c.canvas_x)**2 + (p1c.canvas_y-p2c.canvas_y)**2
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
            