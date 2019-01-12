#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
import pcraster as pcr
import VirtualOS as vos
import netCDF4 as nc

class IrrigationParameters(object):

    def __init__(self, IrrigationParameters_variable, config_section_name):
        """Initialise IrrigationParameters object"""
        self.var = IrrigationParameters_variable
        self.lc_configuration = getattr(self.var._configuration, config_section_name)

    def initial(self):
        self.var.irrigation_efficiency = np.ones((1, 1, self.var.nCell), dtype=np.float64)
        self.read()
        
    def read(self):
        pass
        
    def dynamic(self):
        pass
