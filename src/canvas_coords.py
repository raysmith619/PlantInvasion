# canvas_coords.py    14May2020  crs
""" Canvas-Image-Distance Translations
"""
from select_trace import SelectError

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
        nc = 0
        if canvas_x is not None or canvas_y is not None: nc += 1
        if lat is not None or long is not None: nc += 1
        if x_dist is not None or y_dist is not None: nc += 1
        if x_image is not None or y_image is not None: nc += 1
        if nc == 0:
            raise SelectError("One of canvas, lat/long, dist or image is REQUIRED")
        
        if nc > 1:
            raise SelectError("Only one of canvas, lat/long, dist, image allowed")
        if canvas_x is not None or canvas_y is not None:
            x_image, y_image = sc.canvas2image(canvas_x, canvas_y)
            lat, long = gmi.pixelToLatLong((x_image, y_image))
            x_dist, y_dist = gmi.getPos(xY=(x_image, y_image), unit=unit)
        elif lat is not None or long is not None:
            x_image, y_image = gmi.getXY(latLong=(lat,long))
            x_dist, y_dist = gmi.getPos(latLong=(lat,long), unit=unit)
            canvas_x, canvas_y = sc.image2canvas(x_image,y_image)
        elif x_image is not None or y_image is not None:
            x_dist, y_dist = gmi.getPos(xY=(x_image,y_image), unit=unit)
            canvas_x, canvas_y = sc.image2canvas(x_image, y_image)
            lat, long = gmi.getLatLong(xY=(x_image,y_image))
        elif x_dist is not None or y_dist is not None:
            x_image, y_image = gmi.getXY(pos=(x_dist,y_dist), unit=unit)
            canvas_x, canvas_y = sc.image2canvas(x_image, y_image)
            lat, long = gmi.getLatLong()(xY=(x_image,y_image))
                        
        self.canvas_x = canvas_x
        self.canvas_y = canvas_y
        self.lat = lat
        self.long = long
        self.x_dist = x_dist
        self.y_dist = y_dist
        self.x_image = x_image
        self.y_image = y_image        
