#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np

import logging
logger = logging.getLogger(__name__)

class RootZoneWater(object):
    def __init__(self, RootZoneWater_variable):
        self.var = RootZoneWater_variable

    def initial(self):
        arr_zeros = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nLayer, self.var.nCell))
        self.var.readily_available_water = arr_zeros.copy()
        self.var.total_available_water = arr_zeros.copy()
        self.var.wc_crit = arr_zeros.copy()
        self.update_root_zone_water_content()
        
    def update_root_zone_water_content(self):
        self.var.wc = self.var.th * self.var.root_depth

    def compute_root_zone_depletion_factor(self):
        ETpot = np.minimum(0.1 * (self.var.ETpot * 1000.), 1.)
        p = 1. / (0.76 + 1.5 * ETpot) - 0.4
        p += (ETpot - 0.6) / 4.
        p = p.clip(0., 1.)
        self.var.root_zone_depletion_factor = p.copy()
        self.var.root_zone_depletion_factor = np.broadcast_to(
            self.var.root_zone_depletion_factor[:,:,None,:],
            (self.var.nFarm, self.var.nCrop, self.var.nLayer, self.var.nCell))
        
    def compute_critical_water_content(self):
        # CWATM, soil.py, lines 210-212
        self.compute_root_zone_depletion_factor()
        self.var.wc_crit = (
            ((1. - self.var.root_zone_depletion_factor)
             * (self.var.wc_fc - self.var.wc_wp))
            + self.var.wc_wp)

    def compute_readily_available_water(self):
        self.update_root_zone_water_content()
        self.var.readily_available_water = (
            np.maximum(0., self.var.wc - self.var.wc_wp)
        )        
        # self.var.readily_available_water = (
        #     np.maximum(0., self.var.wc - self.var.wc_wp)
        #     * self.var.root_depth)

    def compute_total_available_water(self):
        self.var.total_available_water = (
            np.maximum(0., self.var.wc_fc - self.var.wc_wp)
        )
        # self.var.total_available_water = (
        #     np.maximum(0., self.var.wc_fc - self.var.wc_wp)
        #     * self.var.root_depth)
        
    def dynamic(self):
        self.update_root_zone_water_content()
        self.compute_critical_water_content()
        self.compute_readily_available_water()
        self.compute_total_available_water()
        # print 'raw :',self.var.readily_available_water[0,0,:,0]
        # print 'taw :',self.var.total_available_water[0,0,:,0]
        # print 'crit:',self.var.critical_available_water[0,0,:,0]

class RootZoneWaterNaturalVegetation(RootZoneWater):
    
    def compute_root_zone_depletion_factor(self):
        # CWATM, soil.py, lines 182-206
        
        # CWATM, soil.py, line 183: "to avoid a strange
        # behaviour of the p-formula's, ETref is set to a
        # maximum of 10mm/day"
        ETpot = np.minimum(0.1 * (self.var.ETpot * 1000.), 1.)
        
        p = 1. / (0.76 + 1.5 * ETpot) - 0.1 * (5. - self.var.crop_group_number)
        p = np.where(
            self.var.crop_group_number <= 2.5,
            p + (ETpot - 0.6)
             / (self.var.crop_group_number
                * (self.var.crop_group_number + 3.)),
            p)
        p = p.clip(0., 1.)
        self.var.root_zone_depletion_factor = p.copy()
        self.var.root_zone_depletion_factor = np.broadcast_to(
            self.var.root_zone_depletion_factor[:,:,None,:],
            (self.var.nFarm, self.var.nCrop, self.var.nLayer, self.var.nCell))
    
class RootZoneWaterIrrigatedLand(RootZoneWater):
    def compute_root_zone_depletion_factor(self):
        # do not use crop group number for irrigated crops,
        # because we assume that irrigated crops have low
        # adaptation to dry climate
        ETpot = np.minimum(0.1 * (self.var.ETpot * 1000.), 1.)
        p = 1. / (0.76 + 1.5 * ETpot) - 0.4
        p += (ETpot - 0.6) / 4.
        p = p.clip(0., 1.)
        self.var.root_zone_depletion_factor = p.copy()
        self.var.root_zone_depletion_factor = np.broadcast_to(
            self.var.root_zone_depletion_factor[:,:,None,:],
            (self.var.nFarm, self.var.nCrop, self.var.nLayer, self.var.nCell))
