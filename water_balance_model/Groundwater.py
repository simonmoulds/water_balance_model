#!/usr/bin/env python
# -*- coding: utf-8 -*-

# AquaCrop crop growth model

import os
import time
import numpy as np
import hydro_model_builder.Messages
import hydro_model_builder.VirtualOS as vos
import datetime as datetime
import logging
logger = logging.getLogger(__name__)

class Groundwater(object):

    def __init__(self, Groundwater_variable):
        # self = Groundwater_variable
        self._configuration = Groundwater_variable._configuration
        self._modelTime = Groundwater_variable._modelTime
        self.cloneMapAttributes = Groundwater_variable.cloneMapAttributes
        self.cloneMap = Groundwater_variable.cloneMap
        self.landmask = Groundwater_variable.landmask

    def initial(self):
        self.WaterTable = bool(int(self._configuration.GROUNDWATER['WaterTable']))
        self.VariableWaterTable = bool(int(self._configuration.GROUNDWATER['VariableWaterTable']))
        self.DailyGroundwaterNC = bool(int(self._configuration.GROUNDWATER['DailyGroundwaterInputFile']))

        zGW = np.ones_like(self.landmask) * 999.
        self.zGW = zGW[self.landmask]
        # self.zGW = np.ones((self.nCell)) * 999.
        
        if self.WaterTable:
            self.gwFileNC = self._configuration.GROUNDWATER['groundwaterInputFile']
            self.gwVarName = self._configuration.GROUNDWATER['groundwaterVariableName']
            self.gwTimeLag = int(self._configuration.GROUNDWATER['timeLag'])

            # if the program is configured to read daily groundwater files and
            # the time lag is positive, we also need to read an initial value
            # file
            if self.DailyGroundwaterNC & (self.gwTimeLag > 0):
                initialGroundwaterLevelNC = str(self._configuration.INITIAL_CONDITIONS['initialGroundwaterLevelInputFile'])
                zGW = vos.netcdf2PCRobjCloneWithoutTime(initialGroundwaterLevelNC,
                                                        self.gwVarName,
                                                        cloneMapFileName = self.cloneMap,
                                                        LatitudeLongitude = True)
                self.zGW = zGW[self.landmask]

    def read(self):

        # method for finding time indexes in the groundwater netdf file:
        # - the default one
        method_for_time_index = None
        # - based on the ini/configuration file (if given)
        # if 'time_index_method_for_groundwater_netcdf' in self._configuration.GROUNDWATER.keys() and\
        #                                                    self._configuration.GROUNDWATER['time_index_method_for_groundwater_netcdf'] != "None":
        #     method_for_time_index = self._configuration.GROUNDWATER['time_index_method_for_groundwater_netcdf']
        
        # reading groundwater:
        if self.WaterTable:
            if self.VariableWaterTable:

                # DailyGroundwaterNC is a logical indicating whether a separate
                # netCDF is used for each time step - use this for coupling
                if self.DailyGroundwaterNC:

                    # introduce this test so that we do not ask the model to read
                    # a file from a timestep prior to the current simulation. 
                    if not (self._modelTime.isFirstTimestep() & (self.gwTimeLag > 0)):
                        
                        tm = self._modelTime.currTime - datetime.timedelta(self.gwTimeLag)
                        day, month, year = tm.day, tm.month, tm.year

                        # Fill named placeholders (NB we have already checked that
                        # the specified filename contains these placeholders)
                        gwFileNC = self.gwFileNC.format(day=day, month=month, year=year)

                        # Check whether the file is present in the filesystem; if
                        # it doesn't, enter a while loop which periodically checks
                        # whether the file exists. We specify a maximum wait time
                        # in order to prevent the model hanging if the file never
                        # materialises.
                        exists = os.path.exists(gwFileNC)
                        max_wait_time = 60
                        wait_time = 0.1
                        total_wait_time = 0
                        while exists is False and total_wait_time <= max_wait_time:
                            time.sleep(wait_time)
                            exists = os.path.exists(gwFileNC)
                            total_wait_time += wait_time

                        if not exists:
                            msg = "groundwater file doesn't exist and maximum wait time exceeded"
                            raise AQError(msg)

                        zGW = vos.netcdf2PCRobjCloneWithoutTime(gwFileNC,
                                                                self.gwVarName,
                                                                cloneMapFileName = self.cloneMap,
                                                                LatitudeLongitude = True)
                        self.zGW = zGW[self.landmask]
                        
                else:
                    zGW = vos.netcdf2PCRobjClone(self.gwFileNC,
                                                 self.gwVarName,
                                                 str(currTimeStep.fulldate),
                                                 useDoy = method_for_time_index,
                                                 cloneMapFileName = self.cloneMap,
                                                 LatitudeLongitude = True)
                    self.zGW = zGW[self.landmask]
                    
            else:
                zGW = vos.netcdf2PCRobjCloneWithoutTime(self.gwFileNC,
                                                        self.gwVarName,
                                                        cloneMapFileName = self.cloneMap,
                                                        LatitudeLongitude = True)    
                self.zGW = zGW[self.landmask]
                    
    def dynamic(self):
        self.read()
