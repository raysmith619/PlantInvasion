# survey_region.py    14May2020    crs
""" Region object similar, but simpler than SelectRegion (crs_dots)
A region is composed of a connected set of edges surrounding a contiguous area
"""
from select_trace import SelectError

from survey_edge import SurveyEdge

class SurveyRegion:
    def __init__(self, mgr):
        """ Region object
        :mgr: point Manager
        """
        self.mgr = mgr
        self.edges = []     # List of edges
        self.points = []    # List of points
        self.completed = False
        
    def add_points(self, *points):
        """ Add zero or more points to end of region
        in preparation to create region
        To complete region these points must be collected in to edges
        which are added to the region.  If edges will consist of two points eacn,
        the creation of edges can be created via the complete_region function
        which with the from_points=True, creates edges from successive points
        p1-p2, p2-p3, ... pN-p1 and adds these edges to the region.
        
        :points: 0 or more args, each is an point or list of points
        """
        for pts in points:
            if not isinstance(pts, list):
                pts = [pts]     # Make list of one
            for point in pts:
                self.points.append(point)
        
    def add_edges(self, *edges):
        """ Add edge(s) to Region
        :edges: 0 or more args, each an edge or list of edges
        """
        for eds in edges:
            if not isinstance(eds, list):
                eds = [eds]     # Make list of one
            for edge in eds:
                self.edges.append(edge)

    def complete_region(self, from_points=True):
        """ Complete region (from points), if possible
        :from_points: Use points to create edges p1,p2, p2,p3,...
                    else use edges
        :returns: True iff successful
        """
        if len(self.points) < 3:
            return False
        
        if from_points:            
            prev_point = None
            for point in self.points:
                if prev_point is not None:
                    edge = SurveyEdge(self.mgr, prev_point, point)
                    self.add_edges(edge)
                    prev_point = point
        self.add_edges(SurveyEdge(self.mgr, self.points[-1], self.points[0]))            
        self.completed = True
        return True

    def get_bearing(self):
        """ get region rotation
            assume direction p2 -> p1
        """
        pts = self.get_points()
        
        p1, p2 = pts[0], pts[1]
        from GeoDraw import get_bearing
        bearing = get_bearing(p2, p1)
        return bearing
        
    def get_points(self):
        """ Get points in region's perimeter possibility not complete
        :returns: list of points
        """
        return self.points
    
    def get_edges(self):
        """ Get list of edges
        :returns: list of edges
        """
        return self.edges
        
    def is_complete(self):
        """ Check if region is complete
        :returns: True if completed region, else False
        """
        return self.completed

    def ullr_ll(self):
        """ Get upper left, lower right corners latitutude, Longitude
        :returns: ul,lr
        """
        min_lat, max_lat, min_long, max_long = self.min_max_ll()
        return (max_lat, min_long), (min_lat, max_long)
            
    def min_max_ll(self):
        """ Find min,max of latitude, longitude
        :returns: (min_lat, max_lat, min_long, max_long)
        """
        min_lat = None
        max_lat = None
        min_long = None
        max_long = None
        for pt in self.get_points():
            if min_lat is None or pt.lat < min_lat:
                min_lat = pt.lat
            if max_lat is None or pt.lat > max_lat:
                max_lat = pt.lat
            if min_long is None or pt.long < min_long:
                min_long = pt.long
            if max_long is None or pt.long > max_long:
                max_long = pt.long
        return min_lat, max_lat, min_long, max_long
    
    def min_max_xy(self):
        """ Find min,max of x,y in image
        :returns: (min_x, min_y, max_x, max_y)    # ulx,uly, lrx, lry
        """
        gD = self.mgr.get_geoDraw()
        min_x = None
        max_x = None
        min_y = None
        max_y = None
        for pt in self.get_points():
            x,y = gD.getXY(latLong=(pt.lat, pt.long))
            if min_x is None or x < min_x:
                min_x = x
            if max_x is None or x > max_x:
                max_x = x
            if min_y is None or y < min_y:
                min_y = y
            if max_y is None or y > max_y:
                max_y = y
        return min_x, min_y, max_x, max_y

    def is_inside(self, point=None, latLong=None):
        """ Test if point is within region
        Initially must an approximation: within min/max latitude longitude
        :point, latitude, longitude pair
            OR
        :latLong: latitude, latitude pair
        :returns: True if inside
        """
        if point is not None and latLong is not None:
            raise SelectError("Can't have point AND latLong")
        min_lat, max_lat, min_long, max_long = self.min_max_ll()
        if latLong is not None:
            lat, long = latLong
        else:
            lat, long = point.lat, point.long
        if (lat >= min_lat and lat <= max_lat
            and long >= min_long and long <= max_long):
            return True
        
        return False
    
    def get_inside_points(self, points):
        """ return list of points within region
        :points: points (each point must have point.lat, point.long    
        Initially must an approximation: within min/max latitude longitude
        :latLong, latitude, longitude pair
        :returns: list of points within region
        """
        inside_points = []
        for point in points:
            if self.is_inside(point):
                inside_points.append(point)
                
        return inside_points