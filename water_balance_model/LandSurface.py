#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
import pcraster as pcr
import VirtualOS as vos
from Model import Model

from LandCover import *

class LandSurface(object):
    def __init__(self, LandSurface_variable):
        self.var = LandSurface_variable
        self.land_cover_modules = {
            'forest'      : Forest(LandSurface_variable, 'forest'),
            'grassland'   : Grassland(LandSurface_variable, 'grassland'),
            # 'irrPaddy'    : IrrPaddy(LandSurface_variable, 'irrPaddy'),
            'irrNonPaddy' : IrrNonPaddy(LandSurface_variable, 'irrNonPaddy'),
            'sealed'      : Sealed(LandSurface_variable, 'sealed'),
            'water'       : Water(LandSurface_variable, 'water')
            }
        self.land_cover_module_names = [
            'forest',
            'grassland',
            # 'irrPaddy',
            'irrNonPaddy',
            'sealed',
            'water'
        ]
        self.land_cover_module_names_with_soil = [
            'forest',
            'grassland',
            # 'irrPaddy',
            'irrNonPaddy'
        ]
        self.force_cover_fraction_sum_to_equal_one = bool(int(self.var._configuration.LANDCOVER['forceCoverFractionSumToEqualOne']))        
        # self.grid_cell_area_module = GridCellArea(LandSurface_variable)
        
    def initial(self):
        for module in self.land_cover_module_names:
            self.land_cover_modules[module].initial()

        # self.grid_cell_area_module.initial()        
        self.initialize_cover_fraction()
        self.initialize_land_cover_variables_to_aggregate()
        self.aggregate_land_cover_variables()

    def initialize_cover_fraction(self):
        self.cover_fraction = {
            module : np.zeros((self.var.nCell)) for module in self.land_cover_module_names
        }
        self.total_cover_fraction = np.zeros((self.var.nCell))
        self.update_cover_fraction()
            
    def update_cover_fraction(self):
        for index,module in enumerate(self.land_cover_module_names):
            self.cover_fraction[module] = getattr(
                self.land_cover_modules[module],
                'cover_fraction')
        self.total_cover_fraction = np.sum(
            self.cover_fraction.values(),
            axis=0)
        self.correct_cover_fraction()
        
    def correct_cover_fraction(self):
        """Function to correct cover fraction, such that in 
        each grid square the various land cover fractions sum 
        to one
        """
        if self.force_cover_fraction_sum_to_equal_one:
            for index,module in enumerate(self.land_cover_module_names):
                vars(self.land_cover_modules[module])['cover_fraction'] /= self.total_cover_fraction
                self.cover_fraction[module] /= self.total_cover_fraction
        self.total_cover_fraction = np.sum(
            self.cover_fraction.values(),
            axis=0)
        self.total_cover_fraction_soil = np.sum(
            [self.cover_fraction[key] for key in self.land_cover_module_names_with_soil],
            axis=0)

    def initialize_land_cover_variables_to_aggregate(self):
        self.variables_to_aggregate = [
            'interception_storage','interflow',
            'direct_runoff','infiltration',
            'capillary_rise_from_gw','deep_percolation',
            'preferential_flow','ETpot','ETact','EWact',
            'Eact','Tact',
            'water_available_for_infiltration',
            'interception_evaporation'
            ]
        
        self.soil_variables_to_aggregate = [
            'th','wc'
            ]
        
        self.variables_to_aggregate_by_averaging = [
            'th','wc'
            ]
        
        self.aggregate_land_cover_variables()

    def aggregate_land_cover_variables(self):
        """Function to aggregate values computed separately 
        for each land cover
        """
        self.aggregate_variables_for_all_land_covers()
        self.aggregate_variables_for_land_covers_with_soil()
        
    def aggregate_variables_for_all_land_covers(self):
        for var_name in self.variables_to_aggregate:
            var = self.aggregate_single_land_cover_variable(
                var_name,
                self.land_cover_module_names,
                self.total_cover_fraction
            )
            vars(self.var)[var_name] = var.copy()  # remove farm, crop dimension
            
    def aggregate_variables_for_land_covers_with_soil(self):
        for var_name in self.soil_variables_to_aggregate:
            var = self.aggregate_single_land_cover_variable(
                var_name,
                self.land_cover_module_names_with_soil,
                self.total_cover_fraction_soil
                )            
            vars(self.var)[var_name] = var.copy()

    def aggregate_single_land_cover_variable(self, var_name, module_names, total_cover_fraction):
        var_list = []
        for module in module_names:
            attr = getattr(self.land_cover_modules[module], var_name)
            
            # ***TODO*** this needs to be weighted according to
            # the area of farm/crop (perhaps see fao66_behaviour
            # on how to do this). Taking the mean, as we do here,
            # is only acceptable if both farm and crop dimensions
            # have length 1
            attr = np.mean(attr, axis=(0,1))
            
            attr *= (self.cover_fraction[module] * self.var.grid_cell_area)
            var_list.append(attr)
        var = np.sum(var_list, axis=0)
        if var_name in self.variables_to_aggregate_by_averaging:
            var /= self.var.grid_cell_area * total_cover_fraction
        return var
                
    def dynamic(self):
        for module in self.land_cover_module_names:
            self.land_cover_modules[module].dynamic()
        self.correct_cover_fraction()
        self.aggregate_land_cover_variables()
