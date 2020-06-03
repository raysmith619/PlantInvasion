# survey_track.py    18May2020    crs
""" trail segment object similar, but simpler than SelectEdge (crs_dots)
An edge is composed of a connected set of zero or more points
"""
from select_trace import SlTrace

class SurveyTrailSegment:
    def __init__(self, trail):
        """ track object
        :trail: trail, of which we are a member
        :points: list of zero or more points making up the edge
        """
        self.trail = trail
        self.points = []        # List of points
        self.segment_no = 0     # Set by adding function to provide identification
        
    def add_points(self, *points):
        """ Add zero or more points to end of edge
        :points: 0 or more args, each is an point or list of points
        """
        for pts in points:
            if not isinstance(pts, list):
                pts = [pts]     # Make list of one
            for point in pts:
                self.points.append(point)
                    
    def get_points(self):
        """ Get points in region's perimeter possibility not complete
        :returns: list of points
        """
        return self.points

    def get_end_point(self):
        """ Get end point
        :returns: end point, None if none
        """
        return None if len(self.points) == 0 else self.points[-1]

    def hide(self):
        self.hide_points()
        self.trail.hide_point_tracking(self.get_points())
            
    def hide_points(self):
        """ Show points
        """
        for point in self.get_points():
            self.trail.hide_point(point)

    def show_points(self):
        """ Show points
        """
        for point in self.get_points():
            self.trail.show_point(point)

    def delete(self):
        """ Delete segment and resources
        """
        for point in self.points:
            self.delete_points(point)
            self.trail.delete_point(point)
        self.points = []
        
    def delete_points(self, *points):
        """ Delete points from segment, and from mgr via trail
        :points: 0 or more args, each is an point or list of (SurveyPoint)
        :returns: list of points deleted
        """
        del_points = []
        for pts in points:
            if not isinstance(pts, list):
                pts = [pts]     # Make a list of one

            for pt in pts:
                for ip, segpt in enumerate(self.get_points()):
                    if segpt.point_id == pt.point_id:
                        del_points.append(segpt)
                        SlTrace.lg(f"TrailSegment.delete point({self.points[ip]}")
                        del(self.points[ip])
                        self.trail.delete_point(segpt)
                        del_points.append(segpt)
                        break
        return del_points
        