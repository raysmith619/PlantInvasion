# point_place.py    21Apr2020    crs
"""
Measurement point to be position on an image
Provides an updated positioning information of the points position
"""
from tkinter import *

from select_trace import SlTrace
from canvas_coords import CanvasCoords

class PointPlace(Toplevel):
    ID_PREFIX = "PP_"       # Unique tracking type prefix
    id_no = 0               # id no for this tracking type
    # Display point position annotation
    SHOW_POINT_NONE = 1
    SHOW_POINT_LL = 2
    SHOW_POINT_DIST = 3
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

    ROW_X_LINEAR = ROW_LAT + 1
    COL_X_LINEAR_LABEL = COL_LAT_LABEL
    COL_X_LINEAR = COL_X_LINEAR_LABEL+1
    
    ROW_Y_LINEAR = ROW_X_LINEAR
    COL_Y_LINEAR_LABEL = COL_LONG_LABEL
    COL_Y_LINEAR = COL_Y_LINEAR_LABEL + 1
    
    ROW_XY_LINEAR_SET = ROW_X_LINEAR
    COL_XY_LINEAR_SET = COL_Y_LINEAR + 1

    ROW_X_PIXEL = ROW_X_LINEAR + 1
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
    
    ROW_SNAP_SHOT = ROW_POINT_NAME
    COL_SNAP_SHOT = COL_POINT_NAME + 2
    
    def __init__(self, sc=None, parent=None, title=None,
                 point=None,
                 lat_long=None,
                 track_sc=False,
                 cursor_info="lat_long",
                 unit="f"       # Folksey
                 ):
        
        
        """
        :sc: scrollable canvas Must contain sc.gmi GoogleMapImage 
        :parent: - parent - call basis must have tc_destroy to be called if we close
        :title: Window title
        :position: form position (x,y) in pixels on screen
        :size: form size (width, hight) in in pixels of window
        :point: tracked point
        :lat_long: optional starting point latitude, longitude
        :track_sc: Update, based on mouse motion, till Add Point clicked
        :cursor_info: displayed cursor info default: "lat_long"
        :unit: linear length unit m,y,f default: f
        """
        PointPlace.id_no += 1
        self.tracking_id = f"{PointPlace.ID_PREFIX}{PointPlace.id_no}"
        self.connection_line_tag = None # If we have a line
        self.dis_width = 10              # linear form entry width (char)
        self.px_width = 5               # pixel form entry width (char)
        self.ll_width = 11              # long/lat form entry width (char)
        self.px_fmt = ".0f"             # pixel format
        self.ll_fmt = ".7f"             # longitude/latitude format
        self.dis_fmt = ".1f"             # linear format
        self.ref_latLong = None         # Set to reference location when image is loaded
        self.show_point = PointPlace.SHOW_POINT_DIST
        self.show_point_tag = None      # show point text tag
        self.ctls_vars = {}             # var By field   NOTE: This duplicates support in SelectControlWindow
        self.ctls_ctls = {}             # ctl By field
        self.ctls_labels = {}
        self.track_sc = track_sc
        self.unit = unit
        self.tracking_sc = track_sc     # cleared when done
        self.cursor_info = cursor_info
        self.standalone = False
        self.motion_update2 = None     # Used if sc already has a motion call
        self.point = point
        if parent is None:
            parent = Tk()
            ###parent.withdraw()
            self.standalone = True
        self.mw = parent
        super().__init__(parent)
        self.sc = sc
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
        self.ctls_labels[field] = label = Label(master=ctl_frame, text="Latitude")
        label.grid(row=PointPlace.ROW_LAT, column=PointPlace.COL_LAT_LABEL)
        self.ctls_ctls[field] = entry = Entry(ctl_frame, textvariable=content, width=width)
        entry.grid(row=PointPlace.ROW_LAT, column=PointPlace.COL_LAT, sticky=W)
        
        field = "longitude"
        width = self.ll_width
        self.ctls_vars[field] = content = StringVar()
        self.ctls_labels[field] = label = Label(master=ctl_frame, text="Longitude")
        label.grid(row=PointPlace.ROW_LONG, column=PointPlace.COL_LONG_LABEL)
        self.ctls_ctls[field] = entry = Entry(ctl_frame, textvariable=content, width=width)
        entry.grid(row=PointPlace.ROW_LONG, column=PointPlace.COL_LONG, sticky=W)
        
        field = "set_ll"
        width = 20
        self.ctls_vars[field] = content = StringVar()
        self.ctls_ctls[field] = button = Button(ctl_frame, text="SET")
        button.grid(row=PointPlace.ROW_LL_SET, column=PointPlace.COL_LL_SET)
        
        field = "x_dist"
        width = self.dis_width    
        self.ctls_vars[field] = content = StringVar()
        self.ctls_labels[field] = label = Label(master=ctl_frame, text=f"x({self.unit})")
        label.grid(row=PointPlace.ROW_X_LINEAR, column=PointPlace.COL_X_LINEAR_LABEL)
        self.ctls_ctls[field] = entry = Entry(ctl_frame, textvariable=content, width=width, text="")
        entry.grid(row=PointPlace.ROW_X_LINEAR, column=PointPlace.COL_X_LINEAR, sticky=W)
        
        field = "y_dist"
        width = self.dis_width
        self.ctls_vars[field] = content = StringVar()
        self.ctls_labels[field] = label = Label(master=ctl_frame, text=f"y({self.unit})")
        label.grid(row=PointPlace.ROW_Y_LINEAR, column=PointPlace.COL_Y_LINEAR_LABEL)
        self.ctls_ctls[field] = entry = Entry(ctl_frame, textvariable=content, width=width, text="")
        entry.grid(row=PointPlace.ROW_Y_LINEAR, column=PointPlace.COL_Y_LINEAR, sticky=W)
        
        field = "set_xy_dist"
        self.ctls_vars[field] = content = StringVar()
        self.ctls_ctls[field] = button = Button(ctl_frame, text="SET")
        button.grid(row=PointPlace.ROW_XY_LINEAR_SET, column=PointPlace.COL_XY_LINEAR_SET)
            
        field = "x_image"
        width = self.px_width
        self.ctls_vars[field] = content = StringVar()
        self.ctls_labels[field] = label = Label(master=ctl_frame, text="x(image px)")
        label.grid(row=PointPlace.ROW_X_PIXEL, column=PointPlace.COL_X_PIXEL_LABEL)
        self.ctls_ctls[field] = entry = Entry(ctl_frame, textvariable=content, width=width, text="")
        entry.grid(row=PointPlace.ROW_X_PIXEL, column=PointPlace.COL_X_PIXEL, sticky=W)
        
        field = "y_image"
        width = self.px_width
        self.ctls_vars[field] = content = StringVar()
        self.ctls_labels[field] = label = Label(master=ctl_frame, text="y(image px)")
        label.grid(row=PointPlace.ROW_Y_PIXEL, column=PointPlace.COL_Y_PIXEL_LABEL)
        self.ctls_ctls[field] = entry = Entry(ctl_frame, textvariable=content, width=width, text="")
        entry.grid(row=PointPlace.ROW_Y_PIXEL, column=PointPlace.COL_Y_PIXEL, sticky=W)
        
        field = "set_image_xy"
        self.ctls_vars[field] = content = StringVar()
        self.ctls_ctls[field] = button = Button(ctl_frame, text="SET")
        button.grid(row=PointPlace.ROW_XY_PIXEL_SET, column=PointPlace.COL_XY_PIXEL_SET)
            
        field = "canvas_x"
        width = self.px_width
        self.ctls_vars[field] = content = StringVar()
        self.ctls_labels[field] = label = Label(master=ctl_frame, text="canvas x(pixels)")
        label.grid(row=PointPlace.ROW_CANVAS_X_PIXEL, column=PointPlace.COL_CANVAS_X_PIXEL_LABEL)
        self.ctls_ctls[field] = entry = Entry(ctl_frame, textvariable=content, width=width, text="")
        entry.grid(row=PointPlace.ROW_CANVAS_X_PIXEL, column=PointPlace.COL_CANVAS_X_PIXEL, sticky=W)
        
        field = "canvas_y"
        width = self.px_width
        self.ctls_vars[field] = content = StringVar()
        self.ctls_labels[field] = label = Label(master=ctl_frame, text="canvas y(pixels)")
        label.grid(row=PointPlace.ROW_CANVAS_Y_PIXEL,
                                                        column=PointPlace.COL_CANVAS_Y_PIXEL_LABEL)
        self.ctls_ctls[field] = entry = Entry(ctl_frame, textvariable=content, width=width, text="")
        entry.grid(row=PointPlace.ROW_CANVAS_Y_PIXEL, column=PointPlace.COL_CANVAS_Y_PIXEL, sticky=W)
        
        field = "set_canvas_xy"
        self.ctls_vars[field] = content = StringVar()
        self.ctls_ctls[field] = button = Button(ctl_frame, text="SET")
        button.grid(row=PointPlace.ROW_CANVAS_XY_PIXEL_SET, column=PointPlace.COL_CANVAS_XY_PIXEL_SET)
            
        field = "point_name"
        width = 3
        self.ctls_vars[field] = content = StringVar()
        self.ctls_labels[field] = label = Label(master=ctl_frame, text="Point Label")
        label.grid(row=PointPlace.ROW_POINT_NAME, column=PointPlace.COL_POINT_NAME_LABEL)
        self.ctls_ctls[field] = entry = Entry(ctl_frame, textvariable=content, width=width, text="P")
        entry.grid(row=PointPlace.ROW_POINT_NAME, column=PointPlace.COL_POINT_NAME, sticky=W)
        
        field = "add_point"
        self.ctls_vars[field] = content = StringVar()
        self.ctls_ctls[field] = button = Button(ctl_frame, text="Snapshot", command=self.snapshot)
        button.grid(row=PointPlace.ROW_SNAP_SHOT, column=PointPlace.COL_SNAP_SHOT)

        if point is not None:
            self.update_coords(lat=point.lat, long=point.long)
            self.update_coords
        elif lat_long is not None:
            self.set_lat_long(lat_long)
        elif self.sc.gmi is not None:
            lat_long = self.sc.gmi.getCenter()
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
        self.destroy()
        
    def hide(self):
        """ Hide form
        """
        self.mw.withdraw()

    def show(self):
        """  Show form
        """
        self.mw.deiconify()

    def snapshot(self):
        """ Snapshot current point stats
        """
        if self.point is None:
            return
        
        self.point.snapshot(title=f"Tracking: {self.point.label}")
        
    def motion_update(self, canvas_x, canvas_y):
        """ Update based on position
        :canvas_x: x canvas position in pixels
        :canvas_y: y canvas position in pixels
        """
        self.set_canvas_xy(canvas_x,  canvas_y)
        self.show_point_at(canvas_x, canvas_y)
        if self.motion_update2 is not None:         # Used if another call setup
            self.motion_update2(canvas_x, canvas_y)
                
    def change_cursor_info(self, cursor_info):
        self.cursor_info = cursor_info

    def show_point_at(self, canvas_x, canvas_y):
        if self.cursor_info == "none":
            return              # Not showing point
        
        canvas = self.get_canvas()
        if self.show_point_tag is not None:
            canvas.delete(self.show_point_tag)
            self.show_point_tag = None
        char_size = 7
        text_fill = "white"
        text_size = 12
        pcs = CanvasCoords(self.sc, canvas_x=canvas_x, canvas_y=canvas_y, unit=self.unit)        
        if self.cursor_info == "none":
            text = None
        if self.cursor_info == "lat_long":
            text = f"({pcs.lat:{self.ll_fmt}}Lat, {pcs.long:{self.ll_fmt}}Long)"
        elif self.cursor_info == "dist":
            text = f"({pcs.x_dist:{self.dis_fmt}}{self.unit}, {pcs.y_dist:{self.dis_fmt}}{self.unit})"
        elif self.cursor_info == "image":
            text = f"({pcs.x_image:{self.px_fmt}}, {pcs.y_image:{self.px_fmt}})"
        elif self.cursor_info == "canvas":
            text = f"({pcs.canvas_x:{self.px_fmt}}, {pcs.canvas_y:{self.px_fmt}})"
        else:
            text = f"({pcs.lat:{self.ll_fmt}}Lat, {pcs.long:{self.ll_fmt}}Long)"
        if text is not None:
            text_push_v = char_size*2
            text_push = char_size*(len(text)/2.+1)   
            text_x_off = text_size
            text_y_off = text_x_off
            if canvas_x < text_push:
                text_x_off = text_push
            elif canvas_x > canvas.winfo_width() - text_push:
                text_x_off = - text_push
            if canvas_y > canvas.winfo_height() - text_push_v:
                text_y_off = -1*text_push_v
            text_pos = (canvas_x+text_x_off, canvas_y+text_y_off)
                
            self.show_point_tag = canvas.create_text(text_pos, text=text, fill=text_fill)

    def change_unit(self, unit):
        """ Change linear unit, including label display
        :unit:  unit measure
        """
        self.unit = unit
        self.set_ctl_label("x_dist", f"x({unit})")
        self.set_ctl_label("y_dist", f"y({unit})")
        self.update_coords()
        
    def canvas2image(self, canvas_x, canvas_y):
        return self.sc.canvas2image(canvas_x, canvas_y)

    def get_canvas(self):
        """ Get our canvas
        """
        return self.sc.canv
     
    def set_canvas_xy(self, canvas_x, canvas_y):
        """ Set x,y canvas location, updating location display box
        :canvas_x: canvas x location
        :canvas_y: canvas y location
        """
        pc = CanvasCoords(self.sc, canvas_x=canvas_x, canvas_y=canvas_y)
        
        self.update_coords(lat=pc.lat, long=pc.long)
            
            
        
    def set_ctl_val(self, field, val, fmt=".3"):   # NOTE: This duplicates support in SelectControlWindow
        """ Set value
        """
        setattr(self, field, val)               # Set internal value
        ctl_var = self.ctls_vars[field]         # Not updating the display
        ctl_var.set(str(val))              # Not updating the display
        ctl_ctl = self.ctls_ctls[field]         # Directly though control
        ctl_ctl.delete(0,END)
        fmt_str = f"{val:{fmt}}"
        ctl_ctl.insert(0, f"{fmt_str}")
        
    def set_ctl_label(self, field, label):
        """ Set field's associated label, if one
        """
        if field in self.ctls_labels:
            ctl_label = self.ctls_labels[field]
            ctl_label.config(text=label)
        else:
            SlTrace.lg(f"ctl_labels: {', '.join(self.ctls_labels)}")
            SlTrace.lg(f"field({field}) not present - label={label}")
            
    def set_lat_long(self, lat_long):
        """ Set latitude, longitude
        :lat_long: latitude,logitude (deg) pair
        """
        self.update_coords(lat=lat_long[0], long=lat_long[1])

    def redisplay(self):
        """ Redisplay tracking - Numbers may change
        """
        self.update_coords()
                
    def update_coords(self, lat=None, long=None):
        """ Update coords, refreshing displays
        :lat: latitude, default=use current (self.lat)
        :long: longitude default=use current (self.long
        """
        if self.point is None:
            return
        
        if lat is not None:
            self.point.lat = lat
        if long is not None:
            self.point.long = long
        lat = self.point.lat
        long = self.point.long
        if self.sc.gmi is None:
            return
        
        pc = CanvasCoords(self.sc, lat=lat, long=long)
        latitude = pc.lat
        self.set_ctl_val("latitude", latitude, fmt=self.ll_fmt)
        
        longitude = pc.long
        self.set_ctl_val("longitude", longitude, fmt=self.ll_fmt)
        
        x_dist = pc.x_dist
        self.set_ctl_label("x_dist", f"x({self.unit})")
        self.set_ctl_val("x_dist", x_dist, fmt=self.dis_fmt)
        
        y_dist = pc.y_dist
        self.set_ctl_label("y_dist", f"y({self.unit})")
        self.set_ctl_val("y_dist", y_dist, fmt=self.dis_fmt)
        
        x_image = pc.x_image
        self.set_ctl_label("x_image", f"x(image pix)")
        self.set_ctl_val("x_image", x_image, fmt=self.px_fmt)
        
        y_image = pc.y_image
        self.set_ctl_label("y_image", f"y(image pix)")
        self.set_ctl_val("y_image", y_image, fmt=self.px_fmt)
        
        canvas_x = pc.canvas_x
        self.set_ctl_label("canvas_x", f" x(canvas pixels)")
        self.set_ctl_val("canvas_x", canvas_x, fmt=self.px_fmt)
        
        canvas_y = pc.canvas_y
        self.set_ctl_label("canvas_y", f"y(canvas pixels)")
        self.set_ctl_val("canvas_y", canvas_y, fmt=self.px_fmt)


    def update(self):
        if  self.mw is not None:
            if self.mw.winfo_exists():
                self.mw.update()
    
    def destroy(self):
        """ Release resources
        """
        canvas = self.get_canvas()
        if canvas is None:
            return
        
        if self.connection_line_tag is not None:
            canvas.delete(self.connection_line_tag)
        if self.standalone and self.mw is not None:
            ###self.mw.destroy()        SELF.CHILDREN. - RECURSION LOOP
            self.mw = None
        
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