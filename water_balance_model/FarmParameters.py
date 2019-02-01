#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
import scipy.special
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
            np.full((self.var.nCell), 12))    # Hours
        self.var.TubewellMaintenanceCost = (
            np.full((self.var.nCell), 10000)) # Rs
        self.var.TubewellInstallationCost = (
            np.full((self.var.nCell), 10000)) # Rs
        self.var.PumpCost = (
            np.full((self.var.nCell), 10000)) # Rs
        self.var.PumpLifespan = (
            np.full((self.var.nCell), 20))    # years
        self.var.PumpHorsePower = (
            np.full((self.var.nCell), 7.5))   # HP
        self.var.TubewellLifespan = (
            np.full((self.var.nCell), 20))    # years
        # self.var.TubewellAge = (
        #     np.zeros((self.var.nFarmSizeCategory, self.var.nCell)))       # counter

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
        initialTubewellCapacityNC = str(
            self.configuration['initialTubewellOwnershipInputFile'])
        tubewell_capacity_varname = str(
            self.configuration['initialTubewellOwnershipVariableName'])
        tubewell_ownership_rate = vos.netcdf2PCRobjCloneWithoutTime(
            initialTubewellCapacityNC,
            tubewell_capacity_varname,
            cloneMapFileName = self.var.cloneMap,
            LatitudeLongitude = True)
        mask = np.broadcast_to(self.var.landmask, tubewell_ownership_rate.shape)
        tubewell_ownership_rate = np.reshape(
            tubewell_ownership_rate[mask],
            (self.var.nFarmSizeCategory, self.var.nCell))
        tubewell_ownership_rate = np.float64(tubewell_ownership_rate)
        self.var.TubewellOwnershipRate = tubewell_ownership_rate.copy()
        self.var.tubewell_count = (
            self.var.TubewellOwnershipRate
            * self.var.nFarmPerCategory
        ).round()
        
    def dynamic(self):
        pass

class CanalAccess(object):

    def __init__(self, var, configuration):
        self.var = var
        self.configuration = configuration
        
    def initial(self):
        initialCanalAccessNC = str(self.configuration['initialCanalAccessInputFile'])
        canal_access_varname = str(self.configuration['initialCanalAccessVariableName'])
        try:
            canal_access = vos.netcdf2PCRobjCloneWithoutTime(
                initialCanalAccessNC,
                canal_access_varname,
                cloneMapFileName = self.var.cloneMap,
                LatitudeLongitude = True)
        except:
            canal_access = np.ones((self.var.nFarmSizeCategory, self.var.nLat, self.var.nLon))

        mask = np.broadcast_to(self.var.landmask, canal_access.shape)
        canal_access = np.reshape(
            canal_access[mask],
            (self.var.nFarmSizeCategory, self.var.nCell))
        canal_access = np.float64(canal_access)
        self.var.CanalAccess = canal_access.copy()
        # print np.max(self.var.CanalAccess)

    def dynamic(self):
        pass

class DieselPrice(object):
    def __init__(self, var, configuration):
        self.var = var
        self.configuration = configuration
        self.DieselPriceFileNC = (
            str(self.configuration['dieselPriceInputFile']))
        self.DieselPriceVarName = (
            str(self.configuration['dieselPriceVariableName']))

    def initial(self):
        self.var.DieselPrice = np.zeros((self.var.nCell))

    def reset_initial_conditions(self):
        pass
    
    def set_diesel_price(self):
        start_of_model_run = (self.var._modelTime.timeStepPCR == 1)
        start_of_year = (self.var._modelTime.doy == 1)
        if not self.DieselPriceFileNC == "None":
            if start_of_model_run or start_of_year:
                date = datetime.datetime(self.var._modelTime.year, 1, 1, 0, 0, 0)
                diesel_price = vos.netcdf2PCRobjClone(
                    self.DieselPriceFileNC,
                    self.DieselPriceVarName,
                    date,
                    useDoy = None,
                    cloneMapFileName = self.var.cloneMap,
                    LatitudeLongitude = True)
                diesel_price = diesel_price[self.var.landmask]
                self.var.DieselPrice = diesel_price

    def dynamic(self):
        self.set_diesel_price()
        # print np.max(self.var.DieselPrice)
        
class FarmParameters(object):
    def __init__(self, var, configuration):
        self.var = var
        self.configuration = configuration
        self.var.nFarm = int(self.configuration['nFarm'])

        # TEMP
        self.var.max_num_tubewells = np.array([2,2,3,3,5], dtype=np.int64)
        farm_index = []
        farm_category = []
        for index,value in enumerate(self.var.max_num_tubewells):
            n = (value + 1) * 2
            farm_index += [index for i in range(n)]
            farm_category += [(index + 1) for i in range(n)]
        self.var.farm_index = np.array(farm_index, dtype=np.int64)
        self.var.farm_category = (
            np.array(farm_category, dtype=np.int64)[:,None]
            * np.ones((self.var.nCell))[None,:]
        )            
        self.var.nFarm = len(self.var.farm_category)
        
        self.var.nFarmSizeCategory = int(self.configuration['nFarmSizeCategory'])
        
        self.var.start_of_agricultural_year = int(self.configuration['startOfAgriculturalYear'])        
        self.FarmAreaFileNC = (
            str(self.configuration['farmAreaInputFile']))
        self.FarmAreaVarName = (
            str(self.configuration['farmAreaVariableName']))
        # self.FarmCategoryFileNC = (
        #     str(self.configuration['farmCategoryInputFile']))
        # self.FarmCategoryVarName = (
        #     str(self.configuration['farmCategoryVariableName']))
        self.FarmCategoryAreaFileNC = (
            str(self.configuration['farmCategoryAreaInputFile']))
        self.FarmCategoryAreaVarName = (
            str(self.configuration['farmCategoryAreaVariableName']))
        self.AnnualChangeInFarmArea = (
            bool(int(self.configuration['annualChangeInFarmArea'])))
        # self.AnnualChangeInFarmCategory = (
        #     bool(int(self.configuration['annualChangeInFarmCategory'])))
        self.AnnualChangeInFarmCategoryArea = (
            bool(int(self.configuration['annualChangeInFarmCategoryArea'])))

        self.tubewell_module = Tubewells(var, configuration)
        self.canal_access_module = CanalAccess(var, configuration)
        self.diesel_price_module = DieselPrice(var, configuration)
        
    def initial(self):
        self.set_farm_area()
        # self.set_farm_category()
        self.set_farm_category_area()
        self.set_number_of_farms_per_category()
        self.diesel_price_module.initial()  # TODO: put this somewhere else...?
        self.tubewell_module.initial()  # TODO: put this in InitialCondition
        self.canal_access_module.initial()  # TODO: put this in InitialCondition
        self.initial_irrigated_rainfed_area()  # TODO: put this in InitialCondition
        self.update_farm_subcategory_area()
        self.update_farm_subcategory_proportion()
        self.update_farm_subcategory_area_equipped_for_irrigation()
        
    def update_first_day_of_year(self):
        """Function to update variables pertaining to the 
        start of the agricultural year
        """
        # note that we do not need to copy because
        # start_of_agricultural_year is an int, which is
        # immutable in Python (unlike a numpy array)
        start_of_agricultural_year = self.var.start_of_agricultural_year
        isLeapYear = calendar.isleap(self.var._modelTime.year)
        if (isLeapYear & (self.var.start_of_agricultural_year >= 60)):
            start_of_agricultural_year += 1
            
        self.var.IsFirstDayOfYear = False
        self.var.IsLastDayOfYear = False
        if self.var._modelTime.doy == start_of_agricultural_year:
            self.var.IsFirstDayOfYear = True
        elif ((self.var._modelTime.doy + 1) == start_of_agricultural_year):
            self.var.IsLastDayOfYear = True

    def set_farm_area(self):
        """Function to read the mean area of each farm within 
        a given farm category.
        """
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
                        (self.var.nFarmSizeCategory, self.var.nLat, self.var.nLon))
                    farm_area_new = np.reshape(
                        farm_area_new[mask],
                        (self.var.nFarmSizeCategory, self.var.nCell))
                    farm_area_new = np.float64(farm_area_new)

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
                        (self.var.nFarmSizeCategory, self.var.nLat, self.var.nLon))
                    farm_area = np.reshape(
                        farm_area[mask],
                        (self.var.nFarmSizeCategory, self.var.nCell)
                    )
                    farm_area = np.float64(farm_area)
                    self.var.FarmArea = farm_area.copy()
                
    def set_farm_category_area(self):
        """Function to read the total area of all farms within 
        a category. For example, if the mean farm size of 
        category one is 2 Ha and there are 100 farms belonging 
        to that category, then the farm category area is 
        2 * 100 = 200 Ha.
        """
        if not self.FarmCategoryAreaFileNC == "None":
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
                        (self.var.nFarmSizeCategory, self.var.nCell)
                    )
                    farm_cat_area_new = np.float64(farm_cat_area_new)                    

                if np.any(self.var.GrowingSeasonDayOne):
                    self.var.FarmCategoryArea[self.var.GrowingSeasonDayOne] = (
                        farm_cat_area_new[self.var.GrowingSeasonDayOne])
                    total_farm_category_area = np.broadcast_to(
                        np.sum(self.var.FarmCategoryArea, axis=0)[None,:],
                        (self.var.nFarmSizeCategory, self.var.nCell)
                    )                
                    scale_factor = np.divide(
                        self.var.FarmCategoryArea,
                        total_farm_category_area,
                        out=np.zeros_like(self.var.FarmCategoryArea),
                        where=total_farm_category_area > 0)
                    self.var.FarmCategoryArea = (
                        self.var.cover_fraction
                        * self.var.grid_cell_area
                        * scale_factor)
                    
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
                        (self.var.nFarmSizeCategory, self.var.nCell)
                    )
                    farm_cat_area = np.float64(farm_cat_area)
                    self.var.FarmCategoryArea = farm_cat_area.copy()

                    total_farm_category_area = np.broadcast_to(
                        np.sum(self.var.FarmCategoryArea, axis=0)[None,:],
                        (self.var.nFarmSizeCategory, self.var.nCell)
                    )                
                    scale_factor = np.divide(
                        self.var.FarmCategoryArea,
                        total_farm_category_area,
                        out=np.zeros_like(self.var.FarmCategoryArea),
                        where=total_farm_category_area > 0)
                    self.var.FarmCategoryArea = (
                        self.var.cover_fraction
                        * self.var.grid_cell_area
                        * scale_factor)
            
    def set_number_of_farms_per_category(self):
        self.var.nFarmPerCategory = (
            self.var.FarmCategoryArea /
            self.var.FarmArea
        ).round()

        # update farm area so that FarmArea * nFarmPerCategory = FarmCategoryArea
        self.var.FarmArea = (
            self.var.FarmCategoryArea
            / self.var.nFarmPerCategory
        )

    def update_tubewell_ownership_rate(self):
        self.var.TubewellOwnershipRate = (
            self.var.tubewell_count
            / self.var.nFarmPerCategory
        )

    def initial_irrigated_rainfed_area(self):
        canal_probability = self.var.CanalAccess.clip(0.,1.)
        
        # now work out the probability of owning n tubewells,
        # up to the maximum number of tubewells per farm category
        num_tubewell_per_subcategory_list = []
        num_farms_per_subcategory_list = []
        for index in range(self.var.nFarmSizeCategory):

            # add one to account for rainfed (i.e. no tubewell)
            num_tubewell_per_subcategory = (
                np.arange(self.var.max_num_tubewells[index] + 1)[:,None]
                * np.ones((self.var.nCell))[None,:]
            )
            
            # we assume the distribution of tubewells can be modelled
            # using the Poisson distribution with parameter lambda, 
            # which we assume to equal the ownership rate. Hence, the
            # probability of owning at least one tubewell is 1 minus
            # the probability of owning none.
            lambdas = self.var.TubewellOwnershipRate[index,...][None,...]
            prob_tubewell = (
                ((lambdas ** num_tubewell_per_subcategory) * np.exp(-lambdas))
                / scipy.special.factorial(num_tubewell_per_subcategory)
            )            
            # divide by sum so that probabilities sum to one, then
            # repeat to account for the same category with/without
            # canal access
            sum_prob_tubewell = np.sum(prob_tubewell, axis=0)
            prob_tubewell /= sum_prob_tubewell[None,...]
            prob_tubewell = np.repeat(prob_tubewell, 2, axis=0)
            num_tubewell_per_subcategory = np.repeat(
                num_tubewell_per_subcategory,
                2,
                axis=0)
            num_tubewell_per_subcategory_list.append(
                num_tubewell_per_subcategory
            )
            # probability of canal for this category
            prob_canal = canal_probability[index,...]
            prob_not_canal = 1. - prob_canal

            # compute proportion of each farm subcategory
            # within a given category
            farm_subcategory_proportion = (
                prob_tubewell *
                np.resize(
                    np.stack(
                        [prob_not_canal, prob_canal],
                        axis=0
                    ),
                    prob_tubewell.shape
                )
            )
            # compute the area of each subcategory
            farm_subcategory_area = (
                self.var.FarmCategoryArea[index,...]
                * farm_subcategory_proportion
            )

            # get the number of farms per subcategory, round to
            # integers while preserving the sum
            # (https://stackoverflow.com/a/792473)
            num_farms_per_subcategory = (
                farm_subcategory_area
                / self.var.FarmArea[index,...]
            )
            num_farms_per_subcategory_floor = np.floor(
                num_farms_per_subcategory
            )
            num_farms_per_subcategory_remainder = (
                num_farms_per_subcategory
                - num_farms_per_subcategory_floor
            )            
            # negate array so that order is descending, then
            # add one so that the order starts at one rather
            # than zero.
            remainder_order = np.argsort(
                -num_farms_per_subcategory_remainder,
                axis=0
            )
            remainder_order += 1
            num_farms_to_add = (
                self.var.nFarmPerCategory[index,...]
                - np.sum(
                    num_farms_per_subcategory_floor,
                    axis=0
                )
            )
            remainder_order[remainder_order > num_farms_to_add] = 0
            num_farms_per_subcategory_floor[remainder_order > 0] += 1
            num_farms_per_subcategory_list.append(num_farms_per_subcategory_floor)

        self.var.num_farms_per_subcategory = np.concatenate(
            num_farms_per_subcategory_list,
            axis=0
        )
        self.var.num_tubewell_per_subcategory = np.concatenate(
            num_tubewell_per_subcategory_list,
            axis=0
        )
        self.var.has_canal_access = np.broadcast_to(
            np.resize(np.array([False,True]), self.var.nFarm)[:,None],
            (self.var.nFarm, self.var.nCell)
        )
        self.var.has_tubewell_access = (
            self.var.num_tubewell_per_subcategory > 0
        )
        self.var.has_irrigation = (
            self.var.has_canal_access
            | self.var.has_tubewell_access
        )
        
    def update_farm_subcategory_area(self):
        self.var.farm_subcategory_area = (
            self.var.FarmArea[self.var.farm_index,...]
            * self.var.num_farms_per_subcategory
        )

    def update_farm_subcategory_proportion(self):
        self.var.farm_subcategory_proportion = (
            self.var.farm_subcategory_area
            / self.var.FarmCategoryArea[self.var.farm_index,...]
        )

    def update_farm_subcategory_area_equipped_for_irrigation(self):
        self.var.area_with_irrigation = (
            self.var.farm_subcategory_area
            * self.var.has_irrigation
        )
        self.var.area_without_irrigation = (
            self.var.farm_subcategory_area
            * np.logical_not(self.var.has_irrigation)
        )
        
    # def update_irrigated_rainfed_area(self):
    #     self.update_farm_subcategory_area()
    #     self.update_farm_subcategory_proportion()
    #     self.update_farm_subcategory_area_equipped_for_irrigation()

    def dynamic(self):
        self.update_first_day_of_year()
        self.set_farm_area()
        self.set_farm_category_area()
        self.set_number_of_farms_per_category()        
        self.diesel_price_module.dynamic()        
        self.tubewell_module.dynamic()
        self.canal_access_module.dynamic()
        self.update_tubewell_ownership_rate()
        # self.update_irrigated_rainfed_area()
        self.update_farm_subcategory_area()
        self.update_farm_subcategory_proportion()
        self.update_farm_subcategory_area_equipped_for_irrigation()
