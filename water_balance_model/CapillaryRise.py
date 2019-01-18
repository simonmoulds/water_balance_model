#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np

import logging
logger = logging.getLogger(__name__)

class CapillaryRise(object):
    def __init__(self, CapillaryRise_variable):
        self.var = CapillaryRise_variable
        self.capillary_rise = True  # TODO: put this in configuration options
        
    def initial(self):
        self.var.capillary_rise_frac = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))
        self.var.capillary_rise_from_gw = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))

    def compute_capillary_rise_frac(self):
        
        # zGW = np.broadcast_to(self.var.groundwater.zGW[None,None,:], (self.var.nCell))
        zGW = self.var.groundwater.zGW[None,None,:]

        def compute_cap_rise(frac, dz1, dz0, zgw):
            return frac - (dz1 - zgw) * 0.1 / np.maximum(1e-3, dz1 - dz0)
        
        # approximate height of groundwater table and
        # corresponding reach of cell under influence of
        # capillary rise
        if self.capillary_rise:
            CRFRAC = np.minimum(
                1.,
                compute_cap_rise(1., self.var.dzRel0100, self.var.dzRel0090, zGW))
            CRFRAC = np.where(
                zGW < self.var.dzRel0090,
                compute_cap_rise(0.9, self.var.dzRel0090, self.var.dzRel0080, zGW),
                CRFRAC)
            CRFRAC = np.where(
                zGW < self.var.dzRel0080,
                compute_cap_rise(0.8, self.var.dzRel0080, self.var.dzRel0070, zGW),
                CRFRAC)
            CRFRAC = np.where(
                zGW < self.var.dzRel0070,
                compute_cap_rise(0.7, self.var.dzRel0070, self.var.dzRel0060, zGW),
                CRFRAC)
            CRFRAC = np.where(
                zGW < self.var.dzRel0060,
                compute_cap_rise(0.6, self.var.dzRel0060, self.var.dzRel0050, zGW),
                CRFRAC)
            CRFRAC = np.where(
                zGW < self.var.dzRel0050,
                compute_cap_rise(0.5, self.var.dzRel0050, self.var.dzRel0040, zGW),
                CRFRAC)
            CRFRAC = np.where(
                zGW < self.var.dzRel0040,
                compute_cap_rise(0.4, self.var.dzRel0040, self.var.dzRel0030, zGW),
                CRFRAC)
            CRFRAC = np.where(
                zGW < self.var.dzRel0030,
                compute_cap_rise(0.3, self.var.dzRel0030, self.var.dzRel0020, zGW),
                CRFRAC)
            CRFRAC = np.where(
                zGW < self.var.dzRel0020,
                compute_cap_rise(0.2, self.var.dzRel0020, self.var.dzRel0010, zGW),
                CRFRAC)
            CRFRAC = np.where(
                zGW < self.var.dzRel0010,
                compute_cap_rise(0.1, self.var.dzRel0010, self.var.dzRel0005, zGW),
                CRFRAC)
            CRFRAC = np.where(
                zGW < self.var.dzRel0005,
                compute_cap_rise(0.05, self.var.dzRel0005, self.var.dzRel0001, zGW),
                CRFRAC)
            CRFRAC = np.where(
                zGW < self.var.dzRel0001,
                compute_cap_rise(0.01, self.var.dzRel0001, 0., zGW),
                CRFRAC)                
            self.var.capillary_rise_fraction = np.maximum(0. , np.minimum(1., CRFRAC))
        else:
            self.var.capillary_rise_fraction = 0.

    def dynamic(self):
        self.compute_capillary_rise_frac()

        # saturation term in van Genuchten equation
        available_water = np.maximum(0., self.var.wc - self.var.wc_res)        
        sat_term = np.divide(
            available_water,
            self.var.wc_range,
            out=np.zeros_like(self.var.wc),
            where=self.var.wc_range>0)
        sat_term = sat_term.clip(0., 1.)

        k = (
            self.var.ksat
            * np.sqrt(sat_term)
            * np.square(
                1. - (1. - sat_term ** self.var.van_genuchten_inv_m)
                ** self.var.van_genuchten_m))
        
        sat_term_fc = (
            np.maximum(0., self.var.wc - self.var.wc_res)
            / (self.var.wc_fc - self.var.wc_res))
        capillary_rise1 = np.minimum(
            np.maximum(0., (1. - sat_term_fc[...,0,:]) * k[...,1,:]),
            self.var.k_fc12)
        capillary_rise2 = np.minimum(
            np.maximum(0., (1. - sat_term_fc[...,1,:]) * k[...,2,:]),
            self.var.k_fc23)
        
        self.var.capillary_rise_from_gw = np.maximum(0., (1. - sat_term_fc[...,2,:]) * np.sqrt(self.var.ksat[...,2,:] * k[...,2,:]))

        self.var.capillary_rise_from_gw *= (0.5 * self.var.capillary_rise_frac)
        self.var.capillary_rise_from_gw = self.var.capillary_rise_from_gw.clip(0, None)  # storGroundwater???

        self.var.wc[...,0,:] += capillary_rise1
        self.var.wc[...,1,:] += (capillary_rise2 - capillary_rise1)
        self.var.wc[...,2,:] += (self.var.capillary_rise_from_gw - capillary_rise2)

        # CHECK
        self.var.th = self.var.wc / self.var.root_depth
            
        # CWATM:
        # satTermFC1 = np.maximum(0., self.var.w1[No] - self.var.wres1[No]) / (self.var.wfc1[No] - self.var.wres1[No])
        # satTermFC2 = np.maximum(0., self.var.w2[No] - self.var.wres2[No]) / (self.var.wfc2[No] - self.var.wres2[No])
        # satTermFC3 = np.maximum(0., self.var.w3[No] - self.var.wres3[No]) / (self.var.wfc3[No] - self.var.wres3[No])
        # capRise1 = np.minimum(np.maximum(0., (1 - satTermFC1) * kUnSat2), self.var.kunSatFC12[No])
        # capRise2 = np.minimum(np.maximum(0., (1 - satTermFC2) * kUnSat3), self.var.kunSatFC23[No])
        # self.var.capRiseFromGW[No] = np.maximum(0., (1 - satTermFC3) * np.sqrt(self.var.KSat3[NoSoil] * kUnSat3))
        # self.var.capRiseFromGW[No] = 0.5 * self.var.capRiseFrac * self.var.capRiseFromGW[No]
        # self.var.capRiseFromGW[No] = np.minimum(np.maximum(0., self.var.storGroundwater), self.var.capRiseFromGW[No])

        # self.var.w1[No] = self.var.w1[No] + capRise1
        # self.var.w2[No] = self.var.w2[No] - capRise1 +  capRise2
        # self.var.w3[No] = self.var.w3[No] - capRise2 + self.var.capRiseFromGW[No]
      










        
# class CapillaryRiseOld(object):
#     def __init__(self, CapillaryRise_variable):
#         self.var = CapillaryRise_variable

#     def initial(self):
#         self.var.CrTot = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))

#     def maximum_capillary_rise(self, ksat, aCR, bCR, zGW, z):
#         """Function to compute maximum capillary rise for a given soil 
#         profile

#         Args:
#           ksat : saturated hydraulic conductivity of the soil layer
#           aCR  : ... of the soil layer
#           bCR  : ... of the soil layer
#           zGW  : depth of groundwater table
#           z    : depth to midpoint of the soil layer

#         """
#         MaxCR = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))
#         cond1 = ((ksat > 0) & (zGW > 0) & ((zGW - z) < 4))
#         cond11 = (cond1 & (z >= zGW))
#         MaxCR[cond11] = 99            
#         cond12 = (cond1 & np.logical_not(cond11))
#         MaxCR_log = np.log(zGW - z, out=np.zeros((MaxCR.shape)), where=cond12)
#         MaxCR[cond12] = (np.exp(np.divide(MaxCR_log - bCR, aCR, out=np.zeros_like(aCR), where=aCR!=0)))[cond12]
#         MaxCR = np.clip(MaxCR, None, 99)
#         return MaxCR

#     def store_water_from_capillary_rise(self, th, th_fc, th_fc_adj, th_wp, fshape_cr, MaxCR, flux_out, zGW, zBot, dz):

#         thnew = np.copy(th)

#         cond1 = ((np.round(MaxCR * 1000) > 0) & (np.round(flux_out * 1000) == 0))

#         # calculate driving force
#         # Df = driving_force(th, th_fc_adj, th_wp, fshape_cr)
#         Df = np.ones((self.var.nFarm, self.var.nCrop, self.var.nCell))
#         cond11 = cond1 & ((th >= th_wp) & (fshape_cr > 0))
#         Df[cond11] = (1 - (((th - th_wp) / (th_fc_adj - th_wp)) ** fshape_cr))[cond11]
#         Df = np.clip(Df, 0, 1)
                          
#         # if (NewCond.th(compi) >= Soil.Layer.th_wp(layeri)) && (Soil.fshape_cr > 0)
#         #     Df = 1-(((NewCond.th(compi)-Soil.Layer.th_wp(layeri))/...
#         #         (NewCond.th_fc_Adj(compi)-Soil.Layer.th_wp(layeri)))^Soil.fshape_cr);
#         #     if Df > 1
#         #         Df = 1;
#         #     elseif Df < 0
#         #         Df = 0;
#         #     end
#         # else
#         #     Df = 1;
#         # end        
        
#         # Calculate relative hydraulic conductivity
#         # Krel = relative_hydraulic_conductivity(th, th_fc, th_wp)
#         thThr = (th_wp + th_fc) / 2
#         cond12 = cond1 & (th < thThr)
#         Krel = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))
#         cond121 = cond12 & np.logical_not(((th <= th_wp) | (thThr <= th_wp)))
#         Krel[cond121] = ((th - th_wp) / (thThr - th_wp))[cond121]
#         # % Calculate relative hydraulic conductivity
#         # thThr = (Soil.Layer.th_wp(layeri)+Soil.Layer.th_fc(layeri))/2;
#         # if NewCond.th(compi) < thThr
#         #     if (NewCond.th(compi) <= Soil.Layer.th_wp(layeri)) ||...
#         #             (thThr <= Soil.Layer.th_wp(layeri))
#         #         Krel = 0;
#         #     else
#         #         Krel = (NewCond.th(compi)-Soil.Layer.th_wp(layeri))/...
#         #             (thThr-Soil.Layer.th_wp(layeri));
#         #     end
#         # else
#         #     Krel = 1;
#         # end

#         # Check if room is available to store water from capillary rise
#         arr_zeros = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))
#         dth = np.copy(arr_zeros)
#         dth[cond1] = (th_fc_adj - th)[cond1]                
#         dth = np.round((dth * 1000) / 1000)

#         # Store water if room is available
#         dthMax = np.copy(arr_zeros)
#         CRcomp = np.copy(arr_zeros)
#         cond15 = (cond1 & (dth > 0) & ((zBot - dz / 2) < zGW))

#         dthMax[cond15] = (Krel * Df * MaxCR / (1000 * dz))[cond15]
#         cond151 = (cond15 & (dth >= dthMax))
#         thnew[cond151] += dthMax[cond151]
#         CRcomp[cond151] = (dthMax * 1000 * dz)[cond151]
#         MaxCR[cond151] = 0

#         cond152 = (cond15 & np.logical_not(cond151))
#         thnew[cond152] = th_fc_adj[cond152]
#         CRcomp[cond152] = (dth * 1000 * dz)[cond152]
#         MaxCR[cond152] = ((Krel * MaxCR) - CRcomp)[cond152]    
#         return thnew, CRcomp, MaxCR
    
#     def dynamic(self):
#         """Function to calculate capillary rise from a shallow 
#         groundwater table
#         """
#         if self.var.groundwater.WaterTable:

#             zGW = np.broadcast_to(self.var.groundwater.zGW[None,None,:], (self.var.nFarm, self.var.nCrop, self.var.nCell))
#             # zGW = self.var.zGW[None,:] * np.ones((self.var.nCrop))[:,None]
#             zBot = np.sum(self.var.dz)
#             zBotMid = zBot - (self.var.dz[-1] / 2)  # depth to midpoint of bottom layer
#             thnew = np.copy(self.var.th)

#             # Get maximum capillary rise for bottom compartment
#             MaxCR = self.maximum_capillary_rise(
#                 self.var.ksat[:,:,-1,:],
#                 self.var.aCR[:,:,-1,:],
#                 self.var.bCR[:,:,-1,:],
#                 zGW,
#                 zBotMid)

#             # Check for restrictions on upward flow caused by properties of
#             # compartments that are not modelled in the soil water balance

#             # Find top of next soil layer that is not within modelled soil
#             # profile: find index of layers that are included in the soil
#             # water balance (from self.var.layerIndex), then sum the
#             # thicknesses of these layers; the resulting value will be the
#             # top of the first layer not included in the soil water balance.
            
#             idx = np.arange(0, (self.var.layerIndex[-1] + 1))
#             zTopLayer = np.sum(self.var.zLayer[idx])
#             layeri = self.var.layerIndex[-1]  # layer number of bottom compartment
#             LimCR = np.zeros((self.var.nCrop, self.var.nCell))

#             while np.any(zTopLayer < zGW) & (layeri < (self.var.nLayer - 1)):
#                 layeri += 1
#                 LimCR = self.maximum_capillary_rise(
#                     self.var.ksat[:,:,layeri,:],
#                     self.var.aCR[:,:,layeri,:],
#                     self.var.bCR[:,:,layeri,:],
#                     zGW,
#                     zTopLayer)
#                 MaxCR = np.clip(MaxCR, None, LimCR)
#                 zTopLayer += self.var.zLayer[layeri]  # top of the next layer not included in the soil water balance

#             compi = self.var.nComp - 1
#             CrTot = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))
#             while ((np.any(np.round(MaxCR * 1000) > 0)) & (np.any(np.round(self.var.FluxOut[:,:,compi,:] * 1000) == 0)) & (compi >= 0)):

#                 cond1 = ((np.round(MaxCR * 1000) > 0) & (np.round(self.var.FluxOut[:,:,compi,:] * 1000) == 0))
#                 thnew_comp, CRcomp, MaxCR = self.store_water_from_capillary_rise(
#                     self.var.th[:,:,compi,:],
#                     self.var.th_fc_comp[:,:,compi,:],
#                     self.var.th_fc_adj[:,:,compi,:],
#                     self.var.th_wp_comp[:,:,compi,:],
#                     self.var.fshape_cr,
#                     # self.var.fshape_cr_comp[:,:,compi,:],
#                     MaxCR,
#                     self.var.FluxOut[:,:,compi,:],
#                     zGW,
#                     zBot,
#                     self.var.dz[compi])

#                 thnew[:,:,compi,:][cond1] = thnew_comp[cond1]
#                 CrTot[cond1] += CRcomp[cond1]

#                 # Update bottom elevation of compartment and compartment counter
#                 zBot -= self.var.dz[compi]
#                 compi -= 1

#                 # Update restriction on maximum capillary rise
#                 if compi >= 0:
#                     zBotMid = zBot - (self.var.dz[compi] / 2)
#                     LimCR = self.maximum_capillary_rise(
#                         self.var.ksat_comp[:,:,compi,:],
#                         self.var.aCR_comp[:,:,compi,:],
#                         self.var.bCR_comp[:,:,compi,:],
#                         zGW,
#                         zBotMid)
#                     cond11 = (cond1 & (MaxCR > LimCR))
#                     MaxCR[cond11] = LimCR[cond11]

#             self.var.th = np.copy(thnew)
#             self.var.CrTot = CrTot
