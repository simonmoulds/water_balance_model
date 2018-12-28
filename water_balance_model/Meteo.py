#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
# from pcraster.framework import *
# import pcraster as pcr
import string
import numpy as np
import hydro_model_builder.Messages
import hydro_model_builder.VirtualOS as vos
# from ncConverter import *
# import ETPFunctions as refPotET

import logging
logger = logging.getLogger(__name__)

class Meteo(object):

    def __init__(self, Meteo_variable):
        self.var = Meteo_variable

    def initial(self):
        self.set_input_filenames()
        self.set_nc_variable_names()
        self.set_meteo_conversion_factors()
        # TODO: find out if we can delete this
        # # daily time step
        # self.var.usingDailyTimeStepForcingData = False
        # if self.var._configuration.timeStep == 1.0 and self.var._configuration.timeStepUnit == "day":
        #     self.var.usingDailyTimeStepForcingData = True

    def set_input_filenames(self):
        self.var.preFileNC = self.var._configuration.meteoOptions['precipitationNC']
        # self.var.tmpFileNC = self.var._configuration.meteoOptions['temperatureNC']
        self.var.minDailyTemperatureNC = self.var._configuration.meteoOptions['minDailyTemperatureNC']
        self.var.maxDailyTemperatureNC = self.var._configuration.meteoOptions['maxDailyTemperatureNC']
        self.var.etpFileNC = self.var._configuration.meteoOptions['refETPotFileNC']        
        self.check_input_filenames()

    def check_input_filenames(self):
        self.check_format_args([
            self.var.preFileNC,
            # self.var.tmpFileNC,
            self.var.minDailyTemperatureNC,
            self.var.maxDailyTemperatureNC,
            self.var.etpFileNC
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
        self.var.preVarName = self.var._configuration.meteoOptions['precipitationVariableName']
        self.var.tmnVarName = self.var._configuration.meteoOptions['tminVariableName']
        self.var.tmxVarName = self.var._configuration.meteoOptions['tmaxVariableName']
        self.var.refETPotVarName = self.var._configuration.meteoOptions['refETPotVariableName']
        self.check_nc_variable_names()
        
    def check_nc_variable_names(self):
        # filenames = [self.var.preFileNC, self.var.tmpFileNC, self.var.tmpFileNC, self.var.etpFileNC]
        filenames = [self.var.preFileNC, self.var.minDailyTemperatureNC, self.var.maxDailyTemperatureNC, self.var.etpFileNC]
        variable_names = [self.var.preVarName, self.var.tmnVarName, self.var.tmxVarName, self.var.refETPotVarName]
        day, month, year = (self.var._modelTime.startTime.day, self.var._modelTime.startTime.month, self.var._modelTime.year)        
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
        self.var.preConst       = 0.0
        self.var.preFactor      = 1.0  # divide this method up?
        self.var.tmpConst       = 0.0
        self.var.tmpFactor      = 1.0
        self.var.refETPotConst  = 0.0
        self.var.refETPotFactor = 1.0
        if 'precipitationConstant' in self.var._configuration.meteoOptions:
            self.var.preConst = np.float64(self.var._configuration.meteoOptions['precipitationConstant'])
        if 'precipitationFactor' in self.var._configuration.meteoOptions:
            self.var.preFactor = np.float64(self.var._configuration.meteoOptions['precipitationFactor'])
        if 'temperatureConstant' in self.var._configuration.meteoOptions:
            self.var.tmpConst = np.float64(self.var._configuration.meteoOptions['temperatureConstant'])
        if 'temperatureFactor' in self.var._configuration.meteoOptions:
            self.var.tmpFactor = np.float64(self.var._configuration.meteoOptions['temperatureFactor'])
        if 'ETpotConstant' in self.var._configuration.meteoOptions:
            self.var.refETPotConst = np.float64(self.var._configuration.meteoOptions['ETpotConstant'])
        if 'ETpotFactor' in self.var._configuration.meteoOptions:
            self.var.refETPotFactor = np.float64(self.var._configuration.meteoOptions['ETpotFactor'])
        
    def adjust_precipitation_input_data(self):
        # print self.var.landmask.shape
        # print self.var.precipitation.shape
        self.var.precipitation = self.var.preConst + self.var.preFactor * self.var.precipitation[self.var.landmask]
        self.var.precipitation = np.maximum(0.0, self.var.precipitation)
        self.var.precipitation[np.isnan(self.var.precipitation)] = 0.0
        self.var.precipitation = np.floor(self.var.precipitation * 100000.)/100000.

    def read_precipitation_data(self):
        method_for_time_index = None
        self.var.precipitation = vos.netcdf2PCRobjClone(
            self.var.preFileNC.format(
                day=self.var._modelTime.currTime.day,
                month=self.var._modelTime.currTime.month,
                year=self.var._modelTime.currTime.year),
            self.var.preVarName,
            str(self.var._modelTime.fulldate),
            useDoy = method_for_time_index,
            cloneMapAttributes = self.var.cloneMapAttributes,
            cloneMapFileName = self.var.cloneMap,
            LatitudeLongitude = True)
        self.adjust_precipitation_input_data()

    def adjust_temperature_data(self):
        self.var.tmin = self.var.tmpConst + self.var.tmpFactor * self.var.tmin[self.var.landmask]
        self.var.tmax = self.var.tmpConst + self.var.tmpFactor * self.var.tmax[self.var.landmask]
        self.var.tmin = np.round(self.var.tmin * 1000.) / 1000.
        self.var.tmax = np.round(self.var.tmax * 1000.) / 1000.
        
    def read_temperature_data(self):
        # TODO: work out if we can remove this
        # # method for finding time index in the temperature netdf file:
        # # - the default one
        # method_for_time_index = None
        # # - based on the ini/configuration file (if given)
        # if 'time_index_method_for_temperature_netcdf' in self.var._configuration.meteoOptions.keys() and\
        #                                                  self.var._configuration.meteoOptions['time_index_method_for_temperature_netcdf'] != "None":
        #     method_for_time_index = self.var._configuration.meteoOptions['time_index_method_for_temperature_netcdf']

        method_for_time_index = None        
        self.var.tmin = vos.netcdf2PCRobjClone(
            self.var.minDailyTemperatureNC.format(
                day=self.var._modelTime.currTime.day,
                month=self.var._modelTime.currTime.month,
                year=self.var._modelTime.currTime.year),
            self.var.tmnVarName,
            str(self.var._modelTime.fulldate),
            useDoy = method_for_time_index,
            cloneMapAttributes = self.var.cloneMapAttributes,
            cloneMapFileName = self.var.cloneMap,
            LatitudeLongitude = True)

        self.var.tmax = vos.netcdf2PCRobjClone(
            self.var.maxDailyTemperatureNC.format(
                day=self.var._modelTime.currTime.day,
                month=self.var._modelTime.currTime.month,
                year=self.var._modelTime.currTime.year),
            self.var.tmxVarName,
            str(self.var._modelTime.fulldate),
            useDoy = method_for_time_index,
            cloneMapAttributes = self.var.cloneMapAttributes,
            cloneMapFileName = self.var.cloneMap,
            LatitudeLongitude = True)        
        self.adjust_temperature_data()

    def adjust_reference_ET_data(self):
        self.var.referencePotET = self.var.refETPotConst + self.var.refETPotFactor * self.var.referencePotET[self.var.landmask]

    def read_reference_ET_data(self):
        # TODO: work out if this is required
        # if 'time_index_method_for_ref_pot_et_netcdf' in self.var._configuration.meteoOptions.keys() and self.var._configuration.meteoOptions['time_index_method_for_ref_pot_et_netcdf'] != "None":
        #     method_for_time_index = self.var._configuration.meteoOptions['time_index_method_for_ref_pot_et_netcdf']
        
        method_for_time_index = None
        self.var.referencePotET = vos.netcdf2PCRobjClone(
            self.var.etpFileNC.format(
                day=self.var._modelTime.currTime.day,
                month=self.var._modelTime.currTime.month,
                year=self.var._modelTime.currTime.year),
            self.var.refETPotVarName,
            str(self.var._modelTime.fulldate), 
            useDoy = method_for_time_index,
            cloneMapAttributes = self.var.cloneMapAttributes,
            cloneMapFileName=self.var.cloneMap,
            LatitudeLongitude = True)
        self.adjust_reference_ET_data()
    
    def dynamic(self):
        self.read_precipitation_data()
        self.read_temperature_data()
        self.read_reference_ET_data()

