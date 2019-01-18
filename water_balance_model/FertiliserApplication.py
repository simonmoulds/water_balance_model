#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
import VirtualOS as vos

import logging
logger = logging.getLogger(__name__)
        
class FertiliserApplication(object):

    def __init__(self, FertiliserApplication_variable):
        self.var = FertiliserApplication_variable        
        self.var.AnnualChangeInFertiliserAppRate = (
            bool(int(self.var._configuration.fieldMgmtOptions['AnnualChangeInFertiliserAppRate'])))
        self.var.NitrogenAppRateFileNC = (
            str(self.var._configuration.fieldMgmtOptions['NitrogenApplicationRateNC']))
        self.var.NitrogenAppRateVarName = (
            str(self.var._configuration.fieldMgmtOptions['NitrogenApplicationRateVariableName']))
        self.var.PhosphorusAppRateFileNC = (
            str(self.var._configuration.fieldMgmtOptions['PhosphorusApplicationRateNC']))
        self.var.PhosphorusAppRateVarName = (
            str(self.var._configuration.fieldMgmtOptions['PhosphorusApplicationRateVariableName']))
        self.var.PotassiumAppRateFileNC = (
            str(self.var._configuration.fieldMgmtOptions['PotassiumApplicationRateNC']))
        self.var.PotassiumAppRateVarName = (
            str(self.var._configuration.fieldMgmtOptions['PotassiumApplicationRateVariableName']))

    def initial(self):
        self.fertiliser_price_module.initial()
        arr_zeros = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))
        self.var.NitrogenAppRate = arr_zeros.copy()
        self.var.PhosphorusAppRate = arr_zeros.copy()
        self.var.PotassiumAppRate = arr_zeros.copy()

    def reset_initial_conditions(self):
        pass

    def fertiliser_expenditure(self):
        nitrogen_cost = (self.var.NitrogenAppRate * self.var.NitrogenPrice * self.var.CropArea)
        phosphorus_cost = (self.var.PhosphorusAppRate * self.var.PhosphorusPrice * self.var.CropArea)
        potassium_cost = (self.var.PotassiumAppRate * self.var.PotassiumPrice * self.var.CropArea)
        self.var.FertiliserCost = (nitrogen_cost + phosphorus_cost + potassium_cost)
    
    def reshape_fertiliser_app_rate(self, fert_app_rate, ncFile, ncVarName):        
        fert_app_rate_has_farm_dimension = (
            vos.check_if_nc_variable_has_dimension(
                ncFile,
                ncVarName,
                'farm'))
        # print 'hello, world'
        if fert_app_rate_has_farm_dimension:
            fert_app_rate = np.reshape(
                fert_app_rate[self.var.landmask_farm_crop],
                (self.var.nFarm, self.var.nCrop, self.var.nCell))
        else:
            fert_app_rate = np.reshape(
                fert_app_rate[self.var.landmask_crop],
                (self.var.nCrop, self.var.nCell))
            fert_app_rate = np.broadcast_to(
                fert_app_rate[None,:,:],
                (self.var.nFarm, self.var.nCrop, self.var.nCell))            
        return fert_app_rate
        
    def read_fertiliser_app_rate(self, ncFile, ncVarName, date = None):        
        fert_app_rate = vos.read_netCDF(
            ncFile,
            ncVarName,
            date,
            useDoy = None,
            cloneMapFileName = self.var.cloneMap,
            LatitudeLongitude = True)
        fert_app_rate = self.reshape_fertiliser_app_rate(
            fert_app_rate,
            ncFile,
            ncVarName)
        return fert_app_rate

    def set_fertiliser_app_rate(self):
        date = None
        if self.var.AnnualChangeInFertiliserAppRate:
            date = '%04i-%02i-%02i' % (self.var._modelTime.year, 1, 1)

        if self.var._modelTime.timeStepPCR == 1 or self.var._modelTime.doy == 1:
            if not self.var.NitrogenAppRateFileNC == "None":
                self.var.NitrogenAppRate = self.read_fertiliser_app_rate(
                    self.var.NitrogenAppRateFileNC,
                    self.var.NitrogenAppRateVarName,
                    date)
            if not self.var.PhosphorusAppRateFileNC == "None":
                self.var.PhosphorusAppRate = self.read_fertiliser_app_rate(
                    self.var.PhosphorusAppRateFileNC,
                    self.var.PhosphorusAppRateVarName,
                    date)
            if not self.var.PotassiumAppRateFileNC == "None":
                self.var.PotassiumAppRate = self.read_fertiliser_app_rate(
                    self.var.PotassiumAppRateFileNC,
                    self.var.PotassiumAppRateVarName,
                    date)
                
            # TODO: compute estimated fertiliser price, then adjust if
            # necessary to prevent farmers going into debt (or not,
            # depending on how we want to treat debt)
            
    def dynamic(self):
        self.fertiliser_price_module.dynamic()
        self.set_fertiliser_app_rate()
