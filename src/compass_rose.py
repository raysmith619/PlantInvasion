# compass_rose.py    27May2020

class CompassRose:
    """ Compass Rose (map mark) if one
    """
    def __init__(self, placement=None,
                 present=False, tags=[]):
        """ Setup North facing map mark
        :placement: (x_fraction,  y_fraction, length_fraction)
        -1 => not on map
            default( .35, .50, .1)
        :present: visible
        """
        if placement is None:
            placement = (.20, .75, .1)
        elif isinstance(placement, int) and placement==-1:
            placement=(-1,-1,-1)    # Not on map
        
        self.x_fract = placement[0]
        self.y_fract = placement[1]
        self.len_fract = placement[2]
        self.present = present
        self.tags = tags
        
    def is_live(self):
        """ Check if live object
        """
        return self.x_fract != -1
    
    def live_obj(self):
        """ return object if live else None
        """
        if self.is_live():
            return self
        
        return None
