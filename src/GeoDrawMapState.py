#GeoDrawMapState.py    05Jul2020

"""
Displayed map control/restoration
"""
from wx.lib.masked.maskededit import control
from _testcapi import instancemethod
from docutils.statemachine import State
class GeoDrawMapState:
    
    def __init__(self, geoDraw):
        """ map state control
        :geoDraw: geoDraw instancemethod
        """
        gD = self.geoDraw = geoDraw
        self.image  = self.image.copy()
        self.ulLat  = self.ulLat
        self.ulLong  = self.ulLong
        self.lrLat  = self.lrLat
        self.lrLong  = self.lrLong
        self.ulmx  = self.ulmx
        self.ulmy  = self.ulmy
        self.lrmx  = self.lrmx
        self.lrmy  = self.lrmy
        self.long_width  = self.long_width
        self.lat_height  = self.long_width
        self.ulX  = self.ulX
        self.ulY  = self.ulY
        self.lrX  = self.lrX
        self.lrY  = self.lrY
        
    def setState(self):
        """ set / reset map State
        """
        gD = self.geoDraw
        gD.image = self.image
        gD.ulLat = self.ulLat
        gD.ulLong = self.ulLong
        gD.lrLat = self.lrLat
        gD.lrLong = self.lrLong
        gD.ulmx = self.ulmx
        gD.ulmy = self.ulmy
        gD.lrmx = self.lrmx
        gD.lrmy = self.lrmy
        gD.long_width = self.long_width
        gD.lat_height = self.long_width
        gD.ulX = self.ulX
        gD.ulY = self.ulY
        gD.lrX = self.lrX
        gD.lrY = self.lrY
        