from tkinter import Frame, Canvas, Toplevel, YES, BOTH, SUNKEN
import PIL.ImageTk
import os
from math import cos, sin, pi

from select_trace import SlTrace
from select_error import SelectError
from GoogleMapImage import GoogleMapImage

class ScrolledCanvas(Frame):
    def __init__(self, fileName=None, gmi=None, image=None, title=None, parent=None,
                 mapRotate=None,
                 enlargeForRotate=False,
                 maptype=None,
                 map_address=None,
                 width=None, height=None,
                 mouse_down_call=None,
                 mouse_double_down_call=None,
                 mouse_up_call=None,
                 mouse_move_call=None,
                 resize_call=None,
                 skip_map_ctl=False,
                 map_ctl = None,
                 pt_mgr = None,
                 trailfile=None,
                 unit='m',
                 no_op=False,
                 ):
        """
        :fileName - image file, if present or info file if ending with .imageinfo else
        :gmi: GoogleMapImage, if present
        :image - image, if present
        :mapRotate: map rotation angle, in deg, counter clock wise, with respect to view
                    default: North (None)
        :enlargeForRotate: enlarge image load to account for
                    possible rotation, to facilitate upright pictures
                    default: False no enlargement
        :mouse_down_call: if present, function to call with x,y canvas coordinates
        :mouse_move_call: if present, function to call with x,y canvas coordinates
                             on mouse motion
        :resize_call: call after resize, if present
        :pt_mgr: point manager(SurveyPointManager) manage test points
                    default: create
        :skip_map_ctl: True -don't do map control - find places window
                    default: False - show window
        :map_ctl: Mapping Control (MappingControl) interface accessing addresses
                default: create
        :unit: Linear distance unit m(eter), y(ard), f(oot) - default: "m" - meter
        """
        self.mapRotate = mapRotate
        self.enlargeForRotate = enlargeForRotate
        self.isDown = False
        self.inside = False
        self.scroll_x = 0.          # Scrolling fractions
        self.scroll_y = 0.
        self.canvasAt = (0,0)
        self.canvasXy0 = (0,0)
        self.mouse_down_call = mouse_down_call
        self.mouse_double_down_call = mouse_double_down_call
        self.mouse_up_call = mouse_up_call
        self.mouse_move_call = mouse_move_call
        self.resize_call = resize_call
        self.unit = unit
        self.imOriginal = None      # For restoration/resize without loss
        self.standalone = False
        self.gmi = None
        self.image = None
        self.no_op = no_op
        self.cv_mark_tags = []    # Diagostic markings for canvas
        if no_op:
            return                  # Not a really functioning canvas, just a place holder 
        
        if parent is None:
            parent = Toplevel()
            self.standalone = True
        self.parent = parent
        Frame.__init__(self, parent)
        self.pack(expand=YES, fill=BOTH)
        self.canvas_container_frame = Frame(self)        # Used to hold frame which will be destroyed/reset when  updated
        self.canvas_container_frame.pack(expand=YES, fill=BOTH)
        
        """ resources created and destroyed in set_canvas """
        self.canvas_frame = None                        # created/destroyed each new canvas
        self.canv = None
        self.sbarH = None
        self.sbarV = None
        if title is None:
            if fileName is not None:
                title = os.path.basename(fileName)
            else:
                title = "Map Scroller"
        self.title = title
        self.maptype = maptype
        self.map_address = map_address
        self.width = width
        self.height = height
        if gmi is not None:
            self.update_gmi(gmi)
        elif image is not None:
            self.update_image(image)
        elif fileName is not None:
            self.update_file(fileName)
        else:
            ###raise SelectError("Must provide one of fileName, gmi, or image")
            SlTrace.lg("ScrolledCanvas: Blank Start")
        self.set_pt_mgr(pt_mgr)
        self.map_ctl = map_ctl
        self.curDeg = 0            # For addToPoint
        
    def get_pt_mgr(self):
        """ Return pt manager, created or passed in
        :returns: point manager (SurveyPointManager)
        """
        return self.pt_mgr

    def get_iodraw(self):    
        """ Get drawing object
        """
        return self.get_pt_mgr().get_iodraw()
    
    def get_map_ctl(self):
        """ Get mapping control (MappingControl), created or passed in
        :returns: return mapping control (MappingControl)
        """
        return self.map_ctl 

    def get_image(self):
        """ Get image from geoDraw
        """
        gmi = self.get_gmi()
        return gmi.get_image()

    def get_height(self):
        """ Get canvas height
        """
        return self.canv.winfo_height()

    def get_width(self):
        """ Get canvas width
        """
        return self.canv.winfo_width()

    def getXFract(self, canvas_x):
        return canvas_x/self.get_width()

    def getYFract(self, canvas_y):
        return canvas_y/self.get_height()


    def getXY(self, latLong=None, pos=None, xY=None, xYFract=None, unit=None):
        """
        Get/Convert canvas(overlay) pixel, map fraction, longitude, physical location/specification
        to pixel location
        """
        nloc_spec = 0
        if latLong is not None:
            nloc_spec += 1
        if pos is not None:
            nloc_spec += 1
            latLong = self.posToLatLong(pos)
        if xY is not None:
            nloc_spec += 1
        if xYFract is not None:
            nloc_spec += 1
        
        if nloc_spec > 1:
            raise SelectError("May specify, at most, one of latLong, pos, or xY or xYFract")
        
        if latLong is not None:
            xY =  self.ll_to_canvas(latLong[0], latLong[1])
        elif pos is not None:
            xY = self.pos_to_canvas(pos, unit=unit)
        elif xYFract is not None:
            xY = (xYFract[0]*self.get_canvas_width(), xYFract[1]*self.get_canvas_height())
        if xY is None:
            xY = self.curXY
        return xY

        
    def set_image(self, image=None):
        """ Set image, in preparation to save completed graphics file
        In genera, copy objects like trails which are canvas based objects to
        the image
        """
        if image is None:
            image = self.get_image()
        mgr = self.get_pt_mgr()
        if mgr is None:
            return
        trail = mgr.trail
        if trail is not None:
            ###trail.hide()
            self.gmi.addTrail(mgr.trail, width=trail.width*1.85)
            ###self.canv.tag_raise(self.imgtag)
            self.lower_image()
            ###self.size_image_to_canvas()

    def set_pt_mgr(self, pt_mgr):
        """ Set  up link with pt_mgr
        """
        self.pt_mgr = pt_mgr
        if pt_mgr is not None:
            self.set_resize_call(pt_mgr.resize)
                
    def set_resize_call(self, called):
        """ Link resize event to probably SurveyPointManager.resize
        :called:  function called with event
        """
        self.resize_call = called
                    
    def on_resize(self, event):
        # determine the ratio of old width/height to new width/height
        ###if self.imOriginal is None:
        ###    return                      # Nothing yet
        self.update()                   # Insure sizing completed
        new_width = event.width
        new_height = event.height
        new_width = new_height = min(new_width, new_height)
        self.canv.configure(width=new_width, height=new_height)
        self.canvas_width = new_width
        self.canvas_height = new_height
        SlTrace.lg("new width=%d height=%d" % (new_width, new_height), "resize")
        # resize the canvas 
        ###self.config(width=self.width, height=self.height)
        # rescale all the objects tagged with the "all" tag
        self.size_image_to_canvas()
    
    def size_image_to_canvas(self):
        self.update()
        if self.canv is None:
            return
        
        self.canvas_width = self.canv.winfo_width()
        self.canvas_height = self.canv.winfo_height()
        image = self.get_image()
        image = image.resize((self.canvas_width, self.canvas_height))
        ###self.set_image(image)
        self.canv.config(scrollregion=(0,0,self.canvas_width,self.canvas_height))
        self.im2=PIL.ImageTk.PhotoImage(image)
        self.imgtag=self.canv.create_image(0,0,anchor="nw",image=self.im2)
        self.lower_image()
        self.update()                   # Insure sizing completed
        SlTrace.lg(f"size_image_to_canvas: width: {self.get_width()} height: {self.get_height()}", "resize")
        if self.resize_call is not None:
            self.resize_call()
            
    def set_size(self, width=None, height=None):
        """ Set image size according to canvas size, possibley changed
        :width: canvas width in pixexs, if present - default: unchanged
        :height: canvas width in pixels, if present default: unchanged
        """
        # determine the ratio of old width/height to new width/height
        if width is not None:
            self.canvas_width = width
        if height is not None:
            self.canvas_height = height
        # resize the canvas 
        ###self.config(width=self.width, height=self.height)
        # rescale all the objects tagged with the "all" tag
        if self.imOriginal is None:
            return                      # Nothing yet
        
        if not hasattr(self, "canvas_width"):
            self.canvas_width = self.width
        if not hasattr(self, "canvas_height"):
            self.canvas_height = self.height
        image =  self.get_image().resize((self.canvas_width, self.canvas_height))
        self.canv.config(scrollregion=(0,0,self.canvas_width, self.canvas_height))
        ###self.im2=PIL.ImageTk.PhotoImage(image)
        self.imgtag=self.canv.create_image(0,0,anchor="nw",image=image)

    def ll_to_canvas(self, lat=None, long=None, trace=False):
        """ Convert Lat/Long to canvas x,y
        Transformation:
            1. Scale lat/Long offsets to unrotated canvas x,y Note that image has been
            resized to canvas.
            2. Rotate x,y to mapRotate
            
        Part of single purpose functions, replacing CanvasCoords
        
        :lat: latitude
        :long: Longitude
        :trace: trace operation - Debugging
        """
        gmi = self.get_gmi()
        lat_fract = gmi.getLatFract(lat)
        long_fract = gmi.getLongFract(long)
        canvas_width = self.get_width()
        canvas_height = self.get_height()
        c_x = long_fract*canvas_width
        c_y = lat_fract*canvas_height
        canvas_x, canvas_y = gmi.rotate_xy(x=c_x, y=c_y,
                                        width=canvas_width,
                                        height=canvas_height,
                                        deg=gmi.get_mapRotate())
        ###canvas_x, canvas_y = x_image, y_image
        if trace and SlTrace.trace("ll_to_canvas"):
            ll_fmt = ".6f"
            f_fmt = ".2f"
            i_fmt = ".1f"
            SlTrace.lg(f"lat:{lat:{ll_fmt}} lat_fract:{lat_fract:{f_fmt}}")
            SlTrace.lg(f"long:{long:{ll_fmt}} long_fract:{long_fract:{f_fmt}}")
            ###SlTrace.lg(f"x_image:{x_image:{i_fmt}} fract:{gmi.getXFract(x_image):{f_fmt}}"
            ###           f"  width: {gmi.getWidth():{i_fmt}}")
            ###SlTrace.lg(f"y_image:{y_image:{i_fmt}} fract:{self.getYFract(y_image):{f_fmt}}"
            ###           f"  height: {gmi.getHeight():{i_fmt}}")
            SlTrace.lg(f"canvas_x:{canvas_x:{i_fmt}} fract:{self.getXFract(canvas_x):{f_fmt}}"
                       f"  width: {self.get_width():{i_fmt}}")
            SlTrace.lg(f"canvas_y:{canvas_y:{i_fmt}} fract:{self.getYFract(canvas_y):{f_fmt}}"
                       f"  height: {self.get_height():{i_fmt}}")
        return canvas_x, canvas_y

    def canvas_to_ll(self, canvas_x=None, canvas_y=None, trace=False):
        """ Convert canvas x,y to Lat/Long
        Transformation: TBD
            
        Part of single purpose functions, replacing CanvasCoords
        
        :canvas_x: x offset in canvas
        :canvas_y: y offset (down) in canvas
        :trace: trace operation - Debugging
        """
        gmi = self.get_gmi()
        sc = self
        x_image, y_image = sc.canvas_to_image((canvas_x, canvas_y))
        lat, long = gmi.pixelToLatLong((x_image, y_image))
        if trace and SlTrace.trace("ll_to_canvas"):
            ll_fmt = ".6f"
            f_fmt = ".2f"
            i_fmt = ".1f"
            lat_fract = gmi.getLatFract(lat)
            long_fract = gmi.getLongFract(long)
            SlTrace.lg(f"canvas_x:{canvas_x:{i_fmt}} fract:{self.getXFract(canvas_x):{f_fmt}}"
                       f"  width: {self.get_width():{i_fmt}}")
            SlTrace.lg(f"canvas_y:{canvas_y:{i_fmt}} fract:{self.getYFract(canvas_y):{f_fmt}}"
                       f"  height: {self.get_height():{i_fmt}}")
            SlTrace.lg(f"x_image:{x_image:{i_fmt}} fract:{gmi.getXFract(x_image):{f_fmt}}"
                       f"  width: {gmi.getWidth():{i_fmt}}")
            SlTrace.lg(f"y_image:{y_image:{i_fmt}} fract:{self.getYFract(y_image):{f_fmt}}"
                       f"  height: {gmi.getHeight():{i_fmt}}")
            SlTrace.lg(f"lat:{lat:{ll_fmt}} lat_fract:{lat_fract:{f_fmt}}")
            SlTrace.lg(f"long:{long:{ll_fmt}} long_fract:{long_fract:{f_fmt}}")
        return lat, long
        
    def lower_image(self):
        self.canv.lower(self.imgtag)
        
    def raise_image(self):
        self.canv.tag_raise(self.imgtag)


    def mark_image_place(self):
        """ Mark image, as seen in canvas, for diagnostics
            with a temporary overlay (not in image)
        """
        if SlTrace.trace("mark_image"):
            gd = self.get_gmi().geoDraw
            canvas = self.canv
            if hasattr(self, "mki_tags"):
                if self.mki_tags:
                    for tag in self.mki_tags:
                        canvas.delete(tag)
                self.mki_tags = []
            mark_color = "purple"
            mark_width = 4
            w = gd.get_width()
            h = gd.get_height()
            p1_cx, p1_cy = w/2, 0
            p2_cx, p2_cy = w/2, h
            tag = canvas.create_line(
                p1_cx, p1_cy, p2_cx, p2_cy,
                fill=mark_color,
                width=mark_width)
            self.mki_tags.append(tag)
            p3_cx, p3_cy = 0, h/2
            p4_cx, p4_cy = w, h/2
            tag = canvas.create_line(
                p3_cx, p3_cy, p4_cx, p4_cy,
                fill=mark_color,
                width=mark_width)
            self.mki_tags.append(tag)
            pts = [(0,0), (w,0), (w,h/2), (w,h), (0,h), (0,0)]
            for i in range(1,len(pts)):
                p1_cx, p1_cy = pts[i-1][0], pts[i-1][1]
                p2_cx, p2_cy = pts[i][0], pts[i][1]
                tag = canvas.create_line(
                    p1_cx, p1_cy, p2_cx, p2_cy,
                    fill=mark_color,
                    width=mark_width+1)
                self.mki_tags.append(tag)
        self.update()
    
    def meterToMx(self, meter):
        """
        Convert horizontal position, in meters, to location in xpixels
        """
        
        gmi = self.get_gmi()
        image_pixel =  gmi.meterToPixel(meter)
        canvas_pixel = self.image_to_canvas(image_pixel,0)[0]   # use x,0, assume uniform over map
        return canvas_pixel
    
    def meterToMy(self, meter):
        gmi = self.get_gmi()
        image_pixel =  gmi.meterToPixel(meter)
        canvas_pixel = self.image_to_canvas(0, image_pixel,0)[1]   # use 0,y and assume uniform over map
        return canvas_pixel

    
    def mxToMeter(self, mx):
        """
        Convert horizontal location in pixels to horizontal location in meters
        """
        return mx/self.getWidth()*(self.lrX-self.ulX) + self.ulX
    
    def meterToPixel(self, meter):
        """
        meter to canvas pixel
        :meter: distance in meters
        """
        gmi = self.get_gmi()
        image_pixel =  gmi.meterToPixel(meter)
        canvas_pixel = self.image_to_canvas(image_pixel,0)[0]   # use x,0, assume uniform over map
        return canvas_pixel
    
    def pixelToMeter(self, pixel):
        """
        canvas pixel to meter
        :pixel: distance in pixels
        """
        gmi = self.get_gmi()
        image_pixel = self.canvas_to_image(pixel,0)[0]   # use x,0, assume uniform over map
        meter =  gmi.pixelToMeter(image_pixel)
        return meter

    
    def scale(self, wscale, hscale):
        """
        Scale canvas accordingly
        """
        width = self.width
        height = self.height
        self.canv.config(scrollregion=(0,0,width,height))
        self.image = self.image.resize(width, height)
        self.im2=PIL.ImageTk.PhotoImage(self.image)
        self.imgtag=self.canv.create_image(0,0,anchor="nw",image=self.im2)

    def down (self, event):
        self.isDown = True
        if self.inside:
            SlTrace.lg("Click in canvas event:%s" % event, "mouse")
            cnv = event.widget
            x,y = cnv.canvasx(event.x), cnv.canvasy(event.y)
            SlTrace.lg("x=%d y=%d" % (x,y), "mouse")
            self.canvasXy0 = (self.canv.canvasx(0), self.canv.canvasy(0))
            self.canvasAt = (x,y)
            self.dragged = 0
            self.config (cursor ="hand1")
            if self.mouse_down_call is not None:
                self.mouse_down_call(x,y)

    def double_down(self, event):
        """ Double clicking
        """
        cnv = event.widget
        x,y = cnv.canvasx(event.x), cnv.canvasy(event.y)
        if self.mouse_double_down_call is not None:
            self.mouse_double_down_call(x,y)
            
    def drawCircle(self, xY, radius=None, color=None, **kwargs):
        """ Draw circle on canvas(overlay)
        :xY: x,y coordinates
        :radius: radius in pixels
        :color: fill color
        :**kwargs: passed to elipse
        :returns: list of canvas tags
        """
        canvas = self.get_canvas()
        if radius is None:
            radius = 2
        if color is not None:
            kwargs['fill'] = color
        x, y = xY
        x0 = x - radius
        y0 = y - radius
        x1 = x + radius 
        y1 = y + radius 

        tag = canvas.create_oval(x0, y0, x1, y1,
                                    **kwargs)
        return tag

        
    def drawLine(self, *points, color=None, width=None, **kwargs):
        """ drawLine for canvas (overlay)
        :points:  0 or more x,y pairs
        :width: line width
        :**kwargs: remaining args passed to lowerlevel function
        """
        tags = []
        p1 = None
        canvas = self.get_canvas()
        for p2 in points:
            if p1 is not None:
                tag = canvas.create_line(p1[0],p1[1],p2[0],p2[1],
                                         fill=color, width=width, **kwargs)
                tags.append(tag)
            p1 = p2
        return tags

        
    def drawPolygon(self, *points, color=None, **kwargs):
        """ drawPolygon (ImageOverDraw overlay part)
        """
        if color is not None:
            kwargs['fill'] = color
        pts = []
        for point in points:
            pt = (int(point[0]), int(point[1]))
            pts.append(pt)
        canvas = self.get_canvas()
        tag = canvas.create_polygon(*pts, **kwargs)
        return tag


    def drawText(self, xY, text,  color=None, font=None,**kwargs):
        """ drawText (ImageOverDraw canvas/overlay part)
        :text: text string
        :xY: x,y pixel location
        :**kwargs: unused args passed on
        """
        canvas = self.get_canvas()
        text_x, text_y = xY
        
        tag = canvas.create_text(text_x, text_y,
                                text=text, font=font,
                                fill=color,
                                **kwargs)
        return tag

    
    def canvas2image_OLD(self, x_pixel, y_pixel):
        """ Convert canvas coordinates to image coordinates
        taking into consideration scrolling and scaling, rotation(TBD)
        :x_pixel: canvas x
        :y_pixel: canvas y
        :returns: (x_image, y_image)
        TBD - NEED to handle scrolling/resizing
        """
        canvas = self.get_canvas()
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        if self.gmi is None:
            raise SelectError("canvas2image has no gmi")
        
        image_width = self.gmi.getWidth()
        image_height = self.gmi.getHeight()

        x_image = x_pixel*image_width/canvas_width
        y_image = y_pixel*image_height/canvas_height
        return (x_image, y_image)
    
    def image2canvas_OLD(self, x_image, y_image):
        """ Convert image coordinates to canvas coordinates
        taking into consideration scrolling and scaling, rotation(TBD)
        :x_image: image x coord
        :y_pixel: image y
        :returns: (canvas_x, canvas_y)
        TBD - NEED to handle scrolling/resizing
        """
        canvas = self.get_canvas()
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        if self.gmi is None:
            raise SelectError("image2canvas has no gmi")
        
        image_width = self.gmi.getWidth()
        image_height = self.gmi.getHeight()

        canvas_x = x_image*canvas_width/image_width
        canvas_y = y_image*canvas_height/image_height
        return (canvas_x, canvas_y)

    
    def addToPoint(self, leng=None, lengPix=None, xY=None, pos=None, latLong=None, theta=None, deg=None, unit=None):
        """
        Add to canvas (overlay) point (in unrotated image), returning adjusted point in pixels
        Add requested rotation (curDeg if None) to map rotation, if
        mapRotation is not None
        :leng: length in unit
        :lengPix: length in pixels
        :unit: unit default: self.unit, meter
        """
        gmi = self.get_gmi()
        if leng is None and lengPix is None:
            raise SelectError("leng/LengPix is required")
        if leng is not None and lengPix is not None:
            raise SelectError("Only one of leng/LengPix is allowed")
        if lengPix is not None:
            leng = self.pixelToMeter(lengPix)
        if not isinstance(leng, float) and not isinstance(leng, int):
            raise SelectError(f"leng({leng} {type(leng)}) must be a float or int")
        
        
        if unit is None:
            unit = self.unit
        leng /= gmi.unitLen(unit)
            
        if theta is not None and deg is not None:
            raise SelectError("Only specify theta or deg")
        if theta is not None:
            deg = theta / pi * 180
        if deg is None:
            deg = self.curDeg
            
        npxl = 0
        if pos is not None:
            npxl += 1
        if xY is not None:
            npxl += 1
        if latLong is not None:
            npxl += 1
        if npxl > 1:
            raise SelectError("Only specify one of xY, pos or latLong")
        if npxl != 1:
            raise SelectError("Must specify one of xY, pos or latLong")
        if leng is None:
            raise SelectError("leng is required")
        
        xY = self.getXY(xY=xY, pos=pos, latLong=latLong)
            
        if deg is None:
            deg = 0
        deg += self.get_gmi().get_mapRotate()
            
        theta = deg/180.*pi
        if theta != 0:
            delta_x = cos(theta)*leng
            delta_y = -sin(theta)*leng
        else:
            delta_x = leng
            delta_y = 0.
        return xY[0]+self.meterToMx(delta_x), xY[1]+self.meterToMy(delta_y)


    def canvas_to_image(self, *xY_or_x_y):
        """
        Convert  (unrotated)canvas pixel x,y to (unrotated)image pixel x,y
        1. (No need to)Rotate from up facing to mapRotate
        2. Scale from canvas x,y pixel to image x,y pixel
        ??? 3. Rotate back to mapRotate
        Returning canvas x,y pair
        :xY_or_x_y: canvas coordinates
                1 arg-> canvas_xy tuple
                2 args -> canva_x, canvas_y
        :returns: x_image, y_image
        """
        if len(xY_or_x_y) == 1:
            canvas_x, canvas_y = xY_or_x_y[0] 
        else:
            canvas_x, canvas_y = xY_or_x_y[0], xY_or_x_y[1]

        if len(xY_or_x_y) == 0:
            raise SelectError("imageToCanvas: xY required")
        gD = self.get_geoDraw()
        
        canvas_width = self.get_canvas_width()
        canvas_height = self.get_canvas_height()
        '''
        mapRotate = gmi.get_mapRotate()
        canvas_x, canvas_y = gmi.rotate_xy(
                            x=canvas_x, y=canvas_y,
                            width=canvas_width,
                            height=canvas_height,
                            deg=mapRotate)
        '''
        image_width = gD.getWidth()
        image_height = gD.getHeight()
        x_image = canvas_x*image_width/canvas_width
        y_image = canvas_y*image_height/canvas_height

        return x_image, y_image

    def image_to_canvas(self, *xY_or_x_y):
        """
        Convert  (unrotated)image pixel x,y to (unrotated)canvas pixel x,y
        1. (No need to )Rotate from mapRotate to up facing
        2. Scale from image x,y pixel to canvas x,y
        :xY_or_x_y: image coordinates
                1 arg-> xY tuple
                2 args -> x, y
        :returns: canvas_x, canvas_y
        """
        if len(xY_or_x_y) == 1:
            xY = xY_or_x_y[0]
        else:
            xY = xY_or_x_y[0], xY_or_x_y[1]
            
        gmi = self.get_gmi()
        if gmi is None:
            return 0,0
        
        if len(xY_or_x_y) == 0:
            raise SelectError("imageToCanvas: xY required")
        x_image, y_image = xY
        '''
        mapRotate = gmi.get_mapRotate()
        x_image, y_image = gmi.rotate_xy(x=xY[0], y=xY[1],
                            width=gmi.getWidth(),
                            height=gmi.getHeight(),
                            deg=-mapRotate)
        '''
        image_width = self.gmi.getWidth()
        image_height = self.gmi.getHeight()
        canvas_width = self.get_canvas_width()
        canvas_height = self.get_canvas_height()
        canvas_x = x_image*canvas_width/image_width
        canvas_y = y_image*canvas_height/image_height
        ''' No rotation
        canvas_x, canvas_y = gmi.rotate_xy(     # Returns: x right
                                                #          y downwards
                                x=canvas_x, y=canvas_y,
                                width=canvas_width, height=canvas_height,
                                deg=gmi.get_mapRotate())

        image_width = self.gmi.getWidth()
        image_height = self.gmi.getHeight()
        '''
        return canvas_x, canvas_y


    def image_fract(self, canvas_xy=None):
        """ Convert canvas coordinates (x,y) to image x-fraction,  y-fraction
        :canvas_xy: canvas x,y coordinates
                default: most recent down click
        : return (x-fract, y-fract) of image
        """
        if canvas_xy is None:
            canvas_xy = self.canvasAt
        x_image, y_image = self.canvas2image(canvas_xy[0], canvas_xy[1])
        image_width = float(self.image.width)
        image_height = float(self.image.height)
        fract_x = x_image/image_width
        fract_y = y_image/image_height
        return (fract_x, fract_y)
            
    def motion (self, event):
        ###cnv.itemconfigure (tk.CURRENT, fill ="blue")
        cnv = event.widget
        x,y = float(cnv.canvasx(event.x)), float(cnv.canvasy(event.y))
        ###got = event.widget.coords (tk.CURRENT, x, y)
        if self.inside:
            if self.mouse_move_call is not None:
                self.mouse_move_call(x,y)

    def set_mouse_down_call(self, call):
        call2 = self.mouse_down_call        # To facilitate multiple calls
        self.mouse_down_call = call
        return call2

    def set_mouse_double_down_call(self, call):
        call2 = self.mouse_down_call        # To facilitate multiple calls
        self.mouse_double_down_call = call
        return call2

    def set_mouse_move_call(self, mouse_move_call):
        call2 = self.mouse_move_call        # To facilitate multiple calls
        self.mouse_move_call = mouse_move_call
        return call2

    def set_mouse_up_call(self, call):
        call2 = self.mouse_up_call        # To facilitate multiple calls
        self.mouse_up_call = call
        return call2
        
            
    def leave (self, event):
        SlTrace.lg("leave", "mouse")
        self.inside = False
        self.canv.config(cursor="")
        self.canv.unbind("<Motion>")
        if self.pt_mgr is not None:
            self.pt_mgr.leave()
    
    def enter (self, event):
        SlTrace.lg("enter", "mouse")
        self.inside = True
        self.canv.config(cursor="cross")
        self.canv.bind("<Motion>", self.motion)
    
    def up (self, event):
        self.isDown = False
        self.config (cursor ="arrow")
        if self.inside:
            cnv = event.widget
            x,y = cnv.canvasx(event.x), cnv.canvasy(event.y)
            ###got = event.widget.coords (tk.CURRENT, x, y)
            SlTrace.lg("up at x=%d y=%d" % (x,y), "mouse")
            if self.mouse_up_call is not None:
                self.mouse_up_call(x,y)

    def get_canvas(self):
        """ Get our canvas object
        :returns: base Canvas object
        """
        return self.canv

    def get_canvas_height(self):
        """ Get our canvas width in pixels
        :returns: width in pixelst
        """
        canvas_height = self.get_canvas().winfo_height()
        return canvas_height

    def get_canvas_width(self):
        """ Get our canvas width in pixels
        :returns: width in pixelst
        """
        canvas_width = self.get_canvas().winfo_width()
        return canvas_width

    def get_gmi(self):
        return self.gmi

    def get_geoDraw(self):
        return self.get_gmi().get_geoDraw()
        
    def close(self):
        """
        Close file window
        """
        self.canv.destroy()

    def change_maptype(self, maptype):
        """ Change our default maptype
        :maptype: plot map type
        """
        self.maptype = maptype
 
 
    def save_favorite(self):
        map_ctl = self.get_map_ctl()
        map_ctl.save_favorite()
               
    def set_canvas(self, image, width=None, height=None):
        """ Setup canvas, given original image and dimensions
        :image: original image to display
        :width: display width (pixels) default: image.width
        :height: display hight (pixels) default: image.height
        """
        if self.canvas_frame is not None:
            self.canvas_frame.pack_forget()
            self.canvas_frame.destroy
            self.canvas_frame = None
        if self.canv is not None:
            self.canv.forget()
            self.canv.destroy()
            self.canv = None
        if self.sbarH is not None:
            self.sbarH.forget()
            self.sbarH.destroy()
            self.sbarH = None
        if self.sbarV is not None:
            self.sbarV.forget()
            self.sbarV.destroy()
            self.sbarV = None
        self.canvas_frame = Frame(self.canvas_container_frame)             # Deleted and restored when canvas is updated
        self.canvas_frame.pack(expand=YES, fill=BOTH)
        self.canv = Canvas(self.canvas_frame, relief=SUNKEN)
        self.canv.pack(expand=YES, fill=BOTH)
        if image is None:
            image = self.get_image()
        w,h = image.size
        if width is None:
            width = w
        if height is None:
            height = h
        self.canv_width = self.width = width
        self.canv_height = self.height = height
        SlTrace.lg("sizeWindow width=%d height=%d" % (width, height), "resize")
        im = PIL.ImageTk.PhotoImage(image)
        self.imgtag=self.canv.create_image(0,0,anchor="nw",image=im)
        image = image.resize((width,height))
        ###self.set_image(image)
        
        '''
        self.sbarV = sbarV = Scrollbar(self, orient=VERTICAL)
        self.sbarH = sbarH = Scrollbar(self, orient=HORIZONTAL)
        
        sbarV.config(command=self.canv.yview)
        sbarH.config(command=self.canv.xview)
        
        self.canv.config(yscrollcommand=sbarV.set)
        self.canv.config(xscrollcommand=sbarH.set)
        
        sbarV.pack(side=RIGHT, fill=Y)
        sbarH.pack(side=BOTTOM, fill=X)
        self.canv.pack(side=LEFT, expand=YES, fill=BOTH)
        SlTrace.lg(f"set_canvas: width: {self.get_width()} height: {self.get_height()}")
        self.canv.config(scrollregion=(0,0,width,height))
        SlTrace.lg(f"set_canvas: width: {self.get_width()} height: {self.get_height()}")
        '''
        
        self.canv.bind ("<ButtonPress-1>", self.down)
        self.canv.bind ("<ButtonRelease-1>", self.up)
        self.canv.bind("<Double-Button-1>", self.double_down)
        self.canv.bind ( "<Enter>", self.enter)
        self.canv.bind ("<Leave>", self.leave)
        self.bind("<Configure>", self.on_resize)

    def mark_canvas(self):
        if SlTrace.trace("mark_canvas"):
            if self.cv_mark_tags:
                self.canv.delete(self.cv_mark_tags)
                self.cv_mark_tags = []
            canvas = self.canv
            w = self.get_width()
            h = self.get_height()
            cv_mark_color = "blue"
            cv_mark_width = 2
            p1_cx, p1_cy = w/2, 0
            p2_cx, p2_cy = w/2, h
            tag = canvas.create_line(
                p1_cx, p1_cy, p2_cx, p2_cy,
                fill=cv_mark_color,
                width=cv_mark_width)
            self.cv_mark_tags.append(tag)
            p3_cx, p3_cy = 0, h/2
            p4_cx, p4_cy = w, h/2
            tag = canvas.create_line(
                p3_cx, p3_cy, p4_cx, p4_cy,
                fill=cv_mark_color,
                width=cv_mark_width)
            self.cv_mark_tags.append(tag)
            pts = [(0,0), (w,0), (w,h/2), (w,h), (0,h), (0,0)]
            for i in range(1,len(pts)):
                p1_cx, p1_cy = pts[i-1][0], pts[i-1][1]
                p2_cx, p2_cy = pts[i][0], pts[i][1]
                tag = canvas.create_line(
                    p1_cx, p1_cy, p2_cx, p2_cy,
                    fill=cv_mark_color,
                    width=cv_mark_width+1)
                self.cv_mark_tags.append(tag)
        self.update()

    def update_file(self, fileName, **kwargs):
        """ Update file
        :fileName: file to load ==> GoogleMapImage (file)
        :kwargs: See GoogleMapImage for parameters
        """
        if 'file' in kwargs:
            raise SelectError("update file: should not have file=")

        self.file_name = fileName
        gmi = GoogleMapImage(file=fileName, add_compass_rose=False, **kwargs)
        if gmi is None:
            raise SelectError(f"Can't load GoogleMapImage({fileName}")

        self.update_gmi(gmi)

    def update_general(self, **kwargs):
        """ Update with GoogleMapImage spec 
        :kwargs:  GoogleMapImage parameters
        """

        if self.maptype is not None and 'maptype' not in kwargs:
            kwargs['maptype'] = self.maptype        
        if self.enlargeForRotate is not None and 'enlargeForRotate' not in kwargs:
            kwargs['enlargeForRotate'] = self.enlargeForRotate        
        gmi = GoogleMapImage(**kwargs)
        if gmi is None:
            raise SelectError(f"Can't load GoogleMapImage(latLong{kwargs}")
        
        self.update_gmi(gmi)

    def update_lat_long(self, latLong, centered=True, **kwargs):
        """ Update with latitude/longitude spec 
        :latLong: (lat,long) + GoogleMapImage parameters
        :centered:    latLong are in center of plot, else upper left corner
                default: centered - True
        :kwargs:  GoogleMapImage parameters (NOT file, ulLat, ulLong
        """
        if 'ulLat' in kwargs:
            raise SelectError("Can't have ulLat parameter")
        
        if 'ulLong' in kwargs:
            raise SelectError("Can't have ulLong parameter")

        if self.maptype is not None and 'maptype' not in kwargs:
            kwargs['maptype'] = self.maptype
        gmi = GoogleMapImage(ulLat=latLong[0], ulLong=latLong[1], **kwargs)
        if gmi is None:
            raise SelectError(f"Can't load GoogleMapImage(latLong{latLong}")
        
        self.update_gmi(gmi)

    def update_gmi(self, gmi):
        """ Update gmi, image, and canvas
        :gmi: (GoogleMapImage
        """
        if self.gmi is not None and False:      # TFD avoid destroying 
            self.gmi.destroy()
        self.gmi = gmi
        self.update_image(gmi.get_image())

    def delete_tag(self, tag):
        """ Delete canvas tag
        :tag: to ge deleted
        """
        canvas = self.get_canvas()
        if canvas is None:
            return
        
        canvas.delete(tag)
        
        
    def destroy(self):
        """ Release any resources
        present for uniformity
        """
        self.canv = None
    
    def update_image(self, image=None):
        """ Update image, and canvas
        :image: map image
        """

        if self.image is None:
            image = self.get_image()
        if image is None:
            return
        
        self.set_canvas(image, width=self.width, height=self.height)


if __name__ == "__main__":
    import argparse
    from tkinter.filedialog import askopenfilename
    from GeoDraw import GeoDraw
    
    test_mapFile = '../out/gmi_ulA42_376371_O-71_187576_lRA42_369949_O-71_181274_640x640_sc1z19_h_mr45_AUG.png'
    mapFile = r"C:\Users\raysm\workspace\python\PlantInvasion\out\gmi_ulA42_376000_O-71_177315_lRA42_375640_O-71_176507_640x640_sc1z22_h.png"
    mapInfo = r"C:\Users\raysm\workspace\python\PlantInvasion\out\gmi_ulA42_376000_O-71_177315_lRA42_375640_O-71_176507_640x640_sc1z22_h_png.imageinfo" 
    infoFile = None
    title=None
    height=1000
    width=1500
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--mapfile=', dest='mapFile', default=mapFile)
    parser.add_argument('-i', '--infofile=', dest='infoFile', default=infoFile)
    parser.add_argument('-u', '--height=', type=int, dest='height', default=height)
    parser.add_argument('-w', '--width=', type=int, dest='width', default=width)
    
    args = parser.parse_args()             # or die "Illegal options"

    
    def rotate_map_test():
        npass = 0
        nfail = 0
        ntest = 0
        mapRotate = 0.
        w = 300.
        h = 400.
        im = Image.new("RGB", (int(w), int(h)))    
        gd = GeoDraw(im, mapRotate=mapRotate,
                ulLat=None, ulLong=None,    # Bounding box
                lrLat=None, lrLong=None,
                      ulX=0, ulY=0, lrX=w, lrY=h)
        f_fmt = "10.6f"
        for i in range(0, 6+1):
            x1 = i*50.
            for j in range(0, 4+1):
                y1 = j*100.
                for k in range(0, 8+1):
                    deg = k*45.
                    x2, y2 = gd.rotate_xy(x=x1, y=y1,
                                           width=gd.getWidth(),
                                           height=gd.getHeight(), deg=deg)
                    SlTrace.lg(f"{deg:5.1f}"
                               f" x1: {x1:{f_fmt}} y1: {y1:{f_fmt}}"
                               f"  x2: {x2:{f_fmt}} y2: {y2:{f_fmt}}")
                    if (x1,y1) == (w/2, 0):
                        if deg == 45.:
                            ntest += 1
                            theta = radians(deg)
                            x_shrink = h/2/sqrt(2)
                            y_shrink = h/2/sqrt(2)
                            x2_expect = w/2 - x_shrink
                            y2_expect = h/2 - y_shrink
                            if not close((x2,y2), (x2_expect, y2_expect)):
                                nfail += 1
                                SlTrace.lg(f" FAIL: (x2: {x2:{f_fmt}}, y2: {y2:{f_fmt}})"
                                           f" != (x2_expect: {x2_expect:{f_fmt}},"
                                           f" y2_expect: {y2_expect:{f_fmt}})")
                            else:
                                npass += 1
                                SlTrace.lg(f" PASS: (x2: {x2}, y2: {y2})"
                                           f" == (x2_expect: {x2_expect}, y2_expect: {y2_expect})")
                        if deg == 90.:
                            ntest += 1
                            if not close((x2,y2), ((w-h)/2, h/2)):
                                nfail += 1
                                SlTrace.lg(f" FAIL: (x2: {x2}, y2: {y2})"
                                           f" != ((w-h)/2: {(w-h)/2}, h/2: {h/2})")
                            else:
                                npass += 1
                                SlTrace.lg(f" PASS: (x2: {x2}, y2: {y2})"
                                           f" == ((w-h)/2: {(w-h)/2}, h/2: {h/2})")
        SlTrace.lg(f"{ntest:4d} tests  {npass:4d} pass  {nfail:4d} fail")
    

    
    do_canvas_image_test = True
    if do_canvas_image_test:
        pass                # TBD
        
    do_mapfile_test = False
    if do_mapfile_test:
        mapFile = args.mapFile
        if mapFile == "TEST":
            mapFile = test_mapFile      # Use test file
        infoFile = args.infoFile
        width = args.width
        height = args.height
        ###root = Tk()
        ###Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
        if mapFile is None:
            mapFile = askopenfilename() # show an "Open" dialog box and return the path to the selected file
        SlTrace.lg(f"mapfile: {mapFile}")
        ###width = 100
        ###height = 100
        SlTrace.lg(f"canvas: width={width} height={height}")
        ###frame = Frame(root)
        ###frame.pack()
        sc = ScrolledCanvas(mapFile, width=width, height=height)
        mainloop()
