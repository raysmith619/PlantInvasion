#survey_scale.py
"""
Survey map scale
"""
import re
from math import sqrt, asin, degrees
from PIL import ImageFont

from select_trace import SlTrace
from select_error import SelectError

class SurveyMapScale:
    
    def __init__(self, mgr,
                xY=None, xYFract=None, pos=None, latLong=None,
                xYEnd=None, xYFractEnd=None, posEnd=None, latLongEnd=None,                
                deg=None,
                mapRelative=True,
                leng=None,
                lengFract=None,
                
                unit="m",
                font_name="arial",
                font_size=15,
                tic_dir=1,
                tic_leng=10,
                marks=10,
                bigMarks=10,
                nlabel=4,
                label_at_end=True, 
                color="white"
                 ):
        """
        Add scale marker
        :mgr: SurveyPointManager - access to drawing objects
            One of starting specification
                :xY - starting x,y pixels
                :xYFract - startying x,y fraction of map - TBD - all Fract specs
                :pos - starting x,y meters            
                :latLong - starting latitude,longitude
            
            OR One of ending specification
                :xYEnd - ending
                :xYFractEnd - ending fraction of map
                :posEnd - endin
                :latLongEnd - ending latitude, longitude
        
            OR One of the above AND   
                :leng - Length in pixels
                AND
                :deg: - direction of scale line in degrees from image horizontal
                         (0 - horizontal to right)
                         
            OR xYFract and
                :lengFract
                AND
                :deg: - direction of scale line in degrees from image horizontal
                         (0 - horizontal to right)
            :mapRelative: True - direction is relative to map (not North facing)
                                deg 0 left to right when facing North
                          False - North facing deg 0 ==> left to right, facing map
                        default: True ==> scale left to right on map
            :marks - ticks every marks unit
            :bigMarks - big marks every bigMarks mark
            :nlabel: units every nlabel bigMarks
                    default: 4
            :label_at_end: Place label at end
                    default: True
            :tic_dir: tic direction 1: axis + 90 deg, -1: axix -90 deg
                        default: 1
            :tic_leng: tic marker length in pixels
                    default: 10
            :unitName - text for unit - m - meter, f - foot
            :color - scale color
        :returns: NA
        Raises: NA
        """
        self.mgr = mgr
        
        self.xY = xY          # Initialize all so all can be passed to geoDraw
        self.xYFract = xYFract
        self.xYEnd = xYEnd
        self.xYFractEnd = xYFractEnd
        self.pos = pos
        self.posEnd = posEnd
        self.latLong = latLong
        self.latLongEnd = latLongEnd
        self.leng = leng
        self.lengFract = lengFract
        self.deg = deg
        self.mapRelative = mapRelative
        self.font_name=font_name
        self.font_size=font_size
        self.tic_dir = tic_dir
        self.tic_leng = tic_leng
        self.marks = marks
        self.nlabel = nlabel
        self.label_at_end = label_at_end
        self.bigMarks = bigMarks
        self.unit = unit
        np1_spec = 0
        if xY is not None:
            np1_spec += 1
        if xYFract is not None:
            np1_spec += 1
        if pos is not None:
            np1_spec += 1
        if latLong is not None:
            np1_spec += 1

        np2_spec = 0
        if xYEnd is not None:
            np2_spec += 1
        if xYFractEnd is not None:
            np2_spec += 1
        if posEnd is not None:
            np2_spec += 1
        if latLongEnd is not None:
            np2_spec += 1
        
        if np1_spec == 0:
            xY = (self.getWidth()*.1, self.getHeight()*.9)
            self.xY = xY
            np1_spec += 1
        
        if leng is not None and lengFract is not None:
            raise SelectError("Can't specify both len and lenFract")
        
        if np2_spec == 0:
            if leng is None and lengFract is None:
                lengFract = .8
                
            if deg is None:
                self.deg = 0.
            
        if np1_spec == 0:
            raise SelectError("Atleast one of xY, xYFract, pos, latLong must be present")
        if np1_spec > 1:
            raise SelectError("Only one of xY, xYFract, pos, latLong is allowed")


        if np2_spec > 0 and leng is not None:
            raise SelectError("Neither leng or LengFract are not alowed when ending point is specified")
        if  np2_spec > 0 and deg is not None:
            raise SelectError("deg is not allowed when ending point is specified")
        
        if np2_spec > 1:
            raise SelectError("Only one of xYEnd, posEnd, or latLongEnd may be specified")
            
        if np1_spec > 1:
            raise SelectError("Only one of xY, pos, latLong is allowed")
        
        self.np2_spec = np2_spec
        
        self.marks = marks
        if bigMarks is None:
            self.bigMarks = 5
        
        if tic_dir is None:
            self.tic_dir = 1
        
        self.color = color
        self.display_tags = []      # Display tags, if any
        
    """ Access to display objects
    """
    def get_iodraw(self):
        """ Get overlay/image object
        """
        return self.mgr.get_iodraw()

    def get_gmi(self):
        return self.get_sc().gmi

    def get_sc(self):
        """ Get ScrollableCanvas
        """
        return self.mgr.sc
    """ End of display object access
    """

    def get_deg(self):
        """ Get direction of scale
        """
        deg = 0 if self.deg is None else self.deg
        if self.mapRelative:
            iodraw = self.get_iodraw()
            deg -= iodraw.get_mapRotate()
        return deg
    
                        
    def display(self):
        """ Display scale
        Uses iodraw to facilitate display to overlay or image as appropriate
        """
        iodraw = self.get_iodraw()
        xY = iodraw.getXY(xY=self.xY, xYFract=self.xYFract, pos=self.pos, latLong=self.latLong)
        deg = self.get_deg()
        scale_width = iodraw.adjWidthBySize(4)
        if self.np2_spec > 0:
            xYEnd = iodraw.getXY(xY=self.xYEnd, xYFract=self.xYFractEnd,
                                pos=self.posEnd, latLong=self.latLongEnd)
            chg_x = xYEnd[0]-xY[0]
            chg_y = xYEnd[1]-xY[1]
            leng = sqrt(chg_x**2+chg_y**2)
            theta = -asin(chg_y/leng)
            deg = degrees(theta)
            tag = iodraw.drawLineSeg(xY=xY, xY2=xYEnd,
                                 color=self.color, width=scale_width)
        else:
            leng = self.get_leng()
            deg = self.get_deg()
            tag = iodraw.drawLineSeg(xY=xY, leng=iodraw.pixelToMeter(leng),
                                 deg=deg,
                                 color=self.color, width=scale_width)
            
        tic_deg = deg + self.tic_dir*90
        self.display_tags.append(tag)
        tic_len = self.tic_leng        # tic mark length in pixels
        unit_len = iodraw.unitLen(self.unit)        # Assume meter
        tic_space = self.marks*unit_len      # distance, in distance units (e.g., meters), between tics
        tic_width = iodraw.adjWidthBySize(2)
        tic_big_len = tic_len + 5
        tic_big_width = tic_width + iodraw.adjWidthBySize(3)
        mark_n = 0          # nth marker
        if iodraw.to_image:
            font_name = self.font_name
            if not re.match(r'\.[^.]+$', font_name):
                font_name += ".ttf"
            font = ImageFont.truetype(font_name, size=self.font_size+50)
        else:
            font = (self.font_name, self.font_size)
        nthmark = 0     # Heavy tics
        """
        Move in a straight line in direction of scale line
        between xY and xY end
        """
        scale_xY = xY
        scale_pos = 0           # position relative to length
        scale_end = iodraw.pixelToMeter(leng)
        tic_top = None          # Last big tic, if any
        label = None            # last label, if any
        while scale_pos <= scale_end:
            mark_n += 1
            if mark_n % self.bigMarks == 1:
                nthmark += 1
                iodraw.drawLineSeg(xY=scale_xY, deg=tic_deg, leng=iodraw.pixelToMeter(tic_big_len),
                                      color=self.color, width=tic_big_width)
                label = "%d" % round(scale_pos/unit_len)
                tic_top = iodraw.addToPoint(xY=scale_xY, lengPix=1.8*tic_big_len, deg=tic_deg)
                iodraw.drawText(tic_top, label, 
                           font=font, color=self.color)

            else:
                tic_top = iodraw.addToPoint(xY=scale_xY, lengPix=1.8*tic_big_len, deg=tic_deg)
                iodraw.drawLineSeg(xY=scale_xY, deg=tic_deg, leng=iodraw.pixelToMeter(tic_len),
                                      color=self.color, width=tic_width)
                ###label = "%d" % round(scale_pos/unit_len)
                ###iodraw.drawText(tic_top, label, 
                ###           font=font, color=self.color)
        
            """
            Update position to next tic mark
            """
            if SlTrace.trace("trace_scale"):
                SlTrace.lg("mark_n: %d scale_pos: %.2f scale_xY: %s" %
                      (mark_n, scale_pos, scale_xY))
            
            scale_pos = mark_n * tic_space
                
            scale_xY = iodraw.addToPoint(xY=scale_xY, leng=tic_space, deg=deg)
        # Put units after last big tic
        if tic_top is None:
            tic_top = scale_xY
        if label is None:
            label = " "
        unit_str = " "*len(label) + self.unit
        iodraw.drawText(tic_top, unit_str, font=font, color=self.color)
        

    def get_leng(self):
        """ Get scale length on canvas
        :returns: length in pixels
        """
        if self.leng is not None:
            return self.leng 
        
        return self.lengFract*self.get_sc().get_width()
    

    def addTitle(self, title, xY=None, size=None, color=None, **kwargs):
        if xY is None:
            xY = (self.getWidth()*.1, self.getHeight()*.05)
        if size is None:
            size = 32
        if color is None:
            color = (255, 255, 255, 255)
        title_font = ImageFont.truetype("arial.ttf", size=size)
        title_color = color        
        title_xy = xY
        self.text(title, xY=title_xy, font=title_font, fill=title_color, **kwargs)


    def text(self, text, xY=None,pos=None,latLong=None, **kwargs):
        """
        Draw text, at position, defaulting to current pen position
        like GeoDraw, but overlay
        :returns: list of canvas tags
        """
        canvas = self.get_canvas()
        gmi = self.get_gmi()
        xY = gmi.getXY(xY=xY, pos=pos, latLong=latLong)
        x_image, y_image = xY
        p1c = self.get_canvas_coords(x_image=x_image, y_image=y_image)
        tag = canvas.create_text(p1c.canvas_x, p1c.canvas_y,
                                 text=text, **kwargs)
        return tag
        

    def redisplay(self):
        """ Redisplay scale
        Should be the same as display does not change
        """
        self.display()
