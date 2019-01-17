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
        # self.var.Production = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))        

    def update_cumulative_evapotranspiration(self):
        self.var.ETactCum[self.var.GrowingSeasonDayOne] = 0
        self.var.ETpotCum[self.var.GrowingSeasonDayOne] = 0            
        self.var.ETactCum += self.var.ETact
        self.var.ETpotCum += self.var.ETpot

    def update_crop_yield(self):
        cond1 = self.var._modelTime.doy == self.var.HarvestDateAdj
        self.var.Y[cond1] = (
            (self.var.Yx
             * (1 - self.var.Ky
                * (1 - self.var.ETactCum / self.var.ETpotCum)))
            / 1000)[cond1]  # tonne
        self.var.Y[np.logical_not(cond1)] = 0
        
    def dynamic(self):
        self.update_cumulative_evapotranspiration()
        self.update_crop_yield()
        # # calculate production by multiplying yield by crop area
        # self.var.Production = self.var.Y * (self.var.CropArea / 10000.)
