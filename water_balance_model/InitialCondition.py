#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# AquaCrop
#
import os
import numpy as np
import pcraster as pcr
import VirtualOS as vos
import netCDF4 as nc
import datetime as datetime
import calendar as calendar
import warnings
import scipy.interpolate as interpolate

class InitialCondition(object):
    def __init__(self, InitialCondition_variable):
        self.var = InitialCondition_variable

    def initial_water_content(self):
        landmask = np.broadcast_to(
            self.var.landmask,
            (self.var.nLayer, self.var.nLat, self.var.nLon))
        self.var.initialConditionFileNC = str(
            self.var._configuration.INITIAL_CONDITIONS['initialConditionInputFile'])
        self.var.initialConditionVarName = str(
            self.var._configuration.INITIAL_CONDITIONS['initialConditionVariableName'])
        th = vos.netcdf2PCRobjCloneWithoutTime(
            self.var.initialConditionFileNC,
            self.var.initialConditionVarName,
            cloneMapFileName=self.var.cloneMap)
        
        th = th[landmask].reshape(self.var.nLayer, self.var.nCell)
        self.var.th = np.broadcast_to(
            th[None,None,...],
            (self.var.nFarm, self.var.nCrop, self.var.nLayer, self.var.nCell)).copy()
        self.var.wc = (
            self.var.th
            * self.var.root_depth)

    def initial_interception_storage(self):
        # TODO:
        self.var.interception_storage = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))

    def initial_surface_storage(self):
        self.var.SurfaceStorage = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))

    def initial_snow_cover(self):
        # see CWATM, snow_cover.py, lines 143-150
        num_snow_layers = 7
        self.var.snow_cover_layer = np.zeros((self.var.nFarm, self.var.nCrop, int(num_snow_layers), self.var.nCell))
        self.var.snow_cover = np.sum(self.var.snow_cover_layer, axis=2) / float(num_snow_layers)

    def initial_frost_index(self):
        self.var.frost_index = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))
        
    def initial(self):
        pass
        
    def get_state(self):
        # basic idea here is to provide a list of all variables
        # which define the model state (i.e. variables which evolve
        # from one time step to the next) and add these to a
        # dictionary which can subsequently be written to a netCDF 
        result = {}
        state_vars = []
        for var in state_vars:
            result[var] = vars(self.var)[var]
            
    def dynamic(self):
        pass

class InitialConditionNaturalVegetation(InitialCondition):
        
    def initial(self):
        self.initial_water_content()
        self.initial_interception_storage()
        self.initial_surface_storage()
        self.initial_snow_cover()
        self.initial_frost_index()

class InitialConditionManagedLand(InitialConditionNaturalVegetation):
    pass

class InitialConditionSealedLand(InitialCondition):

    def initial(self):
        self.initial_interception_storage()
        self.initial_snow_cover()
        self.initial_frost_index()

class InitialConditionWater(InitialCondition):
    def initial(self):
        pass
