#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
import pcraster as pcr
import netCDF4 as nc
import datetime as datetime
import calendar as calendar
import VirtualOS as vos

import logging
logger = logging.getLogger(__name__)

class Tubewells(object):
    def __init__(self, var, configuration):
        self.var = var
        self.configuration = configuration
        
    def initial(self):
        self.initial_tubewell_capacity()
        self.var.TubewellOperatingHours = (
            np.full((self.var.nFarm, self.var.nCell), 12))    # Hours
        self.var.TubewellMaintenanceCost = (
            np.full((self.var.nFarm, self.var.nCell), 10000)) # Rs
        self.var.TubewellInstallationCost = (
            np.full((self.var.nFarm, self.var.nCell), 10000)) # Rs
        self.var.PumpCost = (
            np.full((self.var.nFarm, self.var.nCell), 10000)) # Rs
        self.var.PumpLifespan = (
            np.full((self.var.nFarm, self.var.nCell), 20))    # years
        self.var.PumpHorsePower = (
            np.full((self.var.nFarm, self.var.nCell), 7.5))   # HP
        self.var.TubewellLifespan = (
            np.full((self.var.nFarm, self.var.nCell), 20))    # years
        self.var.TubewellAge = (
            np.zeros((self.var.nFarm, self.var.nCell)))       # counter

    def reset_initial_conditions(self):
        pass
    
    def maximum_operating_hours(self):
        pass
    
    def maintenance_cost(self):
        pass

    def installation_cost(self):
        pass

    def pump_cost(self):
        pass

    def pump_horsepower(self):
        pass
        
    def initial_tubewell_capacity(self):

        # TODO - this is where initial tubewell ownership is read to the model

        initialTubewellCapacityNC = str(
            self.configuration['initialTubewellOwnershipInputFile'])
        tubewell_capacity_varname = str(
            self.configuration['initialTubewellOwnershipVariableName'])
        tubewell_count = vos.netcdf2PCRobjCloneWithoutTime(
            initialTubewellCapacityNC,
            tubewell_capacity_varname,
            cloneMapFileName = self.var.cloneMap,
            LatitudeLongitude = True)
        mask = np.broadcast_to(self.var.landmask, tubewell_count.shape)
        tubewell_count = np.reshape(
            tubewell_count[mask],
            (self.var.nFarm, self.var.nCell))
        self.var.TubewellCount = tubewell_count.copy()
        
    def dynamic(self):
        pass

class CanalAccess(object):

    def __init__(self, var, configuration):
        self.var = var
        self.configuration = configuration
        
    def initial(self):
        initialCanalAccessNC = str(self.configuration['initialCanalAccessNC'])
        canal_access_varname = 'canal_access'
        try:
            canal_access = vos.netcdf2PCRobjCloneWithoutTime(
                initialCanalAccessNC,
                canal_access_varname,
                cloneMapFileName = self.var.cloneMap,
                LatitudeLongitude = True)
        except:
            canal_access = np.ones((self.var.nFarm, self.var.nLat, self.var.nLon))

        mask = np.broadcast_to(self.var.landmask, canal_access.shape)
        canal_access = np.reshape(
            canal_access[mask],
            (self.var.nFarm, self.var.nCell))            
        self.var.CanalAccess = canal_access.copy()
        # print np.max(self.var.CanalAccess)

    def dynamic(self):
        pass

# # ***TODO***:
# class FarmCategory(object):
#     """Class to represent farm category data"""
# class FarmArea(object):
#     """Class to represent the area of each farm"""

class FarmParameters(object):
    def __init__(self, var, configuration):
        self.var = var
        self.configuration = configuration
        
        self.var.nFarm = int(self.configuration['nFarm'])
        self.var.nFarmSizeCategory = int(self.configuration['nFarmSizeCategory'])
        self.var.StartOfYear = 305  # TODO: check this is right, and add to configuration
        
        self.FarmAreaFileNC = (
            str(self.configuration['farmAreaInputFile']))
        self.FarmAreaVarName = (
            str(self.configuration['farmAreaVariableName']))
        self.FarmCategoryFileNC = (
            str(self.configuration['farmCategoryInputFile']))
        self.FarmCategoryVarName = (
            str(self.configuration['farmCategoryVariableName']))
        self.FarmCategoryAreaFileNC = (
            str(self.configuration['farmCategoryAreaInputFile']))
        self.FarmCategoryAreaVarName = (
            str(self.configuration['farmCategoryAreaVariableName']))
        self.AnnualChangeInFarmArea = (
            bool(int(self.configuration['annualChangeInFarmArea'])))
        self.AnnualChangeInFarmCategory = (
            bool(int(self.configuration['annualChangeInFarmCategory'])))
        self.AnnualChangeInFarmCategoryArea = (
            bool(int(self.configuration['annualChangeInFarmCategoryArea'])))

        self.tubewell_module = Tubewells(var, configuration)
        self.canal_access_module = CanalAccess(var, configuration)
        
    def initial(self):
        self.set_farm_category()
        self.set_farm_category_area()
        self.set_farm_area()
        self.tubewell_module.initial()
        self.canal_access_module.initial()
        
    def update_first_day_of_year(self):
        isLeapYear = calendar.isleap(self.var._modelTime.year)
        if (isLeapYear & (self.var.StartOfYear >= 60)):
            start_of_year += 1
            
        self.var.IsFirstDayOfYear = False
        self.var.IsLastDayOfYear = False
        if self.var._modelTime.doy == self.var.StartOfYear:
            self.var.IsFirstDayOfYear = True
        elif ((self.var._modelTime.doy + 1) == self.var.StartOfYear):
            self.var.IsLastDayOfYear = True

    def set_farm_area(self):
        if not self.FarmAreaFileNC == "None":
            start_of_model_run = (self.var._modelTime.timeStepPCR == 1)
            start_of_year = (self.var._modelTime.doy == 1)
            if self.AnnualChangeInFarmArea:
                if start_of_model_run or start_of_year:
                    date = datetime.datetime(self.var._modelTime.year, 1, 1, 0, 0, 0)
                    farm_area_new = vos.netcdf2PCRobjClone(
                        self.FarmAreaFileNC,
                        self.FarmAreaVarName,
                        date,
                        useDoy = None,
                        cloneMapFileName = self.var.cloneMap,
                        LatitudeLongitude = True)
                    mask = np.broadcast_to(
                        self.var.landmask,
                        (self.var.nFarm, self.var.nLat, self.var.nLon))
                    farm_area_new = np.reshape(
                        farm_area_new[mask],
                        (self.var.nFarm, self.var.nCell))

                if np.any(self.var.GrowingSeasonDayOne[0,:,:]):
                    self.var.FarmArea[self.var.GrowingSeasonDayOne[0,:,:]] = (
                        farm_area_new[self.var.GrowingSeasonDayOne[0,:,:]])
            else:
                if start_of_model_run:
                    farm_area = vos.netcdf2PCRobjCloneWithoutTime(
                        self.FarmAreaFileNC,
                        self.FarmAreaVarName,
                        cloneMapFileName = self.var.cloneMap)
                    mask = np.broadcast_to(
                        self.var.landmask,
                        (self.var.nFarm, self.var.nLat, self.var.nLon))
                    farm_area = np.reshape(
                        farm_area[mask],
                        (self.var.nFarm, self.var.nCell))
                    self.var.FarmArea = farm_area.copy()
                
    def set_farm_category_area(self):
        if not self.var.FarmCategoryAreaFileNC == "None":
            start_of_model_run = (self.var._modelTime.timeStepPCR == 1)
            start_of_year = (self.var._modelTime.doy == 1)
            if self.AnnualChangeInFarmCategoryArea:
                if start_of_model_run or start_of_year:
                    date = datetime.datetime(self.var._modelTime.year, 1, 1, 0, 0, 0)
                    farm_cat_area_new = vos.netcdf2PCRobjClone(
                        self.FarmCategoryAreaFileNC,
                        self.FarmCategoryAreaVarName,
                        date,
                        useDoy = None,
                        cloneMapFileName = self.var.cloneMap,
                        LatitudeLongitude = True)
                    mask = np.broadcast_to(
                        self.var.landmask,
                        (self.var.nFarmSizeCategory, self.var.nLat, self.var.nLon))
                    farm_cat_area_new = np.reshape(
                        farm_cat_area_new[mask],
                        (self.var.nFarmSizeCategory, self.var.nCell))

                if np.any(self.var.GrowingSeasonDayOne):
                    self.var.FarmCategoryArea[self.var.GrowingSeasonDayOne] = (
                        farm_cat_area_new[self.var.GrowingSeasonDayOne])
            else:
                if start_of_model_run:
                    farm_cat_area = vos.netcdf2PCRobjCloneWithoutTime(
                        self.FarmCategoryAreaFileNC,
                        self.FarmCategoryAreaVarName,
                        cloneMapFileName = self.var.cloneMap)
                    mask = np.broadcast_to(
                        self.var.landmask,
                        (self.var.nFarmSizeCategory, self.var.nLat, self.var.nLon))
                    farm_cat_area = np.reshape(
                        farm_cat_area[mask],
                        (self.var.nFarmSizeCategory, self.var.nCell))
                    self.var.FarmCategoryArea = farm_cat_area.copy()
            
    def set_farm_category(self):
        if not self.var.FarmCategoryFileNC == "None":
            start_of_model_run = (self.var._modelTime.timeStepPCR == 1)
            start_of_year = (self.var._modelTime.doy == 1)
            if self.AnnualChangeInFarmCategory:
                if start_of_model_run or start_of_year:
                    date = datetime.datetime(self.var._modelTime.year, 1, 1, 0, 0, 0)
                    farm_category_new = vos.netcdf2PCRobjClone(
                        self.FarmCategoryFileNC,
                        self.FarmCategoryVarName,
                        date,
                        useDoy = None,
                        cloneMapFileName = self.var.cloneMap,
                        LatitudeLongitude = True)
                    mask = np.broadcast_to(
                        self.var.landmask,
                        (self.var.nFarm, self.var.nLat, self.var.nLon))
                    farm_category_new = np.reshape(
                        farm_category_new[mask],
                        (self.var.nFarm, self.var.nCell))

                if np.any(self.var.GrowingSeasonDayOne):
                    self.var.FarmCategory[self.var.GrowingSeasonDayOne[0,:,:]] = (
                        farm_category_new[self.var.GrowingSeasonDayOne[0,:,:]])
            else:
                if start_of_model_run:
                    farm_category = vos.netcdf2PCRobjCloneWithoutTime(
                        self.FarmCategoryFileNC,
                        self.FarmCategoryVarName,
                        cloneMapFileName = self.var.cloneMap)
                    mask = np.broadcast_to(
                        self.var.landmask,
                        (self.var.nFarm, self.var.nLat, self.var.nLon))
                    farm_category = np.reshape(
                        farm_category[mask],
                        (self.var.nFarm, self.var.nCell))
                    self.var.FarmCategory = farm_category.copy()
                            
    def dynamic(self):
        self.update_first_day_of_year()
        self.set_farm_area()
        self.set_farm_category()
        self.set_farm_category_area()
        self.tubewell_module.dynamic()
        self.canal_access_module.dynamic()
