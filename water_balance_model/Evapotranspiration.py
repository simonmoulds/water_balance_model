#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np

import logging
logger = logging.getLogger(__name__)

class PotentialEvapotranspiration(object):
    def __init__(self, PotentialEvapotranspiration_variable):
        self.var = PotentialEvapotranspiration_variable

    def initial(self):
        arr_zeros = np.zeros((self.var.nLC, self.var.nCell))
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
        self.var.Tpot.clip(0, None)
        
    def dynamic(self):
        self.compute_potential_soil_evaporation()
        self.compute_potential_evapotranspiration()
        self.compute_potential_transpiration()

class ActualEvapotranspiration(object):
    def __init__(self, ActualEvapotranspiration_variable):
        self.var = ActualEvapotranspiration_variable

    def initial(self):
        arr_zeros = np.zeros((1, 1, self.var.nCell))
        self.var.Eact = np.copy(arr_zeros)
        self.var.Tact = np.copy(arr_zeros)
        self.var.ETact = np.copy(arr_zeros)
        self.var.snow_evap = np.copy(arr_zeros)

    def compute_root_zone_water(self):        
        # Water content in each soil compartment, in mm
        self.var.wc = 1000 * self.var.th * self.var.root_depth

    def compute_root_zone_depletion_factor(self):
        # TODO: get root zone depletion factor, perhaps using
        # crop group number method, if this can be clarified
        # by Peter Burek @ IIASA

        # CWATM, soil.py, lines 185-206
        self.var.root_zone_depletion_factor = np.ones((1, 1, self.var.nCell))  # FIXME

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
        
        # broadcast crop depletion factor to compartments
        p = np.broadcast_to(
            self.var.root_zone_depletion_factor[:,:,None,:],
            (1, 1, self.var.nLayer, self.var.nCell))
        
        # work out critical water content (mm)

        # CWATM, soil.py, lines 210-212        
        wCrit = ((1 - p) * (self.var.wc_fc - self.var.wc_wp)) + self.var.wc_wp

        # transpiration reduction factor, CWATM, soil.py, lines
        Ks = np.divide(
            (self.var.wc - self.var.wc_wp),
            (wCrit - self.var.wc_wp),
            out=np.zeros_like(self.var.wc_wp),
            where=wCrit>self.var.wc_wp)
        Ks = np.maximum(np.minimum(1., Ks), 0.)
        Ks *= self.var.root_fraction
        Ks_sum = np.sum(Ks, axis=2)
        Ks_sum.clip(0., 1.)
        TactMax = self.var.Tpot * Ks_sum

        self.var.FrostIndex = np.zeros((1, 1, self.var.nCell))  # FIXME
        self.var.FrostIndexThreshold = np.ones((1, 1, self.var.nCell)) * 999.  # FIXME - currently just a large number

        TactMax = np.where(self.var.FrostIndex > self.var.FrostIndexThreshold, 0., TactMax)
        Tact = (
            np.broadcast_to(
                TactMax[:,:,None,:],
                (1, 1, self.var.nLayer, self.var.nCell))
            * self.var.root_fraction)
        Tact.clip(None, self.var.wc - self.var.wc_wp)
        Tact.clip(0., None)
        self.var.Tact_comp = Tact.copy()
        self.var.Tact = np.sum(self.var.Tact_comp, axis=2)  # sum along compartment axis
        
        self.var.wc -= self.var.Tact_comp
        self.var.th -= np.divide(self.var.Tact_comp, self.var.root_depth * 1000)

    def compute_actual_soil_evaporation(self):
        # CWATM, soil.py, lines 252-260
        self.var.Eact = np.minimum(self.var.Epot, np.maximum(0., self.var.wc[...,0,:] - self.var.wc_res[...,0,:]))
        self.var.Eact = np.where(self.var.FrostIndex > self.var.FrostIndexThreshold, 0., self.var.Eact)
        self.var.Eact[self.var.SurfaceStorage > 0.] = 0  # lines 257-258
        self.var.wc[...,0,:] -= self.var.Eact
        self.var.th[...,0,:] -= np.divide(
            self.var.Eact,
            self.var.root_depth[...,0,:] * 1000,
            out=np.zeros_like(self.var.Eact))

    def dynamic(self):
        self.compute_root_zone_water()
        self.compute_root_zone_depletion_factor()
        # self.compute_root_zone_water()
        self.compute_open_water_evaporation()  # TODO: is this is the right place? where is openWaterEvap computed in CWATM? SurfaceStorage not yet updated for current time step
        self.compute_actual_transpiration()
        self.compute_actual_soil_evaporation()

        # CWATM, soil.py, lines 525-531
        self.var.ETact = self.var.Eact + self.var.Tact + self.var.EWact
        self.var.ETpot.clip(self.var.ETact, None)
        
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
    def compute_runoff(self):
        self.var.Runoff = (
            self.var.water_available_for_infiltration
            - self.var.meteo.EWref)
    def update_actual_evapotranspiration(self):
        self.var.ETact += self.var.EWact        
    def dynamic(self):
        self.compute_open_water_evaporation(1.)
        self.compute_runoff()
        self.update_actual_evapotranspiration()
        
class EvaporationWater(EvaporationSealed):
    """Class to represent Evaporation from water. It inherits
    from Evapotranspiration so that the variables adjusted by 
    this class are initialized to zero.    
    """
    def dynamic(self):
        self.compute_open_water_evaporation(0.2)
        self.compute_runoff()
        self.update_actual_evapotranspiration()
