#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np

import hydro_model_builder.VirtualOS as vos

import logging
logger = logging.getLogger(__name__)

class Irrigation(object):
    """Class to represent irrigation activities"""

    def __init__(self, Irrigation_variable):
        self.var = Irrigation_variable

    def initial(self):
        arr_zeros = np.zeros((self.var.nFarm, self.var.nLC, self.var.nCell))
        self.var.irrigation = np.copy(arr_zeros)
    #     self.var.irrigation_cumulative = np.copy(arr_zeros)

    # def reset_initial_conditions(self):
    #     self.var.irrigation_cumulative[self.var.GrowingSeasonDayOne] = 0
        
    def dynamic(self):
        pass

class IrrigationNonPaddy(Irrigation):
    pass

class IrrigationPaddy(Irrigation):
    def dynamic(self):

        alpha_depletion = 1.    # see CWATM waterdemand.py, lines 129-131
        self.var.irrigation = np.where(
            self.var.cropCoefficient > 0.75,
            np.maximum(
                (alpha_depletion
                 * self.var.zBund  # check units
                 - (self.var.SurfaceStorage  # check units
                    + self.var.water_available_for_infiltration)),  # check units
                0.),
            0.)

        # CWATM: "ignore demand if less that 1m3" - but I thought irrigation was a depth?

        self.var.irrigation_efficiency = 1.  # TODO - put in input
        self.var.irrigation /= self.var.irrigation_efficiency
        self.var.water_available_for_infiltration += self.var.irrigation


class IrrigationNonPaddy(Irrigation):
    def dynamic(self):

        self.var.infiltration_module.compute_infiltration_capacity()

        # compute total and readily available water in the top two soil layers
        self.var.root_zone_water_module.compute_readily_available_water()
        self.var.root_zone_water_module.compute_total_available_water()
        self.var.root_zone_water_module.compute_critical_water_content()

        layer_index = np.array([0,1], np.int64)
        readily_available_water = np.sum(
            self.var.readily_available_water[...,layer_index,:],
            axis=2)
        total_available_water = np.sum(
            self.var.total_available_water[...,layer_index,:],
            axis=2)
        critical_available_water = np.sum(
            self.var.wc_crit[...,layer_index,:],
            axis=2)
        
        alpha_depletion = 1.
        self.var.irrigation = np.where(
            self.var.cropCoefficient > 0.2,
            np.where(
                readily_available_water < (alpha_depletion * critical_available_water),
                np.maximum(0., alpha_depletion * total_available_water),
                0.),
            0.)
        self.var.irrigation.clip(None, self.var.potential_infiltration)

        # from CWATM, waterdemand.py line 335: "ignore demand if less than 1m3" - TODO

        self.var.irrigation_efficiency = 1.  # TODO - put in input
        self.var.irrigation /= self.var.irrigation_efficiency
        self.var.water_available_for_infiltration += self.var.irrigation
