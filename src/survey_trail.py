# survey_trail.py    14May2020    crs
""" Information / support for trail loading, presentation, modification, and saving
"""
from select_trace import SelectError

from gpx_file import GPXFile, GPXPoint, GPXTrackSegment
from survey_trail_segment import SurveyTrailSegment
from survey_point import SurveyPoint

class SurveyTrail:
    def __init__(self, mgr, basis=None, file_name = None,
                 label_pattern="t%d.%d",
                 show_points=False,
                 color="orange", width=2., line_type="line",
                 display_monitor=False):
        """ Region object
        :mgr: point manager, None if none needed
        :basis: basis e.g. GPXFile, SampleFile
            default: GPXFile
        :filename: file to load, if present
        :label_pattern: pattern for point's labeling
                default: "t%d.%d" % (seg_no, point_no)
        :show_points: mark points default: False - don't show points
        :color: color of trail default: orange
        :width: width, in meters, of trail default: 2
        :line_type: trail line type default: line
        :display_monitor: display stats for each pair of points
                        default: False
        """
        self.mgr = mgr
        self.segments = []
        self.file_name = file_name
        self.is_show_points = show_points
        if basis is None:
            basis = GPXFile()
        self.basis = basis
        self.label_pattern = label_pattern
        self.color = color
        self.width = width      # in meters
        self.line_width = int(mgr.meterToPixel(width))

        self.line_type = line_type
        self.display_monitor = display_monitor
        self.load_file(file_name=file_name)

    def delete(self):
        """ Remove trail
        """
        for segment in self.get_segments():
            segment.delete()
        self.segments = []

    def show_point(self, point):
        """ Show point
        """
        self.mgr.show_point(point)

    def show_points(self):
        """ Show points
        """
        for segment in self.get_segments():
            segment.show_points()

    def hide_point(self, point):
        """ Hide point
        """
        self.mgr.hide_point(point)

    def hide_points(self):
        """ Hide points
        """
        for segment in self.get_segments():
            segment.hide_points()

    def delete_point(self, point):
        """ Remove point from system
        """
        self.mgr.remove_point(point)
                
    def load_file(self, file_name=None):
        """ Load file
        :file_name: file to load, if present
        """
        mgr = self.mgr
        unit = mgr.unit
        self.segments = []
        basis = self.basis       
        basis.load_file(file_name)
        self.file_name = basis.file_name
        for seg_no, file_segment in enumerate(basis.get_segments(), start=1):
            segment = SurveyTrailSegment(self)
            file_points = file_segment.get_points()
            for point_no, file_point in enumerate(file_points, start=1):
                label = self.label_pattern % (seg_no, point_no)
                if point_no == 1:
                    prev_point = file_point      # GPXPoint
                prev_latLong = (prev_point.lat,prev_point.long)
                latLong = (file_point.lat, file_point.long)
                delta = mgr.sc.gmi.geoDist(prev_latLong, latLong)
                x_d, y_d = mgr.sc.gmi.getPos(latLong=latLong)
                show_item = str(f"{label}:   x:{x_d:.1f}{unit} y:{y_d:.1f}{unit}"
                                 f"   delta: {delta:.1f}{unit}"
                                 f"   lat:{file_point.lat} Long:{file_point.long}")
                track_point = mgr.get_point_labeled(label) # Don't duplicate
                if track_point is None:
                    track_point = SurveyPoint(mgr, label=label,
                                    show_item=show_item,
                                    lat=file_point.lat, long=file_point.long,
                                    display_size=8,
                                    displayed=self.is_show_points,
                                    color="black")
                    mgr.add_point(track_point, track=False)
                segment.add_points(track_point)
            self.add_segments(segment)

    def add_new_segment(self):
        """ Add new trail segment to end
        :returns: newly created segment
        """
        segment = SurveyTrailSegment(self)
        self.add_segments(segment)
        return segment
                    
    def add_segments(self, *segments):
        """ Add zero or more segments to trail
        :segments: 0 or more args, each is an point or list of (SurveySegment)
        """
        for segs in segments:
            if not isinstance(segs, list):
                segs = [segs]     # Make list of one
            for segment in segs:
                segment.segment_no = len(self.segments) + 1     # self identifier
                self.segments.append(segment)

    def get_segment(self, segment_no):
        """ Get segment, if one
        :segment_no: segment number starting with 1
        :returns: with segment if one, else None
        """
        for segment in self.segments:
            if segment.segment_no == segment_no:
                return segment
            
        return None
    
    
    def get_segments(self):
        return self.segments
                    
    def delete_points(self, *points):
        """ Delete points from trail but not from mgr
        No tracks are deleted
        :points: 0 or more args, each is an point or list of (SurveyPoint)
        :returns: list of points deleted
        """
        del_points = []
        for pts in points:
            if not isinstance(pts, list):
                pts = [pts]     # Make a list of one
            for pt in pts:
                for segment in self.get_segments():
                    del_pts = segment.delete_points(pt)
                    del_points.extend(del_pts)
        return del_points
                    
    def get_points(self):
        """ Get points in trail
        :returns: list of points
        """
        points = []
        for segment in self.get_segments():
            points.extend(segment.get_points())
        return points

    def get_show_items(self, seg_sep=None):
        """ Get list of show_items for SelectList
        :seg_sep: If present separate segments with an item of this text
                    e.g. "===="  default: no separation
        """
        items = []
        for segment in self.get_segments():
            for point in segment.get_points():
                items.append(point.show_item)
            if seg_sep is not None:
                items.append(seg_sep)
        return items

    def get_points_by_show(self):
        """ Create dictionary of points by show_item
        """
        points_by_show = {}
        for point in self.get_points():
            points_by_show[point.show_item] = point
        return points_by_show
        
    def save_file(self, filename):
        basis = self.basis
        if isinstance(basis, GPXFile):
            gpx_segments = []
            for segment in self.get_segments():
                gpx_segment = GPXTrackSegment()
                for point in segment.get_points():
                    gpx_point = GPXPoint(lat=point.lat, long=point.long)
                    gpx_segment.add_points(gpx_point)
                gpx_segments.append(gpx_segment)
            basis.set_segments(gpx_segments)
            ret =  self.basis.save_file(filename)
        else:
            raise SelectError(f"save_file({filename} - doesn't support basis:{basis}")
        
        return ret 
    
        