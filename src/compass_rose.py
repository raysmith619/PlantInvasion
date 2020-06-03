# compass_rose.py    27May2020

class CompassRose:
    """ Compass Rose (map mark) if one
    """
    def __init__(self, x_fract=.35, y_fract=.50, len_fract=.1,
                 present=False, tags=[]):
        self.x_fract = x_fract
        self.y_fract = y_fract
        self.len_fract = len_fract
        self.present = present
        self.tags = tags
        
