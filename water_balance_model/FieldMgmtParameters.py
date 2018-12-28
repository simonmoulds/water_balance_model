#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# AquaCrop
#
import os
import numpy as np
import pcraster as pcr
import hydro_model_builder.VirtualOS as vos
import netCDF4 as nc
import datetime as datetime
import calendar as calendar

class FieldMgmtParameters(object):

    def __init__(self, FieldMgmtParameters_variable):
        self.var = FieldMgmtParameters_variable
        
    def initial(self):
        self.var.fieldMgmtParameterFileNC = self.var._configuration.fieldMgmtOptions['fieldMgmtParameterNC']
        self.var.parameter_names = ['Mulches','MulchPctGS','MulchPctOS','fMulch','Bunds','zBund','BundWater']
        for param in self.var.parameter_names:
            d = vos.netcdf2PCRobjCloneWithoutTime(
                self.var.fieldMgmtParameterFileNC,
                param,
                cloneMapFileName=self.var.cloneMap)
            d = d[self.var.landmask_lc].reshape(self.var.nLC,self.var.nCell)
            vars(self.var)[param] = np.broadcast_to(d, (self.var.nFarm, self.var.nLC, self.var.nCell))

    def dynamic(self):
        pass
