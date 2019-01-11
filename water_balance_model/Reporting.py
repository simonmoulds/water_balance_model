#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import shutil

from types import NoneType
from collections import OrderedDict
from ncConverter import *
# import variable_list as varDicts
# import variable_list

import logging
logger = logging.getLogger(__name__)

class Reporting(object):
    
    def __init__(self, configuration, model, modelTime, variable_list, run_id=None):

        self._model = model
        self._modelTime = modelTime
        self.configuration = configuration
        self.initiate_reporting(variable_list, run_id)

    def create_netcdf_file(self, var, suffix):
        ncFile = self.outNCDir + "/" + str(var) + str(suffix) + ".nc"
        self.netcdfObj.create_netCDF(ncFile, var)

    def initiate_reporting(self, variable_list, run_id):
        """Function to create netCDF files for each output 
        variable
        """
        self.outNCDir  = self.configuration.outNCDir
        self.netcdfObj = np2netCDF(
            self.configuration,
            self._model.dimensions,
            variable_list)

        if run_id is None:
            run_id = ''
        else:
            run_id = '_' + str(run_id)
        self.run_id = run_id
        
        # daily output in netCDF files:
        # #############################        
        self.outDailyTotNC = ["None"]
        try:
            self.outDailyTotNC = list(set([str(var.strip()) for var in self.configuration.reportingOptions['outDailyTotNC'].split(",")]))
        except:
            pass
        
        if self.outDailyTotNC[0] != "None":
            for var in self.outDailyTotNC:
                logger.info("Creating the netcdf file for reporting the daily value of variable %s.", str(var))
                self.create_netcdf_file(var, self.run_id + "_dailyTot_output")

        # month average in netCDF files:
        # ##############################
        self.outMonthAvgNC = ["None"]
        try:
            self.outMonthAvgNC = list(set(self.configuration.reportingOptions['outMonthAvgNC'].split(",")))
        except:
            pass
        if self.outMonthAvgNC[0] != "None":
            for var in self.outMonthAvgNC:
                logger.info("Creating the netcdf file for reporting the monthly average of variable %s.", str(var))
                self.create_netcdf_file(var, self.run_id + "_monthAvg_output")
                vars(self)[var+'_monthAvg'] = np.zeros(vars(self._model)[var].shape[:-1] + (self._model.nLat, self._model.nLon))
                
        # month end in netCDF files:
        # ##########################
        self.outMonthEndNC = ["None"]
        try:
            self.outMonthEndNC = list(set(self.configuration.reportingOptions['outMonthEndNC'].split(",")))
        except:
            pass
        if self.outMonthEndNC[0] != "None":
            for var in self.outMonthEndNC:
                logger.info("Creating the netcdf file for reporting the month end value of variable %s.", str(var))
                self.create_netcdf_file(var, self.run_id + "_monthEnd_output")
                vars(self)[var+'_monthEnd'] = np.zeros((vars(self._model)[var].shape))

        # month total in netCDF files:
        # ############################
        self.outMonthTotNC = ["None"]
        try:
            self.outMonthTotNC = list(set(self.configuration.reportingOptions['outMonthTotNC'].split(",")))
        except:
            pass
        if self.outMonthTotNC[0] != "None":
            for var in self.outMonthTotNC:
                logger.info("Creating the netcdf file for reporting the monthly average of variable %s.", str(var))
                self.create_netcdf_file(var, self.run_id + "_monthTot_output")
                vars(self)[var+'_monthTot'] = np.zeros((vars(self._model)[var].shape))

        # month maximum in netCDF files:
        # ##############################
        self.outMonthMaxNC = ["None"]
        try:
            self.outMonthMaxNC = list(set(self.configuration.reportingOptions['outMonthMaxNC'].split(",")))
        except:
            pass
        if self.outMonthMaxNC[0] != "None":
            for var in self.outMonthMaxNC:
                logger.info("Creating the netcdf file for reporting the monthly maximum of variable %s.", str(var))
                self.create_netcdf_file(var, self.run_id + "_monthMax_output")
                vars(self)[var+'_monthMax'] = np.zeros((vars(self._model)[var].shape))

        # year average in netCDF files:
        # ##############################
        self.outYearAvgNC = ["None"]
        try:
            self.outYearAvgNC = list(set(self.configuration.reportingOptions['outYearAvgNC'].split(",")))
        except:
            pass
        if self.outYearAvgNC[0] != "None":
            for var in self.outYearAvgNC:
                logger.info("Creating the netcdf file for reporting the yearly average of variable %s.", str(var))
                self.create_netcdf_file(var, self.run_id + "_yearAvg_output")
                vars(self)[var+'_yearAvg'] = np.zeros(vars(self._model)[var].shape[:-1] + (self._model.nLat, self._model.nLon))
                # vars(self)[var+'_yearAvg'] = np.zeros((vars(self._model)[var].shape))
                
        # year end in netCDF files:
        # ##########################
        self.outYearEndNC = ["None"]
        try:
            self.outYearEndNC = list(set(self.configuration.reportingOptions['outYearEndNC'].split(",")))
        except:
            pass
        if self.outYearEndNC[0] != "None":
            for var in self.outYearEndNC:
                logger.info("Creating the netcdf file for reporting the year end value of variable %s.", str(var))
                self.create_netcdf_file(var, self.run_id + "_yearEnd_output")
                vars(self)[var+'_yearEnd'] = np.zeros((vars(self._model)[var].shape))

        # year total in netCDF files:
        # ############################
        self.outYearTotNC = ["None"]
        try:
            self.outYearTotNC = list(set(self.configuration.reportingOptions['outYearTotNC'].split(",")))
        except:
            pass
        if self.outYearTotNC[0] != "None":
            for var in self.outYearTotNC:
                logger.info("Creating the netcdf file for reporting the yearly total of variable %s.", str(var))
                self.create_netcdf_file(var, self.run_id + "_yearTot_output")
                vars(self)[var+'_yearTot'] = np.zeros(vars(self._model)[var].shape[:-1] + (self._model.nLat, self._model.nLon))

        # year maximum in netCDF files:
        # ##############################
        self.outYearMaxNC = ["None"]
        try:
            self.outYearMaxNC = list(set(self.configuration.reportingOptions['outYearMaxNC'].split(",")))
        except:
            pass
        if self.outYearMaxNC[0] != "None":
            for var in self.outYearMaxNC:
                logger.info("Creating the netcdf file for reporting the yearly maximum of variable %s.", str(var))
                self.create_netcdf_file(var, self.run_id + "_yearMax_output")
                vars(self)[var+'_yearMax'] = np.zeros(vars(self._model)[var].shape[:-1] + (self._model.nLat, self._model.nLon))
                
        # list of variables that will be reported:
        self.variables_for_report = (
            self.outDailyTotNC +
            self.outMonthAvgNC +
            self.outMonthEndNC +
            self.outMonthTotNC +
            self.outMonthMaxNC +
            self.outYearAvgNC +
            self.outYearEndNC +
            self.outYearTotNC +
            self.outYearMaxNC
            )

        # reduce above list to unique values, and remove None
        self.variables_for_report = list(set(self.variables_for_report))
        if "None" in self.variables_for_report:
            self.variables_for_report.remove("None")

    def post_processing(self):
        """Function to process model variables to output variables. 
        This generally means assigning values to an array with 
        spatial dimensions equal to those of the current landmask.
        """
        if len(self.variables_for_report) > 0:
            for var in self.variables_for_report:
                d = vars(self._model)[var]
                arr = np.ones(d.shape[:-1] + (self._model.nLat, self._model.nLon)) * vos.MV
                arr[...,self._model.landmask] = d
                vars(self)[var] = arr
               
    def report(self):
        
        logger.info("reporting for time %s", self._modelTime.currTime)
        self.post_processing()
        timeStamp = datetime.datetime(
            self._modelTime.year,
            self._modelTime.month,
            self._modelTime.day,
            0)

        if self.outDailyTotNC[0] != "None":
            for var in self.outDailyTotNC:
                fn = self.outNCDir + "/" + str(var) + self.run_id + "_dailyTot_output.nc"
                self.netcdfObj.data2NetCDF(fn,
                                           var,
                                           self.__getattribute__(var),
                                           timeStamp)

        if self.outMonthAvgNC[0] != "None":
            for var in self.outMonthAvgNC:
                if self._modelTime.day == 1: vars(self)[var+'_monthAvg'].fill(0)
                vars(self)[var+'_monthAvg'] += vars(self)[var]
                if self._modelTime.endMonth:
                    divd = np.min((self._modelTime.timeStepPCR, self._modelTime.day))
                    vars(self)[var+'_monthAvg'] = vars(self)[var+'_monthAvg'] / divd
                    self.netcdfObj.data2NetCDF(self.outNCDir+"/"+str(var)+"_monthAvg_output.nc",
                                               var,
                                               self.__getattribute__(var+'_monthAvg'),
                                               timeStamp)
                    

        if self.outMonthEndNC[0] != "None":
            for var in self.outMonthEndNC:
                if self._modelTime.endMonth:
                    vars(self)[var+'_monthEnd'] = vars(self)[var]
                    self.netcdfObj.data2NetCDF(self.outNCDir+"/"+str(var)+"_monthEnd_output.nc",
                                               var,
                                               self.__getattribute__(var+'_monthEnd'),
                                               timeStamp)
                    
        if self.outMonthTotNC[0] != "None":
            for var in self.outMonthTotNC:
                if self._modelTime.day == 1: vars(self)[var+'_monthAvg'].fill(0)
                vars(self)[var+'_monthAvg'] += vars(self)[var]
                if self._modelTime.endMonth:
                    self.netcdfObj.data2NetCDF(self.outNCDir+"/"+str(var)+"_monthTot_output.nc",
                                               var,
                                               self.__getattribute__(var+'_monthAvg'),
                                               timeStamp)                    

        if self.outMonthMaxNC[0] != "None":
            for var in self.outMonthMaxNC:
                if self._modelTime.day == 1: vars(self)[var+'_monthMax'].fill(0)
                vars(self)[var+'_monthMax'].clip(vars(self)[var], None)
                if self._modelTime.endMonth:
                    self.netcdfObj.data2NetCDF(self.outNCDir+"/"+str(var)+"_monthMax_output.nc",
                                               var,
                                               self.__getattribute__(var+'_monthMax'),
                                               timeStamp)                    
                
        if self.outYearAvgNC[0] != "None":
            for var in self.outYearAvgNC:
                if self._modelTime.doy == 1: vars(self)[var+'_yearAvg'].fill(0)
                vars(self)[var+'_yearAvg'] += vars(self)[var]
                if self._modelTime.endYear:
                    divd = np.min((self._modelTime.timeStepPCR, self._modelTime.doy))
                    vars(self)[var+'_yearAvg'] = vars(self)[var+'_yearAvg'] / divd
                    self.netcdfObj.data2NetCDF(self.outNCDir+"/"+str(var)+"_yearAvg_output.nc",
                                               var,
                                               self.__getattribute__(var+'_yearAvg'),
                                               timeStamp)
                    

        if self.outYearEndNC[0] != "None":
            for var in self.outYearEndNC:
                if self._modelTime.endYear:
                    vars(self)[var+'_yearEnd'] = vars(self)[var]
                    self.netcdfObj.data2NetCDF(self.outNCDir+"/"+str(var)+"_yearEnd_output.nc",
                                               var,
                                               self.__getattribute__(var+'_yearEnd'),
                                               timeStamp)
                    
        if self.outYearTotNC[0] != "None":
            for var in self.outYearTotNC:
                if self._modelTime.doy == 1: vars(self)[var+'_yearTot'].fill(0)
                vars(self)[var+'_yearTot'][...,self._model.landmask] += vars(self)[var][...,self._model.landmask]
                if self._modelTime.endYear:
                    self.netcdfObj.data2NetCDF(self.outNCDir+"/"+str(var)+"_yearTot_output.nc",
                                               var,
                                               self.__getattribute__(var+'_yearTot'),
                                               timeStamp)                    

        if self.outYearMaxNC[0] != "None":
            for var in self.outYearMaxNC:
                if self._modelTime.doy == 1:
                    vars(self)[var+'_yearMax'].fill(0)
                vars(self)[var+'_yearMax'] = np.clip(vars(self)[var+'_yearMax'], vars(self)[var], None)
                if self._modelTime.endYear:
                    self.netcdfObj.data2NetCDF(self.outNCDir+"/"+str(var)+"_yearMax_output.nc",
                                               var,
                                               self.__getattribute__(var+'_yearMax'),
                                               timeStamp)
