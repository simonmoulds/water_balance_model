#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
import calendar
import VirtualOS as vos

import logging
logger = logging.getLogger(__name__)

class Investment(object):

    def __init__(self, Investment_variable):
        self.var = Investment_variable        
        
    def initial(self):
        pass
    
    def farm_investment(self):
        if self.var.IsLastDayOfYear:
            self.install_additional_tubewell()

    def install_additional_tubewell(self):
        mean_unmet_irrigation_demand = np.divide(
            self.var.UnmetIrrigationDemand,
            self.var.UnmetIrrigationDemandDays,
            out=np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell)),
            where=self.var.UnmetIrrigationDemandDays>0)  # farm, crop, cell

        total_mean_unmet_irrigation_demand = np.sum(
            mean_unmet_irrigation_demand,
            axis=1)             # farm, cell
        
        print 'total_unmet_irrigation_demand: '
        print total_mean_unmet_irrigation_demand[:,0]

        # max tubewell capacity is the maximum volume of water
        # a single tubewell can abstract in a single day. It is
        # a function of tubewell horsepower and groundwater
        # depth. Hence we need to compute the average capacity
        # during the growing season (see Tubewells class).
        max_tubewell_capacity = 1000.

        # required additional capacity is the the total unmet
        # demand divided by the maximum tubewell capacity.
        required_additional_tubewells = (
            total_mean_unmet_irrigation_demand
            / max_tubewell_capacity
        )
        required_additional_tubewells = np.ceil(required_additional_tubewells)

        # TODO: not currently used
        return_on_investment = self.compute_return_on_investment()  # farm,cell
        positive_benefit = return_on_investment > 0                 # farm,cell
        
        installation_cost = (self.var.TubewellInstallationCost + self.var.PumpCost)  # farm,cell
        print 'savings:'
        print self.var.SavingsAccount[:,0]
        
        farm_investment_factor = 0.75
        tubewells_to_install = np.minimum(
            required_additional_tubewells,
            np.floor((self.var.SavingsAccount * farm_investment_factor) / installation_cost)
        )
        
        print 'current tubewells:'
        print self.var.tubewell_count[:,0]
        # print 'tubewells to install:'
        # print tubewells_to_install[:,0]
        self.var.tubewell_count[positive_benefit] += tubewells_to_install[positive_benefit]
        self.var.SavingsAccount -= (tubewells_to_install * installation_cost)
        # print 'savings:'
        # print self.var.SavingsAccount[:,0]
        print 'updated tubewells:'
        print self.var.tubewell_count[:,0]
        
    def compute_return_on_investment(self):
        annual_cost_of_tubewell = (
            (self.var.TubewellInstallationCost / self.var.TubewellLifespan) +
            (self.var.PumpCost / self.var.PumpLifespan) +
            (self.var.TubewellMaintenanceCost)
            )

        potential_benefit_of_irrigation = (
            self.var.PotentialAnnualCropIncome
            - self.var.AnnualCropIncome)

        # up until now the potential benefit represents the benefit per
        # crop. Now, sum across all crops to get the total benefit.
        sum_potential_benefit_of_irrigation = np.sum(
            potential_benefit_of_irrigation,
            axis=1)
        
        return_on_investment = (
            sum_potential_benefit_of_irrigation
            - annual_cost_of_tubewell)

        # print self.var.PotentialAnnualCropIncome[24,:,102]
        # print self.var.AnnualCropIncome[24,:,102]
        # print sum_potential_benefit_of_irrigation[24,102]
        # print return_on_investment.shape
        # print return_on_investment[:,102]
        
        return return_on_investment
    
    def dynamic(self):
        self.farm_investment()
        
