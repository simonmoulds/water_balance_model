#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import math
import numpy as np
import numexpr as ne

import logging
logger = logging.getLogger(__name__)

class SnowFrost(object):
    def __init__(self, SnowFrost_variable):
        self.var = SnowFrost_variable
        # SNOW:
        self.var.number_snow_layers = int(self.var._configuration.SNOW['numberSnowLayers'])
        self.var.glacier_transport_zone = int(self.var._configuration.SNOW['glacierTransportZone'])
        self.var.temperature_lapse_rate = float(self.var._configuration.SNOW['temperatureLapseRate'])
        self.var.snow_season_adj = float(self.var._configuration.SNOW['snowSeasonAdj'])
        self.var.temp_snow = float(self.var._configuration.SNOW['tempSnow'])
        self.var.snow_factor = float(self.var._configuration.SNOW['snowFactor'])
        self.var.snow_melt_coef = float(self.var._configuration.SNOW['snowMeltCoef'])  # CALIBRATION
        self.var.ice_melt_coef = float(self.var._configuration.SNOW['iceMeltCoef'])
        self.var.temp_melt = float(self.var._configuration.SNOW['tempMelt'])
        # FROST:
        self.var.Kfrost = float(self.var._configuration.FROST['Kfrost'])
        self.var.Afrost = float(self.var._configuration.FROST['Afrost'])
        self.var.frost_index_threshold = float(self.var._configuration.FROST['frostIndexThreshold'])
        self.var.snow_water_equivalent = float(self.var._configuration.FROST['snowWaterEquivalent'])

    def initial(self):
        
        # Difference between (average) air temperature at average elevation of
        # pixel and centers of upper- and lower elevation zones [deg C]
        # ElevationStD:   Standard Deviation of the DEM from Bodis (2009)
        # 0.9674:    Quantile of the normal distribution: u(0,833)=0.9674
        #              to split the pixel in 3 equal parts.
        # for different number of layers
        #  Number: 2 ,3, 4, 5, 6, 7, ,8, 9, 10
        dn = {}
        dn[1] = np.array([0])
        dn[2] = np.array([-0.67448975,  0.67448975])
        dn[3] = np.array([-0.96742157,  0.,  0.96742157])
        dn[5] = np.array([-1.28155157, -0.52440051,  0.,  0.52440051,  1.28155157])
        dn[7] = np.array([-1.46523379, -0.79163861, -0.36610636, 0., 0.36610636,0.79163861, 1.46523379])
        dn[9] = np.array([-1.59321882, -0.96742157, -0.5894558 , -0.28221615,  0., 0.28221615,  0.5894558 ,  0.96742157,  1.59321882])
        dn[10] = np.array([-1.64485363, -1.03643339, -0.67448975, -0.38532047, -0.12566135, 0.12566135,  0.38532047,  0.67448975,  1.03643339,  1.64485363])
        self.var.delta_inv_norm = dn[self.var.number_snow_layers]        
        self.var.delta_t_snow = (
            self.var.elevation_standard_deviation
            * self.var.temperature_lapse_rate)

        # day of the year to degrees: 360/365.25 = 0.9856
        self.var.snow_day_degrees = 0.9856
        self.var.summer_season_start = 165
        self.var.ice_day_degrees = 180./(259- self.var.summer_season_start)
        # days of summer (15th June-15th Sept.) to degree: 180/(259-165)
        self.var.snow_season = self.var.snow_season_adj * 0.5
        # default value of range of seasonal melt factor is set to 0.001 m C-1 day-1
        # 0.5 x range of sinus function [-1,1]

        # TODO - do this in initial condition module
        # # initialize snowcovers as many as snow layers -> read them as SnowCover1 , SnowCover2 ...
        # # SnowCover1 is the highest zone
        # self.var.SnowCoverS = []
        # for i in xrange(self.var.numberSnowLayers):
        #     self.var.SnowCoverS.append(self.var.init_module.load_initial("SnowCover",number = i+1))

        # # initial snow depth in elevation zones A, B, and C, respectively  [mm]
        # self.var.SnowCover = np.sum(self.var.SnowCoverS,axis=0) / self.var.numberSnowLayersFloat + globals.inZero

        # # Pixel-average initial snow cover: average of values in 3 elevation
        # # zones

        # # ---------------------------------------------------------------------------------
        # # Initial part of frost index
        
        # self.var.Kfrost = loadmap('Kfrost')
        # self.var.Afrost = loadmap('Afrost')
        # self.var.FrostIndexThreshold = loadmap('FrostIndexThreshold')
        # self.var.SnowWaterEquivalent = loadmap('SnowWaterEquivalent')

        # # FrostIndexInit=ifthen(defined(self.var.MaskMap),scalar(loadmap('FrostIndexInitValue')))

        # #self.var.FrostIndex = loadmap('FrostIndexIni')
        # self.var.FrostIndex = self.var.init_module.load_initial('FrostIndex')
    
    def dynamic(self):

        seasonal_snow_melt_coefficient = (
            self.var.snow_season
            * np.sin(
                math.radians(
                    (self.var._modelTime.doy - 81)
                    * self.var.snow_day_degrees))
            + self.var.snow_melt_coef)

        if (self.var._modelTime.doy > self.var.summer_season_start) and (self.var._modelTime.doy < 260):
            summer_season = np.sin(math.radians((self.var._modelTime.doy - self.var.summer_season_start) * self.var.ice_day_degrees))
        else:
            summer_season = 0.

        self.var.snow = np.zeros((1, 1, self.var.nCell))
        self.var.rain = np.zeros((1, 1, self.var.nCell))
        self.var.snow_melt = np.zeros((1, 1, self.var.nCell))
        self.var.snow_cover = np.zeros((1, 1, self.var.nCell))

        for i in xrange(self.var.number_snow_layers):
            # Temperature at center of each zone (temperature at zone B equals Tavg)
            # i=0 -> highest zone
            # i=2 -> lower zone            
            tavg_layer = (
                self.var.meteo.tavg[None,None,...]
                + self.var.delta_t_snow
                * self.var.delta_inv_norm[i])
            
            # Precipitation is assumed to be snow if daily average temperature is below TempSnow
            # Snow is multiplied by correction factor to account for undercatch of
            # snow precipitation (which is common)
            avg_temperature_below_snow_temperature = (tavg_layer < self.var.temp_snow)
            snow_layer = np.where(
                avg_temperature_below_snow_temperature,
                self.var.snow_factor * self.var.meteo.precipitation,
                0.)

            rain_layer = np.where(
                np.logical_not(avg_temperature_below_snow_temperature),
                self.var.meteo.precipitation[None,None,:],
                0.)

            # TODO: put this somewhere else (in CWATM, they are in miscInitial)
            self.var.dtsec = 86400.
            self.var.dtday = self.var.dtsec / 86400
            snow_melt_layer = (
                (tavg_layer - self.var.temp_melt)
                * seasonal_snow_melt_coefficient
                * (1. + 0.01 * rain_layer)
                * self.var.dtday)
            snow_melt_layer.clip(0., None)

            # for which layer the ice melt is calcultated with the middle temp.
            # for the others it is calculated with the corrected temp
            # this is to mimic glacier transport to lower zones
            if i <= self.var.glacier_transport_zone:
                ice_melt_layer = (
                    self.var.meteo.tavg[None,None,:]
                    * self.var.ice_melt_coef
                    * self.var.dtday
                    * summer_season)
                # if i = 0 and 1 -> higher and middle zone
                # Ice melt coeff in m/C/deg
            else:
                ice_melt_layer = (
                    tavg_layer
                    * self.var.ice_melt_coef
                    * self.var.dtday
                    * summer_season)

            ice_melt_layer.clip(0., None)
            snow_melt_layer = np.maximum(
                np.minimum(
                    (snow_melt_layer + ice_melt_layer),
                    self.var.snow_cover_layer[...,i,:]), 0.)

            self.var.snow_cover_layer[...,i,:] += (snow_layer - snow_melt_layer)
            self.var.snow += snow_layer
            self.var.rain += rain_layer
            self.var.snow_melt += snow_melt_layer
            self.var.snow_cover += self.var.snow_cover_layer[...,i,:]

        self.var.snow /= self.var.number_snow_layers
        self.var.rain /= self.var.number_snow_layers
        self.var.snow_melt /= self.var.number_snow_layers
        self.var.snow_cover /= self.var.number_snow_layers

        # dynamic part of frost index
        frost_index_change_rate = (
            - (1. - self.var.Afrost)
            * self.var.frost_index
            - self.var.meteo.tavg[None,None,...]
            * np.exp(
                - 0.04
                * self.var.Kfrost
                * self.var.snow_cover
                / self.var.snow_water_equivalent))
        
        self.var.frost_index = np.maximum(
            self.var.frost_index
            + frost_index_change_rate
            * self.var.dtday, 0.)

        # NOTES (from CWATM, snow_frost.py):
        
        # frost index in soil [degree days] based on Molnau and Bissel
        # (1983, A Continuous Frozen Ground Index for Flood
        # Forecasting. In: Maidment, Handbook of Hydrology, p. 7.28,
        # 7.55).
        
        # if Tavg is above zero, FrostIndex will stay 0
        # if Tavg is negative, FrostIndex will increase with 1 per
        # degree C per day
        
        # Exponent of 0.04 (instead of 0.4 in HoH): conversion [cm]
        # to [mm]!
        
        # Division by SnowDensity because SnowDepth is expressed as
        # equivalent water depth(always less than depth of snow pack)
        
        # SnowWaterEquivalent taken as 0.100 (based on density of 100
        # kg/m3) (Handbook of Hydrology, p. 7.5)
        
        # Afrost, (daily decay coefficient) is taken as 0.97
        # (Handbook of Hydrology, p. 7.28)
        
        # Kfrost, (snow depth reduction coefficient) is taken as 0.57
        # [1/cm], (HH, p. 7.28)
