#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
import pcraster as pcr
import VirtualOS as vos
from Model import Model

from Meteo import Meteo
from Groundwater import Groundwater
from CanalSupply import CanalSupply
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
        self.canal_module = CanalSupply(self)
        self.lc_module = LandSurface(self)
        
    def initial(self):
        self.meteo_module.initial()
        self.groundwater_module.initial()
        self.canal_module.initial()
        self.lc_module.initial()
        
    def dynamic(self):
        self.meteo_module.dynamic()
        self.groundwater_module.dynamic()
        self.canal_module.dynamic()
        self.lc_module.dynamic()        
