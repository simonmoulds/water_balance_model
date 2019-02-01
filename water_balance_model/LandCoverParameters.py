#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
import VirtualOS as vos
import netCDF4 as nc
import datetime as datetime

from SoilParameters import *
from TopoParameters import *
from CropParameters import *
from FarmParameters import *
from IrrigationParameters import *
from FieldManagementParameters import *
from PriceData import *

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
        self.var.cover_fraction = np.zeros((self.var.nCell))
        self.update_cover_fraction()
        
    def update_cover_fraction(self):
        
        # TODO: make flexible the day on which land cover is changed
        
        start_of_model_run = (self.var._modelTime.timeStepPCR == 1)
        start_of_year = (self.var._modelTime.doy == 1)
        if self.dynamicLandCover:
            if start_of_model_run or start_of_year:
                date = datetime.datetime(self.var._modelTime.year, 1, 1, 0, 0, 0)
                cover_fraction = vos.netcdf2PCRobjClone(
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
                cover_fraction = np.float64(cover_fraction)
                self.var.cover_fraction = cover_fraction
        else:
            if start_of_model_run:
                date = datetime.datetime(self.staticLandCoverYear, 1, 1, 0, 0, 0)
                cover_fraction = vos.netcdf2PCRobjClone(
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
                cover_fraction = np.float64(cover_fraction)
                self.var.cover_fraction = cover_fraction
                
    def dynamic(self):
        self.update_cover_fraction()

class CropCoefficient(BaseClass):
    
    def initial(self):
        self.cropCoefficientNC = str(self.configuration['cropCoefficientInputFile'])
        self.cropCoefficientVarName = str(self.configuration['cropCoefficientVariableName'])
        self.var.cropCoefficient = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))
        self.update_crop_coefficient()
        
    def update_crop_coefficient(self):
        
        start_of_model_run = (self.var._modelTime.timeStepPCR == 1)
        if start_of_model_run or (self.var._modelTime.day in [1,11,21]):
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
            np.ones((self.var.nFarm, self.var.nCrop, self.var.nCell))
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
            start_of_model_run = (self.var._modelTime.timeStepPCR == 1)
            if start_of_model_run or (self.var._modelTime.day in [1,11,21]):
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
        self.var.interception_capacity = self.var.interception_capacity.clip(self.var.minInterceptCap, None)
        
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
            cloneMapFileName = self.var.cloneMap)
        root_fraction = root_fraction[landmask].reshape(2,self.var.nCell)
        root_fraction = np.broadcast_to(
            root_fraction[None,None,:,:],
            (self.var.nFarm, self.var.nCrop, 2, self.var.nCell))

        # scale root fraction - adapted from CWATM
        # landcoverType.py lines 311-319

        # 1 - add top layer to root fraction input data
        root_fraction_adj = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nLayer, self.var.nCell))
        top_layer_fraction = np.divide(
            self.var.root_depth[...,0,:],
            (self.var.root_depth[...,0,:] + self.var.root_depth[...,1,:])
        )        
        root_fraction_adj[...,0,:] = top_layer_fraction * root_fraction[...,0,:]
        root_fraction_adj[...,1,:] = (1. - top_layer_fraction) * root_fraction[...,1,:]
        root_fraction_adj[...,2,:] = (1. - root_fraction[...,1,:])

        # 2 - scale so that the total root fraction sums to one
        root_fraction_sum = np.sum(root_fraction_adj, axis=-2)
        root_fraction_adj /= root_fraction_sum[...,None,:]
        self.var.root_fraction = root_fraction_adj.copy()
        
    def dynamic(self):
        pass

class MaxRootDepth(BaseClass):
    def initial(self):
        self.var.max_root_depth = np.ones((self.var.nCell)) * 1.

    def compute_root_depth(self):
        """Function to compute the root depth in each soil 
        layer
        """
        self.var.root_depth = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nLayer, self.var.nCell))
        self.var.root_depth[...,0,:] = self.var.soil_depth[...,0,:].copy()

        # make sure that root depth in layer 1 does not exceed
        # the depth of the soil layer
        soildepth12 = (
            self.var.soil_depth[...,1,:]
            + self.var.soil_depth[...,2,:]
        )
        h1 = np.maximum(
            self.var.soil_depth[...,1,:],
            self.var.max_root_depth - self.var.soil_depth[...,0,:]
        )
        self.var.root_depth[...,1,:] = np.minimum(
            (soildepth12 - 0.05),
            h1
        )
        # make sure the root depth in layer 2 is at least 0.05m (?)
        self.var.root_depth[...,2,:] = np.maximum(
            0.05,
            (soildepth12 - self.var.root_depth[...,1,:])
        )
        
    def dynamic(self):
        pass
    
class MaxRootDepthFromFile(MaxRootDepth):
    def initial(self):
        super(MaxRootDepthFromFile, self).initial()
        self.maxRootDepthNC = str(self.configuration['maxRootDepthInputFile'])
        self.maxRootDepthVarName = str(self.configuration['maxRootDepthVariableName'])
        self.read_max_root_depth()
        self.compute_root_depth()
        
    def read_max_root_depth(self):
        max_root_depth = vos.netcdf2PCRobjCloneWithoutTime(
            self.maxRootDepthNC,
            self.maxRootDepthVarName,
            cloneMapFileName = self.var.cloneMap)  # nlat, nlon
        max_root_depth = max_root_depth[self.var.landmask]
        max_root_depth *= self.var.soildepth_factor  # CALIBRATION
        self.var.max_root_depth = np.broadcast_to(
            max_root_depth[None,None,:],
            (self.var.nFarm, self.var.nCrop, self.var.nCell))

class MaxRootDepthDynamic(MaxRootDepth):
    def initial(self):
        super(MaxRootDepthDynamic, self).initial()
        self.compute_max_root_depth()
        self.compute_root_depth()
        
    def compute_max_root_depth(self):
        self.var.max_root_depth = self.var.Zmin # TEMPORARY
    
    def dynamic(self):
        self.var.max_root_depth[self.var.GrowingSeasonIndex] = self.var.Zmin[self.var.GrowingSeasonIndex]
        self.var.max_root_depth[np.logical_not(self.var.GrowingSeasonIndex)] = 1.  # Global Crop Water Model
        self.compute_root_depth()

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
        self.root_depth_module = MaxRootDepthFromFile(var, self.configuration)            
        self.root_fraction_module = RootFraction(var, self.configuration)
        self.field_mgmt_parameters_module = FieldManagementParameters(var, self.configuration)

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
        self.root_depth_module = MaxRootDepthFromFile(var, self.configuration)            
        self.root_fraction_module = RootFraction(var, self.configuration)
        self.field_mgmt_parameters_module = FieldManagementParametersManagedLand(var, self.configuration)
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

class ManagedLandWithFarmerBehaviourParameters(LandCoverParameters):
    def __init__(self, var, config_section_name):
        super(ManagedLandWithFarmerBehaviourParameters, self).__init__(var, config_section_name)
        self.soil_parameters_module = SoilParameters(var, config_section_name)
        self.topo_parameters_module = TopoParametersManagedLand(var, config_section_name)
        self.cover_fraction_module = CoverFraction(var, self.configuration)        
        self.farm_parameters_module = FarmParameters(var, self.configuration)
        # self.price_module = PriceData(var, self.configuration)
        self.crop_parameters_module = CropParameters(var, self.configuration)
        self.crop_area_module = CropArea(var, self.configuration)
        self.intercept_capacity_module = MinimumInterceptionCapacity(var, self.configuration)
        self.price_module = PriceData(var, self.configuration)
        self.root_depth_module = MaxRootDepthDynamic(var, self.configuration)
        self.root_fraction_module = RootFraction(var, self.configuration)
        self.field_mgmt_parameters_module = FieldManagementParametersManagedLand(var, self.configuration)
        self.irrigation_parameters_module = IrrigationParameters(var, config_section_name)

    def initial(self):
        self.soil_parameters_module.initial()
        self.topo_parameters_module.initial()
        self.cover_fraction_module.initial()
        self.farm_parameters_module.initial()
        # self.price_module.initial()
        self.crop_parameters_module.initial()
        self.crop_area_module.initial()
        self.intercept_capacity_module.initial()
        self.price_module.initial()
        self.root_depth_module.initial()
        self.root_fraction_module.initial()
        self.field_mgmt_parameters_module.initial()
        self.irrigation_parameters_module.initial()
        self.soil_parameters_module.compute_soil_hydraulic_parameters()

    def dynamic(self):
        self.soil_parameters_module.dynamic()
        self.topo_parameters_module.dynamic()
        self.cover_fraction_module.dynamic()
        self.farm_parameters_module.dynamic()
        # self.price_module.dynamic()
        self.crop_parameters_module.dynamic()
        self.crop_area_module.dynamic()
        self.intercept_capacity_module.dynamic()
        self.price_module.dynamic()


        
