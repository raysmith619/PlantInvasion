# map_rotator.py    02Jun2020  crs
"""
Rotate map
"""
import os

from tkinter import *

from select_trace import SlTrace
from select_control_window import SelectControlWindow

class MapRotator(SelectControlWindow):
    """ Collection of point selection controls
    """
    CONTROL_NAME_PREFIX = "map_rotator"
    DEF_WIN_X = 500
    DEF_WIN_Y = 300
    
        
            
    def __init__(self, mgr,
                 title=None, control_prefix=None, 
                 **kwargs):
        """ Initialize subclassed SelectControlWindow
             Setup score /undo/redo window
             :mgr: tracking point manager
             :mw: main window if one
        """
        self.mgr = mgr
        if title is None:
            title = "Map Rotator"
        if control_prefix is None:
            control_prefix = TrackingControl.CONTROL_NAME_PREFIX
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

        direction_frame = Frame(controls_frame)
        self.set_fields(direction_frame, "direction", "Direction")
        self.set_entry(field="north", label="north", value=0.0, width=4)
        
        self.arrange_windows()
        if not self.display:
            self.hide_window()

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
    mr = MapRotator(None, mw=None, title="MapRotator Testing",
                         win_x=200, win_y=300, win_width=400, win_height=150,
                         display=True, set_cmd=set_cmd)
    ###tc.control_display()

    root.mainloop()