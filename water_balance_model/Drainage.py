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

        # print 'wc at the start of drainage', self.var.wc[...,:,0]
        
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
        self.var.perc1to2[self.var.FrostIndex > self.var.FrostIndexThreshold] = 0
        self.var.perc2to3[self.var.FrostIndex > self.var.FrostIndexThreshold] = 0

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
        
        # update water content
        self.var.wc[...,0,:] = np.minimum(self.var.wc[...,0,:], self.var.wc_sat[...,0,:])
        self.var.th = self.var.wc / self.var.root_depth
    

# class Drainage_old(object):
#     """Class to infiltrate incoming water"""
    
#     def __init__(self, Drainage_variable):
#         self.var = Drainage_variable

#     def initial(self):
#         # self.var.FluxOut = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nLayer, self.var.nCell))
#         self.var.deep_percolation = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))
#         self.var.Recharge = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))
#         # self.var.RechargeVol = np.zeros((self.var.nFarm, self.var.nCell))
        
#     def compute_dthdt(self, th, th_s, th_fc, th_fc_adj, tau):
#         dthdt = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))
#         cond1 = ne.evaluate("th <= th_fc_adj")
#         dthdt[cond1] = 0
#         cond2 = ne.evaluate("(~cond1) & (th >= th_s)")
#         dthdt[cond2] = ne.evaluate("tau * (th_s - th_fc)")[cond2]
#         cond3 = ne.evaluate("~(cond1 | cond2)")
#         dthdt[cond3] = ne.evaluate("tau * (th_s - th_fc) * ((exp(th - th_fc) - 1) / (exp(th_s - th_fc) - 1))")[cond3]
#         cond4 = ne.evaluate("(cond2 | cond3) & ((th - dthdt) < th_fc_adj)")
#         dthdt[cond4] = ne.evaluate("th - th_fc_adj")[cond4]
#         return dthdt
        
#     def dynamic(self):
#         """Function to redistribute stored soil water"""
#         # dims = self.var.th.shape
#         thnew = np.copy(self.var.th)
#         drainsum = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))
#         for comp in range(self.var.nComp):

#             # Calculate drainage ability of compartment ii
#             dthdt = self.compute_dthdt(self.var.th[:,:,comp,:], self.var.th_s_comp[:,:,comp,:], self.var.th_fc_comp[:,:,comp,:], self.var.th_fc_adj[:,:,comp,:], self.var.tau_comp[:,:,comp,:])

#             # Drainage from compartment ii (mm) (Line 41 in AOS_Drainage.m)
#             draincomp = dthdt * self.var.dz[comp] * 1000

#             # Check drainage ability of compartment ii against cumulative
#             # drainage from compartments above (Lines 45-52 in AOS_Drainage.m)
#             excess = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))
#             prethick = self.var.dzsum[comp] - self.var.dz[comp]
#             drainmax = dthdt * 1000 * prethick
#             drainability = (drainsum <= drainmax)

#             # Drain compartment
#             cond5 = drainability
#             thnew[:,:,comp,:][cond5] = (self.var.th[:,:,comp,:] - dthdt)[cond5]

#             # Update cumulative drainage (mm), restrict to saturated hydraulic
#             # conductivity and adjust excess drainage flow
#             drainsum[cond5] += draincomp[cond5]
#             cond51 = (cond5 & (drainsum > self.var.ksat_comp[:,:,comp,:]))
#             excess[cond51] += (drainsum - self.var.ksat_comp[:,:,comp,:])[cond51]
#             drainsum[cond51] = self.var.ksat_comp[:,:,comp,:][cond51]

#             # Calculate value of theta (thX) needed to provide a drainage
#             # ability equal to cumulative drainage (Lines 70-85 in AOS_Drainage.m)
#             cond6 = np.logical_not(drainability)
#             dthdt[cond6] = np.divide(drainsum, 1000 * prethick, out=np.zeros_like(drainsum), where=prethick!=0)[cond6]
#             thX = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))
#             cond61 = (cond6 & (dthdt <= 0))
#             thX[cond61] = self.var.th_fc_adj[:,:,comp,:][cond61]
#             cond62 = (cond6 & np.logical_not(cond61) & (self.var.tau_comp[:,:,comp,:] > 0))
#             A = (1 + ((dthdt * (np.exp(self.var.th_s_comp[:,:,comp,:] - self.var.th_fc_comp[:,:,comp,:]) - 1)) / (self.var.tau_comp[:,:,comp,:] * (self.var.th_s_comp[:,:,comp,:] - self.var.th_fc_comp[:,:,comp,:]))))
#             thX[cond62] = (self.var.th_fc_adj[:,:,comp,:] + np.log(A))[cond62]
#             thX[cond62] = np.clip(thX, self.var.th_fc_adj[:,:,comp,:], None)[cond62]
#             cond63 = (cond6 & np.logical_not(cond61 | cond62))
#             thX[cond63] = (self.var.th_s_comp[:,:,comp,:] + 0.01)[cond63]

#             # Check thX against hydraulic properties of current soil layer

#             # Increase compartment ii water content with cumulative drainage
#             cond64 = (cond6 & (thX <= self.var.th_s_comp[:,:,comp,:]))
#             thnew[:,:,comp,:][cond64] = (self.var.th[:,:,comp,:] + (drainsum / (1000 * self.var.dz[comp])))[cond64]

#             # Cumulative drainage is the drainage difference between theta_x and
#             # new theta plus drainage ability at theta_x
#             cond641 = (cond64 & (thnew[:,:,comp,:] > thX))
#             drainsum[cond641] = ((thnew[:,:,comp,:] - thX) * 1000 * self.var.dz[comp])[cond641]

#             # Calculate drainage ability for thX
#             dthdt = self.compute_dthdt(thX, self.var.th_s_comp[:,:,comp,:], self.var.th_fc_comp[:,:,comp,:], self.var.th_fc_adj[:,:,comp,:], self.var.tau_comp[:,:,comp,:])

#             # Update cumulative drainage (mm), restrict to saturated hydraulic
#             # conductivity and adjust excess drainage flow
#             drainsum[cond641] += (dthdt * 1000 * self.var.dz[comp])[cond641]
#             cond6415 = (cond641 & (drainsum > self.var.ksat_comp[:,:,comp,:]))
#             excess[cond6415] += (drainsum - self.var.ksat_comp[:,:,comp,:])[cond6415]
#             drainsum[cond6415] = self.var.ksat_comp[:,:,comp,:][cond6415]

#             # Update water content
#             thnew[:,:,comp,:][cond641] = (thX - dthdt)[cond641]

#             # Calculate drainage ability for updated water content
#             cond642 = (cond64 & np.logical_not(cond641) & (thnew[:,:,comp,:] > self.var.th_fc_adj[:,:,comp,:]))
#             dthdt = self.compute_dthdt(thnew[:,:,comp,:], self.var.th_s_comp[:,:,comp,:], self.var.th_fc_comp[:,:,comp,:], self.var.th_fc_adj[:,:,comp,:], self.var.tau_comp[:,:,comp,:])

#             # Update water content
#             thnew[:,:,comp,:][cond642] = (thnew[:,:,comp,:] - dthdt)[cond642]

#             # Update cumulative drainage (mm), restrict to saturated hydraulic
#             # conductivity and adjust excess drainage flow
#             drainsum[cond642] = (dthdt * 1000 * self.var.dz[comp])[cond642]
#             cond6425 = (cond642 & (drainsum > self.var.ksat_comp[:,:,comp,:]))
#             excess[cond6425] += (drainsum - self.var.ksat_comp[:,:,comp,:])[cond6425]
#             drainsum[cond6425] = self.var.ksat_comp[:,:,comp,:][cond6425]

#             # Otherwise, drainage is zero
#             cond643 = (cond64 & np.logical_not(cond641 | cond642))
#             drainsum[cond643] = 0

#             # Increase water content in compartment ii with cumulative
#             # drainage from above
#             cond65 = (cond6 & np.logical_not(cond64) & (thX > self.var.th_s_comp[:,:,comp,:]))
#             thnew[:,:,comp,:][cond65] = (self.var.th[:,:,comp,:] + (drainsum / (1000 * self.var.dz[comp])))[cond65]

#             # Check new water content against hydraulic properties of soil layer
#             # Lines 166-198
#             cond651 = (cond65 & (thnew[:,:,comp,:] <= self.var.th_s_comp[:,:,comp,:]))

#             # Calculate new drainage ability
#             cond6511 = (cond651 & (thnew[:,:,comp,:] > self.var.th_fc_adj[:,:,comp,:]))
#             dthdt = self.compute_dthdt(thnew[:,:,comp,:], self.var.th_s_comp[:,:,comp,:], self.var.th_fc_comp[:,:,comp,:], self.var.th_fc_adj[:,:,comp,:], self.var.tau_comp[:,:,comp,:])

#             # Update water content
#             thnew[:,:,comp,:][cond6511] -= (dthdt)[cond6511]

#             # Update cumulative drainage (mm), restrict to saturated hydraulic
#             # conductivity and adjust excess drainage flow
#             drainsum[cond6511] = (dthdt * 1000 * self.var.dz[comp])[cond6511]
#             cond65115 = (cond6511 & (drainsum > self.var.ksat_comp[:,:,comp,:]))
#             excess[cond65115] += (drainsum - self.var.ksat_comp[:,:,comp,:])[cond65115]
#             drainsum[cond65115] = self.var.ksat_comp[:,:,comp,:][cond65115]

#             cond6512 = (cond651 & (np.logical_not(cond6511)))
#             drainsum[cond6512] = 0

#             # Calculate excess drainage above saturation
#             cond652 = (cond65 & np.logical_not(cond651) & (thnew[:,:,comp,:] > self.var.th_s_comp[:,:,comp,:]))
#             excess[cond652] = ((thnew[:,:,comp,:] - self.var.th_s_comp[:,:,comp,:]) * 1000 * self.var.dz[comp])[cond652]

#             # Calculate drainage ability for updated water content
#             dthdt = self.compute_dthdt(thnew[:,:,comp,:], self.var.th_s_comp[:,:,comp,:], self.var.th_fc_comp[:,:,comp,:], self.var.th_fc_adj[:,:,comp,:], self.var.tau_comp[:,:,comp,:])

#             # Update water content
#             thnew[:,:,comp,:][cond652] = (self.var.th_s_comp[:,:,comp,:] - dthdt)[cond652]

#             # Update drainage, maximum drainage, excess drainage
#             draincomp[cond652] = (dthdt * 1000 * self.var.dz[comp])[cond652]
#             drainmax[cond652] = (dthdt * 1000 * prethick)[cond652]
#             drainmax[cond652] = np.clip(drainmax, None, excess)[cond652]
#             excess[cond652] -= drainmax[cond652]

#             # Update cumulative drainage (mm), restrict to saturated hydraulic
#             # conductivity and adjust excess drainage flow
#             drainsum[cond652] = (draincomp + drainmax)[cond652]
#             cond6525 = (cond652 & (drainsum > self.var.ksat_comp[:,:,comp,:]))
#             excess[cond6525] += (drainsum - self.var.ksat_comp[:,:,comp,:])[cond6525]
#             drainsum[cond6525] = self.var.ksat_comp[:,:,comp,:][cond6525]

#             # Store output flux from compartment ii
#             self.var.FluxOut[:,:,comp,:] = np.copy(drainsum)

#             # Redistribute excess in compartment above
#             precomp = comp + 1
#             while (np.any(excess > 0)) & (precomp != 0):

#                 # Include condition here so that it is updated
#                 cond7 = (excess > 0)

#                 # Update compartment counter
#                 precomp -= 1

#                 # Update flux from compartment
#                 if (precomp < comp):
#                     self.var.FluxOut[:,:,precomp,:][cond7] -= excess[cond7]

#                 # Increase water content to store excess
#                 thnew[:,:,precomp,:][cond7] += (excess / (1000 * self.var.dz[precomp]))[cond7]

#                 # Limit water content to saturation and adjust excess counter
#                 cond71 = (cond7 & (thnew[:,:,precomp,:] > self.var.th_s_comp[:,:,precomp,:]))
#                 excess[cond71] = ((thnew[:,:,precomp,:] - self.var.th_s_comp[:,:,precomp,:]) * 1000 * self.var.dz[precomp])[cond71]
#                 thnew[:,:,precomp,:][cond71] = self.var.th_s_comp[:,:,precomp,:][cond71]

#                 cond72 = (cond7 & np.logical_not(cond71))
#                 excess[cond72] = 0

#         self.var.deep_percolation = np.copy(drainsum)
#         self.var.Recharge = (drainsum / 1000.)  # depth

#         # **TODO**
#         # self.var.RechargeVol = np.sum(
#         #     np.multiply(
#         #         self.var.Recharge,
#         #         self.var.FarmCropArea),
#         #     axis=1)
        
#         # self.var.Recharge = np.sum(
#         #     np.multiply(
#         #         (drainsum / 1000.),
#         #         self.var.CurrentCropArea),
#         #     axis=(0,1))         # FIXME
#         self.var.th = np.copy(thnew)

