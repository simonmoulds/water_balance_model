#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
import pcraster as pcr
import hydro_model_builder.VirtualOS as vos
import netCDF4 as nc
import datetime as datetime
import calendar as calendar

from InitialCondition import InitialCondition
from SoilAndTopoParameters import SoilAndTopoParameters
from Drainage import Drainage
from RainfallPartition import RainfallPartition
from RootZoneWater import RootZoneWater
from Infiltration import Infiltration
from CapillaryRise import CapillaryRise
from RootDevelopment import RootDevelopment
from CropEvapotranspiration import CropEvapotranspiration

class FieldMgmtParameters(object):
    def __init__(self, FieldMgmtParameters_variable):
        self.var = FieldMgmtParameters_variable

    def initial(self):
        self.var.Bunds = np.zeros((self.var.nFarm, self.var.nLC, self.var.nCell))
        self.var.zBund = np.zeros((self.var.nFarm, self.var.nLC, self.var.nCell))
        self.var.BundWater = np.zeros((self.var.nFarm, self.var.nLC, self.var.nCell))

    def dynamic(self):
        pass

class IrrigationMgmtParameters(object):
    def __init__(self, IrrigationMgmtParameters_variable):
        self.var = IrrigationMgmtParameters_variable

    def initial(self):
        self.var.NetIrrSMT = np.zeros((self.var.nFarm, self.var.nLC, self.var.nCell))
        self.var.IrrMethod = np.zeros((self.var.nFarm, self.var.nLC, self.var.nCell))
        self.var.DAP = np.zeros((self.var.nFarm, self.var.nLC, self.var.nCell))
        self.var.SMT1 = np.zeros((self.var.nFarm, self.var.nLC, self.var.nCell))
        self.var.SMT2 = np.zeros((self.var.nFarm, self.var.nLC, self.var.nCell))
        self.var.SMT3 = np.zeros((self.var.nFarm, self.var.nLC, self.var.nCell))
        self.var.SMT4 = np.zeros((self.var.nFarm, self.var.nLC, self.var.nCell))
        self.var.IrrInterval = np.zeros((self.var.nFarm, self.var.nLC, self.var.nCell))
        self.var.AppEff = np.zeros((self.var.nFarm, self.var.nLC, self.var.nCell))
        self.var.MaxIrr = np.zeros((self.var.nFarm, self.var.nLC, self.var.nCell))
        self.var.irrScheduleFileNC = None

    def dynamic(self):
        pass

class CropParameters(object):
    def __init__(self, CropParameters_variable):
        self.var = CropParameters_variable

    def initial(self):
        self.var.Zmin = np.zeros((self.var.nFarm, self.var.nLC, self.var.nCell))
        self.var.GrowingSeasonDayOne = np.zeros((self.var.nFarm, self.var.nLC, self.var.nCell), dtype=np.bool)
        self.var.GrowingSeasonIndex = np.zeros((self.var.nFarm, self.var.nLC, self.var.nCell), dtype=np.bool)

    def dynamic(self):
        pass

# class LandCoverParameters(object):
#     def __init__(self, lc_variable, lc_name):
#         config_section = getattr(lc_variable.var._configuration, lc_name)  # TODO: wrap in try/except
#         lc_variable.cropCoefficientNC = str(config_section['landCoverFractionInputFile'])
#         # self.var.cropCoefficientNC = str(config_section['landCoverFractionInputFile'])
#         # self.var.maxRootDepthNC = str(config_section['maxRootDepthInputFile'])
#         # self.var.minSoilDepthFracNC = str(config_section['minSoilDepthFracInputFile'])
#         # self.var.interceptCapNC = str(config_section['interceptCapInputFile'])

#     def initial(self):
#         pass

#     def dynamic(self):
#         pass

class GenericLandCover(object):
    def __init__(self, var):
        self.var = var
        # copy some information about the model domain, dimensions etc.
        self._configuration = self.var._configuration
        self.cloneMap = self.var.cloneMap
        self.landmask = self.var.landmask
        self.nLat, self.nLon, self.nCell = self.var.nLat, self.var.nLon, self.var.nCell
        self.nFarm, self.nLC = 1, 1  # FIXED
        
class Forest(GenericLandCover):
    def __init__(self, Forest_variable):
        super(Forest, self).__init__(Forest_variable)
        self.var = Forest_variable
        # self.meteo = Forest_variable.meteo_module
        # print np.max(self.meteo.var.precipitation)
        self.soil_parameters_module = SoilAndTopoParameters(
            self,
            self.var._configuration.soilOptions)  # TODO: change this?        
        self.initial_condition_module = InitialCondition(self)        
        self.drainage_module = Drainage(self)
        self.rainfall_partition_module = RainfallPartition(self)
        self.root_zone_water_module = RootZoneWater(self)
        self.infiltration_module = Infiltration(self)
        self.capillary_rise_module = CapillaryRise(self)
        # self.root_development_module = RootDevelopment(self)
        # self.evapotranspiration_module = CropEvapotranspiration(self)
        self.get_forest_parameters()

    def get_forest_parameters(self):
        self.Bunds = np.zeros((self.nFarm, self.nLC, self.nCell), dtype=np.bool)
        self.zBund = np.zeros((self.nFarm, self.nLC, self.nCell))
        self.BundWater = np.zeros((self.nFarm, self.nLC, self.nCell))
    
    def initial(self):
        self.soil_parameters_module.initial()
        self.initial_condition_module.initial()
        self.drainage_module.initial()
        self.rainfall_partition_module.initial()
        self.root_zone_water_module.initial()
        self.infiltration_module.initial()
        self.capillary_rise_module.initial()
        # self.root_development_module.initial()
        # self.evapotranspiration_module.initial()
        
    def dynamic(self):
        self.soil_parameters_module.dynamic()
        # self.drainage_module.dynamic()
        
class Grassland(object):
    def __init__(self, Grassland_variable):
        self.var = Grassland_variable

    def initial(self):
        pass

    def dynamic(self):
        pass

class IrrPaddy(object):
    def __init__(self, IrrPaddy_variable):
        self.var = IrrPaddy_variable
        self.field_mgmt_pars_module = FieldMgmtParameters(IrrPaddy_variable)
        self.irri_mgmt_pars_module = IrrigationMgmtParameters(IrrPaddy_variable)

    def initial(self):
        pass

    def dynamic(self):
        pass

class IrrNonPaddy(object):
    def __init__(self, IrrNonPaddy_variable):
        self.var = IrrNonPaddy_variable
        self.field_mgmt_pars_module = FieldMgmtParameters(IrrNonPaddy_variable)
        self.irri_mgmt_pars_module = IrrigationMgmtParameters(IrrNonPaddy_variable)

    def initial(self):
        pass

    def dynamic(self):
        pass

class Sealed(object):
    def __init__(self, Sealed_variable):
        self.var = Sealed_variable

    def initial(self):
        pass

    def dynamic(self):
        pass

class Water(object):
    def __init__(self, Water_variable):
        self.var = Water_variable

    def initial(self):
        pass

    def dynamic(self):
        pass
    
class LandCover(object):
    def __init__(self, LandCover_variable):
        self.var = LandCover_variable
        # self.var.dynamicLandCover
        # self.var.FixedLandCoverYear

        self.forest_module = Forest(LandCover_variable)
        self.grassland_module = Grassland(LandCover_variable)
        self.irrPaddy_module = IrrPaddy(LandCover_variable)
        self.irrNonPaddy_module = IrrNonPaddy(LandCover_variable)
        self.sealed_module = Sealed(LandCover_variable)
        self.water_module = Water(LandCover_variable)

    def initial(self):
        self.forest_module.initial()
        self.grassland_module.initial()
        self.irrPaddy_module.initial()
        self.irrNonPaddy_module.initial()
        self.sealed_module.initial()
        self.water_module.initial()    

    def dynamic(self):
        self.forest_module.dynamic()
        # print self.forest_module.th.shape
        self.grassland_module.dynamic()
        self.irrPaddy_module.dynamic()
        self.irrNonPaddy_module.dynamic()
        self.sealed_module.dynamic()
        self.water_module.dynamic()    
