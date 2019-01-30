#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
import VirtualOS as vos

import logging
logger = logging.getLogger(__name__)

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
        
