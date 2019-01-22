#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import numexpr as ne

import logging
logger = logging.getLogger(__name__)

class Drainage(object):
    def __init__(self, Drainage_variable):
        self.var = Drainage_variable

        # TODO: percolation impedance
        self.var.percolation_impedance = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))

    def initial(self):
        self.var.perc1to2 = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))
        self.var.perc2to3 = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))
        self.var.perc3toGW = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))
        self.var.interflow = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))
        self.var.deep_percolation = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))

    def dynamic(self):

        available_water = np.maximum(0., self.var.wc - self.var.wc_res)
        storage_capacity = self.var.wc_sat - self.var.wc
        sat_term = np.divide(
            available_water,
            self.var.wc_range,
            out=np.zeros_like(self.var.wc_range),
            where=self.var.wc_range>0)
        sat_term = sat_term.clip(0., 1.)
        k = (
            self.var.ksat
            * np.sqrt(sat_term)
            * np.square(
                1.
                - (1. - sat_term ** self.var.van_genuchten_inv_m)
                ** self.var.van_genuchten_m))
        
        no_sub_steps = 3
        dtsub = 1. / no_sub_steps

        # Copy current value of W1 and W2 to temporary variables,
        # because computed fluxes may need correction for storage
        # capacity of subsoil and in case soil is frozen (after loop)        
        wc_temp = self.var.wc.copy()
        
        # Initialize top- to subsoil flux (accumulated value for all sub-steps)
        # Initialize fluxes out of subsoil (accumulated value for all sub-steps)
        self.var.perc1to2 = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))
        self.var.perc2to3 = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))
        self.var.perc3toGW = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))

        # Start iterating
        for i in xrange(no_sub_steps):            
            if i > 0:           # because we have only just calculated k
                available_water = np.maximum(0., wc_temp - self.var.wc_res)
                sat_term = available_water / self.var.wc_range
                sat_term = sat_term.clip(0., 1.)
                k = (
                    self.var.ksat
                    * np.sqrt(sat_term)
                    * np.square(
                        1.
                        - (1. - sat_term ** self.var.van_genuchten_inv_m)
                        ** self.var.van_genuchten_m))

            # flux from topsoil to subsoil
            subperc1to2 = np.minimum(available_water[...,0,:], np.minimum(k[...,0,:] * dtsub, storage_capacity[...,1,:]))
            subperc2to3 = np.minimum(available_water[...,1,:], np.minimum(k[...,1,:] * dtsub, storage_capacity[...,2,:]))
            subperc3toGW = np.minimum(available_water[...,2,:], np.minimum(k[...,2,:] * dtsub, available_water[...,2,:]))
            
            available_water[...,0,:] -= subperc1to2
            available_water[...,1,:] += subperc1to2 - subperc2to3
            available_water[...,2,:] += subperc2to3 - subperc3toGW
            
            wc_temp = available_water + self.var.wc_res
            storage_capacity = self.var.wc_sat - wc_temp

            self.var.perc1to2 += subperc1to2
            self.var.perc2to3 += subperc2to3
            self.var.perc3toGW += subperc3toGW

        # When the soil is frozen (frostindex larger than threshold), no perc1 and 2
        self.var.perc1to2[self.var.frost_index > self.var.frost_index_threshold] = 0
        self.var.perc2to3[self.var.frost_index > self.var.frost_index_threshold] = 0

        # update soil moisture
        self.var.wc[...,0,:] -= self.var.perc1to2
        self.var.wc[...,1,:] += self.var.perc1to2 - self.var.perc2to3 
        self.var.wc[...,2,:] += self.var.perc2to3 - self.var.perc3toGW

        # compute the amount of water that could not infiltrate and add this water to the surface runoff
        excess = np.maximum(self.var.wc[...,0,:] - self.var.wc_sat[...,0,:], 0.)
        self.var.infiltration -= excess
        self.var.direct_runoff += excess        

        # CWATM, soil.py, lines 540-542
        recharge_or_preferential_flow = self.var.perc3toGW + self.var.preferential_flow
        self.var.interflow = self.var.percolation_impedance * recharge_or_preferential_flow
        self.var.deep_percolation = (
            (1 - self.var.percolation_impedance)
            * recharge_or_preferential_flow
            - self.var.capillary_rise_from_gw)
        
        # update water content (what about excess water?)
        self.var.wc[...,0,:] = np.minimum(self.var.wc[...,0,:], self.var.wc_sat[...,0,:])
        self.var.th = self.var.wc / self.var.root_depth

