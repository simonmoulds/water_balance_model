#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
import pcraster as pcr
import VirtualOS as vos
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
        soil_depth = np.stack([soildepth0, soildepth1, soildepth2])

        # CALIBRATION
        soildepth_factor = 1.   # TODO: read from configuration
        soil_depth[1] *= soildepth_factor
        soil_depth[2] *= soildepth_factor
        # soil_depth12 = self.var.soil_depth[1] + self.var.soil_depth[2]
        self.var.soil_depth = np.broadcast_to(
            soil_depth[None,None,:,:],
            (self.var.nFarm, self.var.nCrop, self.var.nLayer, self.var.nCell))

        # crop group number
        # TODO: would it make more sense to have this per crop?
        self.var.crop_group_number = vos.netcdf2PCRobjCloneWithoutTime(
            str(self.var._configuration.SOIL['cropGroupNumberInputFile']),
            str(self.var._configuration.SOIL['cropGroupNumberVariableName']),
            cloneMapFileName=self.var.cloneMap)[self.var.landmask]
        
        # These parameters have dimensions depth,lat,lon
        landmask = np.broadcast_to(self.var.landmask, (self.var.nLayer, self.var.nLat, self.var.nLon))
        ksat = vos.netcdf2PCRobjCloneWithoutTime(
            str(self.lc_configuration['KsatInputFile']),
            str(self.lc_configuration['KsatVariableName']),
            cloneMapFileName=self.var.cloneMap)
        ksat = ksat[landmask].reshape(self.var.nLayer,self.var.nCell)
        self.var.ksat = np.broadcast_to(ksat[None,None,:,:], (self.var.nFarm, self.var.nCrop, self.var.nLayer, self.var.nCell)).copy()
        self.var.ksat /= 100.   # cm d-1 -> m d-1 ***TODO*** put factor in config

        # Saturated water content
        th_s = vos.netcdf2PCRobjCloneWithoutTime(
            self.lc_configuration['saturatedWaterContentInputFile'],
            self.lc_configuration['saturatedWaterContentVariableName'],
            cloneMapFileName=self.var.cloneMap)
        th_s = th_s[landmask].reshape(self.var.nLayer,self.var.nCell)
        self.var.th_s = np.broadcast_to(th_s[None,None,:,:], (self.var.nFarm, self.var.nCrop, self.var.nLayer, self.var.nCell))

        # # Field capacity
        # th_fc = vos.netcdf2PCRobjCloneWithoutTime(
        #     self.lc_configuration['fieldCapacityInputFile'],
        #     self.lc_configuration['fieldCapacityVariableName'],
        #     cloneMapFileName=self.var.cloneMap)
        # th_fc = th_fc[landmask].reshape(self.var.nLayer,self.var.nCell)
        # self.var.th_fc = np.broadcast_to(th_fc[None,None,:,:], (self.var.nFarm, self.var.nCrop, self.var.nLayer, self.var.nCell))

        # # Wilting point
        # th_wp = vos.netcdf2PCRobjCloneWithoutTime(
        #     self.lc_configuration['wiltingPointInputFile'],
        #     self.lc_configuration['wiltingPointVariableName'],
        #     cloneMapFileName=self.var.cloneMap)
        # th_wp = th_wp[landmask].reshape(self.var.nLayer,self.var.nCell)
        # self.var.th_wp = np.broadcast_to(th_wp[None,None,:,:], (self.var.nFarm, self.var.nCrop, self.var.nLayer, self.var.nCell))

        # Residual water content
        th_res = vos.netcdf2PCRobjCloneWithoutTime(
            self.lc_configuration['residualWaterContentInputFile'],
            self.lc_configuration['residualWaterContentVariableName'],
            cloneMapFileName=self.var.cloneMap)
        th_res = th_res[landmask].reshape(self.var.nLayer,self.var.nCell)
        self.var.th_res = np.broadcast_to(th_res[None,None,:,:], (self.var.nFarm, self.var.nCrop, self.var.nLayer, self.var.nCell))

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
            (self.var.nFarm, self.var.nCrop, self.var.nLayer, self.var.nCell))

        # Van Genuchten lambda shape parameter
        van_genuchten_lambda = vos.netcdf2PCRobjCloneWithoutTime(
            self.lc_configuration['lambdaInputFile'],
            self.lc_configuration['lambdaVariableName'],
            cloneMapFileName=self.var.cloneMap)
        van_genuchten_lambda = van_genuchten_lambda[landmask].reshape(self.var.nLayer,self.var.nCell)
        self.var.van_genuchten_lambda = np.broadcast_to(
            van_genuchten_lambda[None,None,:,:],
            (self.var.nFarm, self.var.nCrop, self.var.nLayer, self.var.nCell))

    def compute_van_genuchten_coefficients(self):
        # compute van Genuchten n, m coefficients
        self.var.van_genuchten_n = self.var.van_genuchten_lambda + 1.
        self.var.van_genuchten_m = self.var.van_genuchten_lambda / self.var.van_genuchten_n
        self.var.van_genuchten_inv_n = 1. / self.var.van_genuchten_n
        self.var.van_genuchten_inv_m = 1. / self.var.van_genuchten_m
        self.var.van_genuchten_inv_alpha = 1. / self.var.van_genuchten_alpha

    def compute_soil_hydraulic_parameters(self):

        self.compute_van_genuchten_coefficients()

        # compute root zone water contents
        self.var.wc_sat = self.var.th_s * self.var.root_depth
        self.var.wc_res = self.var.th_res * self.var.root_depth
        self.var.wc_range = self.var.wc_sat - self.var.wc_res

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
        
    def dynamic(self):
        pass

