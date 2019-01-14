#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
# from pcraster.framework import *
# import pcraster as pcr
import string
import numpy as np
import hydro_model_builder.Messages
import VirtualOS as vos
# from OutputNetCDF import *
# import ETPFunctions as refPotET

import logging
logger = logging.getLogger(__name__)

class Meteo(object):

    def __init__(self, Meteo_variable):
        self._configuration = Meteo_variable._configuration
        self._modelTime = Meteo_variable._modelTime
        self.cloneMapAttributes = Meteo_variable.cloneMapAttributes
        self.cloneMap = Meteo_variable.cloneMap
        self.landmask = Meteo_variable.landmask

    def initial(self):
        self.set_input_filenames()
        self.set_nc_variable_names()
        self.set_meteo_conversion_factors()
        # TODO: find out if we can delete this
        # # daily time step
        # self.usingDailyTimeStepForcingData = False
        # if self._configuration.timeStep == 1.0 and self._configuration.timeStepUnit == "day":
        #     self.usingDailyTimeStepForcingData = True

    def set_input_filenames(self):
        self.preFileNC = self._configuration.METEO['precipitationInputFile']
        self.minDailyTemperatureNC = self._configuration.METEO['minDailyTemperatureInputFile']
        self.maxDailyTemperatureNC = self._configuration.METEO['maxDailyTemperatureInputFile']
        self.avgDailyTemperatureNC = self._configuration.METEO['avgDailyTemperatureInputFile']
        self.etpFileNC = self._configuration.METEO['refETPotInputFile']        
        self.check_input_filenames()

    def check_input_filenames(self):
        self.check_format_args([
            self.preFileNC,
            # self.tmpFileNC,
            self.minDailyTemperatureNC,
            self.maxDailyTemperatureNC,
            self.etpFileNC
            ])
        
    def check_format_args(self, filenames):
        for filename in filenames:
            format_args = vos.get_format_args(filename)
            format_args_ok = vos.check_format_args_ok(format_args, ['day','month','year'])
            if len(format_args) > 0:
                if not format_args_ok:
                    msg = 'Filename ' + filename + ' contains invalid format arguments: only day, month and year are allowable'
                    raise Messages.AQError(msg)
                
    def set_nc_variable_names(self):
        self.preVarName = self._configuration.METEO['precipitationVariableName']
        self.tminVarName = self._configuration.METEO['minDailyTemperatureVariableName']
        self.tmaxVarName = self._configuration.METEO['maxDailyTemperatureVariableName']
        self.tavgVarName = self._configuration.METEO['avgDailyTemperatureVariableName']
        self.refETPotVarName = self._configuration.METEO['refETPotVariableName']
        self.check_nc_variable_names()
        
    def check_nc_variable_names(self):
        # filenames = [self.preFileNC, self.tmpFileNC, self.tmpFileNC, self.etpFileNC]
        filenames = [self.preFileNC, self.minDailyTemperatureNC, self.maxDailyTemperatureNC, self.avgDailyTemperatureNC, self.etpFileNC]
        variable_names = [self.preVarName, self.tminVarName, self.tmaxVarName, self.tavgVarName, self.refETPotVarName]
        day, month, year = (self._modelTime.startTime.day, self._modelTime.startTime.month, self._modelTime.year)        
        result = []
        msg = []
        for filename,variable in zip(filenames,variable_names):
            variable_in_nc = vos.checkVariableInNC(filename.format(day=day, month=month, year=year), variable)
            result.append(variable_in_nc)
            if not variable_in_nc:
                msg.append('File ' + str(filename) + ' does not contain variable ' + str(variable) + '\n')
                
        if not all(result):
            msg = '\n'.join(msg)
            raise Messages.AQError(msg)
        
    def set_meteo_conversion_factors(self):
        self.preConst       = 0.0
        self.preFactor      = 1.0  # divide this method up?
        self.tminConst       = 0.0
        self.tminFactor      = 1.0
        self.tmaxConst       = 0.0
        self.tmaxFactor      = 1.0
        self.tavgConst       = 0.0
        self.tavgFactor      = 1.0
        self.etrefConst  = 0.0
        self.etrefFactor = 1.0
        if 'precipitationConstant' in self._configuration.METEO:
            self.preConst = np.float64(self._configuration.METEO['precipitationConstant'])
        if 'precipitationFactor' in self._configuration.METEO:
            self.preFactor = np.float64(self._configuration.METEO['precipitationFactor'])
        if 'minDailyTemperatureConstant' in self._configuration.METEO:
            self.tminConst = np.float64(self._configuration.METEO['minDailyTemperatureConstant'])
        if 'minDailyTemperatureFactor' in self._configuration.METEO:
            self.tminFactor = np.float64(self._configuration.METEO['minDailyTemperatureFactor'])
        if 'maxDailyTemperatureConstant' in self._configuration.METEO:
            self.tmaxConst = np.float64(self._configuration.METEO['maxDailyTemperatureConstant'])
        if 'maxDailyTemperatureFactor' in self._configuration.METEO:
            self.tmaxFactor = np.float64(self._configuration.METEO['maxDailyTemperatureFactor'])
        if 'avgDailyTemperatureConstant' in self._configuration.METEO:
            self.tavgConst = np.float64(self._configuration.METEO['avgDailyTemperatureConstant'])
        if 'avgDailyTemperatureFactor' in self._configuration.METEO:
            self.tavgFactor = np.float64(self._configuration.METEO['avgDailyTemperatureFactor'])
        if 'ETpotConstant' in self._configuration.METEO:
            self.etrefConst = np.float64(self._configuration.METEO['refETPotConstant'])
        if 'ETpotFactor' in self._configuration.METEO:
            self.etrefFactor = np.float64(self._configuration.METEO['refETPotFactor'])
        
    def adjust_precipitation_input_data(self):
        # TODO: proper unit conversion
        self.precipitation = self.preConst + self.preFactor * self.precipitation * 0.001  # mm -> m
        self.precipitation = np.maximum(0.0, self.precipitation)
        self.precipitation[np.isnan(self.precipitation)] = 0.0
        self.precipitation = np.floor(self.precipitation * 100000.)/100000.

    def read_precipitation_data(self):
        method_for_time_index = None
        self.precipitation = vos.netcdf2PCRobjClone(
            self.preFileNC.format(
                day=self._modelTime.currTime.day,
                month=self._modelTime.currTime.month,
                year=self._modelTime.currTime.year),
            self.preVarName,
            str(self._modelTime.fulldate),
            useDoy = method_for_time_index,
            cloneMapAttributes = self.cloneMapAttributes,
            cloneMapFileName = self.cloneMap,
            LatitudeLongitude = True)[self.landmask][None,None,:]
        self.adjust_precipitation_input_data()

    def adjust_temperature_data(self):
        self.tmin = self.tminConst + self.tminFactor * self.tmin
        self.tmax = self.tmaxConst + self.tmaxFactor * self.tmax
        self.tavg = self.tavgConst + self.tavgFactor * self.tavg
        self.tmin = np.round(self.tmin * 1000.) / 1000.
        self.tmax = np.round(self.tmax * 1000.) / 1000.
        self.tavg = np.round(self.tavg * 1000.) / 1000.
        
    def read_temperature_data(self):
        method_for_time_index = None        
        self.tmin = vos.netcdf2PCRobjClone(
            self.minDailyTemperatureNC.format(
                day=self._modelTime.currTime.day,
                month=self._modelTime.currTime.month,
                year=self._modelTime.currTime.year),
            self.tminVarName,
            str(self._modelTime.fulldate),
            useDoy = method_for_time_index,
            cloneMapAttributes = self.cloneMapAttributes,
            cloneMapFileName = self.cloneMap,
            LatitudeLongitude = True)[self.landmask][None,None,:]

        self.tmax = vos.netcdf2PCRobjClone(
            self.maxDailyTemperatureNC.format(
                day=self._modelTime.currTime.day,
                month=self._modelTime.currTime.month,
                year=self._modelTime.currTime.year),
            self.tmaxVarName,
            str(self._modelTime.fulldate),
            useDoy = method_for_time_index,
            cloneMapAttributes = self.cloneMapAttributes,
            cloneMapFileName = self.cloneMap,
            LatitudeLongitude = True)[self.landmask][None,None,:]

        self.tavg = vos.netcdf2PCRobjClone(
            self.avgDailyTemperatureNC.format(
                day=self._modelTime.currTime.day,
                month=self._modelTime.currTime.month,
                year=self._modelTime.currTime.year),
            self.tavgVarName,
            str(self._modelTime.fulldate),
            useDoy = method_for_time_index,
            cloneMapAttributes = self.cloneMapAttributes,
            cloneMapFileName = self.cloneMap,
            LatitudeLongitude = True)[self.landmask][None,None,:]
        
        self.adjust_temperature_data()

    def adjust_reference_ET_data(self):
        # TODO: unit conversion
        self.referencePotET = self.etrefConst + self.etrefFactor * self.referencePotET * 0.001  # mm -> m

    def read_reference_ET_data(self):
        method_for_time_index = None
        self.referencePotET = vos.netcdf2PCRobjClone(
            self.etpFileNC.format(
                day=self._modelTime.currTime.day,
                month=self._modelTime.currTime.month,
                year=self._modelTime.currTime.year),
            self.refETPotVarName,
            str(self._modelTime.fulldate), 
            useDoy = method_for_time_index,
            cloneMapAttributes = self.cloneMapAttributes,
            cloneMapFileName=self.cloneMap,
            LatitudeLongitude = True)[self.landmask][None,None,:]
        self.adjust_reference_ET_data()
        
    def read_reference_EW_data(self):
        # **TODO**
        self.EWref = self.referencePotET.copy()
        
    def dynamic(self):
        self.read_precipitation_data()
        self.read_temperature_data()
        self.read_reference_ET_data()
        self.read_reference_EW_data()  # for open water evaporation

