#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
import pcraster as pcr
import hydro_model_builder.VirtualOS as vos
import netCDF4 as nc

class SoilParameters(object):

    def __init__(self, SoilParameters_variable, config_section_name):
        """Initialise SoilParameters object"""
        self.var = SoilParameters_variable
        self.lc_configuration = getattr(self.var._configuration, config_section_name)

    def initial(self):
        self.read()
        
    def read(self):
        self.var.nLayer = 3
        
        # soil depths
        soildepth0 = np.full((self.var.nLat, self.var.nLon), 0.05)[self.var.landmask]
        soildepth1 = vos.netcdf2PCRobjCloneWithoutTime(
            str(self.var._configuration.SOIL['soilDepthOneInputFile']),
            str(self.var._configuration.SOIL['soilDepthOneVariableName']),
            cloneMapFileName=self.var.cloneMap)[self.var.landmask]
        soildepth1 = np.maximum(0.05, soildepth1 - soildepth0)

        soildepth2 = vos.netcdf2PCRobjCloneWithoutTime(
            str(self.var._configuration.SOIL['soilDepthTwoInputFile']),
            str(self.var._configuration.SOIL['soilDepthTwoVariableName']),
            cloneMapFileName=self.var.cloneMap)[self.var.landmask]
        soildepth2 = np.maximum(0.05, soildepth2)
        self.var.soil_depth = np.stack([soildepth0, soildepth1, soildepth2])

        # CALIBRATION
        soildepth_factor = 1.   # TODO: read from configuration
        self.var.soil_depth[1] *= soildepth_factor
        self.var.soil_depth[2] *= soildepth_factor
        self.var.soil_depth12 = self.var.soil_depth[1] + self.var.soil_depth[2]
        
        # These parameters have dimensions depth,lat,lon
        # soilParams1 = ['ksat', 'th_s', 'th_fc', 'th_wp']
        landmask = np.broadcast_to(self.var.landmask, (self.var.nLayer, self.var.nLat, self.var.nLon))
        # for param in soilParams1:
        #     d = vos.netcdf2PCRobjCloneWithoutTime(
        #         self.var.soilFileNC,
        #         param,
        #         cloneMapFileName=self.var.cloneMap)
        #     print d.shape
        #     d = d[landmask].reshape(self.var.nLayer,self.var.nCell)
        #     vars(self.var)[param] = np.broadcast_to(d[None,None,:,:], (self.var.nFarm, self.var.nLC, self.var.nLayer, self.var.nCell))

        # Saturated hydraulic conductivity
        ksat = vos.netcdf2PCRobjCloneWithoutTime(
            str(self.lc_configuration['KsatInputFile']),
            str(self.lc_configuration['KsatVariableName']),
            cloneMapFileName=self.var.cloneMap)
        ksat = ksat[landmask].reshape(self.var.nLayer,self.var.nCell)
        self.var.ksat = np.broadcast_to(ksat[None,None,:,:], (1, 1, self.var.nLayer, self.var.nCell))

        # Saturated water content
        th_s = vos.netcdf2PCRobjCloneWithoutTime(
            self.lc_configuration['saturatedWaterContentInputFile'],
            self.lc_configuration['saturatedWaterContentVariableName'],
            cloneMapFileName=self.var.cloneMap)
        th_s = th_s[landmask].reshape(self.var.nLayer,self.var.nCell)
        self.var.th_s = np.broadcast_to(th_s[None,None,:,:], (1, 1, self.var.nLayer, self.var.nCell))

        # # Field capacity
        # th_fc = vos.netcdf2PCRobjCloneWithoutTime(
        #     self.lc_configuration['fieldCapacityInputFile'],
        #     self.lc_configuration['fieldCapacityVariableName'],
        #     cloneMapFileName=self.var.cloneMap)
        # th_fc = th_fc[landmask].reshape(self.var.nLayer,self.var.nCell)
        # self.var.th_fc = np.broadcast_to(th_fc[None,None,:,:], (1, 1, self.var.nLayer, self.var.nCell))

        # # Wilting point
        # th_wp = vos.netcdf2PCRobjCloneWithoutTime(
        #     self.lc_configuration['wiltingPointInputFile'],
        #     self.lc_configuration['wiltingPointVariableName'],
        #     cloneMapFileName=self.var.cloneMap)
        # th_wp = th_wp[landmask].reshape(self.var.nLayer,self.var.nCell)
        # self.var.th_wp = np.broadcast_to(th_wp[None,None,:,:], (1, 1, self.var.nLayer, self.var.nCell))

        # Residual water content
        th_res = vos.netcdf2PCRobjCloneWithoutTime(
            self.lc_configuration['residualWaterContentInputFile'],
            self.lc_configuration['residualWaterContentVariableName'],
            cloneMapFileName=self.var.cloneMap)
        th_res = th_res[landmask].reshape(self.var.nLayer,self.var.nCell)
        self.var.th_res = np.broadcast_to(th_res[None,None,:,:], (1, 1, self.var.nLayer, self.var.nCell))

        # # The following is adapted from AOS_ComputeVariables.m, lines 25
        # self.var.th_dry = self.var.th_wp / 2
                
        # Van Genuchten alpha shape parameter
        van_genuchten_alpha = vos.netcdf2PCRobjCloneWithoutTime(
            self.lc_configuration['alphaInputFile'],
            self.lc_configuration['alphaVariableName'],
            cloneMapFileName=self.var.cloneMap)
        van_genuchten_alpha = van_genuchten_alpha[landmask].reshape(self.var.nLayer,self.var.nCell)
        self.var.van_genuchten_alpha = np.broadcast_to(
            van_genuchten_alpha[None,None,:,:],
            (1, 1, self.var.nLayer, self.var.nCell))

        # Van Genuchten lambda shape parameter
        van_genuchten_lambda = vos.netcdf2PCRobjCloneWithoutTime(
            self.lc_configuration['lambdaInputFile'],
            self.lc_configuration['lambdaVariableName'],
            cloneMapFileName=self.var.cloneMap)
        van_genuchten_lambda = van_genuchten_lambda[landmask].reshape(self.var.nLayer,self.var.nCell)
        self.var.van_genuchten_lambda = np.broadcast_to(
            van_genuchten_lambda[None,None,:,:],
            (1, 1, self.var.nLayer, self.var.nCell))

    # def compute_unsaturated_hydraulic_conductivity(self):
    #     available_water = np.maximum(0., self.var.wc - self.var.wc_res)
    #     storage_capacity = self.var.wc_sat - self.var.wc
    #     sat_term = available_water / self.var.wc_range
    #     sat_term.clip(0., 1.)
    #     k = self.var.ksat * np.sqrt(sat_term) * np.square(1. - (1. - sat_term ** self.var.van_genuchten_inv_m) ** self.var.van_genuchten_m)
        
    def dynamic(self):
        pass

