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

class SealedLandParameters(object):
    def __init__(self, LandCoverParameters_variable, config_section_name):
        self.var = LandCoverParameters_variable
        self.lc_configuration = getattr(
            self.var._configuration,
            config_section_name)
        # self.soil_parameters_module = SoilParameters(
        #     LandCoverParameters_variable,
        #     config_section_name)        
        self.topo_parameters_module = TopoParametersSealed(
            LandCoverParameters_variable,
            config_section_name)
        
    def initial(self):
        self.read_static_params()
        # self.soil_parameters_module.initial()
        self.topo_parameters_module.initial()
        self.var.interception_capacity = (
            np.ones((self.var.nFarm, self.var.nLC, self.var.nCell))
            * self.var.minInterceptCap)
        
    def read_static_params(self):
        self.var.minInterceptCap = np.float(self.lc_configuration['minInterceptCap'])

    def dynamic(self):
        pass
        
class NaturalVegetationParameters(object):
    def __init__(self, LandCoverParameters_variable, config_section_name):
        self.var = LandCoverParameters_variable
        self.lc_configuration = getattr(
            self.var._configuration,
            config_section_name)
        self.soil_parameters_module = SoilParameters(
            LandCoverParameters_variable,
            config_section_name)        
        self.topo_parameters_module = TopoParametersNaturalVegetation(
            LandCoverParameters_variable,
            config_section_name)
        self.field_mgmt_parameters_module = FieldManagementParameters(
            LandCoverParameters_variable,
            config_section_name)

        self.dynamicLandCover = bool(int(self.var._configuration.LANDCOVER['dynamicLandCover']))
        self.staticLandCoverYear = None
        if not self.dynamicLandCover:
            self.staticLandCoverYear = int(self.var._configuration.LANDCOVER['staticLandCoverYear'])
            
        self.coverFractionNC = str(self.lc_configuration['landCoverFractionInputFile'])
        self.coverFractionVarName = str(self.lc_configuration['landCoverFractionVariableName'])
        self.cropCoefficientNC = str(self.lc_configuration['cropCoefficientInputFile'])
        self.cropCoefficientVarName = str(self.lc_configuration['cropCoefficientVariableName'])
        self.interceptCapNC = str(self.lc_configuration['interceptCapInputFile'])
        self.interceptCapVarName = str(self.lc_configuration['interceptCapVariableName'])

    def initial(self):
        self.soil_parameters_module.initial()
        self.topo_parameters_module.initial()
        self.field_mgmt_parameters_module.initial()
        self.initialize_dynamic_params()
        self.read_static_params()
        self.soil_parameters_module.compute_soil_hydraulic_parameters()
        
    def initialize_dynamic_params(self):
        """Function to initialize dynamic parameters"""
        arr_zeros = np.zeros((self.var.nFarm, self.var.nLC, self.var.nCell))
        self.var.coverFraction = arr_zeros.copy()
        self.var.cropCoefficient = arr_zeros.copy()
        self.var.interception_capacity = arr_zeros.copy()

    def read_root_fraction(self):
        self.rootFractionNC = str(self.lc_configuration['rootFractionInputFile'])
        self.rootFractionVarName = str(self.lc_configuration['rootFractionVariableName'])        
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

    def read_max_root_depth(self):
        self.maxRootDepthNC = str(self.lc_configuration['maxRootDepthInputFile'])
        self.maxRootDepthVarName = str(self.lc_configuration['maxRootDepthVariableName'])
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

    # def read_min_soil_depth_frac(self):
    #     self.minSoilDepthFracNC = str(self.lc_configuration['minSoilDepthFracInputFile'])
    #     self.minSoilDepthFracVarName = str(self.lc_configuration['minSoilDepthFracVariableName'])
    #     min_soil_depth_frac = vos.netcdf2PCRobjCloneWithoutTime(
    #         self.configuration['minSoilDepthFracInputFile'],
    #         self.configuration['minSoilDepthFracVariableName'],
    #         cloneMapFileName = self.var.cloneMap)
    #     min_soil_depth_frac = min_soil_depth_frac[self.var.landmask].reshape(self.var.nLayer, self.var.nCell)
    #     self.var.MinSoilDepthFrac = np.broadcast_to(
    #         min_soil_depth_frac[None,None,:,:],
    #         (self.var.nFarm, self.var.nLC, self.var.nLayer, self.var.nCell))
        
    def read_static_params(self):
        self.var.minInterceptCap = np.float(self.lc_configuration['minInterceptCap'])
        self.var.cropDeplFactor = np.float(self.lc_configuration['cropDeplFactor'])
        self.var.minCropKc = np.float(self.var._configuration.SOIL['minCropKc'])  # TODO: put this somewhere logical in the config file
        self.read_max_root_depth()
        self.read_root_fraction()
        # self.read_min_soil_depth_frac()
        
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
                    LatitudeLongitude = True)
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
                    LatitudeLongitude = True)
    
    def dynamic(self):
        self.soil_parameters_module.dynamic()
        self.topo_parameters_module.dynamic()
        self.update_cover_fraction()
        self.update_crop_coefficient()
        self.update_intercept_capacity()        

class ManagedLandParameters(NaturalVegetationParameters):
    def __init__(self, LandCoverParameters_variable, config_section_name):
        super(ManagedLandParameters, self).__init__(
            LandCoverParameters_variable,
            config_section_name)
        self.topo_parameters_module = TopoParametersManagedLand(
            LandCoverParameters_variable,
            config_section_name)
        self.irrigation_parameters_module = IrrigationParameters(
            LandCoverParameters_variable,
            config_section_name)
        self.field_mgmt_parameters_module = FieldManagementParametersManagedLand(
            LandCoverParameters_variable,
            config_section_name)

    def initial(self):
        self.soil_parameters_module.initial()
        self.topo_parameters_module.initial()
        self.irrigation_parameters_module.initial()
        self.field_mgmt_parameters_module.initial()
        self.initialize_dynamic_params()
        self.read_static_params()
        self.soil_parameters_module.compute_soil_hydraulic_parameters()
        
    def dynamic(self):
        self.soil_parameters_module.dynamic()
        self.topo_parameters_module.dynamic()
        self.update_cover_fraction()
        self.update_crop_coefficient()
        # self.update_intercept_capacity()        
