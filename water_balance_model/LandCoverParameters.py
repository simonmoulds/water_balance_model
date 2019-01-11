#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
import hydro_model_builder.VirtualOS as vos
import netCDF4 as nc
import datetime as datetime

from SoilParameters import *
from TopoParameters import *
from IrrigationParameters import *
from FieldManagementParameters import *

class BaseClass(object):
    def __init__(self, var, configuration):
        self.var = var
        self.configuration = configuration
    
class CoverFraction(BaseClass):

    def __init__(self, var, configuration):
        super(CoverFraction, self).__init__(var, configuration)
        self.dynamicLandCover = bool(int(self.var._configuration.LANDCOVER['dynamicLandCover']))
        self.staticLandCoverYear = None
        if not self.dynamicLandCover:
            self.staticLandCoverYear = int(self.var._configuration.LANDCOVER['staticLandCoverYear'])
        # print self.dynamicLandCover
        # print self.staticLandCoverYear
        
    def initial(self):
        self.coverFractionNC = str(self.configuration['landCoverFractionInputFile'])
        self.coverFractionVarName = str(self.configuration['landCoverFractionVariableName'])
        self.var.coverFraction = np.zeros((self.var.nCell))
        self.update_cover_fraction()
        
    def update_cover_fraction(self):
        
        # TODO: make flexible the day on which land cover is changed
        
        start_of_model_run = (self.var._modelTime.timeStepPCR == 1)
        start_of_year = (self.var._modelTime.doy == 1)
        if self.dynamicLandCover:
            if start_of_model_run or start_of_year:
                date = datetime.datetime(self.var._modelTime.year, 1, 1, 0, 0, 0)
                self.var.coverFraction = vos.netcdf2PCRobjClone(
                    self.coverFractionNC.format(
                        day=self.var._modelTime.currTime.day,
                        month=self.var._modelTime.currTime.month,
                        year=self.var._modelTime.currTime.year),
                    self.coverFractionVarName,
                    date,
                    # useDoy = method_for_time_index,
                    # cloneMapAttributes = self.cloneMapAttributes,
                    cloneMapFileName = self.var.cloneMap,
                    LatitudeLongitude = True)[self.var.landmask]
        else:
            if start_of_model_run:
                date = datetime.datetime(self.staticLandCoverYear, 1, 1, 0, 0, 0)
                self.var.coverFraction = vos.netcdf2PCRobjClone(
                    self.coverFractionNC.format(
                        day=self.var._modelTime.currTime.day,
                        month=self.var._modelTime.currTime.month,
                        year=self.var._modelTime.currTime.year),
                    self.coverFractionVarName,
                    date,
                    # useDoy = method_for_time_index,
                    # cloneMapAttributes = self.cloneMapAttributes,
                    cloneMapFileName = self.var.cloneMap,
                    LatitudeLongitude = True)[self.var.landmask]
                
    def dynamic(self):
        self.update_cover_fraction()

class CropCoefficient(BaseClass):
    
    def initial(self):
        self.cropCoefficientNC = str(self.configuration['cropCoefficientInputFile'])
        self.cropCoefficientVarName = str(self.configuration['cropCoefficientVariableName'])
        self.var.cropCoefficient = np.zeros((1, 1, self.var.nCell))
        self.update_crop_coefficient()
        
    def update_crop_coefficient(self):
        self.var.cropCoefficient = vos.netcdf2PCRobjClone(
            self.cropCoefficientNC.format(
                day=self.var._modelTime.currTime.day,
                month=self.var._modelTime.currTime.month,
                year=self.var._modelTime.currTime.year),
            self.cropCoefficientVarName,
            datetime.datetime(
                2000,
                self.var._modelTime.currTime.month,
                self.var._modelTime.currTime.day),
            # useDoy = method_for_time_index,
            # cloneMapAttributes = self.cloneMapAttributes,
            cloneMapFileName = self.var.cloneMap,
            LatitudeLongitude = True)[self.var.landmask]
        
    def dynamic(self):
        self.update_crop_coefficient()

class MinimumInterceptionCapacity(BaseClass):
    def initial(self):
        self.var.minInterceptCap = np.float(self.configuration['minInterceptCap'])
        self.var.interception_capacity = (
            np.ones((self.var.nFarm, self.var.nLC, self.var.nCell))
            * self.var.minInterceptCap)
        
    def dynamic(self):
        pass
        
class InterceptionCapacity(MinimumInterceptionCapacity):
    
    def initial(self):
        super(InterceptionCapacity, self).initial()
        self.interceptCapNC = str(self.configuration['interceptCapInputFile'])
        self.interceptCapVarName = str(self.configuration['interceptCapVariableName'])
        self.update_intercept_capacity()
        
    def update_intercept_capacity(self):        
        if self.interceptCapNC != "None":
            self.var.interception_capacity = vos.netcdf2PCRobjClone(
                self.interceptCapNC.format(
                    day=self.var._modelTime.currTime.day,
                    month=self.var._modelTime.currTime.month,
                    year=self.var._modelTime.currTime.year),
                self.interceptCapVarName,
                datetime.datetime(
                    2000,
                    self.var._modelTime.currTime.month,
                    self.var._modelTime.currTime.day),
                # useDoy = method_for_time_index,
                # cloneMapAttributes = self.cloneMapAttributes,
                cloneMapFileName = self.var.cloneMap,
                LatitudeLongitude = True)[self.var.landmask]
        self.var.interception_capacity.clip(self.var.minInterceptCap, None)
        
    def dynamic(self):
        self.update_intercept_capacity()

class RootFraction(BaseClass):
    def initial(self):
        self.rootFractionNC = str(self.configuration['rootFractionInputFile'])
        self.rootFractionVarName = str(self.configuration['rootFractionVariableName'])                
        self.read_root_fraction()
        
    def read_root_fraction(self):
        landmask = np.broadcast_to(self.var.landmask, (2, self.var.nLat, self.var.nLon))
        root_fraction = vos.netcdf2PCRobjCloneWithoutTime(
            self.rootFractionNC,
            self.rootFractionVarName,
            cloneMapFileName = self.var.cloneMap) # nlayer, nlat, nlon
        root_fraction = root_fraction[landmask].reshape(2,self.var.nCell)

        # scale root fraction - adapted from CWATM
        # landcoverType.py lines 311-319

        # 1 - add top layer to root fraction input data
        root_fraction_adj = np.zeros((self.var.nLayer, self.var.nCell))
        top_layer_fraction = self.var.root_depth[0] / (self.var.root_depth[0] + self.var.root_depth[1])
        root_fraction_adj[0] = top_layer_fraction * root_fraction[0]
        root_fraction_adj[1] = (1. - top_layer_fraction) * root_fraction[1]
        root_fraction_adj[2] = (1. - root_fraction[1])

        # 2 - scale so that the total root fraction sums to one
        root_fraction_adj /= np.sum(root_fraction_adj, axis=0)  # rhs is broadcast automatically
        self.var.root_fraction = root_fraction_adj.copy()
        
    def dynamic(self):
        pass

class MaxRootDepth(BaseClass):
    def initial(self):
        self.maxRootDepthNC = str(self.configuration['maxRootDepthInputFile'])
        self.maxRootDepthVarName = str(self.configuration['maxRootDepthVariableName'])
        self.read_max_root_depth()
        
    def read_max_root_depth(self):
        max_root_depth = vos.netcdf2PCRobjCloneWithoutTime(
            self.maxRootDepthNC,
            self.maxRootDepthVarName,
            cloneMapFileName = self.var.cloneMap)  # nlat, nlon
        max_root_depth = max_root_depth[self.var.landmask]

        self.var.root_depth = np.zeros((self.var.nLayer, self.var.nCell))
        self.var.root_depth[0] = self.var.soil_depth[0].copy()
        h1 = np.maximum(self.var.soil_depth[1], max_root_depth - self.var.root_depth[0])
        self.var.root_depth[1] = np.minimum(
            self.var.soil_depth[1] + self.var.soil_depth[2] - 0.05,
            h1)
        self.var.root_depth[2] = np.maximum(
            0.05,
            self.var.soil_depth[1] + self.var.soil_depth[2] - self.var.root_depth[1])
        
    def dynamic(self):
        pass

class LandCoverParameters(object):
    def __init__(self, LandCoverParameters_variable, config_section_name):
        self.var = LandCoverParameters_variable
        self.configuration = getattr(
            self.var._configuration,
            config_section_name)

        # TODO: move this somewhere else
        self.var.minCropKc = np.float(self.var._configuration.SOIL['minCropKc'])  # TODO: put this somewhere logical in the config file

class SealedLandParameters(LandCoverParameters):
    """Class for parameters relevant to sealed land cover"""
    def __init__(self, var, config_section_name):
        super(SealedLandParameters, self).__init__(var, config_section_name)
        self.topo_parameters_module = TopoParametersSealed(var, config_section_name)
        self.cover_fraction_module = CoverFraction(var, self.configuration)
        self.intercept_capacity_module = MinimumInterceptionCapacity(var, self.configuration)        
    def initial(self):
        self.topo_parameters_module.initial()
        self.cover_fraction_module.initial()
        self.intercept_capacity_module.initial()
    def dynamic(self):
        self.cover_fraction_module.dynamic()
        self.intercept_capacity_module.dynamic()

class WaterParameters(SealedLandParameters):
    """Class for parameters relevant to water land cover"""
    
class NaturalVegetationParameters(LandCoverParameters):
    def __init__(self, var, config_section_name):
        super(NaturalVegetationParameters, self).__init__(var, config_section_name)
        self.soil_parameters_module = SoilParameters(var, config_section_name)
        self.topo_parameters_module = TopoParametersNaturalVegetation(var, config_section_name)
        self.cover_fraction_module = CoverFraction(var, self.configuration)
        self.crop_coefficient_module = CropCoefficient(var, self.configuration)
        self.intercept_capacity_module = InterceptionCapacity(var, self.configuration)
        self.root_depth_module = MaxRootDepth(var, self.configuration)            
        self.root_fraction_module = RootFraction(var, self.configuration)
        self.field_mgmt_parameters_module = FieldManagementParameters(var, config_section_name)

    def initial(self):
        self.soil_parameters_module.initial()
        self.topo_parameters_module.initial()
        self.cover_fraction_module.initial()
        self.crop_coefficient_module.initial()
        self.intercept_capacity_module.initial()
        self.root_depth_module.initial()
        self.root_fraction_module.initial()
        self.field_mgmt_parameters_module.initial()
        self.soil_parameters_module.compute_soil_hydraulic_parameters()

    def dynamic(self):
        self.soil_parameters_module.dynamic()
        self.topo_parameters_module.dynamic()
        self.cover_fraction_module.dynamic()
        self.crop_coefficient_module.dynamic()
        self.intercept_capacity_module.dynamic()
        
class ManagedLandParameters(LandCoverParameters):
    def __init__(self, var, config_section_name):
        super(ManagedLandParameters, self).__init__(var, config_section_name)
        self.soil_parameters_module = SoilParameters(var, config_section_name)
        self.topo_parameters_module = TopoParametersManagedLand(var, config_section_name)
        self.cover_fraction_module = CoverFraction(var, self.configuration)
        self.crop_coefficient_module = CropCoefficient(var, self.configuration)
        self.intercept_capacity_module = MinimumInterceptionCapacity(var, self.configuration)
        self.root_depth_module = MaxRootDepth(var, self.configuration)            
        self.root_fraction_module = RootFraction(var, self.configuration)
        self.field_mgmt_parameters_module = FieldManagementParametersManagedLand(var, config_section_name)
        self.irrigation_parameters_module = IrrigationParameters(var, config_section_name)

    def initial(self):
        self.soil_parameters_module.initial()
        self.topo_parameters_module.initial()
        self.cover_fraction_module.initial()
        self.crop_coefficient_module.initial()
        self.intercept_capacity_module.initial()
        self.root_depth_module.initial()
        self.root_fraction_module.initial()
        self.field_mgmt_parameters_module.initial()
        self.irrigation_parameters_module.initial()
        self.soil_parameters_module.compute_soil_hydraulic_parameters()

    def dynamic(self):
        self.soil_parameters_module.dynamic()
        self.topo_parameters_module.dynamic()
        self.cover_fraction_module.dynamic()
        self.crop_coefficient_module.dynamic()
        self.intercept_capacity_module.dynamic()
        
