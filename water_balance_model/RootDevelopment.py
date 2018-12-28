#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np

import logging
logger = logging.getLogger(__name__)

class RootDevelopment(object):
    def __init__(self, RootDevelopment_variable):
        self.var = RootDevelopment_variable

    def initial(self):
        self.var.Zroot = self.var.Zmin

    def dynamic(self):
        self.var.Zroot[self.var.GrowingSeasonIndex] = self.var.Zmin[self.var.GrowingSeasonIndex]
        self.var.Zroot[np.logical_not(self.var.GrowingSeasonIndex)] = 1.  # Global Crop Water Model
