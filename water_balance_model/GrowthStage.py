#!/usr/bin/env python
# -*- coding: utf-8 -*-

# AquaCrop crop growth model

import numpy as np

import logging
logger = logging.getLogger(__name__)

class GrowthStage(object):
    def __init__(self, GrowthStage_variable):
        self.var = GrowthStage_variable

    def initial(self):
        self.var.GrowthStage = np.zeros((self.var.nFarm, self.var.nLC, self.var.nCell))

    def reset_initial_conditions(self):
        self.var.GrowthStage[self.var.GrowingSeasonDayOne] = 0

    def dynamic(self):
        if np.any(self.var.GrowingSeasonDayOne):
            self.reset_initial_conditions()

        L_day = np.stack((self.var.L_ini_day,
                          self.var.L_dev_day,
                          self.var.L_mid_day,
                          self.var.L_late_day), axis=0)        
        L_day = np.cumsum(L_day, axis=0)

        cond1 = (self.var.GrowingSeasonIndex & (self.var.DAP < L_day[0,:]))
        cond2 = (self.var.GrowingSeasonIndex & (self.var.DAP >= L_day[0,:]) & (self.var.DAP < L_day[1,:]))
        cond3 = (self.var.GrowingSeasonIndex & (self.var.DAP >= L_day[1,:]) & (self.var.DAP < L_day[2,:]))
        cond4 = (self.var.GrowingSeasonIndex & (self.var.DAP >= L_day[2,:]))
        self.var.GrowthStage[cond1] = 1
        self.var.GrowthStage[cond2] = 2
        self.var.GrowthStage[cond3] = 3
        self.var.GrowthStage[cond4] = 4
        self.var.GrowthStage[np.logical_not(self.var.GrowingSeasonIndex)] = 0
        
