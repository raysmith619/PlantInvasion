# survey_edge.py    14May2020    crs
""" edge object similar, but simpler than SelectEdge (crs_dots)
An edge is composed of a connected set of two or more points
"""

class SurveyEdge:
    def __init__(self, mgr, *points):
        """ Region object
        :mgr: point Manager
        :points: list of zero or more points making up the edge
        """
        self.mgr = mgr
        self.points = points    # List of points
        
    def add_points(self, *points):
        """ Add zero or more points to end of edge
        :points: 0 or more args, each is an point or list of points
        """
        for pts in points:
            if not isinstance(pts, list):
                pts = [pts]     # Make list of one
            for point in pts:
                self.points.append(point)
        
    def add_edges(self, *edges):
        """ Add zero or more edges to end of edge
        Making an edge a composite self, *edges
        :edges: 0 or more args, each is an edge or list of edges
        """
        for eds in edges:
            if not isinstance(eds, list):
                eds = [eds]     # Make list of one
            for edge in eds:
                points = edge.get_points()
                self.add_points(points)
                    
                    
    def get_points(self):
        """ Get points in region's perimeter possibility not complete
        :returns: list of points
        """
        return self.points
    
        