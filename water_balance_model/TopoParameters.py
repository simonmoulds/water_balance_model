#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
import pcraster as pcr
import hydro_model_builder.VirtualOS as vos
import netCDF4 as nc

class TopoParameters(object):

    def __init__(self, TopoParameters_variable, config_section_name):
        """Initialise TopoParameters object"""
        self.var = TopoParameters_variable
        self.lc_configuration = getattr(self.var._configuration, config_section_name)

    def initial(self):
        self.read()
        
    def read(self):
        relative_elevation_var_names = [
            'dzRel0001','dzRel0005','dzRel0010','dzRel0020',
            'dzRel0030','dzRel0040','dzRel0050','dzRel0060',
            'dzRel0070','dzRel0080','dzRel0090','dzRel0100']
            
        for var_name in relative_elevation_var_names:
            d = vos.netcdf2PCRobjCloneWithoutTime(
                str(self.lc_configuration['relativeElevationInputFile']),
                var_name,
                cloneMapFileName=self.var.cloneMap)[self.var.landmask]
            vars(self.var)[var_name] = d

        self.var.elevation_standard_deviation = vos.netcdf2PCRobjCloneWithoutTime(
            str(self.lc_configuration['elevationStandardDeviationInputFile']),
            'dem_standard_deviation',
            cloneMapFileName = self.var.cloneMap)[self.var.landmask]
        
    def dynamic(self):
        pass

class TopoParametersNaturalVegetation(TopoParameters):
    def initial(self):
        super(TopoParametersNaturalVegetation, self).initial()
        self.compute_arno_beta()

    def compute_arno_beta(self):
        """Function to estimate parameter b of the improved 
        Arno rainfall-runoff scheme
        """
        # adapted from CWATM landcoverType.py lines 301-308
        # CALIBRATION PARAMETER - TODO
        self.var.arno_beta_add = 0.
        self.var.arno_beta = float(self.lc_configuration['arnoBeta'])
        
        self.var.arno_beta_oro = np.divide(
            (self.var.elevation_standard_deviation - 10.),
            (self.var.elevation_standard_deviation + 1500.))
        self.var.arno_beta_oro += self.var.arno_beta_add
        self.var.arno_beta_oro.clip(0.01, 1.2)
        self.var.arno_beta += self.var.arno_beta_oro
        self.var.arno_beta.clip(0.01, 1.2)
        
class TopoParametersManagedLand(TopoParametersNaturalVegetation):
    pass
    
class TopoParametersSealed(TopoParameters):
    pass
