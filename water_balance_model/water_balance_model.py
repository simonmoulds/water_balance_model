#!/usr/bin/env python
# -*- coding: utf-8 -*-

from Meteo import Meteo
from Groundwater import Groundwater
from LandCover import *
from SoilAndTopoParameters import *
from CheckGroundwaterTable import *
from PreIrrigation import *
from Drainage import *
from RainfallPartition import *
from Irrigation import *
from Infiltration import *
from CapillaryRise import *
from Inflow import *

from FieldMgmtParameters import *
from IrrigationMgmtParameters import *
from InitialCondition import *
from RootZoneWater import *
from GrowthStage import *
from RootDevelopment import *
from CropEvapotranspiration import *

# from GridCellMean import *

import logging
logger = logging.getLogger(__name__)

class WaterBalanceModel(object):

    def __init__(self, var):
        self.meteo_module = Meteo(var)
        self.groundwater_module = Groundwater(var)
        # self.farm_parameters_module = FarmParameters(var)
        # self.crop_parameters_module = FAO56CropParameters(var)
        self.land_cover_module = LandCover(var)
        # self.crop_area_module = CropArea(var)
        # self.field_mgmt_parameters_module = FieldMgmtParameters(var)
        # self.irrigation_mgmt_parameters_module = IrrigationMgmtParameters(var)
        self.soil_parameters_module = SoilAndTopoParameters(var)        
        self.initial_condition_module = InitialCondition(var)        
        self.check_groundwater_table_module = CheckGroundwaterTable(var)
        self.pre_irrigation_module = PreIrrigation(var)
        self.drainage_module = Drainage(var)
        self.rainfall_partition_module = RainfallPartition(var)
        self.root_zone_water_module = RootZoneWater(var)
        self.irrigation_demand_module = Irrigation(var)        
        self.infiltration_module = Infiltration(var)
        self.capillary_rise_module = CapillaryRise(var)
        # self.growth_stage_module = GrowthStage(var)
        self.root_development_module = RootDevelopment(var)
        self.evapotranspiration_module = CropEvapotranspiration(var)
        self.inflow_module = Inflow(var)

    def initial(self):
        """Function to initialize sub-modules"""
        self.meteo_module.initial()
        self.groundwater_module.initial()
        # self.farm_parameters_module.initial()        
        # self.crop_parameters_module.initial()
        self.land_cover_module.initial()
        # self.crop_area_module.initial()
        # self.field_mgmt_parameters_module.initial()
        # self.irrigation_mgmt_parameters_module.initial()
        self.soil_parameters_module.initial()        
        self.initial_condition_module.initial()
        self.check_groundwater_table_module.initial()
        self.pre_irrigation_module.initial()
        self.drainage_module.initial()
        self.rainfall_partition_module.initial()
        self.root_zone_water_module.initial()
        self.irrigation_demand_module.initial()
        self.infiltration_module.initial()
        self.capillary_rise_module.initial()
        # self.growth_stage_module.initial()
        self.root_development_module.initial()
        self.evapotranspiration_module.initial()
        self.inflow_module.initial()
        
    def dynamic(self):
        """Function to update crop model state for current 
        time step
        """
        self.meteo_module.dynamic()
        self.groundwater_module.dynamic()
        # self.farm_parameters_module.dynamic()
        # self.crop_parameters_module.dynamic()
        self.land_cover_module.dynamic()
        # self.crop_area_module.dynamic()
        # self.irrigation_mgmt_parameters_module.dynamic()
        self.initial_condition_module.dynamic()
        self.check_groundwater_table_module.dynamic()
        self.pre_irrigation_module.dynamic()
        self.drainage_module.dynamic()
        self.rainfall_partition_module.dynamic()                
        self.root_zone_water_module.dynamic()        
        self.irrigation_demand_module.dynamic()
        self.infiltration_module.dynamic()
        self.capillary_rise_module.dynamic()
        # self.growth_stage_module.dynamic()
        self.root_zone_water_module.dynamic()
        self.evapotranspiration_module.dynamic()
        self.inflow_module.dynamic()
        self.root_zone_water_module.dynamic()
