#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
import pcraster as pcr
from hydro_model_builder.Model import Model
from hydro_model_builder import VirtualOS as vos

from LandCover import *

# TODO: should this really be called 'LandSurface' ?
class LandSurface(object):
    def __init__(self, LandSurface_variable):
        # self.var = LandCover_variable
        # self.var.dynamicLandCover
        # self.var.FixedLandCoverYear
        self.forest_module = Forest(LandSurface_variable, 'forest')
        self.grassland_module = Grassland(LandSurface_variable, 'grassland')
        self.irrPaddy_module = IrrPaddy(LandSurface_variable, 'irrPaddy')
        self.irrNonPaddy_module = IrrNonPaddy(LandSurface_variable, 'irrNonPaddy')
        self.sealed_module = Sealed(LandSurface_variable, 'sealed')
        self.water_module = Water(LandSurface_variable, 'water')

    def initial(self):
        self.forest_module.initial()
        self.grassland_module.initial()
        self.irrPaddy_module.initial()
        self.irrNonPaddy_module.initial()
        self.sealed_module.initial()
        self.water_module.initial()    
        
    def correct_cover_frac(self):
        """Function to correct cover fraction, such that in 
        each grid square the various land cover fractions sum 
        to one
        """
        pass
    
    def dynamic(self):
        self.correct_cover_frac()
        self.forest_module.dynamic()
        self.grassland_module.dynamic()
        self.irrPaddy_module.dynamic()
        self.irrNonPaddy_module.dynamic()
        self.sealed_module.dynamic()
        self.water_module.dynamic()    
        # need some function here to bring everything together
