#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np

import logging
logger = logging.getLogger(__name__)

class Infiltration(object):
    """Class to infiltrate incoming water (rainfall and irrigation)"""
    
    def __init__(self, Infiltration_variable):
        self.var = Infiltration_variable

    def initial(self):
        arr_zeros = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))
        self.var.potential_infiltration = arr_zeros.copy()
        self.var.infiltration = arr_zeros.copy()
        self.var.direct_runoff = arr_zeros.copy()
        self.var.preferential_flow = arr_zeros.copy()

    def reset_initial_conditions(self):
        pass

    def compute_infiltration_capacity(self):
        # CWATM, soil.py, lines 267-287
        soil_water_storage = self.var.wc[...,0,:] + self.var.wc[...,1,:]
        soil_water_storage_capacity = self.var.wc_sat[...,0,:] + self.var.wc_sat[...,1,:]
        self.var.relative_saturation = soil_water_storage / soil_water_storage_capacity
        saturated_area_fraction = 1. - (1. - self.var.relative_saturation) ** self.var.arno_beta
        saturated_area_fraction = saturated_area_fraction.clip(0, 1)
        store = soil_water_storage_capacity / (self.var.arno_beta + 1.)
        potential_beta = (self.var.arno_beta + 1.) / self.var.arno_beta
        self.var.potential_infiltration = store - store * (1. - (1. - saturated_area_fraction) ** potential_beta)
        
        # additionally, limit by saturated hydraulic conductivity of top layer        
        self.var.potential_infiltration = self.var.potential_infiltration.clip(None, self.var.ksat[...,0,:])

    def compute_preferential_flow(self):
        # CWATM, soil.py, lines 295-300

        self.include_preferential_flow = False
        # CALIBRATION - TODO
        self.var.cPrefFlow = 0.        
        if self.include_preferential_flow:
            self.var.preferential_flow = (
                self.var.water_available_for_infiltration
                * self.var.relative_saturation
                ** self.var.cPrefFlow)            
            self.var.preferential_flow[self.var.frost_index > self.var.frost_index_threshold] = 0.

    def dynamic(self):
        self.compute_infiltration_capacity()
        self.compute_preferential_flow()

        ToStore = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))
        RunoffIni = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))
        InflTot = (
            self.var.water_available_for_infiltration
            + self.var.SurfaceStorage)

        # Infiltration limited by saturated hydraulic conductivity of surface
        # soil layer; additional water ponds on surface
        ksat_top = self.var.ksat[:,:,0,:]
        cond1 = (self.var.Bunds == 1) & (self.var.zBund > 0.001)
        cond11 = (cond1 & (InflTot > 0))
        cond111 = (cond11 & (InflTot > self.var.potential_infiltration))
        ToStore[cond111] = self.var.potential_infiltration[cond111]
        self.var.SurfaceStorage[cond111] = (InflTot - self.var.potential_infiltration)[cond111]

        # Otherwise all water infiltrates and surface storage becomes zero
        cond112 = (cond11 & np.logical_not(cond111))
        ToStore[cond112] = InflTot[cond112]
        self.var.SurfaceStorage[cond112] = 0

        # Calculate additional RunoffIni if water overtops bunds
        cond113 = (cond11 & (self.var.SurfaceStorage > (self.var.zBund * 1000.)))
        RunoffIni[cond113] = (self.var.SurfaceStorage - (self.var.zBund * 1000.))[cond113]
        self.var.SurfaceStorage[cond113] = (self.var.zBund * 1000.)[cond113]

        # Otherwise excess water does not overtop bunds and there is no RunoffIni
        cond114 = (cond11 & np.logical_not(cond113))
        RunoffIni[cond114] = 0.

        # If total infiltration is zero then there is no storage or RunoffIni
        cond12 = (cond1 & np.logical_not(cond11))
        ToStore[cond12] = 0.
        RunoffIni[cond12] = 0.
        
        # If there are no bunds then infiltration is divided between RunoffIni
        # and infiltration according to saturated conductivity of surface
        # layer
        cond2 = (self.var.Bunds == 0)
        cond21 = (cond2 & (self.var.water_available_for_infiltration > self.var.potential_infiltration))

        ToStore[cond21] = self.var.potential_infiltration[cond21]
        RunoffIni[cond21] = (self.var.water_available_for_infiltration - self.var.potential_infiltration)[cond21]
        cond22 = (cond2 & np.logical_not(cond21))
        ToStore[cond22] = self.var.water_available_for_infiltration[cond22]
        RunoffIni[cond22] = 0

        self.var.infiltration = ToStore.copy()
        self.var.direct_runoff = RunoffIni.copy()

        # infiltration to top soil layer; if this is full then
        # infiltrate to second soil layer
        self.var.wc[...,0,:] += ToStore
        saturation_excess = self.var.wc[...,0,:] - self.var.wc_sat[...,0,:]
        saturation_excess = saturation_excess.clip(0., None)
        self.var.wc[...,1,:] += saturation_excess
        self.var.wc[...,0,:] -= saturation_excess
        
        self.var.th[...,0,:] = self.var.wc[...,0,:] / self.var.root_depth[...,0,:]
        self.var.th[...,1,:] = self.var.wc[...,1,:] / self.var.root_depth[...,1,:]
        
class InfiltrationSealed(Infiltration):
    """Class to represent infiltration for sealed area

    N.B. We could eventually adapt this class to represent 
    drainage to a sewer network, e.g.
    """
    def dynamic(self):
        self.var.direct_runoff = self.var.water_available_for_infiltration - self.var.EWact

class InfiltrationWater(InfiltrationSealed):
    """Class to represent infiltration for water body"""
