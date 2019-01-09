#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import datetime
import time
import re
import glob
import subprocess
import netCDF4 as nc
import numpy as np
import pcraster as pcr
import hydro_model_builder.VirtualOS as vos
# import variable_list as VarDict

valid_time_dimnames = ['time']

class np2netCDF(object):
    
    def __init__(self, configuration, model_dimensions, variable_list, specificAttributeDictionary=None):
        # self._model = model
        self.model_dimensions = model_dimensions
        self.variable_list = variable_list
        self.set_netcdf_y_orientation(configuration)
        self.set_general_netcdf_attributes(configuration, specificAttributeDictionary)
        self.set_netcdf_format_options(configuration)        

    def set_netcdf_format_options(self, configuration):
        self.format = 'NETCDF3_CLASSIC'
        self.zlib = False
        if 'formatNetCDF' in configuration.reportingOptions.keys():
            self.format = str(configuration.reportingOptions['formatNetCDF'])
        if 'zlib' in configuration.reportingOptions.keys():
            if configuration.reportingOptions['zlib'] == "True": self.zlib = True
        
    def set_netcdf_y_orientation(self, configuration):        
        self.netcdf_y_orientation_follow_cf_convention = False
        if 'netcdf_y_orientation_follow_cf_convention' in configuration.reportingOptions.keys() and\
            configuration.reportingOptions['netcdf_y_orientation_follow_cf_convention'] == "True":
            msg = "Latitude (y) orientation for output netcdf files start from the bottom to top."
            self.netcdf_y_orientation_follow_cf_convention = True        

    def set_general_netcdf_attributes(self,configuration,specificAttributeDictionary=None):
        """Function to set general netCDF attributes"""
        
        # netCDF attributes (based on the configuration file or specificAttributeDictionary):
        self.attributeDictionary = {}
        if specificAttributeDictionary == None:
            self.attributeDictionary['institution'] = configuration.globalOptions['institution']
            self.attributeDictionary['title'      ] = configuration.globalOptions['title'      ]
            self.attributeDictionary['description'] = configuration.globalOptions['description']
        else:
            self.attributeDictionary['institution'] = specificAttributeDictionary['institution']
            self.attributeDictionary['title'      ] = specificAttributeDictionary['title'      ]
            self.attributeDictionary['description'] = specificAttributeDictionary['description']
        
    def add_dimension_time(self, netcdf, dimname, dimvar):
        shortname = self.variable_list.netcdf_short_name[dimname]
        try:
            datatype = self.variable_list.netcdf_datatype[dimname]
        except:
            datatype = 'f4'
        dimensions = self.variable_list.netcdf_dimensions[dimname]
        netcdf.createDimension(shortname, None)
        var = netcdf.createVariable(
            shortname,
            datatype,
            dimensions,
            zlib=self.zlib)        
        var.standard_name = self.variable_list.netcdf_standard_name[dimname]
        var.long_name = self.variable_list.netcdf_long_name[dimname]
        var.units = self.variable_list.netcdf_unit[dimname]
        var.calendar = self.variable_list.netcdf_calendar[dimname]

    def add_dimension_not_time(self, netcdf, dimname, dimvar):
        ndim = len(dimvar)
        shortname = self.variable_list.netcdf_short_name[dimname]
        try:
            datatype = self.variable_list.netcdf_datatype[dimname]
        except:
            datatype = 'f4'
        dimensions = self.variable_list.netcdf_dimensions[dimname]
        standard_name = self.variable_list.netcdf_standard_name[dimname]
        if standard_name in ['latitude','longitude']:
            keyword_args = {'zlib' : True, 'least_significant_digit' : 16}
        else:
            keyword_args = {'zlib' : self.zlib}

        if standard_name in ['latitude']:
            if not self.netcdf_y_orientation_follow_cf_convention:
                dimvar = dimvar[::-1]
        
        netcdf.createDimension(shortname, ndim)
        var = netcdf.createVariable(
            shortname,
            datatype,
            dimensions,
            **keyword_args)
        var.standard_name = self.variable_list.netcdf_standard_name[dimname]
        var.long_name = self.variable_list.netcdf_long_name[dimname]
        var.units = self.variable_list.netcdf_unit[dimname]
        var[:] = np.array(dimvar)

    def add_dimension(self, netcdf, dimname, dimvar):
        isTimeDim = dimname in ['time']
        if isTimeDim:
            self.add_dimension_time(netcdf, dimname, None)
        else:
            self.add_dimension_not_time(netcdf, dimname, dimvar)
    
    def add_variable(self, netcdf, varname, **kwargs):
        self.repair_variable_dict(varname)
        shortname = self.variable_list.netcdf_short_name[varname]
        try:
            datatype = self.variable_list.netcdf_datatype[varname]
        except:
            datatype = 'f4'
        dimensions = self.variable_list.netcdf_dimensions[varname]
        var = netcdf.createVariable(
            shortname,
            datatype,
            dimensions,
            **kwargs)
        var.standard_name = self.variable_list.netcdf_standard_name[varname]
        var.long_name = self.variable_list.netcdf_long_name[varname]
        var.units = self.variable_list.netcdf_unit[varname]        

    def repair_variable_dict(self, varname):
        # TODO: complete this function
        if self.variable_list.netcdf_long_name[varname] is None:
            self.variable_list.netcdf_long_name[varname] = self.variable_list.netcdf_short_name[varname]

    def get_variable_dimensions(self, varname):
        try:
            var_dims = self.variable_list.netcdf_dimensions[varname]
        except:
            var_dims = []
            for item in varname:
                var_dims += list(self.variable_list.netcdf_dimensions[item])
            var_dims = tuple(set(var_dims))
        return var_dims
            
    def create_netCDF(self, ncFileName, varname, dimensions=None):
        """Function to create netCDF file"""
        # FIXME: make dimensions a required arg
        netcdf = nc.Dataset(ncFileName, 'w', format=self.format)

        if dimensions is None:
            dimensions = self.get_variable_dimensions(varname)
        for dim in dimensions:
            self.add_dimension(netcdf, dim, self.model_dimensions[dim])

        if isinstance(varname, str):
            varname = [varname]
            
        for item in varname:
            self.add_variable(netcdf, item, zlib=self.zlib, fill_value=vos.MV)
            
        attributeDictionary = self.attributeDictionary
        for k, v in attributeDictionary.items():
            setattr(netcdf,k,v)

        netcdf.sync()
        netcdf.close()
        
    def data2NetCDF(self, ncFileName, varname, varField, timeStamp=None, posCnt=None):
        """Function to write data to netCDF"""
        netcdf = nc.Dataset(ncFileName, 'a')
        short_name = self.variable_list.netcdf_short_name[varname]
        dims = self.variable_list.netcdf_dimensions[varname]
        has_time_dim = any([dim in valid_time_dimnames for dim in dims])
        if has_time_dim:
            self.data2NetCDFWithTime(netcdf, short_name, dims, varField, timeStamp, posCnt)
        else:
            self.data2NetCDFWithoutTime(netcdf, short_name, dims, varField)            
            # self.data2NetCDFWithoutTime(netcdf, short_name, dims, varField)            
        netcdf.sync()
        netcdf.close()
        
    def data2NetCDFWithTime(self, netcdf, shortVarName, var_dims, varField, timeStamp=None, posCnt=None):
        time_dimname = [dim for dim in var_dims if dim in valid_time_dimnames][0]
        date_time = netcdf.variables[time_dimname]
        if posCnt is None:
            posCnt = len(date_time)

        date_time[posCnt] = nc.date2num(
            timeStamp,
            date_time.units,
            date_time.calendar)

        # The CF convention is for latitudes to go from high to low
        # (which corresponds with numpy). Hence if the config specifies
        # NOT to follow CF convention then we must flip the latitude
        # dimension such that latitudes go from low to high.
        if not self.netcdf_y_orientation_follow_cf_convention:
            lat_axis = [index for index,dim in enumerate(var_dims) if dim == 'lat']
            varField = np.flip(varField, axis=-2)
                
        time_axis = [i for i in range(len(var_dims)) if var_dims[i] == time_dimname][0]
        slc = [slice(None)] * len(var_dims)
        slc[time_axis] = posCnt
        netcdf.variables[shortVarName][slc] = varField
    
    def data2NetCDFWithoutTime(self, netcdf, shortVarName, var_dims, varField):
        """Function to write data to netCDF without a time dimension"""
        if not self.netcdf_y_orientation_follow_cf_convention:
            lat_axis = [index for index,dim in enumerate(var_dims) if dim == 'lat']
            if len(lat_axis) == 1:
                varField = np.flip(varField, axis=-2)
        netcdf.variables[shortVarName][:] = varField           
        
    def close(self, ncFileName):
        """Function to close netCDF file"""
        rootgrp = nc.Dataset(ncFileName,'w')
        rootgrp.close()
