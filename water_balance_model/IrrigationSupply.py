#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import calendar
import numpy as np
from hydro_model_builder import VirtualOS as vos
from aquacrop.Messages import *
import logging
logger = logging.getLogger(__name__)

class DieselPrice(object):

    def __init__(self, DieselPrice_variable):
        self.var = DieselPrice_variable        
        self.var.DieselPriceFileNC = (
            str(self.var._configuration.priceOptions['dieselPriceNC']))
        self.var.DieselPriceVarName = (
            str(self.var._configuration.priceOptions['dieselPriceVariableName']))

    def initial(self):
        self.var.DieselPrice = np.zeros((self.var.nCell))

    def reset_initial_conditions(self):
        pass
    
    def set_diesel_price(self):
        if self.var._modelTime.timeStepPCR == 1 or self.var._modelTime.doy == 1:
            date = '%04i-%02i-%02i' % (self.var._modelTime.year, 1, 1)
            if not self.var.DieselPriceFileNC == "None":
                diesel_price = vos.netcdf2PCRobjClone(
                    self.var.DieselPriceFileNC,
                    self.var.DieselPriceVarName,
                    date,
                    useDoy = None,
                    cloneMapFileName = self.var.cloneMap,
                    LatitudeLongitude = True)
                diesel_price = diesel_price[self.var.landmask]
                # diesel_price = np.broadcast_to(
                #     diesel_price[None,None,:],            
                #     (self.var.nFarm, self.var.nCrop, self.var.nCell))
                self.var.DieselPrice = diesel_price

    def dynamic(self):
        self.set_diesel_price()

class IrrigationSupply(object):

    def __init__(self, IrrigationSupply_variable):
        self.var = IrrigationSupply_variable
        self.diesel_price_module = DieselPrice(IrrigationSupply_variable)
    
    def initial(self):
        self.diesel_price_module.initial()
        arr_zeros = np.zeros((self.var.nFarm, self.var.nCell))
        self.var.GwPumpingVol = arr_zeros.copy()
        self.var.SwPumpingVol = arr_zeros.copy()
        self.var.UnmetIrrigationDemand = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))
        self.var.UnmetIrrigationDemandDays = np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell))
        # self.var.UnmetIrrigationDemand = arr_zeros.copy()
        # self.var.UnmetIrrigationDemandDays = arr_zeros.copy()
        
    def reset_initial_conditions(self):
        if self.var.IsFirstDayOfYear:
            self.var.UnmetIrrigationDemand[:] = 0
            self.var.UnmetIrrigationDemandDays[:] = 0

    def irrigation_expenditure(self):
        self.diesel_pump_cost()
        self.electric_pump_cost()
        self.var.IrrigationCost = self.var.DieselPumpCost + self.var.ElectricPumpCost
        
    def diesel_pump_cost(self):
        fuel_efficiency = 1.
        unit_fuel_consumption = (0.1133 * self.var.zGW) + 0.7949
        unit_fuel_consumption = unit_fuel_consumption * fuel_efficiency / 102.87
        self.var.DieselPumpCost = (
            unit_fuel_consumption
            * self.var.GwPumpingVol
            * self.var.DieselPrice
            * 0.4)              # TODO: ask JoK the reason for multiplying by 0.4 (subsidy, efficiency?)
        
    def electric_pump_cost(self):
        self.var.ElectricPumpCost = 0.

    def surface_water_irrigation_cost(self):
        pass
            
    def irrigation_supply(self):

        # Compute irrigation demand in m3 (depth -> volume)
        irrigation_depth = self.var.Irr / 1000
        irrigation_demand = np.multiply(
            irrigation_depth,
            self.var.FarmCropArea,
            out=np.zeros_like(self.var.FarmCropArea),
            where=self.var.FarmCropArea > 0)
        
        # Sum along crop axis to get total irrigation demand across
        # all crops
        total_irrigation_demand = np.sum(irrigation_demand, axis=1)  # farm, cell

        # Compute the relative irrigation demand of each crop grown
        # on a given farm (farm, crop, cell)
        relative_irrigation_demand = np.divide(
            irrigation_demand,
            total_irrigation_demand[:,None,:],
            out=np.zeros_like(irrigation_demand),
            where=total_irrigation_demand[:,None,:] > 0)

        # The following variables (up to total_irrigation_supply) have
        # dimensions (farm, cell)
        canal_supply = np.broadcast_to(
            self.var.CanalSupply,
            (self.var.nFarm, self.var.nCell)).copy()
        canal_supply *= self.var.CanalAccess
        canal_demand = np.clip(canal_supply, 0, total_irrigation_demand)

        # Attempt to meet the outstanding demand from groundwater
        groundwater_demand = np.clip(
            total_irrigation_demand - canal_demand,
            0, None)

        # Compute the maximum amount of groundwater which can be
        # extracted on a given day, based on assumptions about operating
        # hours and pump horsepower 
        # (http://krishikosh.egranth.ac.in/bitstream/1/65128/1/thesis.pdf)
        max_groundwater_supply_divd = (
            self.var.TubewellOperatingHours
            * 129574.1
            * self.var.PumpHorsePower)
        max_groundwater_supply_divs = (
            self.var.zGW
            + np.divide(
                (255.5998 * self.var.TubewellOperatingHours ** 2),
                (self.var.zGW ** 2 * 4 ** 4),
                out=np.zeros((self.var.nFarm, self.var.nCell)),
                where=self.var.zGW>0))
        max_groundwater_supply = np.divide(
            max_groundwater_supply_divd,
            max_groundwater_supply_divs,
            out=np.zeros((self.var.nFarm, self.var.nCell)),
            where=max_groundwater_supply_divs>0)
        max_groundwater_supply /= 1000 # litres -> m3                                     
        max_groundwater_supply *= self.var.TubewellCount

        groundwater_supply = np.clip(
            groundwater_demand,
            None,
            max_groundwater_supply)

        self.var.SwPumpingVol = canal_demand.copy()
        self.var.GwPumpingVol = groundwater_supply.copy()
        
        # unmet_irrigation_demand = np.clip(
        #     (total_irrigation_demand
        #      - canal_supply
        #      - groundwater_supply),
        #     0,
        #     None)        
        # self.var.UnmetIrrigationDemand += unmet_irrigation_demand
        # self.var.UnmetIrrigationDemandDays[unmet_irrigation_demand > 0] += 1
        
        # ***TODO: adjust according to available account balance***        
        
        total_irrigation_supply = (
            self.var.SwPumpingVol
            + self.var.GwPumpingVol)

        # Get irrigation supply as a volume, then divide by crop area
        # to get depth
        irrigation_supply_vol = np.multiply(
            total_irrigation_supply[:,None,:],
            relative_irrigation_demand)

        unmet_irrigation_demand = np.clip(
            (irrigation_demand - irrigation_supply_vol),
            0,
            None)        
        self.var.UnmetIrrigationDemand += unmet_irrigation_demand
        self.var.UnmetIrrigationDemandDays[unmet_irrigation_demand > 0] += 1
        
        # Lastly, limit calculated irrigation demand to the maximum
        # available supply
        irrigation_supply = np.divide(
            irrigation_supply_vol,
            self.var.FarmCropArea,
            out=np.zeros_like(self.var.FarmCropArea),
            where=self.var.FarmCropArea > 0)
        irrigation_supply *= 1000.  # m -> mm
        # irrigation_supply = np.round(irrigation_supply * 1000., decimals=3)
        self.var.Irr = np.clip(self.var.Irr, None, irrigation_supply)  # farm, crop, cell        

        # compute irrigation expenses
        self.irrigation_expenditure()
        
    def dynamic(self):
        self.reset_initial_conditions()
        self.diesel_price_module.dynamic()
        self.irrigation_supply()
