#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import shutil

from types import NoneType
from collections import OrderedDict
from OutputNetCDF import *

import logging
logger = logging.getLogger(__name__)

class Reporting(object):

    def __init__(self, model, output_dir, netcdf_attr, reporting_options, variable_list, run_id=None):
        self._model = model
        self._modelTime = model._modelTime
        self.output_dir = output_dir
        self.reporting_options = reporting_options
        self.initiate_reporting(netcdf_attr, variable_list, run_id)        

    def create_netcdf_file(self, var, suffix):
        ncFile = self.output_dir + "/" + str(var) + str(suffix) + ".nc"
        self.netcdfObj.create_netCDF(ncFile, var)

    def initiate_reporting(self, netcdf_attr, variable_list, run_id):
        """Function to create netCDF files for each output 
        variable
        """
        self.netcdfObj = OutputNetCDF(
            netcdf_attr,
            self._model.dimensions,
            variable_list)

        if run_id is None:
            run_id = ''
        else:
            run_id = '_' + str(run_id)
        self.run_id = run_id

        self.initiate_daily_total_reporting()
        self.initiate_month_average_reporting()
        self.initiate_month_end_reporting()
        self.initiate_month_total_reporting()
        self.initiate_month_maximum_reporting()
        self.initiate_year_average_reporting()
        self.initiate_year_end_reporting()
        self.initiate_year_total_reporting()
        self.initiate_year_maximum_reporting()
        
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

    def get_variable_names_for_reporting(self, option):
        var_names = [str(var.strip()) for var in self.reporting_options[option].split(',')]
        return list(set(var_names))
    
    def initiate_daily_total_reporting(self):
        self.outDailyTotNC = ["None"]
        try:
            self.outDailyTotNC = self.get_variable_names_for_reporting('outDailyTotNC')
        except:
            pass
        
        if self.outDailyTotNC[0] != "None":
            for var in self.outDailyTotNC:
                logger.info("Creating the netcdf file for reporting the daily value of variable %s.", str(var))
                self.create_netcdf_file(var, self.run_id + "_dailyTot_output")

    def initiate_month_average_reporting(self):
        self.outMonthAvgNC = ["None"]
        try:
            self.outMonthAvgNC = self.get_variable_names_for_reporting('outMonthAvgNC')
        except:
            pass
        if self.outMonthAvgNC[0] != "None":
            for var in self.outMonthAvgNC:
                logger.info("Creating the netcdf file for reporting the monthly average of variable %s.", str(var))
                self.create_netcdf_file(var, self.run_id + "_monthAvg_output")
                vars(self)[var+'_monthAvg'] = np.zeros(vars(self._model)[var].shape[:-1] + (self._model.nLat, self._model.nLon))

    def initiate_month_end_reporting(self):
        self.outMonthEndNC = ["None"]
        try:
            self.outMonthEndNC = list(set(self.reporting_options['outMonthEndNC'].split(",")))
        except:
            pass
        if self.outMonthEndNC[0] != "None":
            for var in self.outMonthEndNC:
                logger.info("Creating the netcdf file for reporting the month end value of variable %s.", str(var))
                self.create_netcdf_file(var, self.run_id + "_monthEnd_output")
                vars(self)[var+'_monthEnd'] = np.zeros(vars(self._model)[var].shape[:-1] + (self._model.nLat, self._model.nLon))

    def initiate_month_total_reporting(self):
        self.outMonthTotNC = ["None"]
        try:
            self.outMonthTotNC = self.get_variable_names_for_reporting('outMonthTotNC')
        except:
            pass
        if self.outMonthTotNC[0] != "None":
            for var in self.outMonthTotNC:
                logger.info("Creating the netcdf file for reporting the monthly average of variable %s.", str(var))
                self.create_netcdf_file(var, self.run_id + "_monthTot_output")
                vars(self)[var+'_monthTot'] = np.zeros(vars(self._model)[var].shape[:-1] + (self._model.nLat, self._model.nLon))

    def initiate_month_maximum_reporting(self):
        self.outMonthMaxNC = ["None"]
        try:
            self.outMonthMaxNC = list(set(self.reporting_options['outMonthMaxNC'].split(",")))
        except:
            pass
        if self.outMonthMaxNC[0] != "None":
            for var in self.outMonthMaxNC:
                logger.info("Creating the netcdf file for reporting the monthly maximum of variable %s.", str(var))
                self.create_netcdf_file(var, self.run_id + "_monthMax_output")
                vars(self)[var+'_monthMax'] = np.zeros(vars(self._model)[var].shape[:-1] + (self._model.nLat, self._model.nLon))

    def initiate_year_average_reporting(self):
        self.outYearAvgNC = ["None"]
        try:
            self.outYearAvgNC = list(set(self.reporting_options['outYearAvgNC'].split(",")))
        except:
            pass
        if self.outYearAvgNC[0] != "None":
            for var in self.outYearAvgNC:
                logger.info("Creating the netcdf file for reporting the yearly average of variable %s.", str(var))
                self.create_netcdf_file(var, self.run_id + "_yearAvg_output")
                vars(self)[var+'_yearAvg'] = np.zeros(vars(self._model)[var].shape[:-1] + (self._model.nLat, self._model.nLon))
                # vars(self)[var+'_yearAvg'] = np.zeros((vars(self._model)[var].shape))

    def initiate_year_end_reporting(self):
        self.outYearEndNC = ["None"]
        try:
            self.outYearEndNC = list(set(self.reporting_options['outYearEndNC'].split(",")))
        except:
            pass
        if self.outYearEndNC[0] != "None":
            for var in self.outYearEndNC:
                logger.info("Creating the netcdf file for reporting the year end value of variable %s.", str(var))
                self.create_netcdf_file(var, self.run_id + "_yearEnd_output")
                vars(self)[var+'_yearEnd'] = np.zeros((vars(self._model)[var].shape))

    def initiate_year_total_reporting(self):
        self.outYearTotNC = ["None"]
        try:
            self.outYearTotNC = self.get_variable_names_for_reporting('outYearTotNC')
        except:
            pass
        if self.outYearTotNC[0] != "None":
            for var in self.outYearTotNC:
                logger.info("Creating the netcdf file for reporting the yearly total of variable %s.", str(var))
                self.create_netcdf_file(var, self.run_id + "_yearTot_output")
                vars(self)[var+'_yearTot'] = np.zeros(vars(self._model)[var].shape[:-1] + (self._model.nLat, self._model.nLon))

    def initiate_year_maximum_reporting(self):
        self.outYearMaxNC = ["None"]
        try:
            self.outYearMaxNC = list(set(self.reporting_options['outYearMaxNC'].split(",")))
        except:
            pass
        if self.outYearMaxNC[0] != "None":
            for var in self.outYearMaxNC:
                logger.info("Creating the netcdf file for reporting the yearly maximum of variable %s.", str(var))
                self.create_netcdf_file(var, self.run_id + "_yearMax_output")
                vars(self)[var+'_yearMax'] = np.zeros(vars(self._model)[var].shape[:-1] + (self._model.nLat, self._model.nLon))
                
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
        self.time_stamp = datetime.datetime(
            self._modelTime.year,
            self._modelTime.month,
            self._modelTime.day,
            0)
        
        self.report_daily_total()
        self.report_month_average()
        self.report_month_end()
        self.report_month_total()
        self.report_month_maximum()
        self.report_year_average()
        self.report_year_end()
        self.report_year_total()
        self.report_year_maximum()
        
    def report_daily_total(self):
        if self.outDailyTotNC[0] != "None":
            for var in self.outDailyTotNC:
                fn = self.output_dir + "/" + str(var) + self.run_id + "_dailyTot_output.nc"
                self.netcdfObj.add_data_to_netcdf(
                    fn,
                    var,
                    self.__getattribute__(var),
                    self.time_stamp)

    def report_month_average(self):
        if self.outMonthAvgNC[0] != "None":
            for var in self.outMonthAvgNC:
                if self._modelTime.day == 1: vars(self)[var+'_monthAvg'].fill(0)
                vars(self)[var+'_monthAvg'] += vars(self)[var]
                if self._modelTime.endMonth:
                    divd = np.min((self._modelTime.timeStepPCR, self._modelTime.day))
                    vars(self)[var+'_monthAvg'] = vars(self)[var+'_monthAvg'] / divd
                    fn = self.output_dir + "/" + str(var) + self.run_id + "_monthAvg_output.nc"
                    self.netcdfObj.add_data_to_netcdf(
                        fn,
                        var,
                        self.__getattribute__(var+'_monthAvg'),
                        self.time_stamp)
                    
    def report_month_end(self):
        if self.outMonthEndNC[0] != "None":
            for var in self.outMonthEndNC:
                if self._modelTime.endMonth:
                    vars(self)[var+'_monthEnd'] = vars(self)[var]
                    fn = self.output_dir + "/" + str(var) + self.run_id + "_monthEnd_output.nc"
                    self.netcdfObj.add_data_to_netcdf(
                        fn,
                        var,
                        self.__getattribute__(var+'_monthEnd'),
                        self.time_stamp)

    def report_month_total(self):
        if self.outMonthTotNC[0] != "None":
            for var in self.outMonthTotNC:
                if self._modelTime.day == 1: vars(self)[var+'_monthTot'].fill(0)
                vars(self)[var+'_monthTot'][...,self._model.landmask] += vars(self)[var][...,self._model.landmask]
                
                if self._modelTime.endMonth:
                    fn = self.output_dir + "/" + str(var) + self.run_id + "_monthTot_output.nc"
                    self.netcdfObj.add_data_to_netcdf(
                        fn,
                        var,
                        self.__getattribute__(var+'_monthTot'),
                        self.time_stamp)                    

    def report_month_maximum(self):
        if self.outMonthMaxNC[0] != "None":
            for var in self.outMonthMaxNC:
                if self._modelTime.day == 1: vars(self)[var+'_monthMax'].fill(0)
                vars(self)[var+'_monthMax'] = vars(self)[var+'_monthMax'].clip(vars(self)[var], None)
                if self._modelTime.endMonth:
                    fn = self.output_dir + "/" + str(var) + self.run_id + "_monthMax_output.nc"
                    self.netcdfObj.add_data_to_netcdf(
                        fn,
                        var,
                        self.__getattribute__(var+'_monthMax'),
                        self.time_stamp)                    

    def report_year_average(self):
        if self.outYearAvgNC[0] != "None":
            for var in self.outYearAvgNC:
                if self._modelTime.doy == 1: vars(self)[var+'_yearAvg'].fill(0)
                vars(self)[var+'_yearAvg'] += vars(self)[var]
                if self._modelTime.endYear:
                    divd = np.min((self._modelTime.timeStepPCR, self._modelTime.doy))
                    vars(self)[var+'_yearAvg'] = vars(self)[var+'_yearAvg'] / divd
                    fn = self.output_dir + "/" + str(var) + self.run_id + "_yearAvg_output.nc"
                    self.netcdfObj.add_data_to_netcdf(
                        fn,
                        var,
                        self.__getattribute__(var+'_yearAvg'),
                        self.time_stamp)
                    

    def report_year_end(self):
        if self.outYearEndNC[0] != "None":
            for var in self.outYearEndNC:
                if self._modelTime.endYear:
                    vars(self)[var+'_yearEnd'] = vars(self)[var]
                    fn = self.output_dir + "/" + str(var) + self.run_id + "_yearEnd_output.nc"
                    self.netcdfObj.add_data_to_netcdf(
                        fn,
                        var,
                        self.__getattribute__(var+'_yearEnd'),
                        self.time_stamp)

    def report_year_total(self):
        if self.outYearTotNC[0] != "None":
            for var in self.outYearTotNC:
                if self._modelTime.doy == 1: vars(self)[var+'_yearTot'].fill(0)
                vars(self)[var+'_yearTot'][...,self._model.landmask] += vars(self)[var][...,self._model.landmask]
                if self._modelTime.endYear:
                    fn = self.output_dir + "/" + str(var) + self.run_id + "_yearTot_output.nc"
                    self.netcdfObj.add_data_to_netcdf(
                        fn,
                        var,
                        self.__getattribute__(var+'_yearTot'),
                        self.time_stamp)                    

    def report_year_maximum(self):
        if self.outYearMaxNC[0] != "None":
            for var in self.outYearMaxNC:
                if self._modelTime.doy == 1:
                    vars(self)[var+'_yearMax'].fill(0)
                vars(self)[var+'_yearMax'] = vars(self)[var+'_yearMax'].clip(vars(self)[var], None)
                if self._modelTime.endYear:
                    fn = self.output_dir + "/" + str(var) + self.run_id + "_yearMax_output.nc"
                    self.netcdfObj.add_data_to_netcdf(
                        fn,
                        var,
                        self.__getattribute__(var+'_yearMax'),
                        self.time_stamp)
