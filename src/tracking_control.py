# track_points.py    29Apr2020  crs
"""
Facilitate tracking single point, using PointPlace
Facilitate tracking point pairs using PointPlaceTwo

Keeps a list of tracked points
Keeps a list of tracked point-pairs
"""
from tkinter import *

from select_trace import SlTrace
from select_control_window import SelectControlWindow
from point_place_two import PointPlaceTwo

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

        single_point_frame = Frame(controls_frame)
        self.set_fields(single_point_frame, "single_point", title="Single")
        self.set_button(field="track_two_points", label="Track", command=self.track_one_point)
        self.set_entry(field="single_point_name", label="name", value="P1", width=4)
        self.set_sep()
        self.set_button(field="untrack_point", label="Un-track", command=self.untrack_one_point)

        two_point_frame = Frame(controls_frame)
        self.set_fields(two_point_frame, "two_points", title="Two points")
        self.set_button(field="track_two_points", label="Track", command=self.track_two_points)
        self.set_entry(field="first_point_name", label="first point", value="P1", width=4)
        self.set_entry(field="second_point_name", label="second point", value="P2", width=4)
        self.set_sep()
        self.set_button(field="untrack_points", label="Un-track", command=self.untrack_two_points)
        
        self.arrange_windows()
        if not self.display:
            self.hide_window()

    def track_one_point(self):
        self.report("track_one_point")

    def untrack_one_point(self):
        self.report("untrack_one_point")

    def track_two_points(self):
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
        SlTrace.lg(f"track_two_points: {p1}-{p2}")
        pp2 = PointPlaceTwo(self.mgr.sc, title=f"Tracking:{p1}-{p2}", point1=point1, point2=point2)
        
        

    def untrack_two_points(self):
        self.report("untrack_two_points")


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