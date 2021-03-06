# maping_control.py    29Apr2020  crs
"""
"""
from tkinter import *

from select_trace import SlTrace
from select_error import SelectError
from GeoDraw import geoMove
from select_control_window import SelectControlWindow
from geo_address import GeoAddress
from select_list import SelectList
###from mapIt import latitude


class FavoriteAddress:
    """ A favorite address
    Supports providing current/favorite settings
    """
    PROP_PREFIX = "FAVORITE"
    def __init__(self, mc, name=None, address=None,
                 centered=True, latitude=None, longitude=None,
                 width=None, height=None, xOffset=None, yOffset=None,
                 maptype=None,
                 mapRotate=None,
                 zoom=None, show="name", unit="meter",
                 map_show_scales=False,
                 
                 ):
        """ Favorite item:
        :mc: mapping control (MappingControl)
        :name: item descriptive name <file:...> image
        :address: address composit string
        :maptype: plot map type
        :centered: plot centered on lat/Long, else ul corner
        :latitude: latitude
        :longitude: longitude
        :width: width of plot
        :height: hight of plot
        :xOffset: plot x-offset (from lat_long)
        :yOffset: plot y-offset (from lat_long)
        :zoom: Google precision
        :unit: linear  units
        :show: field to show in selection list default: "name"
        """
        self.mc = mc
        self.name=name
        self.address = address
        self.maptype = maptype
        self.mapRotate = mapRotate
        self.centered = centered 
        self.latitude = latitude
        self.longitude = longitude
        self.width = width
        self.height = height
        self.xOffset = xOffset
        self.yOffset = yOffset
        self.show = show
        self.zoom = zoom
        self.unit = unit
        self.map_show_scales = mc.map_show_scales
        self.map_scale1_unit = mc.map_scale1_unit
        self.map_scale1_xFract = mc.map_scale1_xFract
        self.map_scale1_yFract = mc.map_scale1_yFract
        self.map_scale1_lengFract = mc.map_scale1_lengFract
        self.map_scale1_deg = mc.map_scale1_deg
        self.map_scale2_unit = mc.map_scale2_unit
        self.map_scale2_xFract = mc.map_scale2_xFract
        self.map_scale2_yFract = mc.map_scale2_yFract
        self.map_scale2_lengFract = mc.map_scale2_lengFract
        self.map_scale2_deg = mc.map_scale2_deg

class MappingControl(SelectControlWindow):
    """ Collection of mapping selection controls
    """
    CONTROL_NAME_PREFIX = "mapping_control"
    DEF_WIN_X = 500
    DEF_WIN_Y = 300
    
    """ favorite to ctl field """
    att_to_ctls = [
        ("name", "address.name"),
        ("address", "address.address"),
        ("maptype", "map.maptype"),
        ("mapRotate", "map.rotate"),
        ("centered", "Lat_Long.centered"),
        ("latitude", "lat_long.latitude"),
        ("longitude", "lat_long.longitude"),
        ("zoom", "lat_long.zoom"),
        ("width", "size.width"),
        ("height", "size.height"),
        ("xOffset", "size.x_offset"),
        ("yOffset", "size.y_offset"),
        ("unit", "distance_units.unit"),
        ("map_show_scales", "map_scales.map_show_scales"),
        ("map_scale1_unit", "map_scale1.unit"),
        ("map_scale1_xFract", "map_scale1.xFract"),
        ("map_scale1_yFract", "map_scale1.yFract"),
        ("map_scale1_lengFract", "map_scale1.lFract"),
        ("map_scale1_deg", "map_scale1.deg"),
        ("map_scale2_unit", "map_scale2.unit"),
        ("map_scale2_xFract", "map_scale2.xFract"),
        ("map_scale2_yFract", "map_scale2.yFract"),
        ("map_scale2_lengFract", "map_scale2.lFract"),
        ("map_scale2_deg", "map_scale2.deg"),
        ]
    
    def field2att(self, field):
        """ Get attribute, given the control field
            Case sensitive field
        :field: control field
        :returns: our attribute
        """
        for att_to_ctl in MappingControl.att_to_ctls:
            att, fld = att_to_ctl
            if field == fld:
                return att
            
    def __init__(self, mgr,
                 title=None, control_prefix=None,
                 name="",
                 address=None,
                 street1="",
                 street2="",
                 city="",
                 state="",
                 zipcode="",
                 country="",
                 maptype="hybrid",
                 enlargeForRotate=False,
                 mapRotate=0.,
                 centered=True,
                 longitude=0.,      # Set float type
                 latitude=0.,       # Set float type
                 zoom=22,
                 width=40.,
                 height=40.,
                 xOffset=0.,
                 yOffset=0.,
                 map_show_scales=True,
                 map_scale1_unit="feet",        # Spelled out as in form
                 map_scale1_xFract=.2,
                 map_scale1_yFract=.85,
                 map_scale1_lengFract=.45,
                 map_scale1_deg=0,
                 map_scale2_unit="meter",
                 map_scale2_xFract=.2,
                 map_scale2_yFract=.95,
                 map_scale2_lengFract=.5,
                 map_scale2_deg=0,
                 unit = "meter",
                 **kwargs):
        """ Initialize subclassed SelectControlWindow
             Setup score /undo/redo window
             :mgr: tracking point manager (SurveyPointManager)
             :wait: True - wait till destroyed
             :mw: main window if one
             :zoom:    Google Maps precision default: 22 (High)
        """
        self.mgr = mgr
        self.unit = unit
        if title is None:
            title = "Finding Places"
        if control_prefix is None:
            control_prefix = MappingControl.CONTROL_NAME_PREFIX
        self.name = name
        if address is None:
            address = ""
        self.address = address
        self.street1 = street1
        self.street2 = street2
        self.city = city
        self.state = state
        self.zipcode = zipcode
        self.country = country
        self.maptype = maptype
        self.mapRotate = mapRotate
        self.enlargeForRotate = enlargeForRotate
        self.centered = centered
        self.latitude = latitude
        self.longitude = longitude
        self.width = width
        self.height = height
        self.xOffset = xOffset
        self.yOffset = yOffset
        self.map_show_scales = map_show_scales
        self.map_scale1_unit = map_scale1_unit
        self.map_scale1_xFract = map_scale1_xFract
        self.map_scale1_yFract = map_scale1_yFract
        self.map_scale1_lengFract = map_scale1_lengFract
        self.map_scale1_deg = map_scale1_deg
        self.map_scale2_unit = map_scale2_unit
        self.map_scale2_xFract = map_scale2_xFract
        self.map_scale2_yFract = map_scale2_yFract
        self.map_scale2_lengFract = map_scale2_lengFract
        self.map_scale2_deg = map_scale2_deg
        self.map_scale_change = True            # Force initial update
        self.zoom = zoom
        if 'enter_command' not in kwargs:
            kwargs['enter_command'] = self.enter_command 
        super().__init__(title=title, control_prefix=control_prefix,
                       **kwargs)
        self.control_display()
        self.wait_location = True
        self.load_favorites()

    def get_favorites_prefix(self):
        """ Return properties file favorites prefix text
        Property_line: <prefix><favorite_name>|<field_name>=<value
        NOTE: Using "|" to delimit favorite_name as it may have ".", "," etc
        """
        prefix = self.get_prop_key("") + f"{FavoriteAddress.PROP_PREFIX}|"
        return prefix

    def add_favorite(self, name=None, address=None, fav=None):
        """ Simple add
        :name: favorite name
        :address: composite address,
        :fav: initial Favorite Address
        """
        if fav is None:
            fav = FavoriteAddress(self, name=name, address=address)
        self.favorites[name] = fav
                    
    def load_favorites(self):
        """ Load favorite addresses
        """
        self.favorites = {}
        """ Prime the pump with our favorites... replaced as modified
        """
        self.add_favorite("Grampy & Grammy's", "233 Common St., Watertown, MA")
        self.add_favorite("Alex & Decklan", "24 Chapman St., Watertown, MA")
        self.add_favorite("Antie Jen", "67 Lenon Rd, Arlington, MA")
        self.add_favorite("Avery & Charlie", "85 Clarendon St, Boston, MA")
        self.add_favorite("Whitney Hill Park", fav =  FavoriteAddress(self, "Whitney Hill Park", "Whitney Hill Park",
                        width=400, height=300, xOffset=100, yOffset=100, zoom=18))
        fav_prefix = self.get_favorites_prefix()           
        fav_keys = SlTrace.getPropKeys(startswith=fav_prefix)
        
        for fav_key in fav_keys:
            name_and_field = fav_key[len(fav_prefix):]      # Skip prefix
            name_end_index = name_and_field.find("|")
            if name_end_index < 0:
                raise SelectError(f"(No name delimiter found in properties key:{fav_key}")
            
            name = name_and_field[0:name_end_index]
            field = name_and_field[name_end_index+1:]
            ctl_val = self.get_val_from_ctl(field)  # Use current as default value/type
            val = SlTrace.getProperty(fav_key, ctl_val)
            if name in self.favorites:
                fav = self.favorites[name]
            else:
                fav = FavoriteAddress(self, name=name)    # Create new entry
                self.favorites[name] = fav
            setattr(fav, self.field2att(field), val)        # NOTE REQUIRES self.name SAME as FavoriteAddress.name
            
        
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
        self.set_entry(field="name", label="name", value=self.name, width=20)
        self.set_entry(field="address", label="address", value=self.address, width=40)
        self.set_button(field="favorites", label="Favorites", command=self.get_favorites)
        address_frame1 = Frame(location_frame)
        self.set_fields(address_frame1, "address", title="")
        self.set_entry(field="street1", label="Street1", value=self.street1)
        self.set_entry(field="street2", label="Street2",  value=self.street2)

        address_frame2 = Frame(location_frame)
        self.set_fields(address_frame2, "address", title="    ")
        self.set_entry(field="city", label="City", value = self.city)
        self.set_entry(field="state", label="State", value = self.state)
        self.set_entry(field="country", label="Country", value=self.country)
         
        map_frame = Frame(location_frame)
        map_frame.pack()
        self.set_fields(map_frame, "map", title="Map Type")
        self.set_radio_button(frame=map_frame, field="maptype", label="roadmap", command=self.change_maptype,
                               set_value=self.maptype)
        self.set_radio_button(frame=map_frame, field="maptype", label="satellite", command=self.change_maptype)
        self.set_radio_button(frame=map_frame, field="maptype", label="hybrid", command=self.change_maptype)
        self.set_radio_button(frame=map_frame, field="maptype", label="terrain", command=self.change_maptype)
        map_rotation_frame = Frame(location_frame)
        map_rotation_frame.pack()
        self.set_fields(map_rotation_frame, "map", title="Map Rotation")
        self.set_button(field="rotate", label="Set", command=self.rotate_map_req)
        map_rotate = self.get_mapRotate()
        self.set_entry(field="rotate", label="Rotation",
                        value=map_rotate, width=6,
                        enter_command=self.rotate_enter)
        entry = self.set_entry(field="rotate_cur", label="Current",
                                value=map_rotate, width=5)
        self.set_ctl("map.rotate_cur", map_rotate)          # Force showing current value
        if map_rotate != 0:
            entry.config(bg="green")
        map_rotation_frame2 = Frame(location_frame)
        map_rotation_frame2.pack()
        self.set_fields(map_rotation_frame2, "map", "Incremental Rotation")
        self.set_entry(field="rotate_change", label="Change Rotation",
                        value=45, width=5,
                        enter_command=self.rotate_change_enter)
        self.set_button(field="rotate", label="Rotate", command=self.rotate_change_map_req)
        self.set_button(field="rotate", label="Clockwise", command=self.rotate_change_map_req_neg)
       
        latitude_longitude_frame = Frame(location_frame)
        self.set_vert_sep(location_frame, text="")
        self.set_fields(latitude_longitude_frame, "lat_long", title="Latitude Longitude")
        self.set_button(field="get_address", label="Get Long Lat", command=self.get_address_ll)
        self.set_check_box(field="centered", label="centered", value=self.centered,
                            command=self.change_centered)
        self.set_entry(field="latitude", label="Latitude", value=self.latitude, width=15)
        self.set_entry(field="longitude", label="Longitude", value=self.longitude, width=15)
        self.set_entry(field="zoom", label="zoom", value=self.zoom, width=3)
        size_frame = Frame(location_frame)
        self.set_fields(size_frame, "size", title="Map")
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
        
        self.set_sep()
        scales_frame = Frame(controls_frame)
        self.set_fields(scales_frame, "map_scales", title="Scales")
        self.set_check_box(field="map_show_scales", label="Show scales", value=self.map_show_scales,
                            command=self.change_map_scale)
        scale1_frame = Frame(scales_frame)
        self.set_fields(scale1_frame, "map_scale1", title="Map Scale1")
        
        self.set_radio_button(frame=scale1_frame, field="unit", label="meter",
                               command=self.change_map_scale,
                               set_value=self.map_scale1_unit)
        self.set_radio_button(frame=scale1_frame, field="unit", label="yard", command=self.change_map_scale)
        self.set_radio_button(frame=scale1_frame, field="unit", label="feet", command=self.change_map_scale)
        self.set_radio_button(frame=scale1_frame, field="unit", label="Smoot", command=self.change_map_scale)
        self.set_radio_button(frame=scale1_frame, field="unit", label="None", command=self.change_map_scale)
        self.set_sep()
        self.set_entry(field="xFract", label="xFract", value=self.map_scale1_xFract, width=4)
        self.set_entry(field="yFract", label="yFract", value=self.map_scale1_yFract, width=4)
        self.set_entry(field="lFract", label="lFract", value=self.map_scale1_lengFract, width=4)
        self.set_entry(field="deg", label="deg", value=self.map_scale1_deg, width=4)
        
        self.set_sep()
        scale2_frame = Frame(scales_frame)
        self.set_fields(scale2_frame, "map_scale2", title="Map Scale2")
        self.set_radio_button(frame=scale2_frame, field="unit", label="meter",
                               set_value=self.map_scale2_unit, command=self.change_map_scale)
        self.set_radio_button(frame=scale2_frame, field="unit", label="yard", command=self.change_map_scale)
        self.set_radio_button(frame=scale2_frame, field="unit", label="feet", command=self.change_map_scale)
        self.set_radio_button(frame=scale2_frame, field="unit", label="Smoot", command=self.change_map_scale)
        self.set_radio_button(frame=scale2_frame, field="unit", label="None", command=self.change_map_scale)
        self.set_sep()
        self.set_entry(field="xFract", label="xFract", value=self.map_scale2_xFract, width=4)
        self.set_entry(field="yFract", label="yFract", value=self.map_scale2_yFract, width=4)
        self.set_entry(field="lFract", label="lFract", value=self.map_scale2_lengFract, width=4)
        self.set_entry(field="deg", label="deg", value=self.map_scale2_deg, width=4)
        
        
        self.arrange_windows()
        if not self.display:
            self.hide_window()

    def enter_command(self, event):
        """ Common entry field enter command - called by default whenever
        the ENTER key is pressed when inside any set_entry field
        """
        _ = event
        self.set_vals()
                 
    def change_centered(self, centered=None):
        self.set_vals()
        if centered is not None:
            self.centered = centered

    def change_map_scale(self, val=True):
        _ = val
        self.map_scale_change = True
        self.set_vals()
        self.mgr.redisplay()
        
                
    def change_maptype(self, maptype=None):
        self.set_vals()
        if maptype is None:
            maptype = self.maptype
        else:
            self.maptype = maptype
        if self.mgr is not None:
            self.mgr.change_maptype(maptype)
        
    def change_unit(self, unit=None):
        self.set_vals()
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
        return (self.latitude,self.longitude)    
            
    def get_address_ll(self, lat=None, long=None, favorite=None, update_map=True):
        """ Display map from form's Latitude, Longitude
        :favorite: favorite entry, if one
                if one, use favorite settings
        """
        if favorite is not None:
            self.set_ctl_from_favorite(favorite)
        if lat is not None:
            self.set_ctl_val("lat_long.latitude", lat)
        if long is not None:
            self.set_ctl_val("lat_long.longitude", long)
        self.set_vals()
        self.wait_location = False
        if update_map:
            latLong = (self.latitude,self.longitude)
            if self.centered:
                latLong = geoMove(latLong, latDist=-self.height/2, longDist=-self.width/2)
                
            self.mgr.sc.update_lat_long(latLong=latLong,
                                        xDim=self.width, yDim=self.height,
                                        xOffset=self.xOffset, yOffset=self.yOffset,
                                        unit=self.unit,
                                        maptype=self.maptype,
                                        mapRotate=self.mapRotate,
                                        enlargeForRotate=self.enlargeForRotate,
                                        zoom=self.zoom)
        self.mgr.sc.size_image_to_canvas()
        self.mgr.redisplay()       # Resets points, trackings display
        self.save_favorite()
        return True    

    def save_favorite(self):
        self.set_vals()
        fav =  self.get_favorite_from_ctl()
        fav_name = self.get_favorite_name(fav.name)
        fav.name = fav_name
        self.set_prop_favorite(fav)
        self.favorites[fav_name] = fav


    def set_prop_favorite(self, favorite):
        """ Save favorite in properties
        :favorite: favorite's values
        """
        fav_prefix = self.get_favorites_prefix()
        fp_plus_name = f"{fav_prefix}{favorite.name}"
        SlTrace.lg("Saving Favorite")
        for att_to_ctl in MappingControl.att_to_ctls:
            att = att_to_ctl[0]
            ctl_field = att_to_ctl[1]
            val = getattr(favorite, att)
            if val is not None:
                prop_key = f"{fp_plus_name}|{ctl_field}"
                SlTrace.setProperty(prop_key, val)
                SlTrace.lg(f"{prop_key} = {val}")
                    
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
                show_str = favorite.address
            favorite_by_show[show_str] = favorite
            favorite_items.append(show_str)
        x0 = 300
        y0 = 400
        width = 200
        height = 400
        SlTrace.lg(f"x0={x0}, y0={y0}, width={width}, height={height}", "select_list")                    
        app = SelectList(title="Select Address",
                         items=favorite_items,
                         position=(x0, y0), size=(width, height))
        selected_field = app.get_selected()
        SlTrace.lg(f"selected_field:{selected_field}")
        if selected_field in favorite_by_show:
            favorite = favorite_by_show[selected_field]
            self.set_ctl_from_favorite(favorite)
            if favorite.latitude is not None and favorite.longitude is not None:
                self.get_address_ll(favorite=favorite)
            else:
                self.get_address(favorite=favorite)    

    def get_favorite_name(self, name=None):
        """ Get unique favorite name
        using given as a starting point
        Force name to be unique.
           If None start with PROP_PREFIX
        Take non-numeric prefix by removing any numeric suffix
        Try ascending numeric suffixes until result is unique
        """
        if name is None or name == "":
            nn = 0
            if name is None or name == "":
                name = FavoriteAddress.PROP_PREFIX
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
            
    def get_address(self, address=None, favorite=None, update_map=True):
        """ Get address and put map up
        :address: address to get, default: use form's
        :favorite: favorite entry if one
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
            self.latitude, self.longitude = None
            self.wait_location = False
            return False
        
        latitude, longitude = lat_long
        self.set_ctl_val("lat_long.latitude", latitude)
        self.set_ctl_val("lat_long.longitude", longitude)
        self.set_vals()
        self.latitude = latitude
        self.longitude = longitude
        self.wait_location = False
        ct_str = "centered" if self.centered else ""
        SlTrace.lg(f"get_loc: lat:{self.latitude}, Long: {self.longitude} {ct_str}")
        res = self.get_address_ll(favorite=favorite, update_map=update_map)
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

    def get_mapRotate(self):
        """ Get current map rotation 0<= deg < 360
        """
        return self.mgr.get_mapRotate()

    def get_favorite_from_ctl(self):
        """ Generate AddressFavorite from controls
        :returns: FavoriteAddress with ctl values
        """
        fv = FavoriteAddress(self)
        for att_to_ctl in MappingControl.att_to_ctls:
            att = att_to_ctl[0]
            ctl_field = att_to_ctl[1]
            val = self.get_val_from_ctl(ctl_field)
            if val is not None:
                setattr(fv, att, val)
        return fv

    def rotate_enter(self, _):
        self.rotate_map_req()

    def rotate_map_req(self):
        """ Rotate map, req from form
        """
        self.set_vals()
        to = self.get_val_from_ctl("map.rotate")
        self.rotate_map(deg=to)

    def rotate_change_enter(self, _):
        self.rotate_change_map_req()

    def rotate_change_map_req(self):
        """ Rotate map, req from form
        """
        self.set_vals()
        towards = self.get_val_from_ctl("map.rotate_change")
        self.rotate_map(deg=towards, incr=True)

    def rotate_change_map_req_neg(self):
        """ Rotate map, req from form
        """
        self.set_vals()
        towards = self.get_val_from_ctl("map.rotate_change")
        self.rotate_map(deg=-towards, incr=True)


                
    def rotate_map(self, deg=None, incr=False):
        """ Rotate map towards this heading
        :towards: degrees from North
        """
        if deg is None:
            self.set_vals()
            deg = self.get_val_from_ctl("map.rotate")
        self.mgr.rotate_map(deg=deg, incr=incr)
        map_rotate = self.get_mapRotate()
        self.set_ctl("map.rotate_cur", map_rotate)
        entry = self.get_ctl("map.rotate_cur")
        if map_rotate != 0:
            entry.config(bg="light green")
        else:
            entry.config(bg="light gray")



    def rotate_map_to(self, towards=None):
        """ Rotate map towards this heading
        :towards: degrees from North
        """
        if towards is None:
            self.set_vals()
            towards = self.get_val_from_ctl("map.rotate")
        self.rotate_map_to(towards, incr=False)
         
        
    def set_ctl_from_favorite(self, favorite):
        """ Update ctls from favorite
        :favorite: favorite's values
        """
        for att_to_ctl in MappingControl.att_to_ctls:
            att = att_to_ctl[0]
            ctl_field = att_to_ctl[1]
            val = getattr(favorite, att)
            if val is not None:
                SlTrace.lg(f"set_ctl_from_favorite(ctl_field({ctl_field}), val={val})", "set_ctl")
                self.set_ctl_val(ctl_field, val)
        
    def set_vals(self):
        """ Update internal values from all form ctls
        """
        self.name = self.update_from_ctl("address.name")
        self.address = self.update_from_ctl("address.address")
        self.street1 = self.update_from_ctl("address.street1")
        self.street2 = self.update_from_ctl("address.street2")
        self.city = self.update_from_ctl("address.city")
        self.state = self.update_from_ctl("address.state")
        self.country = self.update_from_ctl("address.country")
        self.width = self.update_from_ctl("size.width")
        self.height = self.update_from_ctl("size.height")
        self.xOffset = self.update_from_ctl("size.x_offset")
        self.yOffset = self.update_from_ctl("size.y_offset")
        self.unit = self.update_from_ctl("distance_units.unit")
        self.latitude = self.update_from_ctl("lat_long.latitude")
        self.longitude = self.update_from_ctl("lat_long.longitude")
        self.centered = self.update_from_ctl("lat_long.centered")
        self.mapRotate = self.update_from_ctl("map.rotate")
        self.map_show_scales = self.update_from_ctl("map_scales.map_show_scales")
        self.map_scale1_unit = self.update_from_ctl("map_scale1.unit")
        self.map_scale1_xFract = self.update_from_ctl("map_scale1.xFract")
        self.map_scale1_yFract = self.update_from_ctl("map_scale1.yFract")
        self.map_scale1_lengFract = self.update_from_ctl("map_scale1.lFract")
        self.map_scale1_deg = self.update_from_ctl("map_scale1.deg")
        self.map_scale2_unit = self.update_from_ctl("map_scale2.unit")
        self.map_scale2_xFract = self.update_from_ctl("map_scale2.xFract")
        self.map_scale2_yFract = self.update_from_ctl("map_scale2.yFract")
        self.map_scale2_lengFract = self.update_from_ctl("map_scale2.lFract")
        self.map_scale2_deg = self.update_from_ctl("map_scale2.deg")
        self.zoom = self.update_from_ctl("lat_long.zoom")
    
    def destroy(self):
        """ Destroy window resources
        """
        if self.mw is not None:
            self.mw.destroy()
        self.mw = None
        
    
if __name__ == '__main__':

    def set_cmd(ctl):
        SlTrace.lg("Set Button")
    enlargeForRotate = True            
    root = Tk()
    root.withdraw()       # Hide main window

    SlTrace.setProps()
    loop = True
    ###loop = False

    mc = MappingControl(None, mw=None, title="MappingControl Testing",
                        address="Testing Address",
                        enlargeForRotate=enlargeForRotate,
                         win_x=200, win_y=300, win_width=400, win_height=150)
    ###tc.control_display()

    root.mainloop()