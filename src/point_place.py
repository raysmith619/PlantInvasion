# point_place.py    21Apr2020    crs
"""
Measurement point to be position on an image
Provides an updated positioning information of the points position
"""
from tkinter import *

from select_trace import SlTrace


class PointPlace(Toplevel):
    # Display point position annotation
    SHOW_POINT_NONE = 1
    SHOW_POINT_LL = 2
    SHOW_POINT_METER = 3
    SHOW_POINT_PIXEL = 4

    ROW_TITLE = 0
    COL_TITLE = 3

    ROW_LAT = 1
    COL_LAT_LABEL = 1
    COL_LAT = COL_LAT_LABEL+1
    
    ROW_LONG = ROW_LAT
    COL_LONG_LABEL = COL_LAT + 1
    COL_LONG = COL_LONG_LABEL + 1
    
    ROW_LL_SET = ROW_LAT
    COL_LL_SET = COL_LONG + 1

    ROW_X_METER = ROW_LAT + 1
    COL_X_METER_LABEL = COL_LAT_LABEL
    COL_X_METER = COL_X_METER_LABEL+1
    
    ROW_Y_METER = ROW_X_METER
    COL_Y_METER_LABEL = COL_LONG_LABEL
    COL_Y_METER = COL_Y_METER_LABEL + 1
    
    ROW_XY_METER_SET = ROW_X_METER
    COL_XY_METER_SET = COL_Y_METER + 1

    ROW_X_PIXEL = ROW_X_METER + 1
    COL_X_PIXEL_LABEL = COL_LAT_LABEL
    COL_X_PIXEL = COL_X_PIXEL_LABEL+1
    
    ROW_Y_PIXEL = ROW_X_PIXEL
    COL_Y_PIXEL_LABEL = COL_LONG_LABEL
    COL_Y_PIXEL = COL_Y_PIXEL_LABEL + 1
    
    ROW_XY_PIXEL_SET = ROW_X_PIXEL
    COL_XY_PIXEL_SET = COL_Y_PIXEL + 1

    ROW_CANVAS_X_PIXEL = ROW_Y_PIXEL + 1
    COL_CANVAS_X_PIXEL_LABEL = COL_LAT_LABEL
    COL_CANVAS_X_PIXEL = COL_CANVAS_X_PIXEL_LABEL+1
    
    ROW_CANVAS_Y_PIXEL = ROW_CANVAS_X_PIXEL
    COL_CANVAS_Y_PIXEL_LABEL = COL_LONG_LABEL
    COL_CANVAS_Y_PIXEL = COL_CANVAS_Y_PIXEL_LABEL + 1
    
    ROW_CANVAS_XY_PIXEL_SET = ROW_CANVAS_X_PIXEL
    COL_CANVAS_XY_PIXEL_SET = COL_CANVAS_Y_PIXEL + 1

    ROW_POINT_NAME = ROW_CANVAS_X_PIXEL + 1
    COL_POINT_NAME_LABEL = COL_LAT_LABEL
    COL_POINT_NAME = COL_POINT_NAME_LABEL+1
    
    ROW_ADD_POINT = ROW_POINT_NAME
    COL_ADD_POINT = COL_POINT_NAME + 2
    
    def __init__(self, sc=None, parent=None, title=None,
                 position=None,
                 size=None,
                 lat_long=None,
                 track_sc=False,
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
        self.show_point = PointPlace.SHOW_POINT_METER
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
            title_label.grid(row=PointPlace.ROW_TITLE, column=PointPlace.COL_TITLE, columnspan=3)
            
        field = "latitude"
        width = self.ll_width
        self.ctls_vars[field] = content = StringVar()
        Label(master=ctl_frame, text="Latitude").grid(row=PointPlace.ROW_LAT, column=PointPlace.COL_LAT_LABEL)
        self.ctls_ctls[field] = entry = Entry(ctl_frame, textvariable=content, width=width)
        entry.grid(row=PointPlace.ROW_LAT, column=PointPlace.COL_LAT, sticky=W)
        
        field = "longitude"
        width = self.ll_width
        self.ctls_vars[field] = content = StringVar()
        Label(master=ctl_frame, text="Longitude").grid(row=PointPlace.ROW_LONG, column=PointPlace.COL_LONG_LABEL)
        self.ctls_ctls[field] = entry = Entry(ctl_frame, textvariable=content, width=width)
        entry.grid(row=PointPlace.ROW_LONG, column=PointPlace.COL_LONG, sticky=W)
        
        field = "set_ll"
        width = 20
        self.ctls_vars[field] = content = StringVar()
        self.ctls_ctls[field] = button = Button(ctl_frame, text="SET")
        button.grid(row=PointPlace.ROW_LL_SET, column=PointPlace.COL_LL_SET)
        
        field = "x_meter"
        width = self.mt_width    
        self.ctls_vars[field] = content = StringVar()
        Label(master=ctl_frame, text="x(meters)").grid(row=PointPlace.ROW_X_METER, column=PointPlace.COL_X_METER_LABEL)
        self.ctls_ctls[field] = entry = Entry(ctl_frame, textvariable=content, width=width, text="")
        entry.grid(row=PointPlace.ROW_X_METER, column=PointPlace.COL_X_METER, sticky=W)
        
        field = "y_meter"
        width = self.mt_width
        self.ctls_vars[field] = content = StringVar()
        Label(master=ctl_frame, text="y(meters)").grid(row=PointPlace.ROW_Y_METER, column=PointPlace.COL_Y_METER_LABEL)
        self.ctls_ctls[field] = entry = Entry(ctl_frame, textvariable=content, width=width, text="")
        entry.grid(row=PointPlace.ROW_Y_METER, column=PointPlace.COL_Y_METER, sticky=W)
        
        field = "set_xy_meter"
        self.ctls_vars[field] = content = StringVar()
        self.ctls_ctls[field] = button = Button(ctl_frame, text="SET")
        button.grid(row=PointPlace.ROW_XY_METER_SET, column=PointPlace.COL_XY_METER_SET)
            
        field = "x_pixel"
        width = self.px_width
        self.ctls_vars[field] = content = StringVar()
        Label(master=ctl_frame, text="x(pixels)").grid(row=PointPlace.ROW_X_PIXEL, column=PointPlace.COL_X_PIXEL_LABEL)
        self.ctls_ctls[field] = entry = Entry(ctl_frame, textvariable=content, width=width, text="")
        entry.grid(row=PointPlace.ROW_X_PIXEL, column=PointPlace.COL_X_PIXEL, sticky=W)
        
        field = "y_pixel"
        width = self.px_width
        self.ctls_vars[field] = content = StringVar()
        Label(master=ctl_frame, text="y(pixels)").grid(row=PointPlace.ROW_Y_PIXEL, column=PointPlace.COL_Y_PIXEL_LABEL)
        self.ctls_ctls[field] = entry = Entry(ctl_frame, textvariable=content, width=width, text="")
        entry.grid(row=PointPlace.ROW_Y_PIXEL, column=PointPlace.COL_Y_PIXEL, sticky=W)
        
        field = "set_xy_pixel"
        self.ctls_vars[field] = content = StringVar()
        self.ctls_ctls[field] = button = Button(ctl_frame, text="SET")
        button.grid(row=PointPlace.ROW_XY_PIXEL_SET, column=PointPlace.COL_XY_PIXEL_SET)
            
        field = "canvas_x_pixel"
        width = self.px_width
        self.ctls_vars[field] = content = StringVar()
        Label(master=ctl_frame, text="canvas x(pixels)").grid(row=PointPlace.ROW_CANVAS_X_PIXEL,
                                                               column=PointPlace.COL_CANVAS_X_PIXEL_LABEL)
        self.ctls_ctls[field] = entry = Entry(ctl_frame, textvariable=content, width=width, text="")
        entry.grid(row=PointPlace.ROW_CANVAS_X_PIXEL, column=PointPlace.COL_CANVAS_X_PIXEL, sticky=W)
        
        field = "canvas_y_pixel"
        width = self.px_width
        self.ctls_vars[field] = content = StringVar()
        Label(master=ctl_frame, text="canvas y(pixels)").grid(row=PointPlace.ROW_CANVAS_Y_PIXEL,
                                                        column=PointPlace.COL_CANVAS_Y_PIXEL_LABEL)
        self.ctls_ctls[field] = entry = Entry(ctl_frame, textvariable=content, width=width, text="")
        entry.grid(row=PointPlace.ROW_CANVAS_Y_PIXEL, column=PointPlace.COL_CANVAS_Y_PIXEL, sticky=W)
        
        field = "set_canvas_xy_pixel"
        self.ctls_vars[field] = content = StringVar()
        self.ctls_ctls[field] = button = Button(ctl_frame, text="SET")
        button.grid(row=PointPlace.ROW_CANVAS_XY_PIXEL_SET, column=PointPlace.COL_CANVAS_XY_PIXEL_SET)
            
        field = "point_name"
        width = 3
        self.ctls_vars[field] = content = StringVar()
        Label(master=ctl_frame, text="Point Label").grid(row=PointPlace.ROW_POINT_NAME, column=PointPlace.COL_POINT_NAME_LABEL)
        self.ctls_ctls[field] = entry = Entry(ctl_frame, textvariable=content, width=width, text="P")
        entry.grid(row=PointPlace.ROW_POINT_NAME, column=PointPlace.COL_POINT_NAME, sticky=W)
        
        field = "add_point"
        self.ctls_vars[field] = content = StringVar()
        self.ctls_ctls[field] = button = Button(ctl_frame, text="Add Point")
        button.grid(row=PointPlace.ROW_ADD_POINT, column=PointPlace.COL_ADD_POINT)

        if lat_long is not None:
            self.set_lat_long(lat_long)
        elif self.gmi is not None:
            lat_long = self.gmi.getCenter()
            self.set_lat_long(lat_long) 
        self.mw.protocol("WM_DELETE_WINDOW", self.delete_window)
        '''
        if self.track_sc:
            self.motion_update2 = self.sc.set_mouse_move_call(self.motion_update)    
        while self.tracking_sc:
            self.update()
        '''

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
        if self.show_point == PointPlace.SHOW_POINT_NONE:
            return              # Not showing point
        
        canvas = self.get_canvas()
        if self.show_point_tag is not None:
            canvas.delete(self.show_point_tag)
            self.show_point_tag = None
        char_size = 7
        text_fill = "white"
        text_size = 12
                
        x_image, y_image = self.canvas2image(x_pixel, y_pixel)
        
        if self.show_point == PointPlace.SHOW_POINT_LL:
            lat_long = self.gmi.pixelToLatLong((x_image, y_image))
            text = f"({lat_long[0]:{self.ll_fmt}}Lat, {lat_long[1]:{self.ll_fmt}}Long)"
        elif self.show_point == PointPlace.SHOW_POINT_METER:
            x_meter, y_meter = self.gmi.getPos(xY=(x_image, y_image), ref_latLong=self.ref_latLong)
            text = f"({x_meter:{self.mt_fmt}}m, {y_meter:{self.mt_fmt}}m)"
        elif self.show_point == PointPlace.SHOW_POINT_PIXEL:
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
        ctl_var.set(str(self.lat))              # Not updating the display
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
    
    ulLat = 42.3760002
    ulLong = -71.1773149
    width = 1200
    height = 1000
    zoom=22
    lat_long = (ulLat, ulLong)
    gmi = GoogleMapImage(ulLat=ulLat, ulLong=ulLong, xDim=40, zoom=zoom)
    gmi.saveAugmented()
    sc = ScrolledCanvas(gmi=gmi, width=width, height=height)

    pp = PointPlace(sc=sc, title="Testing PointPlace", lat_long=lat_long, track_sc=True)
    mainloop()