#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
import pcraster as pcr
import VirtualOS as vos
from hydro_model_builder.Model import Model

from Meteo import Meteo
from Groundwater import Groundwater
from LandSurface import LandSurface

import logging
logger = logging.getLogger(__name__)

class WaterBalanceModel(Model):    
    def __init__(self, configuration, modelTime, initialState = None):
        super(WaterBalanceModel, self).__init__(
            configuration,
            modelTime,
            initialState)
        
        self.meteo_module = Meteo(self)
        self.groundwater_module = Groundwater(self)
        self.lc_module = LandSurface(self)
        
    def initial(self):
        self.meteo_module.initial()
        self.groundwater_module.initial()
        self.lc_module.initial()
        self.get_model_dimensions()
        
    def get_model_dimensions(self):
        # TODO: remove dependency on PCRaster
        latitudes = np.unique(pcr.pcr2numpy(pcr.ycoordinate(self.cloneMap), vos.MV))[::-1]
        longitudes = np.unique(pcr.pcr2numpy(pcr.xcoordinate(self.cloneMap), vos.MV))
        self.dimensions = {
            'time'     : None,
            'depth'    : np.arange(3), # TODO - put nComp in config section [SOIL]
            'lat'      : latitudes,
            'lon'      : longitudes,
        }
        
    def dynamic(self):
        self.meteo_module.dynamic()
        self.groundwater_module.dynamic()
        self.lc_module.dynamic()        
