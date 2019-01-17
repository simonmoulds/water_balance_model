#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
import VirtualOS as vos

import logging
logger = logging.getLogger(__name__)

# class CropPrice(object):
    
#     def __init__(self, var, configuration):
#         self.var = var
#         self.configuration = configuration
#         self.CropPriceFileNC = str(self.configuration['cropPriceInputFile'])
#         self.CropPriceVarName = str(self.configuration['cropPriceVariableName'])
        
#     def initial(self):
#         self.var.CropPrice = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))

#     def set_crop_price(self):
#         """Function to read crop area"""
#         start_of_model_run = (self.var._modelTime.timeStepPCR == 1)
#         start_of_year = (self.var._modelTime.doy == 1)
#         if start_of_model_run or start_of_year:
#             if not self.CropPriceFileNC == "None":
#                 date = datetime.datetime(self.var._modelTime.year, 1, 1, 0, 0, 0)
#                 crop_price = vos.netcdf2PCRobjClone(
#                     self.CropPriceFileNC,
#                     self.CropPriceVarName,
#                     date,
#                     useDoy = None,
#                     cloneMapFileName = self.var.cloneMap,
#                     LatitudeLongitude = True)
#                 crop_price = np.reshape(
#                     crop_price[self.var.landmask_crop],
#                     (self.var.nCrop, self.var.nCell))
#                 crop_price = np.broadcast_to(
#                     crop_price[None,:,:],
#                     (self.var.nFarm,
#                      self.var.nCrop,
#                      self.var.nCell)).copy()
#                 self.var.CropPrice = crop_price
                                            
#     def dynamic(self):
#         self.set_crop_price()

class Income(object):

    def __init__(self, var):
        self.var = var
        
    def initial(self):
        arr_zeros = np.zeros((self.var.nFarm, self.var.nCell))
        self.var.CropIncome = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))
        self.var.PotentialCropIncome = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))
        self.var.AnnualCropIncome = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))
        self.var.PotentialAnnualCropIncome = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))
        self.var.LabourIncome = arr_zeros.copy()
        self.var.FarmIncome = arr_zeros.copy()
        self.var.AnnualIncome = arr_zeros.copy()

    def reset_initial_conditions(self):
        if self.var.IsFirstDayOfYear:
            self.var.AnnualCropIncome[:] = 0
            self.var.PotentialAnnualCropIncome = 0
    
    def farm_income(self):
        self.crop_income()
        self.labour_income()
        self.var.FarmIncome = (
            np.sum(self.var.CropIncome, axis=1)
            + self.var.LabourIncome)
        
    def crop_income(self):
        self.var.CropIncome = (
            self.var.Y
            * (self.var.FarmCropArea / 10000.)
            * self.var.CropPrice)

        is_harvest = self.var._modelTime.doy == self.var.HarvestDateAdj
        Yx = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))
        Yx[is_harvest] = (self.var.Yx[None,:,:] * np.ones((self.var.nFarm))[:,None,None])[is_harvest]
        self.var.PotentialCropIncome = (
            (Yx / 1000)
            * (self.var.FarmCropArea / 10000.)
            * self.var.CropPrice)

        self.var.AnnualCropIncome += self.var.CropIncome
        self.var.PotentialAnnualCropIncome += self.var.PotentialCropIncome
        
    def labour_income(self):
        pass
    
    def update_annual_income(self):
        self.var.AnnualIncome += self.var.FarmIncome

    def dynamic(self):
        self.reset_initial_conditions()
        self.farm_income()
        self.update_annual_income()
        
