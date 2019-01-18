#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
import datetime as datetime

import VirtualOS as vos

import logging
logger = logging.getLogger(__name__)

class FertiliserPrice(object):
    
    def __init__(self, var, configuration):
        self.var = var
        self.NitrogenPriceFileNC = str(configuration['NitrogenPriceInputFile'])
        self.NitrogenPriceVarName = str(configuration['NitrogenPriceVariableName'])
        self.PhosphorusPriceFileNC = str(configuration['PhosphorusPriceInputFile'])
        self.PhosphorusPriceVarName = str(configuration['PhosphorusPriceVariableName'])
        self.PotassiumPriceFileNC = str(configuration['PotassiumPriceInputFile'])
        self.PotassiumPriceVarName = str(configuration['PotassiumPriceVariableName'])

    def initial(self):
        arr_zeros = np.zeros((self.var.nCell))
        self.var.NitrogenPrice = arr_zeros.copy()
        self.var.PhosphorusPrice = arr_zeros.copy()
        self.var.PotassiumPrice = arr_zeros.copy()

    def reset_initial_conditions(self):
        pass

    def read_fertiliser_price(self, ncFile, ncVarName, date = None):        

        fert_price = vos.netcdf2PCRobjClone(
            ncFile,
            ncVarName,
            date,
            useDoy = None,
            cloneMapFileName = self.var.cloneMap,
            LatitudeLongitude = True)        
        fert_price = fert_price[self.var.landmask]
        return fert_price

    def set_fertiliser_price(self):
        start_of_model_run = (self.var._modelTime.timeStepPCR == 1)
        start_of_year = (self.var._modelTime.doy == 1)
        if start_of_model_run or start_of_year:
            date = datetime.datetime(self.var._modelTime.year, 1, 1, 0, 0, 0)        
            if not self.NitrogenPriceFileNC == "None":                
                self.var.NitrogenPrice = self.read_fertiliser_price(
                    self.NitrogenPriceFileNC,
                    self.NitrogenPriceVarName,
                    date)
                # print np.max(self.var.NitrogenPrice)
            if not self.PhosphorusPriceFileNC == "None":
                self.var.PhosphorusPrice = self.read_fertiliser_price(
                    self.PhosphorusPriceFileNC,
                    self.PhosphorusPriceVarName,
                    date)
                # print np.max(self.var.PhosphorusPrice)
            if not self.PotassiumPriceFileNC == "None":
                self.var.PotassiumPrice = self.read_fertiliser_price(
                    self.PotassiumPriceFileNC,
                    self.PotassiumPriceVarName,
                    date)
                # print np.max(self.var.PotassiumPrice)

    def dynamic(self):
        self.set_fertiliser_price()

class CropPrice(object):    
    def __init__(self, var, configuration):
        self.var = var
        self.CropPriceFileNC = str(configuration['cropPriceInputFile'])
        self.CropPriceVarName = str(configuration['cropPriceVariableName'])
        
    def initial(self):
        self.var.CropPrice = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))

    def set_crop_price(self):
        """Function to read crop area"""
        start_of_model_run = (self.var._modelTime.timeStepPCR == 1)
        start_of_year = (self.var._modelTime.doy == 1)
        if start_of_model_run or start_of_year:
            if not self.CropPriceFileNC == "None":
                date = datetime.datetime(self.var._modelTime.year, 1, 1, 0, 0, 0)
                crop_price = vos.netcdf2PCRobjClone(
                    self.CropPriceFileNC,
                    self.CropPriceVarName,
                    date,
                    useDoy = None,
                    cloneMapFileName = self.var.cloneMap,
                    LatitudeLongitude = True)
                crop_price = np.reshape(
                    crop_price[self.var.landmask_crop],
                    (self.var.nCrop, self.var.nCell))
                crop_price = np.broadcast_to(
                    crop_price[None,:,:],
                    (self.var.nFarm,
                     self.var.nCrop,
                     self.var.nCell)).copy()
                self.var.CropPrice = crop_price
                                            
    def dynamic(self):
        self.set_crop_price()

class PriceData(object):    
    def __init__(self, var, configuration):
        self.var = var
        self.fertiliser_price_module = FertiliserPrice(var, configuration)
        self.crop_price_module = CropPrice(var, configuration)
        
    def initial(self):
        self.fertiliser_price_module.initial()
        self.crop_price_module.initial()

    def dynamic(self):
        self.fertiliser_price_module.dynamic()
        self.crop_price_module.dynamic()
