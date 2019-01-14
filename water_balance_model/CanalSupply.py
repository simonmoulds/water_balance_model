#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import numpy as np
import VirtualOS as vos
from aquacrop.Messages import *

import logging
logger = logging.getLogger(__name__)

class CanalSupply(object):

    def __init__(self, CanalSupply_variable):
        self.var = CanalSupply_variable

    def initial(self):
        self.var.Canal = bool(int(self.var._configuration.canalOptions['Canal']))
        self.var.VariableCanalSupply = bool(int(self.var._configuration.canalOptions['VariableCanalSupply']))
        self.var.DailyCanalNC = bool(int(self.var._configuration.canalOptions['DailyCanalNC']))
        self.var.CanalSupply = np.zeros((self.var.nCell))        
        if self.var.Canal:
            self.var.canalFileNC = self.var._configuration.canalOptions['canalNC']
            self.var.canalVarName = self.var._configuration.canalOptions['canalVariableName']
            self.var.canalTimeLag = self.var._configuration.canalOptions['timeLag']
            # # if the program is configured to read daily canal supply files and
            # # the time lag is positive, we also need to read an initial value
            # # file
            # if self.var.DailyCanalNC & (self.var.canalTimeLag > 0):
            #     initialCanalLevelNC = str(self.var._configuration.canalOptions['initialCanalLevelNC'])
            #     CanalSupply = vos.netcdf2PCRobjCloneWithoutTime(initialCanalLevelNC,
            #                                             self.var.canalVarName,
            #                                             cloneMapFileName = self.var.cloneMap,
            #                                             LatitudeLongitude = True)
            #     self.var.CanalSupply = CanalSupply[self.var.landmask]
                    
    def read(self):

        # reading canal supply:
        if self.var.Canal:
            if self.var.VariableCanalSupply:

                if self.var.DailyCanalNC:

                    # introduce this test so that we do not ask the model to read
                    # a file from a timestep prior to the current simulation. 
                    if not (self.var._modelTime.isFirstTimestep() & (self.var.canalTimeLag > 0)):
                    
                        day, month, year = self.var._modelTime.day, self.var._modelTime.month, self.var._modelTime.year
                        canalFileNC = self.var.canalFileNC.format(day=day, month=month, year=year)
                        exists = os.path.exists(canalFileNC)
                        max_wait_time = 60
                        wait_time = 0.1
                        total_wait_time = 0
                        while exists is False and total_wait_time <= max_wait_time:
                            time.sleep(wait_time)
                            exists = os.path.exists(canalFileNC)
                            total_wait_time += wait_time

                        if not exists:
                            msg = "canal file doesn't exist and maximum wait time exceeded"
                            raise AQError(msg)

                        CanalSupply = vos.netcdf2PCRobjCloneWithoutTime(
                            canalFileNC,
                            self.var.canalVarName,
                            cloneMapFileName = self.var.cloneMap,
                            LatitudeLongitude = True)
                        self.var.CanalSupply = CanalSupply[self.var.landmask]
                        
                else:
                    CanalSupply = vos.netcdf2PCRobjClone(
                        self.var.canalFileNC,
                        self.var.canalVarName,
                        str(currTimeStep.fulldate),
                        useDoy = method_for_time_index,
                        cloneMapFileName = self.var.cloneMap,
                        LatitudeLongitude = True)
                    self.var.CanalSupply = CanalSupply[self.var.landmask]
                    
            else:
                CanalSupply = vos.netcdf2PCRobjCloneWithoutTime(
                    self.var.canalFileNC,
                    self.var.canalVarName,
                    cloneMapFileName = self.var.cloneMap,
                    LatitudeLongitude = True)
                self.var.CanalSupply = CanalSupply[self.var.landmask]
    
    def dynamic(self):
        self.read()
