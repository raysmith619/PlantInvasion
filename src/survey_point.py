# survey_point.py    28Apr2020  crs
"""
Handling point display aspect for points in SurveyPointManager
"""

class SurveyPoint:
    """ Point objects used for doing surveying type operations
    .e.g. distance, direction, area, circumferance measurements
    """
    
    POINT_TYPE_NONE = 1
    POINT_TYPE_CIRCLE = 2
    POINT_TYPE_SQUARE = 3
    POINT_TYPE_CROSS = 4
    point_id = 0                # Unique id
    point_no = 0                # point numbering
    
    def __init__(self, mgr, x=None, y=None,
                 label=None, label_size=None,
                 display_size=None, select_size=None,
                 point_type=None,
                 center_color=None, color=None,
                 point_id=None):
        """ Setup point attributes
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
        self.canvas = mgr.get_canvas()      # Local copy for simplicity
        self.x = x
        self.y = y
        if label is None:
            label = f"{mgr.label}{self.mgr.label_no}" 
            self.mgr.label_no += 1
        self.label = label
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
        
    def delete(self):
        """ Delete point (stop display)
        """
        if self.point_tag is not None:
            self.canvas.delete(self.point_tag)
            self.point_tag = None
        if self.center_tag is not None:
            self.canvas.delete(self.center_tag)
            self.point_tag = None
        if self.label_tag is not None:
            self.canvas.delete(self.label_tag)
            self.label_tag = None
            
    def display(self):
        """ Display point + label
        Adjusting / deleting / replacing canvas tags as appropriate
        """
        self.display_point()
        self.display_label()

    def display_point(self):
        """ Display point part
        """
        if self.point_tag is not None:
            self.canvas.delete(self.point_tag)
            self.point_tag = None
        if self.center_tag is not None:
            self.canvas.delete(self.center_tag)
            self.center_tag = None
        if self.point_type == SurveyPoint.POINT_TYPE_CIRCLE:
            w = h = self.display_size
            x = self.x
            y = self.y
            hw = w/2.
            hh = h/2.
            x0 = x - hw
            y0 = y - hh
            x1 = x0 + w 
            y1 = y0 + h 
            self.point_tag = self.canvas.create_oval(x0, y0, x1, y1, fill=self.color)
            self.center_tag = self.canvas.create_oval(x-1, y-1, x+1, y+1, fill=self.center_color)
            

    def display_label(self):
        """ Display label part
        """
        if self.label_tag is not None:
            self.canvas.delete(self.label_tag)
            self.label_tag = None
        if self.label == "":
            return              # No label
        
        canvas = self.canvas
        text = self.label
        char_size = self.label_size
        text_size = char_size
        text_fill = "white"
        x_pixel = self.x
        y_pixel = self.y
        text_push_v = char_size*2
        text_push = char_size*(len(text)/2.+1)   
        text_x_off = text_size
        text_y_off = text_x_off
        if x_pixel < text_push:
            text_x_off = text_push
        elif x_pixel > canvas.winfo_width() - text_push:
            text_x_off = - text_push
        if y_pixel > canvas.winfo_height() - text_push_v:
            text_y_off = -1*text_push_v
        text_pos = (x_pixel+text_x_off, y_pixel+text_y_off)
            
        self.label_tag = canvas.create_text(text_pos, text=text, fill=text_fill)
        
        

    def move(self, x, y):
        """ Move point
        FUTURE: use canvas move
        """
        self.x = x 
        self.y = y 
        self.display()
        for tracker in self.trackers:            
            tracker(self)

    def add_tracker(self, tracker):
        """ Add tracking function
        :tracker: tracking function to be called with self
        """
        self.trackers.append(tracker)
        
    def is_in(self, x, y):
        """ Check if x,y is within point selection
        :x: x - checking coordinate
        :y: y - checking coordinate
        :returns: True iff x,y is within point selection
        """
        if (self.x-x)**2 + (self.y-y)**2 <= self.select_size**2:
            return True
        
        return False
