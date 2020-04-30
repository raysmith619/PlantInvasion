# point_manager.py    27Apr2020  crs,
""" Point placement / manipulation management for surveying type operations
    The points are referenced in a GoogleMapImage

"""
from select_trace import SlTrace
from select_error import SelectError

from point_place import PointPlace
from survey_point import SurveyPoint                
            
class SurveyPointManager:
    """ Manipulate a list of points (SurveyPoint)
    """
    def __init__(self, scanvas,
                 label=None, label_size=None,
                 display_size=None, select_size=None,
                 point_type=None, center_color=None, color=None, label_no=None,
                 point_id=None,
                 track_sc=True):
        """ Setup point attributes
        :scanvas: canvas (ScrollableCanvas) on which points are positioned/displayed
        :display_size, select_size, point_type, center_color, color - default point attributes
                described in SurveyPoint
        :label_no: starting number for point labels <label><label_no>
                default: 1
        :track_sc:  track/display sc mouse motion
        """
                       
        self.sc = scanvas
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
        
        self.points = []
        self.points_by_label = {}        # Force unique names(case insensitive p1 = P1)
        self.track_sc = track_sc
        if track_sc is not None:
            self.sc_point_place = PointPlace(self.sc)
            self.sc.set_mouse_down_call(self.mouse_down)
            self.sc.set_mouse_double_down_call(self.mouse_double_down)
            self.sc.set_mouse_up_call(self.mouse_up)
            self.sc.set_mouse_move_call(self.mouse_motion)
        self.in_point = None            # Set to point we're in, if any
        self.in_point_start = None      # Set to starting x,y
        self.in_point_is_down = False   # Set True while mouse is down
        self.doing_mouse_motion = False # Suppress multiple concurrent moves
    
    def mouse_down(self, canvas_x, canvas_y):
        """ Capture/process mouse clicks in canvas
        :canvas_x: canvas x-coordinate
        :canvas_y: canvas y-coordinate
        """
        SlTrace.lg(f"mouse_down: canvas_x={canvas_x:.0f} canvas_y={canvas_y:.0f}")
        point = self.get_in(canvas_x, canvas_y)
        if point is not None:
            self.in_point_is_down = True
            self.in_point = point
            self.in_point_start = (canvas_x, canvas_y)  # ref for movement
        else:
            point = self.add_point(SurveyPoint(self, x=canvas_x, y=canvas_y))
            self.in_point_is_down = True
            self.in_point = point
            self.in_point_start = (canvas_x, canvas_y)

    def mouse_double_down(self, canvas_x, canvas_y):
        """ Capture/process double click
        :canvas_x:    x-coordinate
        :canvas_y:    y-coordinate
        """
        _ = canvas_x
        _ = canvas_y

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
        if self.doing_mouse_motion:
            return          # Block multiple calls

        
        self.doing_mouse_motion = True
        if self.in_point is not None and self.in_point_is_down:
            SlTrace.lg(f"mouse_motion(in_point): canvas_x,y={canvas_x:.0f}, {canvas_y:.0f}", "mouse_motion")
            point = self.in_point
            if self.in_point_start is not None:
                x_start = self.in_point_start[0]
                y_start = self.in_point_start[1]
                x_delta = canvas_x-x_start
                y_delta = canvas_y-y_start
                x_new = x_start + x_delta
                y_new = y_start + y_delta
                SlTrace.lg(f"  x,y_start: {x_start:.0f}, {y_start:.0f}"
                           f" x,y_delta:{x_delta:.0f}, {y_delta:.0f} x,y_new:{x_new:.0f},{y_new:.0f}", "mouse_motion")
                point.move(x_new,  y_new)
        else:
            if self.track_sc:
                self.sc_track_update(canvas_x, canvas_y)
        self.doing_mouse_motion = False
        
    def sc_track_update(self, canvas_x, canvas_y):
        """ Update sc tracking display
        :canvas_x:  x-coordinate
        :canvas_y:  y-coordinate
        """
        self.sc_point_place.motion_update(canvas_x, canvas_y)
                
    def add_point(self, point):
        """ Add new point to list
        Checks for unique name - error if pre-existing named point
        :point: point to be env_added
        :returns: added point
        """
        point_label = point.label.lower()
        if point_label in self.points_by_label:
            raise SelectError(f"duplicate point name {point_label} in points list")
        
        self.points.append(point)
        self.points_by_label[point_label] = point
        point.display()
        return point

    def get_canvas(self):
        """ Get Canvas type object
        """
        return self.sc.get_canvas()
    
    def get_in(self, x, y):
        """ Return point if onewithin selection area
        :x: x-Coordinate 
        :y: y-Coordinate
        :returns: first if any, else None
        """
        for point in self.points:
            if point.is_in(x,y):
                return point
            
        return None

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