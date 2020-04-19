import PIL.Image
import PIL.ImageTk
import tkinter as tk
from tkinter import *
import os
from GoogleMapImage import *

class ScrolledCanvas(Frame):
    def __init__(self, fileName=None, image=None, title=None, parent=None,
                 width=None, height=None):
        """
        :fileName - image file, if present or info file if ending with .imageinfo else
        :image - image, if present
        """
        self.isDown = False
        self.inside = False
        Frame.__init__(self, parent)
        if title is None:
            if fileName is not None:
                title = os.path.basename(fileName)
            else:
                title = "Map Scroller"
        self.title = title
        if image is not None:
            self.im = image
        elif fileName is not None:
            image, info = LoadImageFile(fileName)
            if image is None:
                raise GMIError("Can't load image file %s" % fileName)
            
            if info is None:
                print("No image info for file %s" % fileName)
            self.im=image
            self.imageInfo = info
        else:
            print("Must provide one of fileName or image")
            sys.exit(1)
        self.imOriginal = self.im               # To avoid sizing loss
        self.pack(expand=YES, fill=BOTH)
        self.canv = Canvas(self, relief=SUNKEN)
        self.canv.bind ("<ButtonPress-1>", self.down)
        self.canv.bind ("<ButtonRelease-1>", self.up)
        self.canv.bind ( "<Enter>", self.enter)
        self.canv.bind ("<Leave>", self.leave)
        self.width = width
        self.height = height
        self.bind("<Configure>", self.on_resize)
        if width is None:
            width=1000
        if height is None:
            height = 800
            
        self.sizeWindow(image, width=width, height=height)


    def on_resize(self, event):
        # determine the ratio of old width/height to new width/height
        new_width = event.width
        new_height = event.height
        width = self.width = new_width
        height = self.height = new_height
        print("new width=%d height=%d" % (new_width, new_height))
        # resize the canvas 
        self.config(width=self.width, height=self.height)
        # rescale all the objects tagged with the "all" tag
        self.im = self.imOriginal.resize((self.width, self.height))
        self.canv.config(scrollregion=(0,0,width,height))
        self.im2=PIL.ImageTk.PhotoImage(self.im)
        self.imgtag=self.canv.create_image(0,0,anchor="nw",image=self.im2)

    
    def scale(self, wscale, hscale):
        """
        Scale canvas accordingly
        """
        width = self.width
        height = self.height
        self.canv.config(scrollregion=(0,0,width,height))
        self.im = self.im.resize(width, height)
        self.im2=PIL.ImageTk.PhotoImage(self.im)
        self.imgtag=self.canv.create_image(0,0,anchor="nw",image=self.im2)

    def down (self, event):
        self.isDown = True
        if self.inside:
            print("Click in canvas event:%s" % event)
            cnv = event.widget
            x,y = cnv.canvasx(event.x), cnv.canvasy(event.y)
            print("x=%d y=%d" % (x,y))
            self.canvasXy0 = (self.canv.canvasx(0), self.canv.canvasy(0))
            self.canvasAt = (x,y)
            print("sbarV=%s sbarH=%s" % (self.sbarV.get(), self.sbarH.get()))
            self.dragged = 0
            ###event.widget.bind ("<Motion>", self.motion)
            self.config (cursor ="hand1")
            self.motionBindId = self.canv.tag_bind (self.imgtag, "<Motion>", self.motion)
    
    def motion (self, event):
         ###cnv.itemconfigure (tk.CURRENT, fill ="blue")
        cnv = event.widget
        x,y = float(cnv.canvasx(event.x)), float(cnv.canvasy(event.y))
        ###got = event.widget.coords (tk.CURRENT, x, y)
        if self.inside:
            width = float(self.im.width)
            height = float(self.im.height)
            print("motion at x=%d y=%d" % (x,y))
            delta_x = x - float(self.canvasAt[0])
            delta_y = y - float(self.canvasAt[1])
            new_x0 = float(self.canvasXy0[0]) - delta_x
            new_y0 = float(self.canvasXy0[1]) - delta_y
            scroll_x = float(new_x0)
            scroll_y = float(new_y0)
            offset_x = +1 if scroll_x >= 0 else 0
            offset_y = +1 if scroll_y >= 0 else 0
            x_frac = float(scroll_x + offset_x)/width
            y_frac = float(scroll_y + offset_y)/height
            self.canv.xview_moveto(x_frac)
            self.canv.yview_moveto(y_frac)
            print("sbarV=%s sbarH=%s after move" % (self.sbarV.get(), self.sbarH.get()))
            print("x=%d y=%d, scroll_x=%.0f scroll_y=%.0f" % (x,y, scroll_x, scroll_y))
            print("x_frac=%.2f y_frac=%.2f" % (x_frac, y_frac))
            pass
    
    def leave (self, event):
        print("leave")
        self.inside = False
    
    def enter (self, event):
        print("enter")
        self.inside = True
    
    def up (self, event):
        self.isDown = False
        self.config (cursor ="arrow")
        if hasattr(self, 'motionBindId'):
            self.canv.unbind ("<Motion>", self.motionBindId)
        ###event.widget.itemconfigure (tk.CURRENT, fill =self.defaultcolor)
        if self.inside:
            cnv = event.widget
            x,y = cnv.canvasx(event.x), cnv.canvasy(event.y)
            ###got = event.widget.coords (tk.CURRENT, x, y)
            print("up at x=%d y=%d" % (x,y))
 

    def close(self):
        """
        Close file window
        """
        self.canv.destroy()
        
        
    def sizeWindow(self, image=None, width=None, height=None):
        """
        Size/resize window, given image and width,height
        """
        if image is None:
            image = self.im
        
        w,h = self.im.size
        if width is None:
            width = w
        if height is None:
            height = h
        print("sizeWindow width=%d height=%d" % (width, height))
        image = image.resize((width,height))
        self.im = image
        
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
        self.im2=PIL.ImageTk.PhotoImage(self.im)
        self.imgtag=self.canv.create_image(0,0,anchor="nw",image=self.im2)

if __name__ == "__main__":
    import argparse
    from tkinter.filedialog import askopenfilename
    from GMIError import GMIError
    
    test_mapFile = 'out/gmi_ulA42_376371_O-71_187576_lRA42_369949_O-71_181274_640x640_sc1z19_h_mr45_AUG.png'
    mapFile = None 
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
    print(mapFile)
    ###width = 100
    ###height = 100
    sc = ScrolledCanvas(mapFile, width=width, height=height)
    sc.mainloop()
