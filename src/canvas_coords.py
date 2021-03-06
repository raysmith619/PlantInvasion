# canvas_coords.py    14May2020  crs
""" Canvas-Image-Distance Translations
"""
from select_trace import SlTrace
from select_error import SelectError

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
        gmi = sc.gmi
        if unit is None:
            unit = gmi.unit
        self.unit = unit
        nc = 0
        if canvas_y is not None: nc += 1
        if long is not None: nc += 1
        if y_dist is not None: nc += 1
        if y_image is not None: nc += 1
        if nc == 0:
            raise SelectError("One of canvas, lat/long, dist or image is REQUIRED")
        
        if nc > 1:
            raise SelectError("Only one of canvas, lat/long, dist, image allowed")
        if canvas_x is not None:
            if canvas_y is None:
                raise SelectError("canvas_x with no canvas_y")
            
            x_image, y_image = sc.canvas_to_image((canvas_x, canvas_y))
            lat, long = gmi.pixelToLatLong((x_image, y_image))
            x_dist, y_dist = gmi.getPos(xY=(x_image, y_image), unit=unit)
        elif lat is not None:
            if long is None:
                raise SelectError("lat with no Long")
            
            x_image, y_image = gmi.getXY(latLong=(lat,long))
            x_dist, y_dist = gmi.getPos(latLong=(lat,long), unit=unit)
            if SlTrace.trace("track_scale"):
                SlTrace.lg(f"lat={lat} long={long} x_dist={x_dist} y_dist={y_dist}")
            canvas_x, canvas_y = sc.image_to_canvas((x_image,y_image))
        elif x_image is not None:
            if y_image is None:
                raise SelectError("x_image with no y_image")
            
            x_dist, y_dist = gmi.getPos(xY=(x_image,y_image), unit=unit)
            canvas_x, canvas_y = sc.image_to_canvas((x_image, y_image))
            lat, long = gmi.getLatLong(xY=(x_image,y_image))
        elif x_dist is not None:
            if y_dist is None:
                raise SelectError("x_dist and no y_dist")
            
            x_image, y_image = gmi.getXY(pos=(x_dist,y_dist), unit=unit)
            canvas_x, canvas_y = sc.image_to_canvas((x_image, y_image))
            lat, long = gmi.getLatLong(xY=(x_image,y_image))
        else:
            if canvas_y is not None:
                missing = "canvas y with no canvas_x"
            elif long is not None:
                missing = "long with no lat"
            elif y_image is not None:
                missing = "y_image with no x_image"
            elif y_dist is not None:
                missing = "y_dist with no x_dist"
            else:
                missing = "No canvas_y, long, y_image, or y_dist"
            raise SelectError(f"Specification error: {missing}")
                        
        self.canvas_x = canvas_x
        self.canvas_y = canvas_y
        self.lat = lat
        self.long = long
        self.x_dist = x_dist
        self.y_dist = y_dist
        self.x_image = x_image
        self.y_image = y_image        
