#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
import pcraster as pcr
import VirtualOS as vos
import netCDF4 as nc

class FieldManagementParameters(object):

    def __init__(self, var, configuration):
        """Initialise FieldManagementParameters object"""
        self.var = var
        self.configuration = configuration

    def initial(self):
        self.var.Bunds = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell), dtype=np.bool)
        self.var.zBund = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))
        
    def read(self):
        pass
        
    def dynamic(self):
        pass

class FieldManagementParametersManagedLand(FieldManagementParameters):
    
    def initial(self):
        bunds = np.bool(np.int(self.configuration['bunds']))
        zbund = np.float(self.configuration['zBund'])
        self.var.Bunds = np.ones((self.var.nFarm, self.var.nCrop, self.var.nCell)) * bunds
        self.var.zBund = np.ones((self.var.nFarm, self.var.nCrop, self.var.nCell)) * zbund
