# track_points.py    29Apr2020  crs
"""
Facilitate tracking single point, using PointPlace
Facilitate tracking point pairs using PointPlaceTwo

Keeps a list of tracked points
Keeps a list of tracked point-pairs
"""
from tkinter import *

from select_trace import SlTrace
from select_error import SelectError
from select_control_window import SelectControlWindow
from point_place_two import PointPlaceTwo
from geo_address import GeoAddress
from select_list import SelectList


class FavoriteAddress:
    """ A favorite address
    Supports providing current/favorite settings
    """
    FN_PREFIX = "FAVORITE_"
    def __init__(self, name=None, address=None, lat_long=None,
                 width=None, height=None, xOffset=None, yOffset=None,
                 zoom=None, show="name", unit="meter"):
        """ Favorite item:
        :name: item descriptive name <file:...> image
        :address: address composit string
        :lat_long: latitude/longitude pair to be used to go
        :width: width of plot
        :height: hight of plot
        :xOffset: plot x-offset (from lat_long)
        :yOffset: plot y-offset (from lat_long)
        :zoom: Google precision
        :unit: linear  units
        :show: field to show in selection list default: "name"
        """
        
        self.name=name
        self.address = address
        self.lat_long = lat_long
        self.width = width
        self.height = height
        self.xOffset = xOffset
        self.yOffset = yOffset
        self.show = show 
        self.zoom = zoom


class MappingControl(SelectControlWindow):
    """ Collection of mapping selection controls
    """
    CONTROL_NAME_PREFIX = "mapping_control"
    DEF_WIN_X = 500
    DEF_WIN_Y = 300
    
    
        
            
    def __init__(self, mgr,
                 title="", control_prefix=None,
                 address="",
                 street1="",
                 street2="",
                 city="",
                 state="",
                 zipcode="",
                 country="",
                 longitude=0.,      # Set float type
                 latitude=0.,       # Set float type
                 zoom=22,
                 width=40.,
                 height=40.,
                 xOffset=0.,
                 yOffset=0.,
                 unit = "meter",
                 **kwargs):
        """ Initialize subclassed SelectControlWindow
             Setup score /undo/redo window
             :mgr: tracking point manager
             :wait: True - wait till destroyed
             :mw: main window if one
             :zoom:    Google Maps precision default: 22 (High)
        """
        self.mgr = mgr
        self.unit = unit
        if title is None:
            title = "Mapping Control"
        if control_prefix is None:
            control_prefix = MappingControl.CONTROL_NAME_PREFIX
        self.address = address
        self.street1 = street1
        self.street2 = street2
        self.city = city
        self.state = state
        self.zipcode = zipcode
        self.country = country
        self.latitude = latitude
        self.longitude = longitude
        self.width = width
        self.height = height
        self.xOffset = xOffset
        self.yOffset = yOffset
        self.zoom = zoom
        super().__init__(title=title, control_prefix=control_prefix,
                       **kwargs)
        self.control_display()
        self.wait_location = True
        self.lat_long = None
        self.load_favorites()
        
    def load_favorites(self):
        """ Load favorite addresses
        """
        self.favorites = {}
        self.favorites[self.get_favorite_name()] =  FavoriteAddress("Grampy & Grammy's", "233 Common St., Watertown, MA")
        self.favorites[self.get_favorite_name()] =  FavoriteAddress("Alex & Decklan", "24 Chapman St., Watertown, MA")
        self.favorites[self.get_favorite_name()] =  FavoriteAddress("Antie Jen", "67 Lenon Rd, Arlington, MA")
        self.favorites[self.get_favorite_name()] =  FavoriteAddress("Avery & Charlie", "85 Clarendon St, Boston, MA")           

    def has_address(self):
        """ Check if address specified and found
        """
        return self.found_address
    
    def control_display(self):
        """ display /redisplay controls to enable
        entry / modification
        """


        super().control_display()       # Do base work        
        
        controls_frame = self.top_frame
        controls_frame.pack(side="top", fill="x", expand=True)
        self.controls_frame = controls_frame

        location_frame = Frame(controls_frame)
        location_frame.pack()
        address_frame = Frame(location_frame)
        self.set_fields(address_frame, "address", title="Address")
        self.set_button(field="get_address", label="Get Address", command=self.get_address)
        self.set_entry(field="address", label="address", value=self.address, width=40)
        self.set_button(field="address", label="Favorites", command=self.get_favorites)
        address_frame1 = Frame(location_frame)
        self.set_fields(address_frame1, "address", title="")
        self.set_entry(field="street1", label="Street1", value=self.street1)
        self.set_entry(field="street2", label="Street2",  value=self.street2)
        address_frame2 = Frame(location_frame)
        self.set_fields(address_frame2, "address", title="    ")
        self.set_entry(field="city", label="City", value = self.city)
        self.set_entry(field="state", label="State", value = self.state)
        self.set_entry(field="country", label="Country", value=self.country)
        
        latitude_longitude_frame = Frame(location_frame)
        self.set_vert_sep(location_frame, text="")
        self.set_fields(latitude_longitude_frame, "lat_long", title="Latitude Longitude")
        self.set_button(field="get_address", label="Get Long Lat", command=self.get_address_ll)
        self.set_entry(field="latitude", label="Latitude", value=self.latitude, width=15)
        self.set_entry(field="longitude", label="Longitude", value=self.longitude, width=15)
        self.set_entry(field="zoom", label="zoom", value=self.zoom, width=3)
        size_frame = Frame(location_frame)
        self.set_fields(size_frame, "size", title="Map Size")
        self.set_entry(field="width", label="Width", value=self.width, width=8)
        self.set_entry(field="height", label="Height", value=self.height, width=8)
        self.set_entry(field="x_offset", label="X-Offset", value=self.xOffset, width=8)
        self.set_entry(field="y_offset", label="y-Offset", value=self.yOffset, width=8)
        
        self.set_sep()
        unit_frame = Frame(controls_frame)
        self.set_fields(unit_frame, "distance_units", title="distance units")
        self.set_radio_button(frame=unit_frame, field="unit", label="meter", command=self.change_unit,
                               set_value=self.unit)
        self.set_radio_button(frame=unit_frame, field="unit", label="yard", command=self.change_unit)
        self.set_radio_button(frame=unit_frame, field="unit", label="foot", command=self.change_unit)
        self.set_radio_button(frame=unit_frame, field="unit", label="Smoot", command=self.change_unit)
        
        self.arrange_windows()
        if not self.display:
            self.hide_window()
        
    def change_unit(self, unit=None):
        if unit is None:
            unit = self.unit
        else:
            self.unit = unit
        if self.mgr is not None:
            self.mgr.change_unit(unit)

    def get_location(self, wait=True):
        """ Get location specified
        :wait: Wait till specified (i.e. Get Address, or Get Lat Long pressed)
        :returns: lat,long pair None if no location found
        """
        if wait:
            while self.wait_location:
                self.update()
        return self.lat_long    
            
    def get_address_ll(self, lat=None, long=None, update_map=True):
        """ Display map from form's Latitude, Longitude
        """
        if lat is not None:
            self.set_ctl_val("lat_long.latitude", lat)
        if long is not None:
            self.set_ctl_val("lat_long.longitude", long)
        self.set_vals()
        self.lat_long = (self.latitude, self.longitude)
        self.wait_location = False
        if update_map:
            self.mgr.sc.update_lat_long(latLong=self.lat_long,
                                         xDim=self.width, yDim=self.height,
                                         xOffset=self.xOffset, yOffset=self.yOffset,
                                         unit=self.unit,
                                         zoom=self.zoom)
        fav_name = self.get_favorite_name(FavoriteAddress.FN_PREFIX + "001")
        fav =  FavoriteAddress(name=fav_name, address=self.address, lat_long=self.lat_long,
                                  width=self.width, height=self.height,
                                  xOffset=self.xOffset, yOffset=self.yOffset,
                                  unit=self.unit, zoom=self.zoom)
        self.favorites[fav.name] = fav
        return True    
            
    def get_favorites(self):
        """ Bring up list of favorite addresses
        """
        favorite_items = []
        favorite_by_show = {}   # by displayed string
        for favorite_name in self.favorites:
            favorite = self.favorites[favorite_name]
            show = favorite.show
            if hasattr(favorite, show):
                show_str = getattr(favorite, show)
                if show_str is None or show_str == "":
                    show_str = favorite.address
                if show_str is None or show_str == "":
                    show_str = str(lat_long)
            if show_str is None or show_str == "":
                show_str = favorite.address
            favorite_by_show[show_str] = favorite
            favorite_items.append(show_str)
        x0 = 300
        y0 = 400
        width = 200
        height = 400
        SlTrace.lg(f"x0={x0}, y0={y0}, width={width}, height={height}", "select_list")                    
        app = SelectList(items=favorite_items,
                         position=(x0, y0), size=(width, height))
        selected_field = app.get_selected()
        SlTrace.lg(f"selected_field:{selected_field}")    

    def get_favorite_name(self, name=None):
        """ Get unique favorite name
        using given as a starting point
        Force name to be unique.
           If None start with FN_PREFIX
        Take non-numeric prefix by removing any numeric suffix
        Try ascending numeric suffixes until result is unique
        """
        if name is None or name in self.favorites:
            nn = 0
            if name is None:
                name = FavoriteAddress.FN_PREFIX
            nm = re.match(r'(.*)(\d+)$', name)
            if nm is not None:
                name = nm.group(1)      # Take part before any number    
            while True:
                nn += 1
                name_str = f"{name}{nn:03d}"
                if name_str not in self.favorites:
                    name = name_str
                    break
        return name
            
    def get_address(self, address=None, update_map=True):
        """ Get address and put map up
        :address: address to get, default: use form's
        :update_map: Update map view, if successful
                    default: True
        """
        if address is not None:
            self.set_ctl_val("address.address", address)
        SlTrace.lg(f"get_address: {self.get_location_str()}")
        ga = GeoAddress(address=self.address,
                        street1=self.street1,
                        street2=self.street2,
                        city=self.city,
                        state=self.state,
                        zipcode=self.zipcode,
                        country=self.country)
        lat_long = ga.get_lat_long()
        if lat_long is None:
            err = ga.get_error()
            SlTrace.lg(f"error:{err}")
            self.report(f'{err}')
            self.lat_Long = None
            self.wait_location = False
            return False
        
        self.set_ctl_val("lat_long.latitude", lat_long[0])
        self.set_ctl_val("lat_long.longitude", lat_long[1])
        self.set_vals()
        self.lat_long = lat_long
        self.wait_location = False
        SlTrace.lg(f"get_loc: lat:{self.latitude}, Long: {self.longitude}")
        res = self.get_address_ll(update_map=update_map)
        return res          # True iff OK

    def list_sep(self, items, sep=", "):
        items_str = ""
        for item in items:
            if item:
                if items_str != "":
                    items_str += sep
                items_str += item
        return items_str
    
    def get_location_str(self):
        """ Get most recently requested location as a string
        """
        loc_str = self.list_sep([self.address, self.street1, self.street2, self.city, self.state, self.country])
        return loc_str

    def set_vals(self):
        """ Update internal values from all form ctls
        """
        self.address = self.get_val_from_ctl("address.address")
        self.street1 = self.get_val_from_ctl("address.street1")
        self.street2 = self.get_val_from_ctl("address.street2")
        self.city = self.get_val_from_ctl("address.city")
        self.state = self.get_val_from_ctl("address.state")
        self.country = self.get_val_from_ctl("address.country")
        self.width = self.get_val_from_ctl("size.width")
        self.height = self.get_val_from_ctl("size.height")
        self.xOffset = self.get_val_from_ctl("size.x_offset")
        self.yOffset = self.get_val_from_ctl("size.y_offset")
        self.unit = self.get_val_from_ctl("distance_units.unit")
        self.latitude = self.get_val_from_ctl("lat_long.latitude")
        self.longitude = self.get_val_from_ctl("lat_long.longitude")
        self.zoom = self.get_val_from_ctl("lat_long.zoom")
    
    def destroy(self):
        """ Destroy window resources
        """
        if self.mw is not None:
            self.mw.destroy()
        self.mw = None
        
    
if __name__ == '__main__':
    from select_trace import SlTrace

    def set_cmd(ctl):
        SlTrace.lg("Set Button")
                
    root = Tk()
    root.withdraw()       # Hide main window

    SlTrace.setProps()
    loop = True
    ###loop = False

    mc = MappingControl(None, mw=None, title="MappingControl Testing",
                        address="Testing Address",
                         win_x=200, win_y=300, win_width=400, win_height=150)
    ###tc.control_display()

    root.mainloop()