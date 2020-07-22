#survey_map_ruler.py
"""
Survey ruler - based on SurveyMapScale
"""
import re
from math import sqrt, asin, degrees
from PIL import ImageFont

from select_trace import SlTrace
from select_error import SelectError
from survey_scale import SurveyMapScale

class SurveyRuler(SurveyMapScale):
    
    def __init__(self, mgr,
                **kwargs
                 ):
        """
        Add ruler
        """
        if 'mapRelative' not in kwargs:
            kwargs['mapRelative'] = False
        if 'font_size' not in kwargs:
            kwargs['font_size'] = 10
        if 'tic_leng' not in kwargs:
            kwargs['tic_leng'] = 5
        if 'color' in kwargs:
            color = kwargs['color']
        else:
            color = 'black'
            kwargs['color'] = color
        if 'tic_color' in kwargs:
            tic_color = kwargs['tic_color']
        else:
            tic_color = "black"
            kwargs['tic_color'] = tic_color
        if 'text_color' in kwargs:
            text_color = kwargs['text_color']
        else:
            text_color = tic_color
            kwargs['text_color'] = text_color
        super().__init__(mgr, **kwargs)
