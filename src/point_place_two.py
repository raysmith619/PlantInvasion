# point_place_two.py    28Apr2020    crs
"""
Measurement between two points
Provides an updated positioning information of the points relation
"""
from tkinter import *
from math import sqrt

from select_trace import SlTrace
from select_error import SelectError
from canvas_coords import CanvasCoords
from GeoDraw import get_bearing
from survey_ruler import SurveyRuler
from docutils.nodes import row

class PointPlaceTwo(Toplevel):
    ID_PREFIX = "PP_"       # Unique tracking type prefix
    id_no = 0               # id no for this tracking type
    # Display point position annotation
    SHOW_POINT_NONE = 1
    SHOW_POINT_LL = 2
    SHOW_POINT_DIST = 3
    SHOW_POINT_PIXEL = 4
    
    CONNECTION_LINE_NONE = "none"
    CONNECTION_LINE_LINE = "line"
    CONNECTION_LINE_IBAR = "ibar"
    CONNECTION_LINE_RULER = "ruler"

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

    ROW_X_DIST = ROW_LAT + 1
    COL_X_DIST_LABEL = COL_LAT_LABEL
    COL_X_DIST = COL_X_DIST_LABEL+1
    
    ROW_Y_DIST = ROW_X_DIST
    COL_Y_DIST_LABEL = COL_LONG_LABEL
    COL_Y_DIST = COL_Y_DIST_LABEL + 1
    
    ROW_LINEAR_DIST = ROW_X_DIST
    COL_LINEAR_DIST = COL_Y_DIST + 1

    ROW_X_IMAGE_PIXEL = ROW_X_DIST + 1
    COL_X_IMAGE_PIXEL_LABEL = COL_LAT_LABEL
    COL_X_IMAGE_PIXEL = COL_X_IMAGE_PIXEL_LABEL+1
    
    ROW_Y_IMAGE_PIXEL = ROW_X_IMAGE_PIXEL
    COL_Y_IMAGE_PIXEL_LABEL = COL_X_IMAGE_PIXEL + 1
    COL_Y_IMAGE_PIXEL = COL_Y_IMAGE_PIXEL_LABEL + 1
    
    ROW_IMAGE_DIST = ROW_X_IMAGE_PIXEL
    COL_IMAGE_DIST = COL_Y_IMAGE_PIXEL + 1

    ROW_CANVAS_X_PIXEL = ROW_Y_IMAGE_PIXEL + 1
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
    
    ROW_P1_P2_HEADING_LABEL = ROW_POINT_NAMES
    COL_P1_P2_HEADING_LABEL = COL_POINT2_NAME + 1
    COL_P1_P2_HEADING = COL_P1_P2_HEADING_LABEL + 1

    ROW_CON_LINE_HEADING = ROW_P1_P2_HEADING_LABEL + 1
    COL_CON_LINE_HEADING = 1
        
    def __init__(self, sc=None, parent=None, title=None,
                 position=None,
                 size=None,
                 lat_long=None,
                 track_sc=False,
                 point1=None,
                 point2=None,
                 unit="f",           # folksy :)
                 connection_line=CONNECTION_LINE_LINE,
                 connection_line_width=2,
                 connection_line_color="red",
                 visible=True,
                 display_monitor=True,
                 show_points=True,
                 ):
        """
        :sc: scrollable canvas Must contain sc.gmi GoogleMapImage 
        :parent: - parent - call basis must have tc_destroy to be called if we close
        :title: Window title
        :position: form position (x,y) in pixels on screen
        :size: form size (width, hight) in in pixels of window
        :lat_long: optional starting point latitude, longitude
        :track_sc: Update, based on mouse motion, till Add Point clicked
        :color: color of connecting line
        :connection_line_type: type of connection line
        :connection_line_width: with of line in pixels
        :display_monitor: show connection attributes in monitor
            default: display
        :show_points: display end points
        :visible: connection is currently visible
                default: True - visible
        :unit" - linear unit default: "m"
        """
        self.mw = None
        PointPlaceTwo.id_no += 1
        self.tracking_id = f"{PointPlaceTwo.ID_PREFIX}{PointPlaceTwo.id_no}"
        self.sc = sc
        self.visible = visible
        if sc is not None:
            self.gmi = sc.gmi
            self.ref_latLong = self.gmi.get_ref_latLong() 
        else:
            self.gmi = None
            self.ref_latLong = None
             
        self.parent = parent
        self.title = title
        self.position = position
        self.size = size
        self.lat_long = lat_long
        self.point1 = point1
        self.point2= point2
        self.connection_line = connection_line
        self.connection_line_width = connection_line_width
        self.connection_line_color = connection_line_color
        self.display_monitor = display_monitor
        self.show_points = show_points
        self.mt_width = 10              # meter form entry width (char)
        self.px_width = 6               # pixel form entry width (char)
        self.ll_width = 11              # long/lat form entry width (char)
        self.px_fmt = ".0f"             # pixel format
        self.ll_fmt = ".7f"             # longitude/latitude format
        self.dis_fmt = ".3f"             # linear distance format
        self.ref_latLong = None         # Set to reference location when image is loaded
        self.show_point = PointPlaceTwo.SHOW_POINT_DIST
        self.show_point_tag = None      # show point text tag
        self.ctls = {}                  # Used by set_radio_button
        self.ctls_vars = {}             # var By field
        self.ctls_ctls = {}             # ctl By field
        self.ctls_labels = {}           # ctl labels (if one) by field
        self.track_sc = track_sc
        self.tracking_sc = track_sc     # cleared when done
        self.standalone = False
        self.motion_update2 = None     # Used if sc already has a motion call
        self.unit = unit
        self.connection_line_tag = None # Connection line tag(s), if any
        self.connection_line_ruler = None   # Ruler, if any
        self.connection_line_width=connection_line_width
        self.connection_line_color=connection_line_color
        self.display_monitor = display_monitor
        self.row = 0
        self.col = -1
        if display_monitor:
            self.setup_display_monitor()
        
        if self.point1 is not None and self.point2 is not None:
            self.set_ctl_val("point1_name", self.point1.label)
            self.point1.add_tracker(self.point1_moved)
            self.set_ctl_val("point2_name", self.point2.label)
            self.point2.add_tracker(self.point2_moved)
            self.point1_moved(point1)               # Force first listing
        elif self.lat_long is not None:
            self.set_lat_long(lat_long)
        elif self.gmi is not None:
            lat_long = self.gmi.getCenter()
            self.set_lat_long(lat_long) 
    
    def setup_display_monitor(self):
        """ Setup the two point tracking monitor window
        Called if and when a display monitor window is desired
        """
        if self.parent is None:
            parent = Tk()
            ###parent.withdraw()
            self.standalone = True
        self.mw = parent
        ###super().__init__(parent)
        top_frame = Frame(self.mw)
        top_frame.grid()
        ctl_frame = top_frame
        self.ctl_frame = ctl_frame
        self.top_frame = top_frame
        if self.title is not None:
            title_label = Label(master=self.top_frame, text=self.title, font="bold")
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
        
        field = "x_dist"
        width = self.mt_width    
        self.ctls_vars[field] = content = StringVar()
        self.ctls_labels[field] = label = Label(master=ctl_frame, text=f"x({self.unit})")
        label.grid(row=PointPlaceTwo.ROW_X_DIST, column=PointPlaceTwo.COL_X_DIST_LABEL)
        self.ctls_ctls[field] = entry = Entry(ctl_frame, textvariable=content, width=width, text="")
        entry.grid(row=PointPlaceTwo.ROW_X_DIST, column=PointPlaceTwo.COL_X_DIST, sticky=W)
        
        field = "y_dist"
        width = self.mt_width
        self.ctls_vars[field] = content = StringVar()
        self.ctls_labels[field] = label = Label(master=ctl_frame, text=f"y({self.unit})")
        label.grid(row=PointPlaceTwo.ROW_Y_DIST, column=PointPlaceTwo.COL_Y_DIST_LABEL)
        self.ctls_ctls[field] = entry = Entry(ctl_frame, textvariable=content, width=width, text="")
        entry.grid(row=PointPlaceTwo.ROW_Y_DIST, column=PointPlaceTwo.COL_Y_DIST, sticky=W)
        
        field = "linear_dist"
        width = self.mt_width    
        self.ctls_vars[field] = content = StringVar()
        self.ctls_ctls[field] = entry = Entry(ctl_frame, textvariable=content, width=width)
        entry.grid(row=PointPlaceTwo.ROW_LINEAR_DIST, column=PointPlaceTwo.COL_LINEAR_DIST, sticky=W)
            
        field = "x_image"
        width = self.px_width
        self.ctls_vars[field] = content = StringVar()
        Label(master=ctl_frame, text="x(image px)").grid(row=PointPlaceTwo.ROW_X_IMAGE_PIXEL, column=PointPlaceTwo.COL_X_IMAGE_PIXEL_LABEL)
        self.ctls_ctls[field] = entry = Entry(ctl_frame, textvariable=content, width=width, text="")
        entry.grid(row=PointPlaceTwo.ROW_X_IMAGE_PIXEL, column=PointPlaceTwo.COL_X_IMAGE_PIXEL, sticky=W)
        
        field = "y_image"
        width = self.px_width
        self.ctls_vars[field] = content = StringVar()
        Label(master=ctl_frame, text="y(image px)").grid(row=PointPlaceTwo.ROW_X_IMAGE_PIXEL, column=PointPlaceTwo.COL_Y_IMAGE_PIXEL_LABEL)
        self.ctls_ctls[field] = entry = Entry(ctl_frame, textvariable=content, width=width, text="")
        entry.grid(row=PointPlaceTwo.ROW_Y_IMAGE_PIXEL, column=PointPlaceTwo.COL_Y_IMAGE_PIXEL, sticky=W)
        
        field = "image_dist"
        width = self.px_width
        self.ctls_vars[field] = content = StringVar()
        self.ctls_ctls[field] = entry = Entry(ctl_frame, textvariable=content, width=width, text="")
        entry.grid(row=PointPlaceTwo.ROW_IMAGE_DIST, column=PointPlaceTwo.COL_IMAGE_DIST, sticky=W)
            
        field = "canvas_x"
        width = self.px_width
        self.ctls_vars[field] = content = StringVar()
        Label(master=ctl_frame, text="canvas x(pixels)").grid(row=PointPlaceTwo.ROW_CANVAS_X_PIXEL,
                                                               column=PointPlaceTwo.COL_CANVAS_X_PIXEL_LABEL)
        self.ctls_ctls[field] = entry = Entry(ctl_frame, textvariable=content, width=width, text="")
        entry.grid(row=PointPlaceTwo.ROW_CANVAS_X_PIXEL, column=PointPlaceTwo.COL_CANVAS_X_PIXEL, sticky=W)
        
        field = "canvas_y"
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

        field = "p1_p2_heading"
        width = self.ll_width
        self.ctls_vars[field] = content = StringVar()
        Label(master=ctl_frame, text="P1-P2 Heading").grid(
            row=PointPlaceTwo.ROW_P1_P2_HEADING_LABEL,
            column=PointPlaceTwo.COL_P1_P2_HEADING_LABEL)
        self.ctls_ctls[field] = entry = Entry(ctl_frame, textvariable=content, width=width)
        entry.grid(row=PointPlaceTwo.ROW_P1_P2_HEADING_LABEL,
                   column=PointPlaceTwo.COL_P1_P2_HEADING, sticky=W)

        field = "con_line"
        self.set_label(text="Connection",
                            row=PointPlaceTwo.ROW_CON_LINE_HEADING,
                            col=PointPlaceTwo.COL_CON_LINE_HEADING)
        self.set_radio_button(field=field,
                              label="none", set_value=self.connection_line,
                              command=self.change_connection_line)
        self.set_radio_button(field=field, label="line", command=self.change_connection_line)
        self.set_radio_button(field=field, label="ruler", command=self.change_connection_line)
        
        self.mw.protocol("WM_DELETE_WINDOW", self.delete_window)
        
        if self.track_sc:
            self.motion_update2 = self.sc.set_mouse_move_call(self.motion_update)    
        while self.tracking_sc:
            self.update()

    def change_line(self, line):
        line = line.lower()
        if line == "none":
            self.connection_line = PointPlaceTwo.CONNECTION_LINE_NONE
        if line == "line":
            self.connection_line = PointPlaceTwo.CONNECTION_LINE_LINE
        if line == "ruler":
            self.connection_line = PointPlaceTwo.CONNECTION_LINE_RULER
        self.update_connection()

    def change_color(self, color):
        self.connection_line_color = color
        self.update_connection()
        
    def change_width(self, width):
        self.connection_line_width = width
        self.update_connection()
        
        
    def change_line_attr(self, line=None, color=None,
                         width=None):
        if line is not None:
            self.change_line(line)
        if color is not None:
            self.change_color(color)
        if width is not None:
            self.change_width(width)
                    
    def point1_moved(self, point):
        self.point1 = point
        self.update_point2_minus_p1()
    
    def point2_moved(self, point):
        self.point2 = point
        self.update_point2_minus_p1()

    def update_point2_minus_p1(self):   
        """ Update differences between 2 and 1
        """
        if self.display_monitor:
            p1 = self.point1 
            p1c = CanvasCoords(self.sc, lat=p1.lat, long=p1.long, unit=self.unit)
            p2 = self.point2
            if SlTrace.trace("track_scale"):
                SlTrace.lg(f"tracking: {p1} to {p2}")         
            p2c = CanvasCoords(self.sc, lat=p2.lat, long=p2.long, unit=self.unit)
            
            latitude_dist = p2c.lat - p1c.lat
            self.set_ctl_val("latitude", latitude_dist, fmt=self.ll_fmt)
            
            longitude_dist = p2c.long - p1c.long
            self.set_ctl_val("longitude", longitude_dist, fmt=self.ll_fmt)
            
            ll_dist = sqrt(latitude_dist**2
                               + longitude_dist**2)
            self.set_ctl_val("ll_dist", ll_dist, fmt=self.ll_fmt)
            
            x_dist = p2c.x_dist - p1c.x_dist
            self.set_ctl_label("x_dist", f"x({self.unit})")
            self.set_ctl_val("x_dist", x_dist, fmt=self.dis_fmt)
            
            y_dist = p2c.y_dist - p1c.y_dist
            self.set_ctl_label("y_dist", f"y({self.unit})")
            self.set_ctl_val("y_dist", y_dist, fmt=self.dis_fmt)
            
            linear_dist = sqrt((p2c.x_dist-p1c.x_dist)**2
                               +(p2c.y_dist-p1c.y_dist)**2)
            self.set_ctl_val("linear_dist", linear_dist, fmt=self.dis_fmt)
            if SlTrace.trace("track_scale"):
                gmi = self.get_gmi()
                SlTrace.lg(f"p1 x_dist:{p1c.x_dist:{self.dis_fmt}} y_dist:{p1c.y_dist:{self.dis_fmt}}")
                SlTrace.lg(f"p2 x_dist:{p2c.x_dist:{self.dis_fmt}} y_dist:{p2c.y_dist:{self.dis_fmt}}")
                SlTrace.lg(f"p2-p1 x_dist:{p2c.x_dist-p1c.x_dist:{self.dis_fmt}} y_dist:{p2c.y_dist-p1c.y_dist:{self.dis_fmt}}")
                SlTrace.lg(f"linear_dist:{linear_dist:{self.dis_fmt}} {self.unit}")
                geo_dist = gmi.geoDist((p2c.lat,p2c.long),
                                      (p1c.lat,p1c.long),
                                       unit=self.unit)
                SlTrace.lg(f"geoDist:{geo_dist:{self.dis_fmt}} {self.unit}")
            x_image = p2c.x_image - p1c.x_image
            self.set_ctl_label("x_image", f"x({self.unit})")
            self.set_ctl_val("x_image", x_image, fmt=self.px_fmt)
            
            y_image = p2c.y_image - p1c.y_image
            self.set_ctl_label("y_image", f"y({self.unit})")
            self.set_ctl_val("y_image", y_image, fmt=self.px_fmt)
            
            image_dist = sqrt((p2c.x_image-p1c.x_image)**2
                               +(p2c.y_image-p1c.y_image)**2)
            self.set_ctl_val("image_dist", image_dist, fmt=self.px_fmt)
            
            canvas_x = p2c.canvas_x - p1c.canvas_x
            self.set_ctl_label("canvas_x", f"x({self.unit})")
            self.set_ctl_val("canvas_x", canvas_x, fmt=self.px_fmt)
            
            canvas_y = p2c.canvas_y - p1c.canvas_y
            self.set_ctl_label("canvas_y", f"y({self.unit})")
            self.set_ctl_val("canvas_y", canvas_y, fmt=self.px_fmt)
            
            canvas_dist = sqrt((p2c.canvas_x-p1c.canvas_x)**2
                               +(p2c.canvas_y-p1c.canvas_y)**2)
            self.set_ctl_val("canvas_dist", canvas_dist, fmt=self.px_fmt)
            
            p1_p2_heading = get_bearing(p1,p2)
            self.set_ctl_val("p1_p2_heading", p1_p2_heading, fmt=self.ll_fmt)

        self.update_connection() 

    def redisplay(self):
        self.update_connection()

    def update_connection(self):
        """ Update connection view between tracked point pairs
        """
        iodraw = self.get_iodraw()
        if self.connection_line_tag is not None:
            iodraw.delete_tag(self.connection_line_tag)
            self.connection_line_tag = None
        if self.connection_line_ruler is not None:
            self.connection_line_ruler.delete()
            self.connection_line_ruler = None    
        if not self.visible:
            return
        
        p1 = self.point1 
        p1_canvas_x, p1_canvas_y = self.sc.ll_to_canvas(lat=p1.lat, long=p1.long)
        p2 = self.point2         
        p2_canvas_x, p2_canvas_y = self.sc.ll_to_canvas(lat=p2.lat, long=p2.long)
        if self.connection_line == PointPlaceTwo.CONNECTION_LINE_NONE:
            return
        
        if self.connection_line == PointPlaceTwo.CONNECTION_LINE_LINE:
            self.connection_line_tag = iodraw.drawLine(
                (p1_canvas_x, p1_canvas_y), (p2_canvas_x, p2_canvas_y),
                color=self.connection_line_color,
                width=self.connection_line_width)
        elif self.connection_line == PointPlaceTwo.CONNECTION_LINE_RULER:
            self.show_ruler(p1,p2)
        elif self.connection_line == PointPlaceTwo.CONNECTION_LINE_IBAR:
            pass
        if self.show_points:
            p1.display()        # Redisplay points
            p2.display()

    def show_ruler(self,p1, p2):
        """ Show connection line as a ruler
        :p1: starting point
        :p2: ending point
        """
        if self.connection_line_ruler is not None:
            self.connection_line_ruler.delete()
            self.connection_line_ruler = None
        p1_canvas_x, p1_canvas_y = self.sc.ll_to_canvas(lat=p1.lat, long=p1.long)
        p2_canvas_x, p2_canvas_y = self.sc.ll_to_canvas(lat=p2.lat, long=p2.long)
        ruler = SurveyRuler(p1.mgr,
                    xY=(p1_canvas_x, p1_canvas_y),
                    xYEnd=(p2_canvas_x, p2_canvas_y),
                    color=self.connection_line_color,
                    width=self.connection_line_width,
                    unit=self.unit)
        ruler.display()
        self.connection_line_ruler = ruler                 
    def delete_window(self):
        """ Delete window
        """
        if self.standalone:
            self.mw.destroy()
        else:
            super().destroy()
            
        self.mw = None

    def hide(self):
        """ Hide connection and form
        """
        if self.mw is not None:
            self.mw.withdraw()
        self.visible = False
        self.redisplay()

    def show(self):
        """  Show form
        """
        if self.mw is not None:
            self.mw.deiconify()
        self.visible = True
        self.redisplay()
        
        
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
        
        iodraw = self.get_iodraw()
        if self.show_point_tag is not None:
            iodraw.delete_tag(self.show_point_tag)
            self.show_point_tag = None
        char_size = 7
        text_color = "white"
        text_size = 12
                
        x_image, y_image = self.canvas2image(x_pixel, y_pixel)
        
        if self.show_point == PointPlaceTwo.SHOW_POINT_LL:
            lat_long = self.gmi.pixelToLatLong((x_image, y_image))
            text = f"({lat_long[0]:{self.ll_fmt}}Lat, {lat_long[1]:{self.ll_fmt}}Long)"
        elif self.show_point == PointPlaceTwo.SHOW_POINT_DIST:
            x_dist, y_dist = self.gmi.getPos(xY=(x_image, y_image), ref_latLong=self.ref_latLong)
            text = f"({x_dist:{self.dis_fmt}}{self.unit}, {y_dist:{self.dis_fmt}}{self.unit})"
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
        elif x_pixel > iodraw.getWidth() - text_push:
            text_x_off = - text_push
        if y_pixel > iodraw.getHeight() - text_push_v:
            text_y_off = -1*text_push_v
        text_pos = (x_pixel+text_x_off, y_pixel+text_y_off)
            
        self.show_point_tag = iodraw.drawText(text_pos, text=text, color=text_color)

    def canvas2image(self, x_pixel, y_pixel):
        return self.sc.canvas2image(x_pixel, y_pixel)

    def get_iodraw(self):
        """ Get our drawing object
        """
        return self.sc.get_iodraw()
     
    def set_canvas_xy(self, x_pixel, y_pixel):
        """ Set x,y canvas location, updating location display box
        :x_pixel: canvas x location
        :y_pixel: canvas y location
        """
        if self.display_monitor:
            self.set_ctl_val("canvas_x_pixel", x_pixel, ".0f")
            self.set_ctl_val("canvas_y_pixel", y_pixel, ".0f")
        x_image, y_image = self.canvas2image(x_pixel, y_pixel)
        lat_long = self.gmi.pixelToLatLong((x_image, y_image))
        self.set_lat_long(lat_long)
        
    def set_ctl_val(self, field, val, fmt=".3"):
        """ Set value
        """
        setattr(self, field, val)               # Set internal value
        if not self.display_monitor:
            return
        if field not in self.ctls_vars:
            SlTrace.lg(f"ctls_vars:{', '.join(self.ctls_vars.keys())}")
        ctl_var = self.ctls_vars[field]         # Not updating the display
        if hasattr(self, "lat"):
            ctl_var.set(str(self.lat))          # Not updating the display
        ctl_ctl = self.ctls_ctls[field]         # Directly though control
        ctl_ctl.delete(0,END)
        fmt_str = f"{val:{fmt}}"
        ctl_ctl.insert(0, f"{fmt_str}")
        
    def set_ctl_label(self, field, label):
        """ Set field's associated label, if one
        """
        if not self.display_monitor:
            return
        
        if field in self.ctls_labels:
            ctl_label = self.ctls_labels[field]
            ctl_label.config(text=label)

    def set_label(self, text, row=None, col=None):
        """ Set text label
        :text: text label
        :row:  row, default current row
        :col: col, current column
        """
        if row is None:
            row = self.row
        else:
            self.row = row
        if col is None:
            col = self.col
        else:
            self.col = col
        Label(master=self.ctl_frame, text=text).grid(row=row, column=col)

        
    def set_radio_button(self, field, row=None, col=None,
                        label=None, value=None, set_value=None,
                        command=None):
        """ Set up one radio button for field
        :field: identifying field
        :row: grid row, default: use current row
        :col: grid column, default add one to current col
        :label: button label - must be unique in this group
        :value: value associated with this button
                    default: label string
        :set_value: set group value if present
                    default: leave group_value alone
                    Anyone of the set_radio_button calls
                    can set/change the value
                    if present, value is overridden
                    by property value
        :command: function called with button group value when button selected
        
        """
        if row is None:
            row = self.row
        else:
            self.row = row
        if col is None:
            self.col += 1
            col = self.col
        else:
            self.col = col
        if label is None:
            SelectError("set_radio_button - label is missing")
        if value is None:
            value = label
        if command is None:
            cmd = None
        else:
            cmd=lambda cmd=command : cmd(value)
            
            
        full_field = field
        if full_field not in self.ctls_vars:
            content = StringVar()          # Create new one for group
            self.ctls_vars[full_field] = content
            ctls_ctl = self.ctls[full_field] = {}  # dictionary of Radiobutton button widgets
        else:
            content = self.ctls_vars[full_field]
            ctls_ctl = self.ctls[full_field]
        if set_value is not None:
            content.set(set_value)
        widget =  Radiobutton(master=self.ctl_frame, variable=content,
                            text=label, value=value,
                            command=cmd)
        widget.grid(row=row, column=col)
        ctls_ctl[full_field + "." + label] = widget           # Store each button in hash

        
    def set_lat_long(self, lat_long):
        """ Set latitude, longitude
        :lat_long: latitude,logitude (deg) pair
        """
        self.lat = lat_long[0]
        self.long = lat_long[1]
        if self.display_monitor:
            self.set_ctl_val("latitude", lat_long[0], self.ll_fmt)
            self.set_ctl_val("longitude", lat_long[1], self.ll_fmt)
        if self.gmi is not None:
            x_dist, y_dist = self.gmi.getPos(latLong=lat_long, unit=self.unit, ref_latLong=self.ref_latLong)
            if self.display_monitor:
                self.set_ctl_val("x_dist", x_dist, self.dis_fmt)
                self.set_ctl_val("y_dist", y_dist, self.dis_fmt)
                x_pixel, y_pixel = self.gmi.getXY(latLong=lat_long)
                self.set_ctl_val("x_pixel", x_pixel, self.px_fmt)
                self.set_ctl_val("y_pixel", y_pixel, self.px_fmt)

    def update(self):
        if  self.mw is not None:
            if self.mw.winfo_exists():
                self.mw.update()

    def change_connection_line(self, line):
        """ Change linear unit, including label display
        :line:  line-type
        """
        self.connection_line = line
        self.update_point2_minus_p1()

    def change_unit(self, unit):
        """ Change linear unit, including label display
        :unit:  unit measure
        """
        self.unit = unit
        if self.display_monitor:
            self.set_ctl_label("x_dist", f"x({unit})")
            self.set_ctl_label("y_dist", f"y({unit})")
        self.update_point2_minus_p1()
    
    def destroy(self):
        """ Release resources
        """
        iodraw = self.get_iodraw()
        if iodraw is None:
            return
        
        if self.connection_line_tag is not None:
            iodraw.delete_tag(self.connection_line_tag)
            self.connection_line_tag = None
        if self.connection_line_ruler is not None:
            self.connection_line_ruler.delete()
            self.connection_line_ruler = None
        if self.standalone and self.mw is not None:
            self.mw.destroy()
            self.mw = None

    def get_gmi(self):
        return self.sc.gmi
    
if __name__ == "__main__":
    from select_trace import SlTrace
    
    from GoogleMapImage import GoogleMapImage
    from scrolled_canvas import ScrolledCanvas
    from point_place import PointPlace
    from manage_survey_point import SurveyPointManager
    from survey_point import SurveyPoint
    ulLat = 42.3760002
    ulLong = -71.1773149
    width = 1200
    height = 1000
    no_display = True
    if no_display:
        zoom=18
        lat_long = (ulLat, ulLong)
        gmi = GoogleMapImage(ulLat=ulLat, ulLong=ulLong, xDim=40, zoom=zoom)
        gmi.saveAugmented()
        sc = ScrolledCanvas(gmi=gmi, width=width, height=height)
        pt_mgr = sc.get_pt_mgr()
        p1 = SurveyPoint(pt_mgr, lat=ulLat, long=ulLong)
        p2_lat, p2_long = gmi.addToPointLL(latLong=(p1.lat, p1.long), leng=20, deg=0.)
        p2 = SurveyPoint(pt_mgr, lat=p2_lat, long=p2_long)
        pp2_no_dis = PointPlaceTwo(sc, p1, p2, display_monitor=False)
        SlTrace.lg("After no display tracking")
        mainloop()
    else:        
        zoom=20
        lat_long = (ulLat, ulLong)
        gmi = GoogleMapImage(ulLat=ulLat, ulLong=ulLong, xDim=40, zoom=zoom)
        gmi.saveAugmented()
        sc = ScrolledCanvas(gmi=gmi, width=width, height=height)
    
        pp = PointPlace(sc=sc, title="Scrolled Canvas Tracking", lat_long=lat_long, track_sc=True)
        pp2 = PointPlaceTwo(title="Two Point Tracking")
        pp2_no_dis = PointPlaceTwo(lat_long=lat_long, track_sc=True)
        pt_mgr = SurveyPointManager(sc)
        mainloop()