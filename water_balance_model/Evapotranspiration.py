#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np

import logging
logger = logging.getLogger(__name__)

class PotentialEvapotranspiration(object):
    def __init__(self, PotentialEvapotranspiration_variable):
        self.var = PotentialEvapotranspiration_variable

    def initial(self):
        arr_zeros = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))
        self.var.Epot = np.copy(arr_zeros)
        self.var.Tpot = np.copy(arr_zeros)
        self.var.ETpot = np.copy(arr_zeros)

    def compute_potential_soil_evaporation(self):

        # CALIBRATION
        self.var.cropCorrect = 1.

        # CWATM, evaporation.py, lines 48-53
        potential_bare_soil_evap = (
            self.var.cropCorrect
            * self.var.minCropKc
            * self.var.meteo.referencePotET)
        self.var.snow_evap = np.minimum(
            self.var.snow_melt,
            potential_bare_soil_evap)
        self.var.snow_melt -= self.var.snow_evap
        self.var.Epot = potential_bare_soil_evap - self.var.snow_evap

    def compute_potential_evapotranspiration(self):
        # CWATM, evaporation.py, line 75
        self.var.ETpot = self.var.cropCorrect * self.var.cropCoefficient * self.var.meteo.referencePotET

    def compute_potential_transpiration(self):
        # CWATM, evaporation.py, line 80
        self.var.Tpot = self.var.ETpot - self.var.Epot - self.var.snow_evap
        self.var.Tpot = self.var.Tpot.clip(0, None)
        
    def dynamic(self):
        self.compute_potential_soil_evaporation()
        self.compute_potential_evapotranspiration()
        self.compute_potential_transpiration()

class ActualEvapotranspiration(object):
    def __init__(self, ActualEvapotranspiration_variable):
        self.var = ActualEvapotranspiration_variable

    def initial(self):
        arr_zeros = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))
        self.var.Eact = np.copy(arr_zeros)
        self.var.Tact = np.copy(arr_zeros)
        self.var.ETact = np.copy(arr_zeros)
        self.var.EWact = np.copy(arr_zeros)
        # self.var.snow_evap = np.copy(arr_zeros)
        
    def compute_open_water_evaporation(self):
        # CWATM, soil.py, lines 149-171
        # self.var.SurfaceStorage is currently updated in Infiltration.py
        # EWact is equivalent to openWaterEvap in CWATM
        self.var.EWact = np.minimum(np.maximum(0., self.var.SurfaceStorage), self.var.meteo.EWref)
        self.var.SurfaceStorage -= self.var.EWact
        # self.var.Infl = ... # CWATM, soil.py, line 162
        self.var.Epot = np.maximum(0., self.var.Epot - self.var.EWact)
        
    def compute_actual_transpiration(self):

        # CWATM, soil.py, lines 210-251
        
        # compute total and readily available water in the top two soil layers
        # self.var.root_zone_water_module.dynamic()
        
        # transpiration reduction factor, CWATM, soil.py, lines
        Ks = np.divide(
            (self.var.wc - self.var.wc_wp),
            (self.var.wc_crit - self.var.wc_wp),
            out=np.zeros_like(self.var.wc_wp),
            where=self.var.wc_crit>self.var.wc_wp)
        Ks = np.maximum(np.minimum(1., Ks), 0.)
        Ks *= self.var.root_fraction
        Ks_sum = np.sum(Ks, axis=2)
        Ks_sum = Ks_sum.clip(0., 1.)
        TactMax = self.var.Tpot * Ks_sum
        TactMax = np.where(self.var.frost_index > self.var.frost_index_threshold, 0., TactMax)
        Tact = (
            np.broadcast_to(
                TactMax[:,:,None,:],
                (self.var.nFarm, self.var.nCrop, self.var.nLayer, self.var.nCell))
            * self.var.root_fraction)
        Tact = Tact.clip(None, self.var.wc - self.var.wc_wp)
        Tact = Tact.clip(0., None)
        self.var.Tact_comp = Tact.copy()
        self.var.Tact = np.sum(self.var.Tact_comp, axis=2)  # sum along compartment axis        
        self.var.wc -= self.var.Tact_comp
        self.var.th -= np.divide(self.var.Tact_comp, self.var.root_depth * 1000)

    def compute_actual_soil_evaporation(self):
        # CWATM, soil.py, lines 252-260
        self.var.Eact = np.minimum(self.var.Epot, np.maximum(0., self.var.wc[...,0,:] - self.var.wc_res[...,0,:]))
        self.var.Eact = np.where(self.var.frost_index > self.var.frost_index_threshold, 0., self.var.Eact)
        self.var.Eact[self.var.SurfaceStorage > 0.] = 0  # lines 257-258
        self.var.wc[...,0,:] -= self.var.Eact
        self.var.th[...,0,:] -= np.divide(
            self.var.Eact,
            self.var.root_depth[...,0,:],
            out=np.zeros_like(self.var.Eact))

    def dynamic(self):
        # # self.compute_root_zone_water()
        # self.var.root_zone_water_module.update_root_zone_water_content()
        # self.var.root_zone_water_module.compute_critical_water_content()
        # # self.compute_root_zone_water()
        
        self.compute_open_water_evaporation()  # TODO: is this is the right place? where is openWaterEvap computed in CWATM? SurfaceStorage not yet updated for current time step
        self.compute_actual_transpiration()
        self.compute_actual_soil_evaporation()

        # CWATM, soil.py, lines 525-531
        self.var.ETact = self.var.Eact + self.var.Tact + self.var.EWact
        
        self.var.ETact += self.var.interception_evaporation + self.var.snow_evap * 0.2  # CHECK
        
        self.var.ETpot = self.var.ETpot.clip(self.var.ETact, None)        
        
class Evapotranspiration(object):
    def __init__(self, Evapotranspiration_variable):
        self.var = Evapotranspiration_variable
        self.potential_et_module = PotentialEvapotranspiration(Evapotranspiration_variable)
        self.actual_et_module = ActualEvapotranspiration(Evapotranspiration_variable)
        
    def initial(self):
        self.potential_et_module.initial()
        self.actual_et_module.initial()

    def dynamic(self):
        self.potential_et_module.dynamic()
        self.actual_et_module.dynamic()

class EvaporationSealed(Evapotranspiration):
    """Class to represent Evaporation from sealed land. It inherits
    from Evapotranspiration so that the variables adjusted by 
    this class are initialized to zero.    
    """
    def compute_open_water_evaporation(self, mult):
        self.var.EWact = np.minimum(
            mult * self.var.meteo.EWref,
            self.var.water_available_for_infiltration)
    def update_actual_evapotranspiration(self):
        self.var.ETact += self.var.EWact        
    def dynamic(self):
        self.compute_open_water_evaporation(1.)
        self.update_actual_evapotranspiration()
        
class EvaporationWater(EvaporationSealed):
    """Class to represent Evaporation from water. It inherits
    from Evapotranspiration so that the variables adjusted by 
    this class are initialized to zero.    
    """
    def dynamic(self):
        self.compute_open_water_evaporation(0.2)
        self.update_actual_evapotranspiration()
