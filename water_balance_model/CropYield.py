#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import VirtualOS as vos
import logging
logger = logging.getLogger(__name__)

class CropYield(object):
    def __init__(self, var):
        self.var = var

    def initial(self):
        self.var.ETactCum = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))
        self.var.ETpotCum = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))
        self.var.Y = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))
        self.var.Production = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))        

    def update_cumulative_evapotranspiration(self):
        self.var.ETactCum[np.logical_not(self.var.GrowingSeasonIndex)] = 0
        self.var.ETpotCum[np.logical_not(self.var.GrowingSeasonIndex)] = 0            
        self.var.ETactCum[self.var.GrowingSeasonIndex] += self.var.Tact[self.var.GrowingSeasonIndex]
        self.var.ETpotCum[self.var.GrowingSeasonIndex] += self.var.Tpot[self.var.GrowingSeasonIndex]

    def update_crop_yield(self):
        cond1 = self.var._modelTime.doy == self.var.HarvestDateAdj
        ET_ratio = np.divide(
            self.var.ETactCum,
            self.var.ETpotCum,
            np.zeros_like(self.var.ETpotCum),
            where=self.var.ETpotCum>0)
        self.var.Y[cond1] = (
            (self.var.Yx
             * (1 - self.var.Ky
                * (1 - ET_ratio)))
            / 1000)[cond1]  # tonne / hectare
        self.var.Y[np.logical_not(cond1)] = 0

    def update_crop_production(self):
        self.var.Production = (
            self.var.Y
            * self.var.FarmCropArea
            / 10000.
        )
        
    def dynamic(self):
        self.update_cumulative_evapotranspiration()
        self.update_crop_yield()
        self.update_crop_production()
