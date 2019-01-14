#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
import pcraster as pcr
import VirtualOS as vos
import netCDF4 as nc
import datetime as datetime
import calendar as calendar

class CropParameters(object):
    def __init__(self, var, configuration):
        self.var = var
        self.configuration = configuration
        self.var.nCrop = int(self.configuration['nCrop'])

        self.CropParameterNC = str(self.configuration['cropParameterInputFile'])
        self.crop_parameters_to_read = [
            'PlantingDate','HarvestDate',
            'L_ini','L_dev','L_mid','L_late',
            'Kc_ini','Kc_mid','Kc_end','p_std',
            'Zmin','Zmax','Ky']

        self.crop_parameters_to_compute = [
            'L_ini_day','L_dev_day','L_mid_day','L_late_day',
            'PlantingDateAdj','HarvestDateAdj']

        # initialise parameters
        self.crop_parameter_names = (
            self.crop_parameters_to_read
            + self.crop_parameters_to_compute)
        arr_zeros = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))
        for param in self.crop_parameter_names:
            vars(self.var)[param] = np.copy(arr_zeros)

        # potential yield
        self.crop_parameter_names += ['Yx']
        self.PotYieldNC = self.configuration['potentialYieldInputFile']
        self.PotYieldVarName = self.configuration['potentialYieldVariableName']
        self.AnnualChangeInPotYield = bool(int(self.configuration['annualChangeInPotentialYield']))

        # landmask, broadcast to crop dimension
        self.var.landmask_crop = (
            self.var.landmask[None,:,:]
            * np.ones((self.var.nCrop), dtype=np.bool)[:,None,None])
        
        arr_zeros = np.zeros((self.var.nCrop, self.var.nCell))
        self.var.CropDead = np.copy(arr_zeros).astype(bool)
        self.var.CropMature = np.copy(arr_zeros).astype(bool)        
        self.read() 
        
    def initial(self):
        arr_zeros = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))
        self.var.GrowingSeasonIndex = np.copy(arr_zeros.astype(bool))
        self.var.GrowingSeasonDayOne = np.copy(arr_zeros.astype(bool))
        self.var.DAP = np.copy(arr_zeros)
        
    def read(self):
        """Function to read crop input parameters"""
        if len(self.crop_parameters_to_read) > 0:
            for param in self.crop_parameters_to_read:
                d = vos.netcdf2PCRobjCloneWithoutTime(
                    self.CropParameterNC,
                    param,
                    cloneMapFileName=self.var.cloneMap)
                d = d[self.var.landmask_crop].reshape(self.var.nCrop,self.var.nCell)
                vars(self.var)[param] = np.broadcast_to(
                    d,
                    (self.var.nFarm, self.var.nCrop, self.var.nCell))
        
    def adjust_planting_and_harvesting_date(self):
        """Function to adjust planting and harvest dates 
        (given as day of year) for leap years.
        """
        if self.var._modelTime.timeStepPCR == 1 or self.var._modelTime.doy == 1:            
            pd = self.var.PlantingDate.copy()
            hd = self.var.HarvestDate.copy()
            isLeapYear1 = calendar.isleap(self.var._modelTime.currTime.year)
            pd[(isLeapYear1 & (pd >= 60))] += 1
            hd[(isLeapYear1 & (hd >= 60) & (hd > pd))] += 1            
            self.var.PlantingDateAdj = np.copy(pd)
            self.var.HarvestDateAdj = np.copy(hd)

    def update_growing_season(self):
        """Function to update growing season based on 
        adjusted planting and harvest dates
        """
        cond1 = ((self.var.PlantingDateAdj < self.var.HarvestDateAdj)
                 & ((self.var.PlantingDateAdj <= self.var._modelTime.doy)
                    & (self.var._modelTime.doy <= self.var.HarvestDateAdj)))
        cond2 = ((self.var.PlantingDateAdj > self.var.HarvestDateAdj)
                 & ((self.var.PlantingDateAdj <= self.var._modelTime.doy)
                    | (self.var._modelTime.doy <= self.var.HarvestDateAdj)))

        # check the harvest date is before the end of the simulation period
        hd_arr = (
            np.datetime64(str(datetime.datetime(self.var._modelTime.year, 1, 1)))
            + np.array(self.var.HarvestDateAdj - 1, dtype='timedelta64[D]')
        )        
        cond3 = hd_arr <= np.datetime64(str(self.var._modelTime.endTime))

        # check the planting date is after the start of the simaltion period
        cond4 = ((self.var._modelTime.doy - self.var.PlantingDateAdj) < self.var._modelTime.timeStepPCR)

        self.var.GrowingSeason = ((cond1 | cond2) & cond3 & cond4)
        self.var.GrowingSeasonIndex = self.var.GrowingSeason.copy()
        self.var.GrowingSeasonIndex *= np.logical_not(self.var.CropDead | self.var.CropMature)
        self.var.GrowingSeasonDayOne = self.var._modelTime.doy == self.var.PlantingDateAdj
        # self.var.DAP[self.var.GrowingSeasonDayOne] = 0
        self.var.GrowingSeasonIndex[self.var.GrowingSeasonDayOne] = True
        # self.var.DAP[self.var.GrowingSeasonIndex] += 1
        # self.var.DAP[np.logical_not(self.var.GrowingSeasonIndex)] = 0

    def update_days_after_planting(self):
        """Function to update days after planting"""
        self.var.DAP[self.var.GrowingSeasonDayOne] = 0
        # self.var.GrowingSeasonIndex[self.var.GrowingSeasonDayOne] = True
        self.var.DAP[self.var.GrowingSeasonIndex] += 1
        self.var.DAP[np.logical_not(self.var.GrowingSeasonIndex)] = 0
        
    def compute_growth_stage_length(self):

        if np.any(self.var.GrowingSeasonDayOne):
            nday = self.var.HarvestDateAdj - self.var.PlantingDateAdj
            nday[nday < 0] += 365
            # correct nday by adding one, because e.g. 20-10=10 but len(10:20)=11
            nday += 1
            
            ndaymax = np.max(nday).astype(np.int32)
            tmp = (
                np.ones((ndaymax, self.var.nFarm, self.var.nCrop, self.var.nCell))
                * np.arange(1, ndaymax + 1)[:,None,None,None]
                )            
            frac = np.divide(tmp,nday)

            L_accum = np.cumsum(
                np.concatenate(
                    (self.var.L_ini[None,:],
                     self.var.L_dev[None,:],
                     self.var.L_mid[None,:],
                     self.var.L_late[None,:])),
                axis=0)

            self.var.L_ini_day = (
                np.sum(
                    (frac <= L_accum[0,:]),
                    axis=0,
                    dtype=np.float64)
                )
            
            self.var.L_dev_day = (
                np.sum(
                    (frac > L_accum[0,:])
                    & (frac <= L_accum[1,:]),
                    axis=0,
                    dtype=np.float64)
                )
                
            self.var.L_mid_day = (
                np.sum(
                    (frac > L_accum[1,:])
                    & (frac <= L_accum[2,:]),
                    axis=0,
                    dtype=np.float64)
                )
                
            self.var.L_late_day = (
                np.sum(
                    (frac > L_accum[2,:])
                    & (frac <= L_accum[3,:]),
                    axis=0,
                    dtype=np.float64)
                )            

    def read_potential_crop_yield(self):        
        start_of_model_run = (self.var._modelTime.timeStepPCR == 1)
        start_of_year = (self.var._modelTime.doy == 1)
        if self.AnnualChangeInPotYield:
            if start_of_model_run or start_of_year:
                date = datetime.datetime(self.var._modelTime.year, 1, 1, 0, 0, 0)
                Yx = vos.netcdf2PCRobjClone(
                    self.var.PotYieldFileNC,
                    self.var.PotYieldVarName,
                    date,
                    useDoy = None,
                    cloneMapFileName = self.var.cloneMap,
                    LatitudeLongitude = True)
                self.var.Yx = Yx[self.var.landmask_crop].reshape(self.var.nCrop, self.var.nCell)
        else:
            if start_of_model_run:
                # date = datetime.datetime(self.staticLandCoverYear, 1, 1, 0, 0, 0) # ***TODO***
                Yx = vos.netcdf2PCRobjCloneWithoutTime(
                    self.var.PotYieldFileNC,
                    self.var.PotYieldVarName,
                    cloneMapFileName = self.var.cloneMap)
                self.var.Yx = Yx[self.var.landmask_crop].reshape(self.var.nCrop, self.var.nCell)

    def dynamic(self):
        self.adjust_planting_and_harvesting_date()
        self.update_growing_season()
        self.update_days_after_planting()
        self.compute_growth_stage_length()
        # self.read_crop_area()
        self.read_potential_crop_yield()
    
# class CropParameters_old(object):
    
#     def __init__(self, CropParameters_variable):
#         self.var = CropParameters_variable
#         self.var.CropParameterFileNC = str(self.var._configuration.cropOptions['cropParameterNC'])
#         # self.var.CropAreaFileNC = str(self.var._configuration.cropOptions['cropAreaNC'])
#         # self.var.AnnualChangeInCropArea = self.var._configuration.cropOptions['AnnualChangeInCropArea']
#         self.var.nCrop = int(self.var._configuration.cropOptions['nCrop'])        
#         # self.var.nCrop = vos.get_dimension_variable(self.var.CropParameterFileNC,'crop').size
#         # self.var.nCrop = vos.netcdfDim2NumPy(self.var.CropParameterFileNC,'crop').size

#         # self.var.cropAreaFileNC = str(self.var._configuration.cropOptions['cropAreaNC'])
#         # self.var.dynamicCropArea = False
#         # if self.var._configuration.cropOptions['dynamicCropArea']:
#         #     self.var.dynamicCropArea = True
                                      
#         self.var.landmask_crop = (
#             self.var.landmask[None,:,:]
#             * np.ones((self.var.nCrop), dtype=np.bool)[:,None,None])
        
#         self.var.crop_parameters_to_read = []
#         self.var.crop_parameters_to_compute = []

#         # Declare variables
#         self.var.crop_parameters_to_read = [
#             'PlantingDate','HarvestDate',
#             'L_ini','L_dev','L_mid','L_late','Kc_ini','Kc_mid','Kc_end','p_std',
#             'Zmin','Zmax','Ky']

#         self.var.crop_parameters_to_compute = [
#             'L_ini_day','L_dev_day','L_mid_day','L_late_day',
#             'PlantingDateAdj','HarvestDateAdj']

#         # initialise parameters
#         self.var.crop_parameter_names = self.var.crop_parameters_to_read + self.var.crop_parameters_to_compute
#         arr_zeros = np.zeros((self.var.nCrop, self.var.nCell))
#         for param in self.var.crop_parameter_names:
#             vars(self.var)[param] = np.copy(arr_zeros)

#         # potential yield
#         self.var.crop_parameter_names += ['Yx']
#         self.var.PotYieldFileNC = self.var._configuration.cropOptions['PotYieldNC']
#         self.var.PotYieldVarName = 'Yx' 
#         if 'PotYieldVariableName' in self.var._configuration.cropOptions:
#             self.var.PotYieldVarName = self.var._configuration.cropOptions['PotYieldVariableName']
#         # self.var.co2_set_per_year  = False

#         # find out whether potential crop yield parameter is dynamic
#         self.var.AnnualChangeInPotYield = False
#         if 'AnnualChangeInPotYield' in self.var._configuration.cropOptions:
#             if self.var.AnnualChangeInPotYield == "True":
#                 self.var.AnnualChangeInPotYield = True
                
#         # # TODO: only read data if the year has changed        
#         # date = '%04i-%02i-%02i' %(self.var._modelTime.year, 1, 1)
#         # self.var.Yx = vos.netcdf2PCRobjClone(self.var.PotYieldFileNC,
#         #                                      self.var.PotYieldVarName,
#         #                                      date,
#         #                                      useDoy = None,
#         #                                      cloneMapFileName = self.var.cloneMap,
#         #                                      LatitudeLongitude = True)
         
#         arr_zeros = np.zeros((self.var.nCrop, self.var.nCell))
#         self.var.CropDead = np.copy(arr_zeros).astype(bool)
#         self.var.CropMature = np.copy(arr_zeros).astype(bool)        
#         self.read() 
        
#     def initial(self):
#         arr_zeros = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))
#         self.var.GrowingSeasonIndex = np.copy(arr_zeros.astype(bool))
#         self.var.GrowingSeasonDayOne = np.copy(arr_zeros.astype(bool))
#         self.var.DAP = np.copy(arr_zeros)
#         # self.var.CurrentCropArea = np.ones((self.var.nFarm, self.var.nCrop, self.var.nCell))
        
#     def read(self):
#         """Function to read crop input parameters"""
#         if len(self.var.crop_parameters_to_read) > 0:
#             for param in self.var.crop_parameters_to_read:
#                 d = vos.netcdf2PCRobjCloneWithoutTime(
#                     self.var.CropParameterFileNC,
#                     param,
#                     cloneMapFileName=self.var.cloneMap)
#                 d = d[self.var.landmask_crop].reshape(self.var.nCrop,self.var.nCell)
#                 vars(self.var)[param] = np.broadcast_to(d, (self.var.nFarm, self.var.nCrop, self.var.nCell))
        
#     def adjust_planting_and_harvesting_date(self):

#         if self.var._modelTime.timeStepPCR == 1 or self.var._modelTime.doy == 1:
            
#             pd = np.copy(self.var.PlantingDate)
#             hd = np.copy(self.var.HarvestDate)
#             st = self.var._modelTime.currTime
#             sd = self.var._modelTime.currTime.timetuple().tm_yday

#             # adjust values for leap year (objective is to preserve date)
#             isLeapYear1 = calendar.isleap(st.year)
#             # isLeapYear2 = calendar.isleap(st.year + 1)
#             pd[(isLeapYear1 & (pd >= 60))] += 1  # TODO: check these
#             hd[(isLeapYear1 & (hd >= 60) & (hd > pd))] += 1
#             # hd[(isLeapYear2 & (hd >= 60) & (hd < pd))] += 1
            
#             self.var.PlantingDateAdj = np.copy(pd)
#             self.var.HarvestDateAdj = np.copy(hd)

#     def update_growing_season(self):

#         # TODO: check both PlantingDateAdj and HarvestDateAdj are not the same!        
#         cond1 = ((self.var.PlantingDateAdj < self.var.HarvestDateAdj)
#                  & ((self.var.PlantingDateAdj <= self.var._modelTime.doy)
#                     & (self.var._modelTime.doy <= self.var.HarvestDateAdj)))
#         cond2 = ((self.var.PlantingDateAdj > self.var.HarvestDateAdj)
#                  & ((self.var.PlantingDateAdj <= self.var._modelTime.doy)
#                     | (self.var._modelTime.doy <= self.var.HarvestDateAdj)))

#         # check the harvest date is before the end of the simulation period
#         hd_arr = (np.datetime64(str(datetime.datetime(self.var._modelTime.year, 1, 1))) + np.array(self.var.HarvestDateAdj - 1, dtype='timedelta64[D]'))        
#         cond3 = hd_arr <= np.datetime64(str(self.var._modelTime.endTime))

#         # check the planting date is after the start of the simaltion period
#         cond4 = ((self.var._modelTime.doy - self.var.PlantingDateAdj) < self.var._modelTime.timeStepPCR)

#         self.var.GrowingSeason = ((cond1 | cond2) & cond3 & cond4)
#         # self.var.GrowingSeason = ((cond1 & cond3) | (cond2 & cond3))

#         self.var.GrowingSeasonIndex = self.var.GrowingSeason.copy()
#         self.var.GrowingSeasonIndex *= np.logical_not(self.var.CropDead | self.var.CropMature)

#         self.var.GrowingSeasonDayOne = self.var._modelTime.doy == self.var.PlantingDateAdj
#         self.var.DAP[self.var.GrowingSeasonDayOne] = 0

#         self.var.GrowingSeasonIndex[self.var.GrowingSeasonDayOne] = True
#         self.var.DAP[self.var.GrowingSeasonIndex] += 1
#         self.var.DAP[np.logical_not(self.var.GrowingSeasonIndex)] = 0

#     def compute_growth_stage_length(self):

#         if np.any(self.var.GrowingSeasonDayOne):
#             nday = self.var.HarvestDateAdj - self.var.PlantingDateAdj
#             nday[nday < 0] += 365
#             nday += 1               # add one to account for the fact that e.g. 20-10=10 but length(10:20)=11
#             ndaymax = np.max(nday).astype(np.int32)
#             tmp = np.ones((ndaymax, self.var.nFarm, self.var.nCrop, self.var.nCell)) * np.arange(1,ndaymax+1)[:,None,None,None]
#             frac = np.divide(tmp,nday)

#             L_accum = np.cumsum(np.concatenate((self.var.L_ini[None,:],
#                                                 self.var.L_dev[None,:],
#                                                 self.var.L_mid[None,:],
#                                                 self.var.L_late[None,:])), axis=0)

#             self.var.L_ini_day = np.sum((frac <= L_accum[0,:]), axis=0, dtype=np.float64)
#             self.var.L_dev_day = np.sum((frac > L_accum[0,:]) & (frac <= L_accum[1,:]), axis=0, dtype=np.float64)
#             self.var.L_mid_day = np.sum((frac > L_accum[1,:]) & (frac <= L_accum[2,:]), axis=0, dtype=np.float64)
#             self.var.L_late_day = np.sum((frac > L_accum[2,:]) & (frac <= L_accum[3,:]), axis=0, dtype=np.float64)

#     def read_potential_crop_yield(self):
#         if self.var.AnnualChangeInPotYield:
#             if self.var._modelTime.timeStepPCR == 1 or self.var._modelTime.doy == 1:
#                 date = '%04i-%02i-%02i' %(self.var._modelTime.year, 1, 1)
#                 Yx = vos.netcdf2PCRobjClone(
#                     self.var.PotYieldFileNC,
#                     self.var.PotYieldVarName,
#                     date,
#                     useDoy = None,
#                     cloneMapFileName = self.var.cloneMap,
#                     LatitudeLongitude = True)
#                 self.var.Yx = Yx[self.var.landmask_crop].reshape(self.var.nCrop, self.var.nCell)
#         else:
#             if self.var._modelTime.timeStepPCR == 1:
#                 Yx = vos.netcdf2PCRobjCloneWithoutTime(
#                     self.var.PotYieldFileNC,
#                     self.var.PotYieldVarName,
#                     cloneMapFileName = self.var.cloneMap)
#                 self.var.Yx = Yx[self.var.landmask_crop].reshape(self.var.nCrop, self.var.nCell)

#     def dynamic(self):
#         self.adjust_planting_and_harvesting_date()
#         self.update_growing_season()
#         self.compute_growth_stage_length()
#         # self.read_crop_area()
#         self.read_potential_crop_yield()

