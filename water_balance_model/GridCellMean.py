#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import calendar
import numpy as np
import VirtualOS as vos

import logging
logger = logging.getLogger(__name__)

# def farm_to_grid(arr, farm_cat, cats, farm_cat_area):
def farm_to_grid(arr, farm_cat, cats, farm_cat_area):
    """Function to compute grid cell mean from 
    farm-level values
    """
    # First, take average value across all farms within a
    # given category. I *DON'T THINK* we should weight by
    # farm area.
    arr_list = []
    for cat in cats:
        arr_mask = np.ma.masked_array(arr, mask=farm_cat!=cat)
        arr_mask = np.ma.average(arr_mask, axis=0, weights=None)
        arr_list.append(arr_mask)

    # Second, take average value across categories, weighting
    # according to the total area of each category within
    # the grid square. Use np.ma.average because this is robust
    # against weight values which sum to zero. 
    arr_ave = np.ma.average(
        np.stack(arr_list, axis=0),
        # arr,
        axis=0,
        weights=farm_cat_area).filled(0)
    return arr_ave

class GridCellMean(object):

    def __init__(self, GridCellMean_variable):
        self.var = GridCellMean_variable
    
    def initial(self):

        self.var.irrigation_mean = np.zeros((self.var.nCrop, self.var.nCell))
        # self.var.YieldMean = np.zeros((self.var.nCrop, self.var.nCell))
        # self.var.ProductionMean = np.zeros((self.var.nCrop, self.var.nCell))
        # self.var.RechargeVolMean = np.zeros((self.var.nCell))
        
        self.var.FarmCategoryCrop = np.broadcast_to(
            self.var.farm_category[:,None,:],
            (self.var.nFarm, self.var.nCrop, self.var.nCell))  # FIXME
        
        self.var.FarmCategoryAreaCrop = np.broadcast_to(
            self.var.FarmCategoryArea[:,None,:],
            (self.var.nFarmSizeCategory, self.var.nCrop, self.var.nCell))
    
    def dynamic(self):
        self.var.irrigation_mean = farm_to_grid(
            self.var.irrigation,
            self.var.FarmCategoryCrop,
            [1,2,3,4,5],
            self.var.FarmCategoryAreaCrop)

        # self.var.YieldMean = farm_to_grid(
        #     self.var.Y,
        #     self.var.FarmCategoryCrop,
        #     [1,2,3,4,5],
        #     self.var.FarmCategoryAreaCrop)

        # self.var.ProductionMean = self.var.YieldMean * (self.var.CurrentCropArea / 10000.)
        
        # self.var.RechargeVolMean = farm_to_grid(
        #     self.var.RechargeVol,
        #     self.var.FarmCategory,
        #     [1,2,3,4,5],
        #     self.var.FarmCategoryArea)
            
