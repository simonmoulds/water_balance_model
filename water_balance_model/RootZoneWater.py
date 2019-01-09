#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np

import logging
logger = logging.getLogger(__name__)

class RootZoneWater(object):
    def __init__(self, RootZoneWater_variable):
        self.var = RootZoneWater_variable

    def initial(self):
        arr_zeros = np.zeros((1, 1, self.var.nLayer, self.var.nCell))
        self.var.readily_available_water = arr_zeros.copy()
        self.var.total_available_water = arr_zeros.copy()
        self.var.critical_available_water = arr_zeros.copy()
        self.update_root_zone_water_content()
        
    def update_root_zone_water_content(self):
        self.var.wc = self.var.th * self.var.root_depth

    def compute_root_zone_depletion_factor(self):
        # TODO: get root zone depletion factor, perhaps using
        # crop group number method, if this can be clarified
        # by Peter Burek @ IIASA

        # NB this will be different for natural vegetation and
        # irrigated crops
        
        # CWATM, soil.py, lines 185-206
        self.var.root_zone_depletion_factor = np.ones((1, 1, self.var.nCell))  # FIXME

    def compute_critical_water_content(self):
        # CWATM, soil.py, lines 210-212
        self.compute_root_zone_depletion_factor()
        p = np.broadcast_to(
            self.var.root_zone_depletion_factor[:,:,None,:],
            (1, 1, self.var.nLayer, self.var.nCell))        
        self.var.wc_crit = ((1 - p) * (self.var.wc_fc - self.var.wc_wp)) + self.var.wc_wp
        
    def compute_readily_available_water(self):
        self.update_root_zone_water_content()
        self.var.readily_available_water = (
            np.maximum(0., self.var.wc - self.var.wc_wp)
            * self.var.root_depth)

    def compute_total_available_water(self, nlayer=2):
        self.var.total_available_water = (
            np.maximum(0., self.var.wc_fc - self.var.wc_wp)
            * self.var.root_depth)
        
    def dynamic(self):
        self.update_root_zone_water_content()
