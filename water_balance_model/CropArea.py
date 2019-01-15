#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
import pcraster as pcr
import hydro_model_builder.VirtualOS as vos
import netCDF4 as nc
import datetime as datetime
import calendar as calendar

class CropArea(object):
    
    def __init__(self, CropArea_variable):
        self.var = CropArea_variable
        self.var.CropAreaFileNC = str(self.var._configuration.cropOptions['cropAreaNC'])
        self.var.CropAreaVarName = str(self.var._configuration.cropOptions['cropAreaVariableName'])
        self.var.CroplandAreaFileNC = str(self.var._configuration.cropOptions['croplandAreaNC'])
        self.var.CroplandAreaVarName = str(self.var._configuration.cropOptions['croplandAreaVariableName'])
        self.var.AnnualChangeInCropArea = bool(int(self.var._configuration.cropOptions['AnnualChangeInCropArea']))
        self.var.landmask_crop = np.broadcast_to(
            self.var.landmask[None,:,:],
            (self.var.nCrop, self.var.nLat, self.var.nLon))
        # self.var.landmask_farm_crop = np.broadcast_to(
        #     self.var.landmask[None,None,:,:],
        #     (self.var.nFarm, self.var.nCrop, self.var.nLat, self.var.nLon))
        
    def initial(self):
        self.var.CurrentCropArea = np.ones((self.var.nCrop, self.var.nCell))

    def read_cropland_area(self):
        if self.var.AnnualChangeInCropArea:
            if self.var._modelTime.timeStepPCR == 1 or self.var._modelTime.doy == 1:
                date = '%04i-%02i-%02i' % (self.var._modelTime.year, 1, 1)
                CroplandArea = vos.netcdf2PCRobjClone(
                    self.var.CroplandAreaFileNC,
                    # 'cropland_area',
                    self.var.CroplandAreaVarName,
                    date,
                    useDoy = None,
                    cloneMapFileName = self.var.cloneMap,
                    LatitudeLongitude = True)
                self.var.CroplandArea = CroplandArea[self.var.landmask]
                
        else:
            if self.var._modelTime.timeStepPCR == 1:
                if not self.var.CropAreaFileNC == "None":
                    CroplandArea = vos.netcdf2PCRobjCloneWithoutTime(
                        self.var.CroplandAreaFileNC,
                        # 'cropland_area',
                        self.var.CroplandAreaVarName,
                        cloneMapFileName = self.var.cloneMap)
                    self.var.CroplandArea = CroplandArea[self.var.landmask]
                    
                else:
                    self.var.CroplandArea = np.ones((self.var.nCell)) * self.var.nCrop
    
        # self.var.CroplandArea = np.broadcast_to(
        #     self.var.CroplandArea, (
        #         self.var.nFarm,
        #         self.var.nCrop,
        #         self.var.nCell))
        self.var.CroplandArea = np.float64(self.var.CroplandArea)
        
    def read_crop_area(self, date = None):
        if date is None:
            crop_area = vos.netcdf2PCRobjCloneWithoutTime(
                self.var.CropAreaFileNC,
                self.var.CropAreaVarName,
                cloneMapFileName = self.var.cloneMap,
                LatitudeLongitude = True)
        else:
            crop_area = vos.netcdf2PCRobjClone(
                self.var.CropAreaFileNC,
                self.var.CropAreaVarName,
                date,
                useDoy = None,
                cloneMapFileName = self.var.cloneMap,
                LatitudeLongitude = True)

        # crop_area_has_farm_dimension = (
        #     vos.check_if_nc_variable_has_dimension(
        #         self.var.CropAreaFileNC,
        #         self.var.CropAreaVarName,
        #         'farm'))
        # if crop_area_has_farm_dimension:
        #     crop_area = np.reshape(
        #         crop_area[self.var.landmask_farm_crop],
        #         (self.var.nFarm, self.var.nCrop, self.var.nCell))
        # else:
        crop_area = np.reshape(
            crop_area[self.var.landmask_crop],
            (self.var.nCrop, self.var.nCell))
        # crop_area = np.broadcast_to(
        #     crop_area[None,:,:],
        #     (self.var.nFarm, self.var.nCrop, self.var.nCell))            
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
        # crop_area = self.var.CropArea[0,...]  # remove farm dimension
        crop_area = self.var.CropArea.copy()
        crop_area_daily = crop_area[None,...] * growing_season_idx  # get daily crop area
        total_crop_area_daily = np.sum(crop_area_daily, axis=1)     # sum of all crops grown on a given day
        max_crop_area = np.max(total_crop_area_daily, axis=0)       # get the max crop area considering all growing seasons
        scale_factor = np.divide(self.var.CroplandArea, max_crop_area, out=np.zeros_like(self.var.CroplandArea), where=max_crop_area>0)  # compute scale factor by dividing cropland area by max crop area
        self.var.CropArea *= scale_factor

    def set_crop_area(self):
        """Function to read crop area"""
        if self.var.AnnualChangeInCropArea:
            if self.var._modelTime.timeStepPCR == 1 or self.var._modelTime.doy == 1:
                # In this case crop area is updated on the first day of each year,
                # hence in order to prevent the area under a specific crop changing
                # mid-season, it is necessary to introduce an intermediate variable
                # (i.e. CropAreaNew) and only update the area on the first day of
                # the growing season.
                date = '%04i-%02i-%02i' % (self.var._modelTime.year, 1, 1)
                self.var.CropAreaNew = self.read_crop_area(date = date)
                    
            if np.any(self.var.GrowingSeasonDayOne):
                self.var.CropArea[self.var.GrowingSeasonDayOne] = self.var.CropAreaNew[self.var.GrowingSeasonDayOne]
                self.scale_crop_area()
                
        else:
            if self.var._modelTime.timeStepPCR == 1:
                if not self.var.CropAreaFileNC == "None":
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
