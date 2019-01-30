#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
import pcraster as pcr
import VirtualOS as vos
import netCDF4 as nc
import datetime as datetime
import calendar as calendar

from Reporting import *
import variable_list_crop

from InitialCondition import *
from RootZoneWater import *
from SnowFrost import SnowFrost
from CheckGroundwaterTable import CheckGroundwaterTable
from LandCoverParameters import *
from Drainage import Drainage
from Interception import *
from Irrigation import *
from IrrigationSupply import *
from Infiltration import *
from CapillaryRise import CapillaryRise
from Evapotranspiration import *
from CropYield import CropYield
from Income import Income
from Investment import Investment
from Accounting import Accounting
from GridCellMean import GridCellMean

class LandCover(object):
    def __init__(self, var, config_section_name):
        self.var = var
        self._configuration = var._configuration
        self._modelTime = var._modelTime
        self.cloneMap = var.cloneMap
        self.landmask = var.landmask
        self.grid_cell_area = var.grid_cell_area
        self.dimensions = var.dimensions
        self.nLat, self.nLon, self.nCell = var.nLat, var.nLon, var.nCell
        self.nFarm, self.nCrop = 1, 1
        
        # attach meteorological and groundwater data to land cover object
        self.meteo = var.meteo_module
        self.groundwater = var.groundwater_module
        self.canal = var.canal_module

    def initial(self):
        pass
    
    def add_dimensions(self):
        """Function to add dimensions to model dimensions 
        object. This is necessary if the LandCover object 
        contains a reporting method."""
        self.dimensions['farm'] = np.arange(self.nFarm)
        self.dimensions['crop'] = np.arange(self.nCrop)

    def dynamic(self):
        pass

class NaturalVegetation(LandCover):
    def __init__(self, var, config_section_name):
        super(NaturalVegetation, self).__init__(
            var,
            config_section_name)

        self.lc_parameters_module = NaturalVegetationParameters(self, config_section_name)
        self.initial_condition_module = InitialConditionNaturalVegetation(self)
        self.root_zone_water_module = RootZoneWaterNaturalVegetation(self)
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
        self.root_zone_water_module = RootZoneWaterIrrigatedLand(self)

class ManagedLandIrrNonPaddy(ManagedLand):
    def __init__(self, var, config_section_name):
        super(ManagedLandIrrNonPaddy, self).__init__(
            var,
            config_section_name)
        self.irrigation_module = IrrigationNonPaddy(self)
        self.root_zone_water_module = RootZoneWaterIrrigatedLand(self)

class ManagedLandWithFarmerBehaviour(LandCover):
    def __init__(self, var, config_section_name):
        super(ManagedLandWithFarmerBehaviour, self).__init__(
            var,
            config_section_name)
        
        self.lc_parameters_module = ManagedLandWithFarmerBehaviourParameters(self, config_section_name)
        self.initial_condition_module = InitialConditionManagedLand(self)
        self.root_zone_water_module = RootZoneWaterIrrigatedLand(self)
        self.snow_frost_module = SnowFrost(self)
        self.potential_et_module = PotentialEvapotranspiration(self)
        self.interception_module = Interception(self)
        self.irrigation_demand_module = IrrigationMultipleCrops(self)
        self.irrigation_supply_module = IrrigationSupply(self)
        self.infiltration_module = Infiltration(self)
        self.capillary_rise_module = CapillaryRise(self)
        self.drainage_module = Drainage(self)
        self.actual_et_module = ActualEvapotranspiration(self)        
        self.crop_yield_module = CropYield(self)
        self.income_module = Income(self)
        self.accounting_module = Accounting(self)
        self.investment_module = Investment(self)
        self.grid_cell_mean_module = GridCellMean(self)
        self.add_dimensions()
        
    def initial(self):
        self.lc_parameters_module.initial()
        self.initial_condition_module.initial()
        self.root_zone_water_module.initial()
        self.snow_frost_module.initial()
        self.potential_et_module.initial()        
        self.interception_module.initial()
        self.irrigation_demand_module.initial()
        self.irrigation_supply_module.initial()
        self.infiltration_module.initial()
        self.capillary_rise_module.initial()
        self.drainage_module.initial()
        self.actual_et_module.initial()        
        self.crop_yield_module.initial()
        self.income_module.initial()
        self.accounting_module.initial()
        self.investment_module.initial()
        self.grid_cell_mean_module.initial()
        self.reporting_module = Reporting(
            self,
            self._configuration.outNCDir,
            self._configuration.NETCDF_ATTRIBUTES,
            self._configuration.irrNonPaddy,
            variable_list_crop,
            'irrNonPaddy')
        
    def dynamic(self):
        self.lc_parameters_module.dynamic()
        self.initial_condition_module.dynamic()
        
        self.root_zone_water_module.dynamic()
        self.snow_frost_module.dynamic()
        self.potential_et_module.dynamic()
        self.interception_module.dynamic()
        self.root_zone_water_module.dynamic()
        self.infiltration_module.compute_infiltration_capacity()        
        self.irrigation_demand_module.dynamic()        
        self.irrigation_supply_module.dynamic()

        # the order here (infiltration/cap rise/drainage)
        # is the same as in CWATM
        self.infiltration_module.dynamic()
        self.root_zone_water_module.dynamic()
        self.capillary_rise_module.dynamic()
        self.drainage_module.dynamic()
        
        self.root_zone_water_module.dynamic()
        self.actual_et_module.dynamic()
        self.crop_yield_module.dynamic()
        self.income_module.dynamic()
        self.accounting_module.dynamic()
        self.investment_module.dynamic()
        self.grid_cell_mean_module.dynamic()
        self.reporting_module.report()
        
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
        self.infiltration_module = InfiltrationSealed(self)
        self.capillary_rise_module = CapillaryRise(self)
        self.drainage_module = Drainage(self)

    def initial(self):
        self.lc_parameters_module.initial()
        self.initial_condition_module.initial()
        self.snow_frost_module.initial()
        self.interception_module.initial()
        self.evapotranspiration_module.initial()
        self.infiltration_module.initial()
        self.capillary_rise_module.initial()
        self.drainage_module.initial()
        
    def dynamic(self):
        self.lc_parameters_module.dynamic()
        self.initial_condition_module.dynamic()
        self.snow_frost_module.dynamic()
        self.interception_module.dynamic()
        self.evapotranspiration_module.dynamic()
        self.infiltration_module.dynamic()

class OpenWater(LandCover):
    def __init__(self, var, config_section_name):
        super(OpenWater, self).__init__(
            var,
            config_section_name)        
        self.lc_parameters_module = WaterParameters(self, config_section_name)
        self.initial_condition_module = InitialConditionSealedLand(self)
        self.snow_frost_module = SnowFrost(self)
        self.interception_module = InterceptionWater(self)
        self.evapotranspiration_module = EvaporationWater(self)
        self.infiltration_module = InfiltrationWater(self)
        # include these modules so that some variables are initialized to zero
        self.capillary_rise_module = CapillaryRise(self)  
        self.drainage_module = Drainage(self)

    def initial(self):
        self.lc_parameters_module.initial()
        self.initial_condition_module.initial()
        self.snow_frost_module.initial()
        self.interception_module.initial()
        self.evapotranspiration_module.initial()
        self.infiltration_module.initial()
        self.capillary_rise_module.initial()
        self.drainage_module.initial()
        
    def dynamic(self):
        self.lc_parameters_module.dynamic()
        self.initial_condition_module.dynamic()
        self.snow_frost_module.dynamic()
        self.interception_module.dynamic()
        self.evapotranspiration_module.dynamic()
        self.infiltration_module.dynamic()
        
class Forest(NaturalVegetation):
    """Class to represent forest land cover"""
        
class Grassland(NaturalVegetation):
    """Class to represent grassland"""

class IrrPaddy(ManagedLandIrrPaddy):
    """Class to represent irrigated paddy"""

class IrrNonPaddy(ManagedLandWithFarmerBehaviour):
    """Class to represent irrigated non-paddy"""
# class IrrNonPaddy(ManagedLandIrrNonPaddy):
#     """Class to represent irrigated non-paddy"""
    
class Sealed(SealedLand):
    """Class to represent sealed area"""

class Water(OpenWater):
    """Class to represent water"""
