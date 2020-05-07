#google_address.py    03May2020  crs
""" Obtain latitude, Longitude pairs given address
Uses Google
"""
import re
import urllib
import urllib.request, urllib.parse, urllib.error, io
import json
import time
from select_trace import SlTrace

class GeoAddress:
    PROP_KEY_START = "adr_lat_long."
    
    def __init__(self, 
               address=None,
               street1=None,
               street2=None,
               city=None,
               state=None,
               zipcode=None,
               country=None,
               key=None
               ):
        """ Translate between address and latitude/longitude pair
        :address: address string, to which rest of parts, if present are appended
        :street1: first part of street address, if any
        :street2: second part of street address, if any
        :city: city, if any
        :state: state if any
        :zipcode: zipcode
        :country: country  default: "U.S.A."
        """
        self.address = address
        self.street1 = street1
        self.street2 = street2
        self.city = city
        self.state = state
        self.zipcode = zipcode
        self.country = country
        self.key = key
        self.load_address_ll()

    def load_address_ll(self):
        """ Load address, lat, long hash from properties file
        """
        self.address_ll_hash = {}   # by address: (address, lat, long)
        prop_keys = SlTrace.getPropKeys(startswith=GeoAddress.PROP_KEY_START)
        for prop_key in prop_keys:
            prop_val = SlTrace.getProperty(prop_key)
            address_string, lat_str, long_str = prop_val.split("|")
            SlTrace.lg(f"prop_key: {prop_key} prop_val: {address_string} lat:{lat_str} long: {long_str}")
            url_address_str = prop_key[len(GeoAddress.PROP_KEY_START):]
            self.address_ll_hash[url_address_str] = (address_string, float(lat_str), float(long_str))
               
    def get_lat_long(self,
               address=None,
               street1=None,
               street2=None,
               city=None,
               state=None,
               zipcode=None,
               country=None,
               key=None):
        """ Get address latitude, longitude equivalent
        :args: default to init
        :returns: (latitude, longitude) pair, None if can't find
        """
        if address is None:
            address = self.address
        if street1 is None:
            street1 = self.street1
        if street2 is None:
            street2 = self.street2
        if city is None:
            city = self.city
        if state is None:
            state = self.state
        if zipcode is None:
            zipcode = self.zipcode
        if country is None:
            country = self.country
        if key is None:
            key = self.key
        address_string = ""
        if address is not None and address != "":
            address_string = address
        if street1 is not None and street1 != "":
            if address_string != "":
                address_string += ", "
            address_string += street1
        if street2 is not None and street2 != "":
            if address_string != "":
                address_string += ", "
            address_string += street2
        if city is not None and city != "":
            if address_string != "":
                address_string += ", "
            address_string += city
        if city is None or city == "":
            ctm = re.match(r'.*(watertown|belmont|boston|arlington|waltham|concord|lexington)',
                            address_string, re.IGNORECASE)
            if ctm is None:
                address_string += ", Watertown"

        
        if state is not None and state != "":
            if address_string != "":
                address_string += ", "
            address_string += state
        """ Personal abbreviations """
        if state is None or state == "":
            stm = re.match(r'.*(ma|massachusetts|nh|main)', address_string, re.IGNORECASE)
            if stm is None:
                address_string += ", MA"
        if country is None or country == "":
            coutm = re.match(r'.*(\bUS\b|France|England|Spain|Mexico)', address_string, re.IGNORECASE)
            if coutm is None:
                address_string += ", US"
        


        url_address_str = urllib.parse.quote(address_string)
        if url_address_str in self.address_ll_hash:
            _, lat, long = self.address_ll_hash[url_address_str]
            return lat, long
        
        SlTrace.lg(f"Not in hash: {url_address_str} address: {address}"
                f" address_string: {address_string}")            
        ''' Geocode is not free
        url = 'https://maps.googleapis.com/maps/api/geocode/jason?'    # GeoCode - Not Free
        param_dict = {
            'address' : address_string,
                'key' : APIKey(),
                }
        url = 'https://geocode.xyz/'
        urlparams = urllib.parse.urlencode(param_dict)
        url +=  urlparams
        '''
        """ Try geocode.xyz
        """
        url = 'https://geocode.xyz/'
        url_address_str = urllib.parse.quote(address_string)
        url += url_address_str
        url += "?json=1"
        SlTrace.lg("url=%s" % url, "url_trace")
        max_try = 10
        ntry = 0
        while ntry < max_try:
            ntry += 1
            try:
                f=urllib.request.urlopen(url)
                ret = f.read()
                djson = json.loads(ret)
                if "error" in djson:
                    error = djson["error"]
                    description = error["description"]
                    SlTrace.lg(f"description:{description}")
                    return None
                break
            except:
                SlTrace.lg(f"fail on try: {ntry} - wait a second")
                time.sleep(1)
        SlTrace.lg(f"try{ntry}: ret:{ret}", "url_trace")
        SlTrace.lg(f"djson:{djson}", "url_trace")
        lat = djson['latt']
        long = djson['longt']
        self.address_ll_hash[address_string] = (url_address_str, lat, long)
        SlTrace.setProperty(f"{GeoAddress.PROP_KEY_START}{url_address_str}",
                             f"{address_string}|{lat}|{long}")
        SlTrace.lg(f"latitude:{lat} longitude: {long}", "ll_trace")
        return lat, long
    
if __name__ == "__main__":
    SlTrace.setProps()
    SlTrace.clearFlags()
    ###SlTrace.setFlags("url_trace")
    addresses = ["233 Common St., Watertown, MA ,US",
                 "24 Chapman St., Watertown, MA, US",
                 "67 Lennon Rd., Arlington, MA",
                 "75 Clarendon St., Boston, MA, US",
                 "226 Common St.",
                 ]
    ga = GeoAddress()
    for address in addresses:
        lat_long = ga.get_lat_long(address)
        if lat_long is None:
            SlTrace.lg(f"No luck with address: {address}")
            continue
        lat, long = lat_long
        SlTrace.lg(f"address: {address} lat: {lat} long: {long}")
    
    