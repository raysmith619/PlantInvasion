#image_over_draw.py    28Jun2020  crs, Author
"""
Facilitate combined image and canvas based drawing
Support drawing to canvas for real-time animated overlays and selective
transfer of these overlays to the image for saving
"""
from math import ceil, sqrt
import os
from PIL import ImageFont

from select_trace import SlTrace
from select_error import SelectError
from compass_rose import CompassRose
from GeoDraw import GeoDraw, geoUnitLen

class ImageOverDraw:
    
    def __init__(self, geoDraw=None, sc=None, to_image=False):
        """ Setup drawing access
            de
        :geoDraw: image access, via geoDraw object
                image writing only enabled if present
        :sc: canvas access, via ScrolledCanvas object
                canvas(overlay) writing only enabled if present
        :to_image: default destination of writing
                default: scanvas(False)
        """
        self.set_geoDraw(geoDraw)
        self.set_sc(sc)
        self.to_image = to_image
        self.trail_title_tag = None     # trail display tags
        self.trail_tags = []            # trail display tags
        
    def get_geoDraw(self):
        """ access to geoDraw
        if not present - Error
        future access may allow "lazy" evaluation/update
        """
        if self.geoDraw is None:
            raise SelectError("geoDraw not setup")
        return self.geoDraw

    def get_mapRotate(self):
        """ Get map rotation (counter clockwise)
        """
        return self.get_geoDraw().get_mapRotate()
    
    def get_pt_mgr(self):
        """ Get SurveyPointManager
        """
        sc = self.get_sc()
        pt_mgr = sc.get_pt_mgr()
        return pt_mgr
            
    def get_sc(self):
        """ access to ScrolledCanvas (overlay)
        if not present - Error
        future access may allow "lazy" evaluation/update
        """
        if self.sc is None:
            raise SelectError("geoDraw not setup")
        return self.sc

    

    def getXY(self, latLong=None, pos=None, xY=None, xYFract=None, unit=None, dest_based=False):
        """
        Get/Convert location pixel, map fraction, longitude, physical location/specification
        :dest_based: If True - give x,y based on self.to_image, else CANVAS
                    default: False

        """
        if dest_based and self.to_image:
            return self.get_geoDraw().getXY(latLong=latLong, pos=pos,
                                        xY=xY, xYFract=xYFract, unit=unit)
            
        return self.get_sc().getXY(latLong=latLong, pos=pos,
                                    xY=xY, xYFract=xYFract, unit=unit)


    def getWidth(self, dest_based=False):
        """ get display width
        """
        if dest_based and self.to_image:
            return self.get_geoDraw().getWidth()
        else:
            return self.get_sc().get_canvas_width()

    def getHeight(self, dest_based=False):
        """ get display width
        """
        if dest_based and self.to_image:
            return self.get_geoDraw().getHeight()
        else:
            return self.get_sc().get_canvas_height()
        
    def set_geoDraw(self, geoDraw):
        """ setup/update of GeoDraw
        ALL setup/update MUST go through here
        :geoDraw: geoDraw (image) access
        """
        self.geoDraw = geoDraw

    def set_sc(self, sc):
        """ setup/update of sc (ScrolledCanvas)
        ALL setup/update MUST go through here
        :sc: ScrolledCanvas (overlay) access
        """
        self.sc = sc

    def set_to_image(self, to_image=True):
        self.to_image = to_image

    def addTrail(self, trail_in, title=None, color_code=False,color="orange",
                 keep_outside=True,
                 width=3.):
        """
        :trail_in: trail input trail info
        :title: title (may be point file full path)
        :color: trail color
        :width: trail width in meters
        :color_code: color code longer point distances
        :keep_outside: Keep points even if outside region
                further back than self.max_dist_allowed,
                False: skip points outside region
                default: keep
        """
        if title is not None:
            self.trail_title = os.path.basename(title)
            title_xy = (self.getWidth()*.5, self.getHeight()*.05)
            self.addTitle(self.title, xY=title_xy)
        self.max_dist_allowed = 150.
        trail = self.cleanTrail(trail_in, keep_outside=keep_outside)
        for track in trail.get_segments():
            points = track.get_points()
            if color_code:
                return self.addTrail_color_code(points)
            
            line_width = int(self.meterToPixel(width))
            line_points = []
            for point in points:
                latLong = (point.lat, point.long)
                xY = self.getXY(latLong=latLong)
                line_points.append(xY)
            self.line(line_points, width=line_width,
                        fill=color)
        return True
            
    def addTrail_color_code(self, points):
        """ Do map with color coded line segments
        :points:
        :title:
        """
        prev_point = None
        for i, point in enumerate(points):
            if prev_point is not None:
                line_len = abs(self.geoDist(prev_point.latLong(), point.latLong()))
                line_color = None
                if line_len > 100:
                    line_color = "red"
                    SlTrace.lg(f"point {i+1}: {point} is at a distance {line_len:.1f}m")
                elif line_len > 20:
                    line_color = "blue"
                elif line_len > 10:
                    line_color = "green"
                elif line_len > 5:
                    line_color = "yellow"
                if line_len > self.max_dist_allowed:
                    SlTrace.lg(f"Ignoring Suspicious line {i+1}:"
                               f" {prev_point} to {point} as being too long: {line_len:.1f}m")
                    line_color = "red"
                else:
                    self.addTrailLine(prev_point, point, color=line_color)
            prev_point = point
        return True

    
    def addSample(self, point, color="red",
                  show_LL=True):
        """
        Add sample to current image
        :point: SamplePoint
        :color: sample label color
        :show_LL: show Latitude, Longitude
                default: True - show LL
    
        """
        label_color = (255,0,0)
        label_size = 30
        label_font = ImageFont.truetype("arial.ttf", size=label_size)
        latlong_size = label_size/2
        if isinstance(point, dict):
            plot_key = point["plot"]                    # Older
            lat, long = point["lat"], point["long"]
        else:
            plot_key = point.get_plot_key()
            lat, long = point.latLong()
        plot_id = plot_key
        xY = self.getXY(latLong=(lat,long))
        plot_color = (0,255,0, 128)
        plot_radius = 10.
        plot_radius_pixel = self.meterToPixel(plot_radius)
        if plot_key == "TBM":
            radius_pixel = self.meterToPixel(plot_radius*.25)
            self.circle(xY=xY, radius=radius_pixel, fill="#adf0f5")
            latlong_size *= 2
            label_xy = self.addToPoint(xY=xY, leng=1.5*label_size, deg=75)
            self.text(plot_id, xY=label_xy,  font=label_font, fill=label_color)
        else:    
            self.circle(xY=xY, radius=plot_radius_pixel, fill=plot_color)
            label_xy = self.addToPoint(xY=xY, leng=1.5*label_size, deg=75)
            self.text(plot_id, xY=label_xy,  font=label_font, fill=label_color)
        
        cent_color = (255,0,0)
        cent_radius = 1
        cent_radius_pixel = self.meterToPixel(cent_radius)
        self.circle(xY=xY, radius=cent_radius_pixel, fill=cent_color)
        # get a font
        # use a truetype font
        if show_LL:
            latlong_size = int(latlong_size)
            loc_string = "%.5f\n%.5f" % (long, lat)
            font_loc = ImageFont.truetype("arial.ttf", size=latlong_size)
            latlong_xy = self.addToPoint(latLong=(lat,long),
                                         leng=latlong_size, deg=-self.get_mapRotate())
            self.text(loc_string, xY=latlong_xy, font=font_loc,
                       fill=(255,255,255,255))    


    def addSamples(self, points, title=None, color=None,
                   show_LL=True):
        """ Add trail, given ll points
        First try just add line segments connecting thepoints
        :points: sample points (SamplePoint)
        :title: title (may be point file full path)
        :color: color for sample
        :show_LL: show Latitude, longitude
        """
        if title is not None:
            self.title = os.path.basename(title)
            title_xy = (self.getWidth()*.5, self.getHeight()*.1)
            self.addTitle(self.title, xY=title_xy)
        for point in points:
            self.addSample(point, color=color, show_LL=show_LL)
        return True

    
    def addToPoint(self, leng=None, lengPix=None, xY=None, pos=None,
                   latLong=None, theta=None, deg=None, unit=None, dest_based=False):
        """
        Add to point (in unrotated drawing), returning adjusted point in appropriate pixels
        Add requested rotation (curDeg if None) to map rotation, if
        mapRotation is not None
        :dest_based: If True - give x,y based on self.to_image, else CANVAS
                    default: False
        """
        if dest_based and self.to_image:
            return self.get_geoDraw().addToPoint(leng=leng, lengPix=lengPix, xY=xY, pos=pos,
                                                 latLong=latLong, theta=theta, deg=deg, unit=unit)
 
        return self.get_sc().addToPoint(leng=leng, lengPix=lengPix, xY=xY, pos=pos,
                                        latLong=latLong, theta=theta, deg=deg, unit=unit)
 
            
    def addTrailLine(self, p1, p2, color=None):
        """ Do trail segment from p1, 2p
        :p1: First point GPXPoint
        :p2: Second point GPXPoint    
        """
        if color is None:
            color = "orange"
        line_width = self.meterToPixel(self.trail_width)
        self.lineSeg(latLong=(p1.lat,p1.long), latLong2=(p2.lat,p2.long), width=int(line_width),
                     fill=color)

    def cleanTrail(self, trail_in, keep_outside=True):
        """ Adjust initial points to most likely to be valid measurements
            Assemble trail stats
            1. Throw any points outside border
            :trail_in: raw trail info (SurveyTrail)
            :keep_outside: Keep points even if outside region
                or further back than self.max_dist_allowed
                False: skip points outside region
                default: keep
        """
        return trail_in  # For now - no changes
        '''
        trail = SurveyTrail()
        n_diff = 0              # Number of distances (n good pts - 1)
        n_outside = 0
        dist_sum = 0.
        max_dist = None
        min_dist = None
        points_len = len(points_in)
        for i, point in enumerate(points_in):
            if not self.is_inside(latLong=point.latLong()):
                n_outside += 1
                SlTrace.lg(f"Questioning point {i+1}: {point} as outside border", "clean_trail")
                if not keep_outside:
                    continue    # Skip point outside border
            if i == 0 and len(points_in) > 1:
                p1_ll = points_in[i].latLong()
                p2_ll = points_in[i+1].latLong()
                dist = abs(self.geoDist(p1_ll, p2_ll))
                if dist > self.max_dist_allowed:
                    n_outside += 1
                    SlTrace.lg(f"Questioning point {i+1}: {point} as too far")
                    if not keep_outside:
                        continue
            point_prev = points[-1] if len(points) > 0 else None
            check_prev = True if point_prev is not None else False
            if i >= points_len-1:
                check_next = False
            else:
                check_next = True
                point_next = points_in[i+1]
            if check_prev:
                dist_prev = abs(self.geoDist(point_prev.latLong(), point.latLong()))
                dist = dist_prev
            if check_next:
                dist_next = abs(self.geoDist(point.latLong(), point_next.latLong()))
                dist = dist_next
            if check_prev and check_next:
                dist = max(dist_prev, dist_next)
            points.append(point)
            if check_prev:
                n_diff += 1
            if min_dist is None or dist < min_dist:
                min_dist = dist
            if max_dist is None or dist > max_dist:
                max_dist = dist
            dist_sum += dist            
        SlTrace.lg("Trail Statistics")
        SlTrace.lg(f"Number of points: {len(points_in)}")
        SlTrace.lg(f"Number of displayed points: {len(points)}")
        avg_dist = 0 if n_diff == 0 else dist_sum/n_diff
        if len(points) > 0:
            SlTrace.lg(f"minimum distance: {min_dist:.1f}m maximum distance: {max_dist:.1f}m average: {avg_dist:.2f}m")
            SlTrace.lg(f"Total path distance: {dist_sum:.1f}m") 

        return trail
        '''
 
    def drawLineSeg(self, xY=None, xYFract=None, pos=None, latLong=None,
                xY2=None, xYFract2=None, pos2=None, latLong2=None,
                 leng=10, theta=None, deg=None, **kwargs):
        """
        Draw line segment, supporting pixel, pos, latLong
        :xY: x_image, y_image
        :leng: length in meters
        Draw line segment starting at given point
        position(xY or pos or latLong) and going to 
            2nd point:
                (xY2 or pos2 or latLong2)
                    or
                point 2 plus length leng at angle (theta radians or deg degrees)
            
        Extra named args are passed to drawLine...
        :returns: list of canvas tags, if appropriate
        """
        xY = self.getXY(xY=xY, xYFract=xYFract, pos=pos, latLong=latLong)
        if xY2 is not None or xYFract2 is not None or pos2 is not None or latLong2 is not None:
            new_xY = self.getXY(xY=xY2, xYFract=xYFract2, pos=pos2, latLong=latLong2)
        else:
            new_xY = self.addToPoint(leng=leng, xY=xY, theta=theta, deg=deg)
        tag = self.drawLine(xY, new_xY, **kwargs)
        return tag

    def meterToPixel(self, meter, dest_based=False):
        """ cvt meter to pixel
        """
        if dest_based and self.to_image:
            return self.get_geoDraw().meterToPixel(meter)
        else:
            return self.get_sc().meterToPixel(meter)

    def pixelToMeter(self, pixel, dest_based=False):
        """ cvt pixel to meter
        """
        if dest_based and self.to_image:
            return self.get_geoDraw().pixelToMeter(pixel)
        else:
            return self.get_sc().pixelToMeter(pixel)
            
    def drawTrailTitle(self, title, xY=None, size=None, color=None, **kwargs):
        """ 
        """
        if self.trail_title_tag is not None:
            self.get_sc().delete_tag(self.trail_title_tag)
            self.trail_title_tag = None
        if xY is None:
            xY = (self.getWidth()*.1, self.getHeight()*.05)
        ###xY = self.adj_xY(xY)
        if size is None:
            size = 16
        if self.to_image:
            size += 55
        if color is None:
            color = "white"
        if self.to_image:
            title_font = ImageFont.truetype("arial.ttf", size=size+35)
        else:
            title_font = ("tahoma", size)
        title_xy = xY
        self.trail_title_tag = self.drawText(title_xy,
                                    font=title_font,
                                     text=title, color=color,
                                     **kwargs)

    def delete_tag(self, tag):
        """ delete canvas tag
        """
        self.get_sc().delete_tag(tag)



    def adjWidthBySize(self, lineWidth):
        """
        Adjust line widths to account for large canvas/images
        """
        mindim = min(self.getWidth(), self.getHeight())
        adj_lineWidth = lineWidth
        if mindim == 0:
            mindim = 1
        line_fract = lineWidth/mindim
        min_line_fract = .001
        if line_fract < min_line_fract * adj_lineWidth:
            adj_lineWidth = ceil(min_line_fract * mindim * lineWidth)
        if lineWidth < 1:
            adj_lineWidth = 1
        if adj_lineWidth > lineWidth:
            return lineWidth            # Leave alone
        
        return adj_lineWidth


    def adj_xY(self, xY):
        """ Adjust coordinate based on self.to_image
        :xY: canvas x,y coordinates
        :returns: appropriate x,y coordinates for display
        """
        if self.to_image:
            return self.get_sc().canvas_to_image(xY)
        
        return xY 
    
        
    def drawCircle(self, xY=None, radius=None, color=None, **kwargs):
        """
        Draw circle, depending on to_image(image,overlay),
        at current location with radius, in pixels
        """
        xY = self.adj_xY(xY)
        if radius is None:
            radius = 2
        if self.to_image:
            geoDraw = self.get_geoDraw()
            return geoDraw.drawCircle(xY=xY, radius=radius, color=color, **kwargs)
        else:
            sc = self.get_sc()
            return sc.drawCircle(xY=xY, radius=radius, color=color, **kwargs)


            
    def drawCompassRose(self, compassRose=None):
        """
        Add orientation marker overlay/image based on to_image
        Stores canvas tags in self.compass_rose_tags
        :returns: list of tags created
        :compassRose: instance of CompassRose
                    OR (x_fract, y_fract, len_fract) of x,y, length(smallest)

        :to_image: True --> place figure in image (permanent for saving)
                    False(default) --> place figure in canvas
        """
        SlTrace.lg("drawCompassRose", "compass_rose")
        if compassRose is not None:
            if isinstance(compassRose, CompassRose):
                self.compass_rose = compassRose
            else:
                self.compass_rose = CompassRose(compassRose).live_obj()
        if self.compass_rose is None:
            return
        
        cro = self.compass_rose
        if cro.tags:                    # Always remove previous
            for tag in cro.tags:
                self.delete_tag(tag)
            cro.tags = []
        x_fract = cro.x_fract
        y_fract = cro.y_fract
        lenFraction = cro.len_fract * 1
        canvas_width = self.getWidth()
        canvas_height = self.getHeight()
        ap_px =  canvas_width * x_fract
        ap_py = canvas_height * y_fract
        ap_px = (ap_px, ap_py)
        label_size = 16
        arrow_len = int(sqrt(canvas_width**2 + canvas_height**2) * lenFraction)
        arrow_len_m = self.pixelToMeter(arrow_len)
        text_off = label_size
        text_off_m = self.pixelToMeter(text_off)
        cent_color = "red"
        north_deg = GeoDraw.NORTH_DEG     # Default map north
        arrow_color = "green"
        arrow_width = 3
        arrow_point_len = 10*arrow_width
        arrowshape=(arrow_point_len, 1.5*arrow_point_len,
                    arrow_point_len*.2)
        arrow_point_len_m = self.pixelToMeter(arrow_point_len)
        aps_px = self.addToPoint(leng=-arrow_len_m/2, xY=ap_px,
                                   deg=north_deg, unit="m")
        ap_st = aps_px
        
        ap_pt_px = self.addToPoint(leng=arrow_point_len_m/2+arrow_len_m/2,
                                   xY=ap_px,
                                   deg=north_deg, unit="m")
        """ Shorten arrow shaft under arrow head """
        ap_pt_shortened_px = self.addToPoint(leng=-arrow_point_len_m*.8,
                                   xY=ap_pt_px,
                                   deg=north_deg, unit="m")
        # addToPoint takes into consideration image rotation
 
        tag = self.drawLine(ap_st, ap_pt_shortened_px,
                                 color=arrow_color,
                                 width=arrow_width)
        cro.tags.append(tag)
        """
        To facilitate image CompassRose
        we draw the arrow head as a polygon
        """
        arh_pts_px = []                      # Arrow head pts ccw, image pts
        arh_d1, arh_d2, arh_d3 = arrowshape     # arrowshape  d1,d2,d3
        arh_d1_m = self.pixelToMeter(arh_d1)    # arrowshape in meters
        arh_d2_m = self.pixelToMeter(arh_d2)
        arh_d3_m = self.pixelToMeter(arh_d3)
        arh_pt_px = ap_pt_px
        arh_pts_px.append(arh_pt_px)   # arrow head point (p1)
        
        arh_height_m = sqrt(arh_d2_m**2 - arh_d3_m**2)
        arh_base_px = self.addToPoint(leng=-arh_height_m,      # Move down by height of arrow head
                                       xY=arh_pt_px,
                                       deg=north_deg, unit="m")
        arh_p2_px = self.addToPoint(leng=arh_d3_m,             # Move left by width/2 of arrow head
                                       xY=arh_base_px,
                                       deg=north_deg+90, unit="m")
        arh_pts_px.append(arh_p2_px)
        
        arh_p3_px = self.addToPoint(leng=arh_height_m-arh_d1_m,            # Move up/down to base center of arrow head
                                                                            # depending on d3 vs height
                                       xY=arh_base_px,
                                       deg=north_deg, unit="m")
        arh_pts_px.append(arh_p3_px)
        arh_p4_px = self.addToPoint(2*arh_d3_m,                            # Move right 2*d3 from p2 point
                                        xY=arh_p2_px,
                                        deg=north_deg-90, unit="m")
        arh_pts_px.append(arh_p4_px)
        cr_arrow_head = self.drawPolygon(*arh_pts_px, color=arrow_color)
        cro.tags.append(cr_arrow_head)
                                        
        cr_circle = self.drawCircle(ap_px,
                      radius=4, color=cent_color)
        cro.tags.append(cr_circle)
        cr_circle_cent = self.drawCircle(ap_px,
                      radius=2, color=arrow_color)
        cro.tags.append(cr_circle_cent)
        # North Label
        text_px = self.addToPoint(leng=text_off_m, xY=ap_pt_px,
                                   deg=north_deg, unit="m") 
        if self.to_image:
            north_label_font = ImageFont.truetype("arial.ttf", size=label_size+60)
        else:
            north_label_font = ("Helvetica", label_size)
        tag = self.drawText(text_px,
                               text = "North",
                               font=north_label_font, color=arrow_color)
        cro.tags.append(tag)

    def image_line_width(self, width=1):
        """ Convert canvas line width to image line width
            based on relative canvas / image size
        """
        gD = self.get_geoDraw()
        sc = self.get_sc()
        image_to_canvas_width = gD.getWidth()/sc.get_width() 
        image_to_canvas_height = gD.getHeight()/sc.get_height()
        image_to_canvas = max(image_to_canvas_width, image_to_canvas_height, 1)
        return width*image_to_canvas 
        
    def drawLine(self, *points, color=None, width=None, **kwargs):
        apoints = [self.adj_xY(point) for point in points]
        if self.to_image:
            gD = self.get_geoDraw()
            width = self.image_line_width(width)  # Adjust for different size
            gD.drawLine(*apoints, color=color, width=width, **kwargs)
            return
        
        sc = self.get_sc()
        tag = sc.drawLine(*apoints,
            color=color, width=width, **kwargs)
        return tag


        
    def drawPolygon(self, *points, color=None, **kwargs):
        """ drawPolygon (ImageOverDraw image part
        """
        apoints = [self.adj_xY(point) for point in points]
        if color is not None:
            kwargs['fill'] = color
        pts = []
        for point in apoints:
            pt = (int(point[0]), int(point[1]))
            pts.append(pt)
        if self.to_image:
            geoDraw = self.get_geoDraw()
            geoDraw.drawPolygon(*apoints, color=color, **kwargs)
            return
        
        sc = self.get_sc()
        tag = sc.drawPolygon(*apoints,
            color=color, **kwargs)
        return tag

        
    def drawText(self, xY, text, font=None, color=None, **kwargs):
        """ Draw text overlay/image
        :unused args passed to appropriate drawText
        :returns: canvas tags, iff appropriate

        """
        xY = self.adj_xY(xY)
        if self.to_image:
            gD = self.get_geoDraw()
            gD.drawText(xY, text, color=color, font=font, **kwargs)
        else:
            sc = self.get_sc()
            if font is not None:
                if not isinstance(font, tuple):
                    if hasattr(font, 'font'):
                        font = font.font
                    font_family = font.family
                    font_height = font.height
                    font = (font_family, font_height)
                
            text_tag = sc.drawText(xY, text,
                                   font=font,
                                   color=color, **kwargs)
            
            return text_tag
        
        

    def drawTrail(self, trail=None, title=None, color=None,
                     color_points=None,
                     line_width=None,
                     show_points=False):
        """ Display trail depending on in_image setting
        :trail: trail info (SurveyTrail)
        :title: title (may be point file full path)
        :color: trail color default: orange
        :line_width: trail line width
                    default: from trail
        :show_points: Show points, default: False - points not shown
        :color_points: points color default: same as color
        :returns: trail (SurveyTrail) overlaid
        """
        """ Remove any previous trail display """
        self.remove_trail_display()
            
        if color is None:
            color = "orange"
        if color_points is None:
            color_points = "black"
            
        if trail is None:
            trail_selection = self.get_point_list("trails")
            if trail_selection is None:
                SlTrace.lg("Trail added")
                self.add_trail_file(self.trailfile)
                trail_selection = self.get_point_list("trails")
            trail = trail_selection.point_list
        if title is not None:
            self.trail_title = os.path.basename(title)
            title_xy = (self.getWidth()*.5, self.getHeight()*.05)
            if self.to_image:
                title_xy = (self.getWidth()*.05, self.getHeight()*.05)   # Not centered
                
            self.drawTrailTitle(self.trail_title, xY=title_xy)
        self.trail_width = 2.       # Trail width in meters
        self.max_dist_allowed = 150.
        if line_width is None:
            line_width = max(self.meterToPixel(self.trail_width), 2)
        sc = self.get_sc()
        for track in trail.get_segments():
            track_points = track.get_points()
            prev_pt = None              # Define, set after each iteration
            for point_no, point in enumerate(track_points, start=1):
                pt = sc.ll_to_canvas(lat=point.lat, long=point.long)
                if point_no > 1:
                    tag = self.drawLine(prev_pt, pt, color=color,
                                       width=line_width)
                    if not self.to_image:
                        self.trail_tags.append(tag)
                if show_points:
                    point.display(displayed=True, color=color_points)
                prev_pt = pt
        sc = self.sc
        sc.set_size()
        sc.lower_image()        # Place map below points/lines
        return trail

    def remove_trail_display(self):
        """ Remove trail display, possibly in preparation for updating
        """
        pt_mgr = self.get_pt_mgr()
        if pt_mgr is None or pt_mgr.trail is None:
            return      # None to dispaly
        
        SlTrace.lg("Removing trail display", "trail")
        self.remove_trail_title_display()
        for tag in self.trail_tags:
            self.delete_tag(tag)
        self.trail_tags = []   
            
    def remove_trail_title_display(self):
        if self.trail_title_tag is not None:
            self.delete_tag(self.trail_title_tag)
            self.trail_title_tag = None

    def unitLen(self, unit):
        """ Unit length in meters
        :unit: unit name (only looks at first letter)
                feet, meeter, yard, smoot
                default: self.unit, meter
        """
        if unit is None:
            unit = self.unit
        return geoUnitLen(unit)
        