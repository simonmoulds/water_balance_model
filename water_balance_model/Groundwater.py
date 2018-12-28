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
        self.var = Groundwater_variable

    def initial(self):
        self.var.WaterTable = bool(int(self.var._configuration.groundwaterOptions['WaterTable']))
        self.var.VariableWaterTable = bool(int(self.var._configuration.groundwaterOptions['VariableWaterTable']))
        self.var.DailyGroundwaterNC = bool(int(self.var._configuration.groundwaterOptions['DailyGroundwaterNC']))

        self.var.zGW = np.ones((self.var.nCell)) * 999.
        
        if self.var.WaterTable:
            self.var.gwFileNC = self.var._configuration.groundwaterOptions['groundwaterNC']
            self.var.gwVarName = self.var._configuration.groundwaterOptions['groundwaterVariableName']
            self.var.gwTimeLag = int(self.var._configuration.groundwaterOptions['timeLag'])

            # if the program is configured to read daily groundwater files and
            # the time lag is positive, we also need to read an initial value
            # file
            if self.var.DailyGroundwaterNC & (self.var.gwTimeLag > 0):
                initialGroundwaterLevelNC = str(self.var._configuration.groundwaterOptions['initialGroundwaterLevelNC'])
                zGW = vos.netcdf2PCRobjCloneWithoutTime(initialGroundwaterLevelNC,
                                                        self.var.gwVarName,
                                                        cloneMapFileName = self.var.cloneMap,
                                                        LatitudeLongitude = True)
                self.var.zGW = zGW[self.var.landmask]

    def read(self):

        # method for finding time indexes in the groundwater netdf file:
        # - the default one
        method_for_time_index = None
        # - based on the ini/configuration file (if given)
        # if 'time_index_method_for_groundwater_netcdf' in self.var._configuration.groundwaterOptions.keys() and\
        #                                                    self.var._configuration.groundwaterOptions['time_index_method_for_groundwater_netcdf'] != "None":
        #     method_for_time_index = self.var._configuration.groundwaterOptions['time_index_method_for_groundwater_netcdf']
        
        # reading groundwater:
        if self.var.WaterTable:
            if self.var.VariableWaterTable:

                # DailyGroundwaterNC is a logical indicating whether a separate
                # netCDF is used for each time step - use this for coupling
                if self.var.DailyGroundwaterNC:

                    # introduce this test so that we do not ask the model to read
                    # a file from a timestep prior to the current simulation. 
                    if not (self.var._modelTime.isFirstTimestep() & (self.var.gwTimeLag > 0)):
                        
                        tm = self.var._modelTime.currTime - datetime.timedelta(self.var.gwTimeLag)
                        day, month, year = tm.day, tm.month, tm.year

                        # Fill named placeholders (NB we have already checked that
                        # the specified filename contains these placeholders)
                        gwFileNC = self.var.gwFileNC.format(day=day, month=month, year=year)

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
                                                                self.var.gwVarName,
                                                                cloneMapFileName = self.var.cloneMap,
                                                                LatitudeLongitude = True)
                        self.var.zGW = zGW[self.var.landmask]
                        
                else:
                    zGW = vos.netcdf2PCRobjClone(self.var.gwFileNC,
                                                 self.var.gwVarName,
                                                 str(currTimeStep.fulldate),
                                                 useDoy = method_for_time_index,
                                                 cloneMapFileName = self.var.cloneMap,
                                                 LatitudeLongitude = True)
                    self.var.zGW = zGW[self.var.landmask]
                    
            else:
                zGW = vos.netcdf2PCRobjCloneWithoutTime(self.var.gwFileNC,
                                                        self.var.gwVarName,
                                                        cloneMapFileName = self.var.cloneMap,
                                                        LatitudeLongitude = True)    
                self.var.zGW = zGW[self.var.landmask]
                    
    def dynamic(self):
        self.read()
