#!/usr/bin/python
"""
Support for scalable image map
Loosly adapted from PoolWindow, using Tkinter
"""
import os
import sys

from tkinter import *
from tkinter.filedialog import askopenfilename
from numpy.lib._datasource import _FileOpeners
import GoogleMapImage
from GoogleMapImage import *
from scrollableimage import ScrolledCanvas

"""
Here, we are creating our class, Window, and inheriting from the Frame
class. Frame is a class from the tkinter module. (see Lib/tkinter/__init__)
"""
class GeoWindow(Frame):

    def __init__(self,
                 mw=None,       # Main window
                 ow=None,       # Our window
                 title=None,
                 mapFile=None,
                 mapInfo=None,
                 width=None,
                 height=None,
                 geoExit=exit,
                 ):
        """
        Setup a scaleable window.
        Use mapFile, if provided
        :title - window title, if present, else use mapFile if present, else use program file name
        :mapFile - file path to image file
        :infoFile - dictionary of map information
                    if not present use INFO file based on mapFile
        
        """
        #reference to the mw widget, which is the tk window                 
        self.mw = mw
        if ow is None:
            ow = mw             # Default to main window
        self.ow = ow
            
        # parameters that you want to send through the Frame class. 
        Frame.__init__(self, ow)   

        if geoExit is None:
            geoExit = self.geoExit
        self.geoExit = geoExit
        if title is None:
            if mapFile is not None:
                title = os.path.basename(mapFile)
            if title is None:
                title = os.path.basename(sys.argv[0])
        self.title = title
        
        if mapFile is not None or infoFile is not None:
            mapImage, mapInfo = LoadImageFile(mapFile, infoFile)
            self.mapImage = mapImage
            self.mapInfo = mapInfo
        else:
            self.mapImage = self.mapInfo = None
        if width is None:
            if self.mapImage is not None:
                width = self.mapImage.width
        self.width = width
        
        if height is None:
            if self.mapImage is not None:
                height = self.mapImage.height
        self.height = height
        
        self.init_window()
        self.sc = ScrolledCanvas(image=self.mapImage, title=title, width=width, height=height, parent=self)
        if self.mapImage is not None:
            self.sc.mainloop()

        
    #Creation of init_window
    def init_window(self):

        # changing the title of our mw widget      
        self.ow.title(self.title)

        # allowing the widget to take the full space of the root window
        self.pack(fill=BOTH, expand=1)

        # creating a menu instance
        menubar = Menu(self.ow)
        self.ow.config(menu=menubar)

        # create the file Menu
        filemenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="Open", command=self.fileOpen)
        filemenu.add_command(label="Save", command=self.fileSave)
        filemenu.add_command(label="Close", command=self.fileClose)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.geoExit)

        # Selection Menu
        selectmenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Select", menu=selectmenu)
        selectmenu.add_command(label="Display bounds", command=self.displayBounds)

        # Scale Menu
        scalemenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Scale", menu=scalemenu)
        scalemenu.add_command(label="full screen", command=self.fullScreen)
        scalemenu.add_command(label="drag frame", command=self.dragFrame)
 
    def fileOpen(self):
        mapFile = askopenfilename() # show an "Open" dialog box

        gW = self.newWindow(self.mw,
                            ow=self.ow,
                    mapFile=mapFile,
                    geoExit=self.geoExit,
                    )
 
    def fileClose(self):
        if self.sc is not None:
            self.sc.close()
            self.sc = None
            
    
    def fileSave(self):
        pass
    
    def geoExit(self, code=0):
        sys.exit(code)


    def displayBounds(self):
        print("displayBouns")
        """
        1. Create a default selection rectangle (middle third?)
            A. display the rectangle region with strong accents plus weak, but visible, rectangle
               edge-continuation lines to the display region edges.  These continuation-lines are
               to aid alignment with objects outside the rectangle.
            B. Provide handles on corners which can be dragged in all directions, repositioning the corner.
            C. Provide handles on edges which can be dragged vertically to the edge.
            D. Provide an internal region of the rectangle (all that will not be confused
               with the other handles) which can be dragged in all directions, moving the whole rectangle
        2. Implement the "handles" so that mouse-down on the handles will begin the dragging process, which
           continues until mouse-up
        3. Choice of Select Menu - "Complete" expands the selection region to fill the complete display region.
               
        """
    
    def fullScreen(self):

        screen_width = self.ow.winfo_screenwidth()
        screen_height = self.ow.winfo_screenheight()   
        self.sc.sizeWindow(width=screen_width, height=screen_height)
    
    def dragFrame(self):
        pass


    def newWindow(self,
                 mw=None,
                 ow=None,
                 title=None,
                 mapFile=None,
                 mapInfo=None,
                 width=None,
                 height=None,
                 geoExit=exit,
                 ):
        """
        Create new window, using current window values as defaults
        """
        if mw is None:
            mw = self.mw
        if ow is None:
            ow = mw
        if width is None:
            width = self.width 
        if height is None:
            height = self.height
        if geoExit is None:
            geoExit = self.geoExit
        top = Toplevel(ow)    
        gw = GeoWindow(mw, ow=top, title=title, mapFile=mapFile, mapInfo=mapInfo, width=width, height=height, geoExit=geoExit)
        
#######################################################################
#          Self Test
#######################################################################
if __name__ == "__main__":
    import sys
    import argparse
    from GMIError import GMIError
    
    mapFile = "../out/gmi_ulA42_375619_O-71_186837_lRA42_370701_O-71_182013_640x640_sc1z21_h_mr45.png"
    infoFile = None
    title=None
    height=500
    width=1000
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--mapfile=', dest='mapFile', default=mapFile)
    parser.add_argument('-i', '--infofile=', dest='infoFile', default=infoFile)
    parser.add_argument('-u', '--height=', dest='height', default=height)
    parser.add_argument('-w', '--width=', dest='width', default=width)
    
    args = parser.parse_args()             # or die "Illegal options"
    mapFile = args.mapFile
    infoFile = args.infoFile
    width = args.width
    height = args.height
    
    print("%s %s\n" % (os.path.basename(sys.argv[0]), " ".join(sys.argv[1:])))
    print("args: %s\n" % args)
    
    
    def full_size():
        print("full_size")
        
        
    def drag_frame():
        print("drag_frame")
        
        
    def size_window():
        print("size_window")
        
        
    def annotate():
        print("annotate")
        
        
    # root window created. Here, that would be the only window, but
    # you can later have windows within windows.
    mw = Tk()
    def user_exit():
        print("user_exit")
        exit()
        
        
    ###mw.geometry("400x300")

    #creation of an instance
    gW = GeoWindow(mw,
                mapFile=mapFile,
                geoExit=user_exit,
                title=title,
                width=width,
                height=height
                    )
    
    
    #mainloop 
    mw.mainloop()  

