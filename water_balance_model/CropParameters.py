#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
import pcraster as pcr
import VirtualOS as vos
import netCDF4 as nc
import datetime as datetime
import calendar as calendar

class CropArea(object):
    
    def __init__(self, var, configuration):
        self.var = var
        self.configuration = configuration
        self.CropAreaFileNC = str(self.configuration['cropAreaInputFile'])
        self.CropAreaVarName = str(self.configuration['cropAreaVariableName'])
        self.CropTypes = [str(crop.strip()) for crop in self.configuration['cropTypes'].split(',')]
        self.CropIsIrrigated = [bool(int(irri.strip())) for irri in self.configuration['cropIrrigated'].split(',')]
        self.AnnualChangeInCropArea = bool(int(self.configuration['annualChangeInCropArea']))
        self.var.landmask_crop = np.broadcast_to(
            self.var.landmask[None,:,:],
            (self.var.nCrop, self.var.nLat, self.var.nLon))
        
    def initial(self):
        self.var.CurrentCropArea = np.ones((self.var.nCrop, self.var.nCell))

    def read_cropland_area(self):
        self.var.CroplandArea = (
            self.var.coverFraction
            * self.var.grid_cell_area)
        
    def read_crop_area(self, date = None):
        if date is None:
            crop_area = vos.netcdf2PCRobjCloneWithoutTime(
                self.CropAreaFileNC,
                self.CropAreaVarName,
                cloneMapFileName = self.var.cloneMap,
                LatitudeLongitude = True)
        else:
            crop_area = vos.netcdf2PCRobjClone(
                self.CropAreaFileNC,
                self.CropAreaVarName,
                date,
                useDoy = None,
                cloneMapFileName = self.var.cloneMap,
                LatitudeLongitude = True)
        crop_area = np.reshape(
            crop_area[self.var.landmask_crop],
            (self.var.nCrop, self.var.nCell))
        crop_area = np.float64(crop_area)
        return crop_area

    def scale_crop_area(self):
        """Function to scale crop area to match cropland area
        """
        pd = self.var.PlantingDate.copy()[0,...]
        hd = self.var.HarvestDate.copy()[0,...]
        hd[hd < pd] += 365
        max_harvest_date = int(np.max(hd))
        day_idx = np.arange(1, max_harvest_date + 1)[:,None,None] * np.ones((self.var.nCrop, self.var.nCell))[None,:,:]
        growing_season_idx = ((day_idx >= pd) & (day_idx <= hd))
        crop_area = self.var.CropArea.copy()
        crop_area_daily = crop_area[None,...] * growing_season_idx  # get daily crop area
        total_crop_area_daily = np.sum(crop_area_daily, axis=1)     # sum of all crops grown on a given day
        max_crop_area = np.max(total_crop_area_daily, axis=0)       # get the max crop area considering all growing seasons
        scale_factor = np.divide(self.var.CroplandArea, max_crop_area, out=np.zeros_like(self.var.CroplandArea), where=max_crop_area>0)  # compute scale factor by dividing cropland area by max crop area
        self.var.CropArea *= scale_factor

    def set_crop_area(self):
        """Function to read crop area"""
        start_of_model_run = (self.var._modelTime.timeStepPCR == 1)
        start_of_year = (self.var._modelTime.doy == 1)
        if self.AnnualChangeInCropArea:
            if start_of_model_run or start_of_year:
                # In this case crop area is updated on the first day of each year,
                # hence in order to prevent the area under a specific crop changing
                # mid-season, it is necessary to introduce an intermediate variable
                # (i.e. CropAreaNew) and only update the area on the first day of
                # the growing season.
                date = datetime.datetime(self.var._modelTime.year, 1, 1, 0, 0, 0)
                self.var.CropAreaNew = self.read_crop_area(date = date)
                    
            if np.any(self.var.GrowingSeasonDayOne):
                self.var.CropArea[self.var.GrowingSeasonDayOne] = self.var.CropAreaNew[self.var.GrowingSeasonDayOne]
                self.scale_crop_area()
                
        else:
            if start_of_model_run:
                if not self.CropAreaFileNC == "None":
                    # If crop area doesn't change then there is no need for an
                    # intermediate variable
                    self.var.CropArea = self.read_crop_area(date = None)
                else:
                    self.var.CropArea = np.ones(
                        (self.var.nFarm,
                         self.var.nCrop,
                         self.var.nCell))
                self.scale_crop_area()

    def compute_current_crop_area(self):
        """Function to work out the relative area of current crops and 
        fallow area, and divide fallow land proportionally between 
        crops that are not currently grown. This is necessary because 
        the program continues to compute the water balance for crops 
        which are not currently grown).
        """
        crop_area = self.var.CropArea * self.var.GrowingSeasonIndex[0,:,:]
        total_crop_area = np.sum(crop_area, axis=0)
        
        # Compute scale factor to represent the relative area of
        # each crop not currently grown by dividing fallow area
        # by total fallow area
        crop_area_not_grown = (
            self.var.CropArea
            * np.logical_not(self.var.GrowingSeasonIndex[0,:,:]))        
        total_crop_area_not_grown = np.sum(
            crop_area_not_grown
            * np.logical_not(self.var.GrowingSeasonIndex[0,:,:]),
            axis=0)

        # TODO: estimate irrigated and unirrigated area
        # farms without access to irrigation must grow rainfed crops, so allocate these first
        # farms with irrigation can grow either rainfed or irrigated crops
        # irrigated_crop_area = (
        #     self.var.CropArea
        #     * self.CropIsIrrigated[:,None,None]
        #     * self.var.GrowingSeasonIndex[0,:,:]
        # )
        # total_irrigated_crop_area = np.sum(irrigated_crop_area, axis=0)

        # # rainfed area
        # # ############
        # rainfed_area = (
        #     self.var.CropArea
        #     * np.logical_not(self.CropIsIrrigated[:,None,None])
        #     * self.var.GrowingSeasonIndex[0,:,:]
        # )
        # total_rainfed_area = np.sum(rainfed_crop_area, axis=0)        
        # rainfed_area_not_grown = (
        #     self.var.CropArea
        #     * np.logical_not(self.CropIsIrrigated[:,None,None])            
        #     * np.logical_not(self.var.GrowingSeasonIndex[0,:,:]))        
        # total_rainfed_area_not_grown = np.sum(
        #     rainfed_area_not_grown,
        #     axis=0)

        # rainfed_scale_factor = np.divide(
        #     rainfed_area_not_grown,
        #     total_rainfed_area_not_grown,
        #     out=np.zeros_like(rainfed_area_not_grown),
        #     where=total_rainfed_area_not_grown>0)

        # target_rainfed_fallow_area = np.clip(self.var.CroplandArea - total_rainfed_area, 0, None)
        # rainfed_fallow_area = target_fallow_area * scale_factor
        
        
        # # irrigated area
        # # ##############
        # irrigated_area = (
        #     self.var.CropArea
        #     * np.logical_not(self.var.CropIsIrrigated[:,None,None])
        #     * self.var.GrowingSeasonIndex[0,:,:]
        # )
        # total_irrigated_area = np.sum(irrigated_crop_area, axis=0)        
        # irrigated_area_not_grown = (
        #     self.var.CropArea
        #     * np.logical_not(self.var.CropIsIrrigated[:,None,None])            
        #     * np.logical_not(self.var.GrowingSeasonIndex[0,:,:]))        
        # total_irrigated_area_not_grown = np.sum(
        #     irrigated_area_not_grown,
        #     axis=0)
        
        scale_factor = np.divide(
            crop_area_not_grown,
            total_crop_area_not_grown,
            out=np.zeros_like(crop_area_not_grown),
            where=total_crop_area_not_grown>0)
        
        # Compute the area which remains fallow during the growing
        # season, and scale according to the relative area of the
        # crops *not* currently grown.
        target_fallow_area = np.clip(self.var.CroplandArea - total_crop_area, 0, None)
        fallow_area = target_fallow_area * scale_factor

        self.var.CurrentCropArea = self.var.CropArea.copy()
        self.var.CurrentCropArea[np.logical_not(self.var.GrowingSeasonIndex[0,:,:])] = (
            (fallow_area[np.logical_not(self.var.GrowingSeasonIndex[0,:,:])]))
        
        # # Check CurrentCropArea sums to CroplandArea:
        # print np.sum(self.var.CurrentCropArea[:,249])
        # print self.var.CroplandArea[249]
        
        # CurrentCropArea represents the crop area in the entire grid
        # cell; it does not represent the area of the respective crops
        # grown on the respective farms. Thus, create a farm scale factor
        # to scale the current cropped area down to the level of individual
        # farms.
        
        # TODO: the default behaviour here should be to have one farm per
        # grid cell, such that the farm_scale_factor equals 1

        farm_scale_factor = np.divide(
            self.var.FarmArea,
            self.var.CroplandArea,
            out=np.zeros_like(self.var.FarmArea),
            where=self.var.CroplandArea>0)        
        
        # The farm scale factor represents the fraction of total cropland
        # found within each farm. Thus, multiplying the scale factor by
        # CurrentCropArea provides an estimate of the area of each crop
        # within a given farm.        
        self.var.FarmCropArea = farm_scale_factor[:,None,:] * self.var.CurrentCropArea
        
    def dynamic(self):
        self.read_cropland_area()
        self.set_crop_area()
        self.compute_current_crop_area()
    
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
        self.var.GrowthStage = np.copy(arr_zeros)
        self.var.cropCoefficient = np.copy(arr_zeros)
        
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

    # def reset_initial_conditions(self):
    #     self.var.GrowthStage[self.var.GrowingSeasonDayOne] = 0
    def update_growth_stage(self):
        # if np.any(self.var.GrowingSeasonDayOne):
        #     self.reset_initial_conditions()
        L_day = np.stack((self.var.L_ini_day,
                          self.var.L_dev_day,
                          self.var.L_mid_day,
                          self.var.L_late_day), axis=0)        
        self.var.L_day = np.cumsum(L_day, axis=0)

        cond1 = (self.var.GrowingSeasonIndex & (self.var.DAP < self.var.L_day[0,:]))
        cond2 = (self.var.GrowingSeasonIndex & (self.var.DAP >= self.var.L_day[0,:]) & (self.var.DAP < self.var.L_day[1,:]))
        cond3 = (self.var.GrowingSeasonIndex & (self.var.DAP >= self.var.L_day[1,:]) & (self.var.DAP < self.var.L_day[2,:]))
        cond4 = (self.var.GrowingSeasonIndex & (self.var.DAP >= self.var.L_day[2,:]))
        self.var.GrowthStage[cond1] = 1
        self.var.GrowthStage[cond2] = 2
        self.var.GrowthStage[cond3] = 3
        self.var.GrowthStage[cond4] = 4
        self.var.GrowthStage[np.logical_not(self.var.GrowingSeasonIndex)] = 0

    def update_crop_coefficient(self):
        # L_day = np.stack((self.var.L_ini_day,
        #                   self.var.L_dev_day,
        #                   self.var.L_mid_day,
        #                   self.var.L_late_day), axis=0)        
        # L_day = np.cumsum(L_day, axis=0)        
        # Kc = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))
        cond1 = self.var.GrowthStage == 1
        cond2 = self.var.GrowthStage == 2
        cond3 = self.var.GrowthStage == 3
        cond4 = self.var.GrowthStage == 4        
        self.var.cropCoefficient[cond1] = self.var.Kc_ini[cond1]
        ini_to_mid_gradient = np.divide(
            (self.var.Kc_mid - self.var.Kc_ini),
            self.var.L_dev_day,
            out=np.zeros_like(self.var.L_dev_day),
            where=self.var.L_dev_day!=0)
        self.var.cropCoefficient[cond2] = (
            self.var.Kc_ini
            + (ini_to_mid_gradient *
               (self.var.DAP - self.var.L_day[0,:])))[cond2]
        
        self.var.cropCoefficient[cond3] = self.var.Kc_mid[cond3]

        mid_to_end_gradient = np.divide(
            (self.var.Kc_end - self.var.Kc_mid),
            self.var.L_late_day,
            out=np.zeros_like(self.var.L_late_day),
            where=self.var.L_late_day!=0)
        
        self.var.cropCoefficient[cond4] = (
            self.var.Kc_mid +
            (mid_to_end_gradient
             * (self.var.DAP - self.var.L_day[2,:])))[cond4]

        # Global Crop Water Model        
        self.var.cropCoefficient[np.logical_not(self.var.GrowingSeasonIndex)] = 0.5

    def read_potential_crop_yield(self):        
        start_of_model_run = (self.var._modelTime.timeStepPCR == 1)
        start_of_year = (self.var._modelTime.doy == 1)
        if self.AnnualChangeInPotYield:
            if start_of_model_run or start_of_year:
                date = datetime.datetime(self.var._modelTime.year, 1, 1, 0, 0, 0)
                Yx = vos.netcdf2PCRobjClone(
                    self.PotYieldNC,
                    self.PotYieldVarName,
                    date,
                    useDoy = None,
                    cloneMapFileName = self.var.cloneMap,
                    LatitudeLongitude = True)
                self.var.Yx = Yx[self.var.landmask_crop].reshape(self.var.nCrop, self.var.nCell)
        else:
            if start_of_model_run:
                # date = datetime.datetime(self.staticLandCoverYear, 1, 1, 0, 0, 0) # ***TODO***
                Yx = vos.netcdf2PCRobjCloneWithoutTime(
                    self.PotYieldNC,
                    self.PotYieldVarName,
                    cloneMapFileName = self.var.cloneMap)
                self.var.Yx = Yx[self.var.landmask_crop].reshape(self.var.nCrop, self.var.nCell)

    def dynamic(self):
        self.adjust_planting_and_harvesting_date()
        self.update_growing_season()
        self.update_days_after_planting()
        self.compute_growth_stage_length()
        self.update_growth_stage()
        self.update_crop_coefficient()
        # self.read_crop_area()
        self.read_potential_crop_yield()
