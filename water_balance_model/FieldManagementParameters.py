#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
import pcraster as pcr
import hydro_model_builder.VirtualOS as vos
import netCDF4 as nc

class FieldManagementParameters(object):

    def __init__(self, FieldManagementParameters_variable, config_section_name):
        """Initialise FieldManagementParameters object"""
        self.var = FieldManagementParameters_variable
        self.lc_configuration = getattr(self.var._configuration, config_section_name)

    def initial(self):
        self.var.Bunds = np.zeros((self.var.nFarm, self.var.nLC, self.var.nCell), dtype=np.bool)
        self.var.zBund = np.zeros((self.var.nFarm, self.var.nLC, self.var.nCell))
        
    def read(self):
        pass
        
    def dynamic(self):
        pass

class FieldManagementParametersManagedLand(FieldManagementParameters):
    
    def initial(self):
        bunds = np.bool(np.int(self.lc_configuration['bunds']))
        zbund = np.float(self.lc_configuration['zBund'])
        self.var.Bunds = np.ones((1, 1, self.var.nCell)) * bunds
        self.var.zBund = np.ones((1, 1, self.var.nCell)) * zbund
