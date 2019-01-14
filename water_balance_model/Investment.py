#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
import calendar
from hydro_model_builder import VirtualOS as vos

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
            where=self.var.UnmetIrrigationDemandDays>0)

        return_on_investment = self.compute_return_on_investment()  # farm,cell
        positive_benefit = return_on_investment > 0                 # farm,cell
        installation_cost = (self.var.TubewellInstallationCost + self.var.PumpCost)  # farm,cell
        sufficient_resources = (self.var.SavingsAccount > installation_cost)
        cond = positive_benefit & sufficient_resources
        print np.sum(self.var.TubewellCount)
        self.var.TubewellCount[cond] += 1
        print np.sum(self.var.TubewellCount)

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
        
