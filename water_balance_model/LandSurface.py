#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
import pcraster as pcr
from hydro_model_builder.Model import Model
from hydro_model_builder import VirtualOS as vos

from LandCover import *

class LandSurface(object):
    def __init__(self, LandSurface_variable):
        self.var = LandSurface_variable
        # self.var.dynamicLandCover
        # self.var.FixedLandCoverYear
        self.land_cover_modules = {
            'forest'      : Forest(LandSurface_variable, 'forest'),
            'grassland'   : Grassland(LandSurface_variable, 'grassland'),
            'irrPaddy'    : IrrPaddy(LandSurface_variable, 'irrPaddy'),
            'irrNonPaddy' : IrrNonPaddy(LandSurface_variable, 'irrNonPaddy'),
            'sealed'      : Sealed(LandSurface_variable, 'sealed'),
            'water'       : Water(LandSurface_variable, 'water')
            }
        
        # self.forest_module = Forest(LandSurface_variable, 'forest')
        # self.grassland_module = Grassland(LandSurface_variable, 'grassland')
        # self.irrPaddy_module = IrrPaddy(LandSurface_variable, 'irrPaddy')
        # self.irrNonPaddy_module = IrrNonPaddy(LandSurface_variable, 'irrNonPaddy')
        # self.sealed_module = Sealed(LandSurface_variable, 'sealed')
        # self.water_module = Water(LandSurface_variable, 'water')
        
    def initial(self):
        # self.forest_module.initial()
        # self.grassland_module.initial()
        # self.irrPaddy_module.initial()
        # self.irrNonPaddy_module.initial()
        # self.sealed_module.initial()
        # self.water_module.initial()
        for module in self.land_cover_modules.keys():
            self.land_cover_modules[module].initial()
        self.correct_cover_fraction()
        self.aggregate_land_cover_variables()
        
    def correct_cover_fraction(self):
        """Function to correct cover fraction, such that in 
        each grid square the various land cover fractions sum 
        to one
        """
        cover_fraction = []
        for module in self.land_cover_modules.keys():
            cover_fraction.append(getattr(self.land_cover_modules[module_name], 'coverFraction'))
        cover_fraction = np.stack(cover_fraction, axis=0)
        
        # TODO: put in configuration, LANDCOVER
        allow_cover_fraction_sum_less_than_one = False
        force_cover_fraction_sum_to_equal_one = True
        if allow_cover_fraction_sum_less_than_one or force_cover_fraction_sum_to_equal_one:
            cover_fraction_sum = np.sum(cover_fraction, axis=0)

        # TODO

    def aggregate_land_cover_variables(self):
        """Function to aggregate values computed separately 
        for each land cover
        """
        # TODO: put these in initial method
        # Perhaps initialize variables by checking the dimension in the land cover class
        self.natural_vegetation_module_names = ['forest_module','grassland_module']
        self.managed_land_module_names = ['irrPaddy_module','irrNonPaddy_module']
        self.vegetation_module_names = (
            self.natural_vegetation_module_names +
            self.managed_land_module_names)
        self.sealed_land_module_names = ['sealed_module']
        self.open_water_module_names = ['water_module']
        self.module_names = (
            self.natural_vegetation_module_names
            + self.managed_land_module_names
            + self.sealed_land_module_names
            + self.open_water_module_names)
        variables_to_sum = ['ETact']
        variables_to_average = ['th']
        
        for var_name in variables_to_sum:
            data = []
            for module_name in self.land_cover_modules.keys():
                attr = getattr(self.land_cover_modules[module_name], var_name)
                # attr *= land_cover_area[module_name]
                data.append(attr)
                
            # TODO: test performance
            vars(self)[var_name] = np.sum(data, axis=0)  
        
    def dynamic(self):
        self.correct_cover_fraction()
        self.aggregate_land_cover_variables()        
        for module in self.land_cover_modules.keys():
            self.land_cover_modules[module].dynamic()
        
        # self.forest_module.dynamic()
        # self.grassland_module.dynamic()
        # self.irrPaddy_module.dynamic()
        # self.irrNonPaddy_module.dynamic()
        # self.sealed_module.dynamic()
        # self.water_module.dynamic()    
