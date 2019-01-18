#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np

import logging
logger = logging.getLogger(__name__)

class Interception(object):

    def __init__(self, Interception_variable):
        self.var = Interception_variable
        
    def initial(self):
        arr_zeros = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))  # make global parameter
        self.var.interception_storage = arr_zeros.copy()
        self.var.water_available_for_infiltration = arr_zeros.copy()
        self.var.interception_evaporation = arr_zeros.copy()
        
    def compute_water_available_for_infiltration(self):
        # CWATM, interception.py        
        throughfall = np.maximum(
            0.,
            self.var.rain
            + self.var.interception_storage
            - self.var.interception_capacity)
        self.var.interception_storage += (self.var.rain - throughfall)
        self.var.water_available_for_infiltration = np.maximum(0., throughfall + self.var.snow_melt)

    def compute_interception_evaporation_from_vegetation(self):
        # vegetated land covers:
        mult = np.divide(
            self.var.interception_storage,
            self.var.interception_capacity) ** (2. / 3.)
        self.var.interception_evaporation = np.minimum(
            self.var.interception_storage,
            self.var.Tpot * mult)

    def compute_interception_evaporation_from_sealed_land(self):
        self.var.interception_evaporation = np.maximum(
            np.minimum(
                self.var.interception_storage,
                self.var.meteo.EWref), 0.)

    def update_interception_storage(self):
        self.var.interception_storage -= self.var.interception_evaporation

    def update_potential_transpiration(self):
        self.var.Tpot = np.maximum(
            0.,
            self.var.Tpot
            - self.var.interception_evaporation)

    # def update_actual_evapotranspiration(self):
    #     # update actual evaporation - TODO: find a way to put this Evapotranspiration class
    #     self.var.ETact += self.var.interception_evaporation + self.var.snow_evap * 0.2
        
    def dynamic(self):

        self.compute_water_available_for_infiltration()
        self.compute_interception_evaporation_from_vegetation()
        self.update_interception_storage()
        self.update_potential_transpiration()
        # self.update_actual_evapotranspiration()

class InterceptionSealed(Interception):
    def dynamic(self):
        self.compute_water_available_for_infiltration()
        self.compute_interception_evaporation_from_sealed_land()
        self.update_interception_storage()
        # self.update_actual_evapotranspiration()

class InterceptionWater(InterceptionSealed):
    pass
