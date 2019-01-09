#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
import pcraster as pcr
import hydro_model_builder.VirtualOS as vos
import netCDF4 as nc
import datetime as datetime
import calendar as calendar

from InitialCondition import *
from RootZoneWater import *
from SnowFrost import SnowFrost
from CheckGroundwaterTable import CheckGroundwaterTable
from LandCoverParameters import *
from Drainage import Drainage
from Interception import *
from Irrigation import *
from RainfallPartition import RainfallPartition
from Infiltration import Infiltration
from CapillaryRise import CapillaryRise
from Evapotranspiration import *

class LandCover(object):
    def __init__(self, var, config_section_name):
        self._configuration = var._configuration
        self._modelTime = var._modelTime
        self.cloneMap = var.cloneMap
        self.landmask = var.landmask
        self.nLat, self.nLon, self.nCell = var.nLat, var.nLon, var.nCell
        self.nFarm, self.nLC = 1, 1

        # attach meteorological and groundwater data to land cover object
        self.meteo = var.meteo_module
        self.groundwater = var.groundwater_module        

    def initial(self):
        pass

    def dynamic(self):
        pass

class NaturalVegetation(LandCover):
    def __init__(self, var, config_section_name):
        super(NaturalVegetation, self).__init__(
            var,
            config_section_name)

        self.lc_parameters_module = NaturalVegetationParameters(self, config_section_name)
        self.initial_condition_module = InitialConditionNaturalVegetation(self)
        self.root_zone_water_module = RootZoneWater(self)
        self.snow_frost_module = SnowFrost(self)
        self.evapotranspiration_module = Evapotranspiration(self)
        self.interception_module = Interception(self)
        self.infiltration_module = Infiltration(self)
        self.capillary_rise_module = CapillaryRise(self)
        self.drainage_module = Drainage(self)

    def initial(self):
        self.lc_parameters_module.initial()
        self.initial_condition_module.initial()
        self.root_zone_water_module.initial()
        self.snow_frost_module.initial()
        self.evapotranspiration_module.initial()
        self.interception_module.initial()
        self.infiltration_module.initial()
        self.capillary_rise_module.initial()
        self.drainage_module.initial()
        
    def dynamic(self):
        self.lc_parameters_module.dynamic()
        self.initial_condition_module.dynamic()
        self.root_zone_water_module.dynamic()
        self.snow_frost_module.dynamic()
        self.evapotranspiration_module.dynamic()
        self.interception_module.dynamic()
        self.infiltration_module.dynamic()
        self.capillary_rise_module.dynamic()
        self.drainage_module.dynamic()

class ManagedLand(LandCover):
    def __init__(self, var, config_section_name):
        super(ManagedLand, self).__init__(
            var,
            config_section_name)

        self.lc_parameters_module = ManagedLandParameters(self, config_section_name)
        self.initial_condition_module = InitialConditionManagedLand(self)
        self.root_zone_water_module = RootZoneWater(self)
        self.snow_frost_module = SnowFrost(self)
        self.evapotranspiration_module = Evapotranspiration(self)
        self.interception_module = Interception(self)
        self.infiltration_module = Infiltration(self)
        self.capillary_rise_module = CapillaryRise(self)
        self.drainage_module = Drainage(self)

    def initial(self):
        self.lc_parameters_module.initial()
        self.initial_condition_module.initial()
        self.root_zone_water_module.initial()
        self.snow_frost_module.initial()
        self.evapotranspiration_module.initial()        
        self.interception_module.initial()
        self.irrigation_module.initial()
        self.infiltration_module.initial()
        self.capillary_rise_module.initial()
        self.drainage_module.initial()
        
    def dynamic(self):
        self.lc_parameters_module.dynamic()
        self.initial_condition_module.dynamic()
        self.root_zone_water_module.dynamic()
        self.snow_frost_module.dynamic()
        self.evapotranspiration_module.dynamic()
        self.interception_module.dynamic()
        self.irrigation_module.dynamic()
        self.infiltration_module.dynamic()
        self.capillary_rise_module.dynamic()
        self.drainage_module.dynamic()

class ManagedLandIrrPaddy(ManagedLand):
    def __init__(self, var, config_section_name):
        super(ManagedLandIrrPaddy, self).__init__(
            var,
            config_section_name)
        self.irrigation_module = IrrigationPaddy(self)

class ManagedLandIrrNonPaddy(ManagedLand):
    def __init__(self, var, config_section_name):
        super(ManagedLandIrrNonPaddy, self).__init__(
            var,
            config_section_name)
        self.irrigation_module = IrrigationNonPaddy(self)

class SealedLand(LandCover):
    def __init__(self, var, config_section_name):
        super(SealedLand, self).__init__(
            var,
            config_section_name)
        
        self.lc_parameters_module = SealedLandParameters(self, config_section_name)
        self.initial_condition_module = InitialConditionSealedLand(self)
        self.snow_frost_module = SnowFrost(self)
        self.interception_module = InterceptionSealed(self)
        self.evapotranspiration_module = EvaporationSealed(self)
        self.infiltration_module = Infiltration(self)
        self.capillary_rise_module = CapillaryRise(self)
        self.drainage_module = Drainage(self)

    def initial(self):
        self.lc_parameters_module.initial()
        self.initial_condition_module.initial()
        self.snow_frost_module.initial()
        self.interception_module.initial()
        self.evapotranspiration_module.initial()

        # still initialize these modules, so that variables are initialized to zero
        self.infiltration_module.initial()
        self.capillary_rise_module.initial()
        self.drainage_module.initial()
        
    def dynamic(self):
        self.lc_parameters_module.dynamic()
        self.initial_condition_module.dynamic()
        self.snow_frost_module.dynamic()
        self.interception_module.dynamic()
        self.evapotranspiration_module.dynamic()

class OpenWater(LandCover):
    def __init__(self, var, config_section_name):
        super(OpenWater, self).__init__(
            var,
            config_section_name)
        
        self.lc_parameters_module = SealedLandParameters(self, config_section_name)
        self.initial_condition_module = InitialConditionSealedLand(self)
        self.snow_frost_module = SnowFrost(self)
        self.interception_module = InterceptionWater(self)
        self.evapotranspiration_module = EvaporationWater(self)

    def initial(self):
        self.lc_parameters_module.initial()
        self.initial_condition_module.initial()
        self.snow_frost_module.initial()
        self.interception_module.initial()
        self.evapotranspiration_module.initial()
        
    def dynamic(self):
        self.lc_parameters_module.dynamic()
        self.initial_condition_module.dynamic()
        self.snow_frost_module.dynamic()
        self.interception_module.dynamic()
        self.evapotranspiration_module.dynamic()
        
class Forest(NaturalVegetation):
    """Class to represent forest land cover"""
        
class Grassland(NaturalVegetation):
    """Class to represent grassland"""

class IrrPaddy(ManagedLandIrrPaddy):
    """Class to represent irrigated paddy"""

class IrrNonPaddy(ManagedLandIrrNonPaddy):
    """Class to represent irrigated non-paddy"""
    
class Sealed(SealedLand):
    """Class to represent sealed area"""

class Water(OpenWater):
    """Class to represent water"""
