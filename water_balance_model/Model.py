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

        # clone map, land mask
        pcr.setclone(configuration.cloneMap)
        self.cloneMap = self._configuration.cloneMap
        self.cloneMapAttributes = vos.getMapAttributesALL(self.cloneMap)
        
        self.landmask = vos.readPCRmapClone(
            configuration.globalOptions['landmask'],
            configuration.cloneMap,
            configuration.tmpDir,
            configuration.globalOptions['inputDir'],
            True)
        self.landmask = self.landmask > 0

        grid_cell_area = vos.netcdf2PCRobjCloneWithoutTime(
            str(configuration.MASK_OUTLET['gridCellAreaInputFile']),
            str(configuration.MASK_OUTLET['gridCellAreaVariableName']),
            cloneMapFileName = self.cloneMap)
        self.grid_cell_area = grid_cell_area[self.landmask]
        
        # attr = vos.getMapAttributesALL(self.cloneMap)
        self.nLat = int(self.cloneMapAttributes['rows'])
        self.nLon = int(self.cloneMapAttributes['cols'])
        self.nCell = int(np.sum(self.landmask))
        
    @property
    def configuration(self):
        return self._configuration
