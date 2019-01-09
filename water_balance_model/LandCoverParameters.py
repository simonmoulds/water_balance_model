#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
import hydro_model_builder.VirtualOS as vos
import netCDF4 as nc
import datetime as datetime

from SoilParameters import *
from TopoParameters import *

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
        # self.soil_parameters_module.initial()
        self.topo_parameters_module.initial()
        self.read_static_params()
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
        self.initialize_dynamic_params()
        self.read_static_params()
        self.root_zone_water()
        # self.compute_root_depth()
        self.set_field_management_params()
        # self.update_cover_fraction()
        # self.update_crop_coefficient()
        # self.update_intercept_capacity()
        
    def initialize_dynamic_params(self):
        """Function to initialize dynamic parameters"""
        arr_zeros = np.zeros((self.var.nFarm, self.var.nLC, self.var.nCell))
        self.var.coverFraction = arr_zeros.copy()
        self.var.cropCoefficient = arr_zeros.copy()
        self.var.interception_capacity = arr_zeros.copy()

    def set_field_management_params(self):
        """Function to set field management parameters for 
        natural land cover. The parameters must be set 
        because they are used by certain methods which 
        operate on natural and managemed land. However, 
        using a value of zero effectively indicates that 
        there is no field management for these land covers.
        """
        self.var.Bunds = np.zeros((self.var.nFarm, self.var.nLC, self.var.nCell), dtype=np.bool)
        self.var.zBund = np.zeros((self.var.nFarm, self.var.nLC, self.var.nCell))
        self.var.BundWater = np.zeros((self.var.nFarm, self.var.nLC, self.var.nCell))

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

        # CWATM:
        # i = 0
        # for coverType in self.var.coverTypes[:4]:
        #     # calculate rootdepth for each soillayer and each land cover class
        #     # self.var.rootDepth[0][i] = np.minimum(self.var.soildepth[0], self.var.maxRootDepth[i])
        #     self.var.rootDepth[0][i] = self.var.soildepth[0].copy()  # 0.05 m
        #     # if land cover = forest
        #     if coverType <> 'grassland':
        #         # soil layer 1 = root max of land cover  - first soil layer
        #         h1 = np.maximum(self.var.soildepth[1], self.var.maxRootDepth[i] - self.var.soildepth[0])
        #         self.var.rootDepth[1][i] = np.minimum(self.var.soildepth12 - 0.05, h1)
        #         # soil layer is minimim 0.05 m
        #         self.var.rootDepth[2][i] = np.maximum(0.05, self.var.soildepth12 - self.var.rootDepth[1][i])
        #     else:
        #         self.var.rootDepth[1][i] = self.var.soildepth[1].copy()
        #         self.var.rootDepth[2][i] = self.var.soildepth[2].copy()
        #     i += 1
                        
        # self.var.MaxRootDepth = np.broadcast_to(
        #     max_root_depth[None,None,:],
        #     (1, 1, self.var.nCell))

    def read_min_soil_depth_frac(self):
        self.minSoilDepthFracNC = str(self.lc_configuration['minSoilDepthFracInputFile'])
        self.minSoilDepthFracVarName = str(self.lc_configuration['minSoilDepthFracVariableName'])
        min_soil_depth_frac = vos.netcdf2PCRobjCloneWithoutTime(
            self.configuration['minSoilDepthFracInputFile'],
            self.configuration['minSoilDepthFracVariableName'],
            cloneMapFileName = self.var.cloneMap)
        min_soil_depth_frac = min_soil_depth_frac[self.var.landmask].reshape(self.var.nLayer, self.var.nCell)
        self.var.MinSoilDepthFrac = np.broadcast_to(
            min_soil_depth_frac[None,None,:,:],
            (self.var.nFarm, self.var.nLC, self.var.nLayer, self.var.nCell))
        
    def read_static_params(self):
        self.var.minInterceptCap = np.float(self.lc_configuration['minInterceptCap'])
        self.var.cropDeplFactor = np.float(self.lc_configuration['cropDeplFactor'])
        self.var.minCropKc = np.float(self.var._configuration.SOIL['minCropKc'])  # TODO: put this somewhere logical in the config file
        self.read_max_root_depth()
        self.read_root_fraction()
        # self.read_min_soil_depth_frac()

    def compute_van_genuchten_coefficients(self):
        # compute van Genuchten n, m coefficients
        self.var.van_genuchten_n = self.var.van_genuchten_lambda + 1
        self.var.van_genuchten_m = self.var.van_genuchten_lambda / self.var.van_genuchten_n
        self.var.van_genuchten_inv_n = 1. / self.var.van_genuchten_n
        self.var.van_genuchten_inv_m = 1. / self.var.van_genuchten_m
        self.var.van_genuchten_inv_alpha = 1. / self.var.van_genuchten_alpha
        
    def root_zone_water(self):

        self.compute_van_genuchten_coefficients()
        # # compute van Genuchten n, m coefficients
        # van_genuchten_n = self.var.van_genuchten_lambda + 1
        # van_genuchten_m = self.var.van_genuchten_lambda / van_genuchten_n
        # van_genuchten_inv_n = 1. / van_genuchten_n
        # van_genuchten_inv_m = 1. / van_genuchten_m
        # van_genuchten_inv_alpha = 1. / self.var.van_genuchten_alpha

        # compute root zone water contents
        self.var.wc_sat = self.var.th_s * self.var.root_depth
        self.var.wc_res = self.var.th_res * self.var.root_depth
        self.var.wc_range = self.var.wc_sat - self.var.wc_res

        # *** TODO: check the following equations against literature ***

        # soil moisture at field capacity (pF2, 100 cm) [mm water slice]
        # Mualem equation (van Genuchten, 1980)
        self.var.wc_fc = (
            self.var.wc_res
            + self.var.wc_range
            / ((1 + (self.var.van_genuchten_alpha * 100) ** self.var.van_genuchten_n) ** self.var.van_genuchten_m))

        # soil moisture at wilting point (pF4.2, 10**4.2 cm) [mm water slice]
        # Mualem equation (van Genuchten, 1980)        
        self.var.wc_wp = (
            self.var.wc_res
            + self.var.wc_range
            / ((1 + (self.var.van_genuchten_alpha * (10 ** 4.2)) ** self.var.van_genuchten_n) ** self.var.van_genuchten_m))

        # not sure where these are used???
        sat_term_fc = np.maximum(0., self.var.wc_fc - self.var.wc_res) / self.var.wc_range
        k_unsat_fc = self.var.ksat * np.sqrt(sat_term_fc) * np.square(1 - (1 - sat_term_fc ** self.var.van_genuchten_inv_m) ** self.var.van_genuchten_m)
        self.var.k_fc12 = np.sqrt(k_unsat_fc[...,0,:] * k_unsat_fc[...,1,:])
        self.var.k_fc23 = np.sqrt(k_unsat_fc[...,1,:] * k_unsat_fc[...,2,:])
        
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
        
        # TODO: this is only relevant for forest, grassland
        
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

    def initial(self):
        pass

    def dynamic(self):
        pass
        
