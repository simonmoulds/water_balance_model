#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
import sys
import math
import gc
import numpy as np 
import pcraster as pcr
import VirtualOS as vos

# TODO:
# class Model(object)
# class GriddedModel(Model)
# class LumpedModel(Model)

class Model(object):
    
    def __init__(self, configuration, modelTime, initialState = None):                
        self._configuration = configuration
        self._modelTime = modelTime
        self.set_clone_map()
        self.set_landmask()
        self.set_grid_cell_area()
        self.get_model_dimensions()
        
    def set_clone_map(self):
        # TODO: REMOVE DEPENDENCY ON PCRASTER
        pcr.setclone(self._configuration.cloneMap)  # TODO: CHECK IF THIS IS NECESSARY
        self.cloneMap = self._configuration.cloneMap
        self.cloneMapAttributes = vos.getMapAttributesALL(self.cloneMap)

    def set_landmask(self):
        self.landmask = vos.readPCRmapClone(
            self._configuration.globalOptions['landmask'],
            self._configuration.cloneMap,
            self._configuration.tmpDir,
            self._configuration.globalOptions['inputDir'],
            True)
        self.landmask = self.landmask > 0

    def set_grid_cell_area(self):
        grid_cell_area = vos.netcdf2PCRobjCloneWithoutTime(
            str(self._configuration.MASK_OUTLET['gridCellAreaInputFile']),
            str(self._configuration.MASK_OUTLET['gridCellAreaVariableName']),
            cloneMapFileName = self.cloneMap)
        grid_cell_area = np.float64(grid_cell_area)
        self.grid_cell_area = grid_cell_area[self.landmask]

    def get_model_dimensions(self):
        """Function to set model dimensions"""
        self.nLat = int(self.cloneMapAttributes['rows'])
        self.latitudes = np.unique(pcr.pcr2numpy(pcr.ycoordinate(self.cloneMap), vos.MV))[::-1]
        self.nLon = int(self.cloneMapAttributes['cols'])
        self.longitudes = np.unique(pcr.pcr2numpy(pcr.xcoordinate(self.cloneMap), vos.MV))
        self.nCell = int(np.sum(self.landmask))
        self.nLayer = 3         # FIXED        
        self.dimensions = {
            'time'     : None,
            'depth'    : np.arange(self.nLayer), # TODO - put nComp in config section [SOIL]
            'lat'      : self.latitudes,
            'lon'      : self.longitudes,
        }
        
    @property
    def configuration(self):
        return self._configuration
