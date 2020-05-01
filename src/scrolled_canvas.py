import PIL.Image
import PIL.ImageTk
import tkinter as tk
from tkinter import *
import os

from select_trace import SlTrace
from GoogleMapImage import GoogleMapImage

class CanvasCoords:
    """ Aid in converting / using coordinates
    """
    def __init__(self, sc, canvas_x=None, canvas_y=None,
             lat=None, long=None,
             x_dist=None, y_dist=None,
             x_image=None, y_image=None,
             unit="m"):
        """convert canvas coordinates to the others
        TBD: do the other directions too
        """
        self.canvas_x = canvas_x
        self.canvas_y = canvas_y
        gmi = sc.gmi
        self.x_image, self.y_image = sc.canvas2image(canvas_x, canvas_y)
        self.lat, self.long = gmi.pixelToLatLong((self.x_image, self.y_image))
        self.x_dist, self.y_dist = gmi.getPos(xY=(self.x_image, self.y_image),
                                              ref_latLong=gmi.get_ref_latLong(),
                                              unit=unit)

class ScrolledCanvas(Frame):
    def __init__(self, fileName=None, gmi=None, image=None, title=None, parent=None,
                 width=None, height=None,
                 mouse_down_call=None,
                 mouse_double_down_call=None,
                 mouse_up_call=None,
                 mouse_move_call=None,
                 ):
        """
        :fileName - image file, if present or info file if ending with .imageinfo else
        :gmi: GoogleMapImage, if present
        :image - image, if present
        :mouse_down_call: if present, function to call with x,y canvas coordinates
        :mouse_move_call: if present, function to call with x,y canvas coordinates on mouse motion
        :unit: Linear distance unit m(eter), y(ard), f(oot) - default: "m" - meter
        """
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
        self.imOriginal = None      # For restoration/resize without loss
        Frame.__init__(self, parent)
        if title is None:
            if fileName is not None:
                title = os.path.basename(fileName)
            else:
                title = "Map Scroller"
        self.title = title
        self.gmi = None
        self.image = None
        if gmi is not None:
            self.gmi = gmi
            self.image = gmi.image
            self.image = gmi.image
        elif image is not None:
            self.image = image
            self.imOriginal = self.image               # To avoid sizing loss
        elif fileName is not None:
            self.gmi = GoogleMapImage(file=fileName, useOldFile=True)
            if self.gmi is None:
                raise GMIError("Can't load image file %s" % fileName)
            
            self.image = self.gmi.image
            self.imOriginal = self.image
        else:
            SlTrace.lg("Must provide one of fileName, gmi, or image")
            sys.exit(1)
            self.canvasAt = (0,0)
        self.pack(expand=YES, fill=BOTH)
        self.set_canvas(self.image, width=width, height=height)

    def on_resize(self, event):
        # determine the ratio of old width/height to new width/height
        if self.imOriginal is None:
            return                      # Nothing yet
        
        new_width = event.width
        new_height = event.height
        self.canvas_width = new_width
        self.canvas_height = new_height
        SlTrace.lg("new width=%d height=%d" % (new_width, new_height), "resize")
        # resize the canvas 
        ###self.config(width=self.width, height=self.height)
        # rescale all the objects tagged with the "all" tag
        self.image = self.imOriginal.resize((self.canvas_width, self.canvas_height))
        self.canv.config(scrollregion=(0,0,self.canvas_width,self.height))
        self.im2=PIL.ImageTk.PhotoImage(self.image)
        self.imgtag=self.canv.create_image(0,0,anchor="nw",image=self.im2)

    
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
    
    def canvas2image(self, x_pixel, y_pixel):
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
            raise GMIError("canvas2image has no gmi")
        
        image_width = self.gmi.getWidth()
        image_height = self.gmi.getHeight()

        x_image = x_pixel*image_width/canvas_width
        y_image = y_pixel*image_height/canvas_height
        return (x_image, y_image)

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

    def close(self):
        """
        Close file window
        """
        self.canv.destroy()
        
        
    def set_canvas(self, image, width=None, height=None):
        """ Setup canvas, given original image and dimensions
        :image: original image to display
        :width: display width (pixels) default: image.width
        :height: display hight (pixels) default: image.height
        """
        self.image = image
        self.canv = Canvas(self, relief=SUNKEN)
        self.canv.pack(expand=YES, fill=BOTH)
        self.canv.bind ("<ButtonPress-1>", self.down)
        self.canv.bind ("<ButtonRelease-1>", self.up)
        self.canv.bind("<Double-Button-1>", self.double_down)
        self.canv.bind ( "<Enter>", self.enter)
        self.canv.bind ("<Leave>", self.leave)
        
        w,h = self.image.size
        if width is None:
            width = w
        if height is None:
            height = h
        self.canv_width = self.width = width
        self.canv_height = self.height = height
            
        self.canv.config(width=self.canv_width, height=self.canv_height)
        self.bind("<Configure>", self.on_resize)
        
        SlTrace.lg("sizeWindow width=%d height=%d" % (width, height), "resize")
        self.image = image.resize((width,height))
        
        self.canv.config(width=width, height=height)
        #self.canv.config(scrollregion=(0,0,1000, 1000))
        #self.canv.configure(scrollregion=self.canv.bbox('all'))
        self.canv.config(highlightthickness=0)
        
        self.sbarV = sbarV = Scrollbar(self, orient=VERTICAL)
        self.sbarH = sbarH = Scrollbar(self, orient=HORIZONTAL)
        
        sbarV.config(command=self.canv.yview)
        sbarH.config(command=self.canv.xview)
        
        self.canv.config(yscrollcommand=sbarV.set)
        self.canv.config(xscrollcommand=sbarH.set)
        
        sbarV.pack(side=RIGHT, fill=Y)
        sbarH.pack(side=BOTTOM, fill=X)

        self.canv.pack(side=LEFT, expand=YES, fill=BOTH)
        self.canv.config(scrollregion=(0,0,width,height))
        self.im2=PIL.ImageTk.PhotoImage(self.image)
        self.imgtag=self.canv.create_image(0,0,anchor="nw",image=self.im2)

if __name__ == "__main__":
    import argparse
    from tkinter.filedialog import askopenfilename
    from GMIError import GMIError
    from survey_point_manager import SurveyPointManager
    
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
    
    mapFile = args.mapFile
    if mapFile == "TEST":
        mapFile = test_mapFile      # Use test file
    infoFile = args.infoFile
    width = args.width
    height = args.height
    
    ###Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
    if mapFile is None:
        mapFile = askopenfilename() # show an "Open" dialog box and return the path to the selected file
    SlTrace.lg(f"mapfile: {mapFile}")
    ###width = 100
    ###height = 100
    SlTrace.lg(f"canvas: width={width} height={height}")
    sc = ScrolledCanvas(mapFile, width=width, height=height)
    pt_mgr = SurveyPointManager(sc)
    mainloop()
