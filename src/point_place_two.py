# point_place_two.py    28Apr2020    crs
"""
Measurement between two points
Provides an updated positioning information of the points relation
"""
from tkinter import *
from math import sqrt

from select_trace import SlTrace
from scrolled_canvas import CanvasCoords

class PointPlaceTwo(Toplevel):
    # Display point position annotation
    SHOW_POINT_NONE = 1
    SHOW_POINT_LL = 2
    SHOW_POINT_METER = 3
    SHOW_POINT_PIXEL = 4

    ROW_TITLE = 0
    COL_TITLE = 2
    
    ROW_HEADING = ROW_TITLE + 1
    COL_HEADING_DIST = 5

    ROW_LAT = ROW_HEADING + 1
    COL_LAT_LABEL = 1
    COL_LAT = COL_LAT_LABEL+1
    
    ROW_LONG = ROW_LAT
    COL_LONG_LABEL = COL_LAT + 1
    COL_LONG = COL_LONG_LABEL + 1
    
    ROW_LL_DIST = ROW_LAT
    COL_LL_DIST = COL_LONG + 1

    ROW_X_METER = ROW_LAT + 1
    COL_X_METER_LABEL = COL_LAT_LABEL
    COL_X_METER = COL_X_METER_LABEL+1
    
    ROW_Y_METER = ROW_X_METER
    COL_Y_METER_LABEL = COL_LONG_LABEL
    COL_Y_METER = COL_Y_METER_LABEL + 1
    
    ROW_METER_DIST = ROW_X_METER
    COL_METER_DIST = COL_Y_METER + 1

    ROW_X_PIXEL = ROW_X_METER + 1
    COL_X_PIXEL_LABEL = COL_LAT_LABEL
    COL_X_PIXEL = COL_X_PIXEL_LABEL+1
    
    ROW_Y_PIXEL = ROW_X_PIXEL
    COL_Y_PIXEL_LABEL = COL_LONG_LABEL
    COL_Y_PIXEL = COL_Y_PIXEL_LABEL + 1
    
    ROW_PIXEL_DIST = ROW_X_PIXEL
    COL_PIXEL_DIST = COL_Y_PIXEL + 1

    ROW_CANVAS_X_PIXEL = ROW_Y_PIXEL + 1
    COL_CANVAS_X_PIXEL_LABEL = COL_LAT_LABEL
    COL_CANVAS_X_PIXEL = COL_CANVAS_X_PIXEL_LABEL+1
    
    ROW_CANVAS_Y_PIXEL = ROW_CANVAS_X_PIXEL
    COL_CANVAS_Y_PIXEL_LABEL = COL_LONG_LABEL
    COL_CANVAS_Y_PIXEL = COL_CANVAS_Y_PIXEL_LABEL + 1
    
    ROW_CANVAS_PIXEL_DIST = ROW_CANVAS_X_PIXEL
    COL_CANVAS_PIXEL_DIST = COL_CANVAS_Y_PIXEL + 1

    ROW_POINT_NAMES = ROW_CANVAS_X_PIXEL + 1
    COL_POINT_NAMES_LABEL = COL_LAT_LABEL
    COL_POINT1_NAME = COL_POINT_NAMES_LABEL+1
    COL_POINT2_NAME = COL_POINT1_NAME + 1

    ROW_SET_POINTS = ROW_POINT_NAMES + 1
    COL_SET_POINTS = COL_POINT2_NAME + 1

    
    ROW_ADD_POINT = ROW_SET_POINTS
    COL_ADD_POINT = COL_SET_POINTS + 2
    
    def __init__(self, sc=None, parent=None, title=None,
                 position=None,
                 size=None,
                 lat_long=None,
                 track_sc=False,
                 point1=None,
                 point2=None
                 ):
        
        
        """
        :sc: scrollable canvas Must contain sc.gmi GoogleMapImage 
        :parent: - parent - call basis must have tc_destroy to be called if we close
        :title: Window title
        :position: form position (x,y) in pixels on screen
        :size: form size (width, hight) in in pixels of window
        :lat_long: optional starting point latitude, longitude
        :track_sc: Update, based on mouse motion, till Add Point clicked
        """
        self.mt_width = 10              # meter form entry width (char)
        self.px_width = 5               # pixel form entry width (char)
        self.ll_width = 11              # long/lat form entry width (char)
        self.px_fmt = ".0f"             # pixel format
        self.ll_fmt = ".7f"             # longitude/latitude format
        self.mt_fmt = ".3f"             # meter format
        self.ref_latLong = None         # Set to reference location when image is loaded
        self.show_point = PointPlaceTwo.SHOW_POINT_METER
        self.show_point_tag = None      # show point text tag
        self.ctls_vars = {}      # var By field
        self.ctls_ctls = {}      # ctl By field
        self.track_sc = track_sc
        self.tracking_sc = track_sc     # cleared when done
        self.standalone = False
        self.motion_update2 = None     # Used if sc already has a motion call
        if parent is None:
            parent = Tk()
            ###parent.withdraw()
            self.standalone = True
        self.mw = parent
        super().__init__(parent)
        self.sc = sc
        if sc is not None:
            self.gmi = sc.gmi
            self.ref_latLong = self.gmi.get_ref_latLong() 
        else:
            self.gmi = None
        top_frame = Frame(self.mw)
        top_frame.grid()
        ctl_frame = top_frame
        self.top_frame = top_frame
        if title is not None:
            title_label = Label(master=self.top_frame, text=title, font="bold")
            title_label.grid(row=PointPlaceTwo.ROW_TITLE, column=PointPlaceTwo.COL_TITLE, columnspan=3)
        Label(master=ctl_frame, text="Distance").grid(row=PointPlaceTwo.ROW_HEADING, column=PointPlaceTwo.COL_HEADING_DIST)    
        field = "latitude"
        width = self.ll_width
        self.ctls_vars[field] = content = StringVar()
        Label(master=ctl_frame, text="Latitude").grid(row=PointPlaceTwo.ROW_LAT, column=PointPlaceTwo.COL_LAT_LABEL)
        self.ctls_ctls[field] = entry = Entry(ctl_frame, textvariable=content, width=width)
        entry.grid(row=PointPlaceTwo.ROW_LAT, column=PointPlaceTwo.COL_LAT, sticky=W)
        
        field = "longitude"
        width = self.ll_width
        self.ctls_vars[field] = content = StringVar()
        Label(master=ctl_frame, text="Longitude").grid(row=PointPlaceTwo.ROW_LONG, column=PointPlaceTwo.COL_LONG_LABEL)
        self.ctls_ctls[field] = entry = Entry(ctl_frame, textvariable=content, width=width)
        entry.grid(row=PointPlaceTwo.ROW_LONG, column=PointPlaceTwo.COL_LONG, sticky=W)
        
        field = "ll_dist"
        width = 10
        self.ctls_vars[field] = content = StringVar()
        self.ctls_ctls[field] = entry = Entry(ctl_frame, textvariable=content, width=width)
        entry.grid(row=PointPlaceTwo.ROW_LL_DIST, column=PointPlaceTwo.COL_LL_DIST, sticky=W)
        
        field = "x_meter"
        width = self.mt_width    
        self.ctls_vars[field] = content = StringVar()
        Label(master=ctl_frame, text="x(meters)").grid(row=PointPlaceTwo.ROW_X_METER, column=PointPlaceTwo.COL_X_METER_LABEL)
        self.ctls_ctls[field] = entry = Entry(ctl_frame, textvariable=content, width=width, text="")
        entry.grid(row=PointPlaceTwo.ROW_X_METER, column=PointPlaceTwo.COL_X_METER, sticky=W)
        
        field = "y_meter"
        width = self.mt_width
        self.ctls_vars[field] = content = StringVar()
        Label(master=ctl_frame, text="y(meters)").grid(row=PointPlaceTwo.ROW_Y_METER, column=PointPlaceTwo.COL_Y_METER_LABEL)
        self.ctls_ctls[field] = entry = Entry(ctl_frame, textvariable=content, width=width, text="")
        entry.grid(row=PointPlaceTwo.ROW_Y_METER, column=PointPlaceTwo.COL_Y_METER, sticky=W)
        
        field = "meter_dist"
        width = self.mt_width    
        self.ctls_vars[field] = content = StringVar()
        self.ctls_ctls[field] = entry = Entry(ctl_frame, textvariable=content, width=width)
        entry.grid(row=PointPlaceTwo.ROW_METER_DIST, column=PointPlaceTwo.COL_METER_DIST, sticky=W)
            
        field = "x_pixel"
        width = self.px_width
        self.ctls_vars[field] = content = StringVar()
        Label(master=ctl_frame, text="x(pixels)").grid(row=PointPlaceTwo.ROW_X_PIXEL, column=PointPlaceTwo.COL_X_PIXEL_LABEL)
        self.ctls_ctls[field] = entry = Entry(ctl_frame, textvariable=content, width=width, text="")
        entry.grid(row=PointPlaceTwo.ROW_X_PIXEL, column=PointPlaceTwo.COL_X_PIXEL, sticky=W)
        
        field = "y_pixel"
        width = self.px_width
        self.ctls_vars[field] = content = StringVar()
        self.ctls_ctls[field] = entry = Entry(ctl_frame, textvariable=content, width=width, text="")
        entry.grid(row=PointPlaceTwo.ROW_PIXEL_DIST, column=PointPlaceTwo.COL_PIXEL_DIST, sticky=W)
        
        field = "pixel_dist"
        width = self.px_width
        self.ctls_vars[field] = content = StringVar()
        self.ctls_ctls[field] = entry = Entry(ctl_frame, textvariable=content, width=width, text="")
        entry.grid(row=PointPlaceTwo.ROW_PIXEL_DIST, column=PointPlaceTwo.COL_PIXEL_DIST, sticky=W)
            
        field = "canvas_x_pixel"
        width = self.px_width
        self.ctls_vars[field] = content = StringVar()
        Label(master=ctl_frame, text="canvas x(pixels)").grid(row=PointPlaceTwo.ROW_CANVAS_X_PIXEL,
                                                               column=PointPlaceTwo.COL_CANVAS_X_PIXEL_LABEL)
        self.ctls_ctls[field] = entry = Entry(ctl_frame, textvariable=content, width=width, text="")
        entry.grid(row=PointPlaceTwo.ROW_CANVAS_X_PIXEL, column=PointPlaceTwo.COL_CANVAS_X_PIXEL, sticky=W)
        
        field = "canvas_y_pixel"
        width = self.px_width
        self.ctls_vars[field] = content = StringVar()
        Label(master=ctl_frame, text="canvas y(pixels)").grid(row=PointPlaceTwo.ROW_CANVAS_Y_PIXEL,
                                                        column=PointPlaceTwo.COL_CANVAS_Y_PIXEL_LABEL)
        self.ctls_ctls[field] = entry = Entry(ctl_frame, textvariable=content, width=width, text="")
        entry.grid(row=PointPlaceTwo.ROW_CANVAS_Y_PIXEL, column=PointPlaceTwo.COL_CANVAS_Y_PIXEL, sticky=W)
        
        field = "canvas_dist"
        width = self.px_width
        self.ctls_vars[field] = content = StringVar()
        self.ctls_ctls[field] = entry = Entry(ctl_frame, textvariable=content, width=width, text="")
        entry.grid(row=PointPlaceTwo.ROW_CANVAS_PIXEL_DIST, column=PointPlaceTwo.COL_CANVAS_PIXEL_DIST, sticky=W)
            
        field = "point1_name"
        width = 4
        self.ctls_vars[field] = content = StringVar()
        Label(master=ctl_frame, text="Point Labels").grid(row=PointPlaceTwo.ROW_POINT_NAMES, column=PointPlaceTwo.COL_POINT_NAMES_LABEL)
        self.ctls_ctls[field] = entry = Entry(ctl_frame, textvariable=content, width=width)
        entry.grid(row=PointPlaceTwo.ROW_POINT_NAMES, column=PointPlaceTwo.COL_POINT1_NAME, sticky=W)
        self.set_ctl_val(field, "P1")      # content.set(field, "P1") doesn't work for me here
        field = "point2_name"
        self.ctls_vars[field] = content = StringVar()
        self.ctls_ctls[field] = entry = Entry(ctl_frame, textvariable=content, width=width)
        entry.grid(row=PointPlaceTwo.ROW_POINT_NAMES, column=PointPlaceTwo.COL_POINT2_NAME, sticky=W)
        self.set_ctl_val(field, "P2")
        
        field = "set_points"
        self.ctls_vars[field] = content = StringVar()
        self.ctls_ctls[field] = button = Button(ctl_frame, text="Add Point")
        button.grid(row=PointPlaceTwo.ROW_ADD_POINT, column=PointPlaceTwo.COL_ADD_POINT)
        
        field = "add_point"
        self.ctls_vars[field] = content = StringVar()
        self.ctls_ctls[field] = button = Button(ctl_frame, text="Add Point")
        button.grid(row=PointPlaceTwo.ROW_ADD_POINT, column=PointPlaceTwo.COL_ADD_POINT)
        self.point1 = point1
        self.point2 = point2
        if point1 is not None and point2 is not None:
            self.set_ctl_val("point1_name", self.point1.label)
            point1.add_tracker(self.point1_moved)
            self.set_ctl_val("point2_name", self.point2.label)
            point2.add_tracker(self.point2_moved)
            self.point1_moved(point1)               # Force first listing
        elif lat_long is not None:
            self.set_lat_long(lat_long)
        elif self.gmi is not None:
            lat_long = self.gmi.getCenter()
            self.set_lat_long(lat_long) 
        self.mw.protocol("WM_DELETE_WINDOW", self.delete_window)
        
        if self.track_sc:
            self.motion_update2 = self.sc.set_mouse_move_call(self.motion_update)    
        while self.tracking_sc:
            self.update()

    def point1_moved(self, point):
        self.point1 = point
        self.update_point2_minus_p1()
    
    def point2_moved(self, point):
        self.point2 = point
        self.update_point2_minus_p1()

    def update_point2_minus_p1(self):   
        """ Update differences between 2 and 1
        """
        p1 = self.point1 
        p2 = self.point2 
        
        p2c = CanvasCoords(self.sc, p2.x, p2.y)
        p1c = CanvasCoords(self.sc, p1.x, p1.y)
        
        meter_dist = sqrt((p2c.x_meter-p1c.x_meter)**2
                           +(p2c.y_meter-p1c.y_meter)**2)
        self.set_ctl_val("meter_dist", meter_dist)
        
        
    def delete_window(self):
        """ Delete window
        """
        if self.standalone:
            self.mw.destroy()
        else:
            super().destroy()
            
        self.mw = None

    def hide(self):
        """ Hide form
        """
        self.mw.withdraw()

    def show(self):
        """  Show form
        """
        self.mw.deiconify()
        
        
    def motion_update(self, x_pixel, y_pixel):
        """ Update based on position
        :x_pixel: x canvas position in pixels
        :y_pixel: y canvas position in pixels
        """
        self.set_canvas_xy(x_pixel,  y_pixel)
        self.show_point_at(x_pixel, y_pixel)
        if self.motion_update2 is not None:         # Used if another call setup
            self.motion_update2(x_pixel, y_pixel)
        
    def show_point_at(self, x_pixel, y_pixel):
        if self.show_point == PointPlaceTwo.SHOW_POINT_NONE:
            return              # Not showing point
        
        canvas = self.get_canvas()
        if self.show_point_tag is not None:
            canvas.delete(self.show_point_tag)
            self.show_point_tag = None
        char_size = 7
        text_fill = "white"
        text_size = 12
                
        x_image, y_image = self.canvas2image(x_pixel, y_pixel)
        
        if self.show_point == PointPlaceTwo.SHOW_POINT_LL:
            lat_long = self.gmi.pixelToLatLong((x_image, y_image))
            text = f"({lat_long[0]:{self.ll_fmt}}Lat, {lat_long[1]:{self.ll_fmt}}Long)"
        elif self.show_point == PointPlaceTwo.SHOW_POINT_METER:
            x_meter, y_meter = self.gmi.getPos(xY=(x_image, y_image), ref_latLong=self.ref_latLong)
            text = f"({x_meter:{self.mt_fmt}}m, {y_meter:{self.mt_fmt}}m)"
        elif self.show_point == PointPlaceTwo.SHOW_POINT_PIXEL:
            text = f"({x_image:{self.px_fmt}}, {y_image:{self.px_fmt}})"
        else:
            text = f"({x_pixel}, {y_pixel} ??)"
        
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
            
        self.show_point_tag = canvas.create_text(text_pos, text=text, fill=text_fill)

    def canvas2image(self, x_pixel, y_pixel):
        return self.sc.canvas2image(x_pixel, y_pixel)

    def get_canvas(self):
        """ Get our canvas
        """
        return self.sc.canv
     
    def set_canvas_xy(self, x_pixel, y_pixel):
        """ Set x,y canvas location, updating location display box
        :x_pixel: canvas x location
        :y_pixel: canvas y location
        """
        self.set_ctl_val("canvas_x_pixel", x_pixel, ".0f")
        self.set_ctl_val("canvas_y_pixel", y_pixel, ".0f")
        x_image, y_image = self.canvas2image(x_pixel, y_pixel)
        lat_long = self.gmi.pixelToLatLong((x_image, y_image))
        self.set_lat_long(lat_long)
        
    def set_ctl_val(self, field, val, fmt=".3"):
        """ Set value
        """
        setattr(self, field, val)               # Set internal value
        ctl_var = self.ctls_vars[field]         # Not updating the display
        if hasattr(self, "lat"):
            ctl_var.set(str(self.lat))          # Not updating the display
        ctl_ctl = self.ctls_ctls[field]         # Directly though control
        ctl_ctl.delete(0,END)
        fmt_str = f"{val:{fmt}}"
        ctl_ctl.insert(0, f"{fmt_str}")
        
    def set_lat_long(self, lat_long):
        """ Set latitude, longitude
        :lat_long: latitude,logitude (deg) pair
        """
        self.lat = lat_long[0]
        self.long = lat_long[1]
        self.set_ctl_val("latitude", lat_long[0], self.ll_fmt)
        self.set_ctl_val("longitude", lat_long[1], self.ll_fmt)
        if self.gmi is not None:
            x_meter, y_meter = self.gmi.getPos(latLong=lat_long, ref_latLong=self.ref_latLong)
            self.set_ctl_val("x_meter", x_meter, self.mt_fmt)
            self.set_ctl_val("y_meter", y_meter, self.mt_fmt)
            x_pixel, y_pixel = self.gmi.getXY(latLong=lat_long)
            self.set_ctl_val("x_pixel", x_pixel, self.px_fmt)
            self.set_ctl_val("y_pixel", y_pixel, self.px_fmt)

    def update(self):
        if  self.mw is not None:
            if self.mw.winfo_exists():
                self.mw.update()
        
if __name__ == "__main__":
    from GoogleMapImage import GoogleMapImage
    from scrolled_canvas import ScrolledCanvas
    from point_place import PointPlace
    from survey_point_manager import SurveyPointManager
    
    ulLat = 42.3760002
    ulLong = -71.1773149
    width = 1200
    height = 1000
    zoom=22
    lat_long = (ulLat, ulLong)
    gmi = GoogleMapImage(ulLat=ulLat, ulLong=ulLong, xDim=40, zoom=zoom)
    gmi.saveAugmented()
    sc = ScrolledCanvas(gmi=gmi, width=width, height=height)

    pp = PointPlace(sc=sc, title="Scrolled Canvas Tracking", lat_long=lat_long, track_sc=True)
    pp2 = PointPlaceTwo(title="Two Point Tracking")
    pt_mgr = SurveyPointManager(sc)

    mainloop()