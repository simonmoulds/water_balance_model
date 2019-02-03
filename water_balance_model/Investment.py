#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
import calendar
import VirtualOS as vos
import scipy.stats
import math
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
        """Function to install additional tubewells, if 
        required
        """
        # compute mean unmet irrigation demand per crop,
        # then sum to get total unmet demand
        mean_unmet_irrigation_demand = np.divide(
            self.var.UnmetIrrigationDemand,
            self.var.UnmetIrrigationDemandDays,
            out=np.zeros((self.var.nFarm, self.var.nCrop, self.var.nCell)),
            where=self.var.UnmetIrrigationDemandDays>0
        )
        total_mean_unmet_irrigation_demand = np.sum(
            mean_unmet_irrigation_demand,
            axis=1)             # farm, cell
        
        # max tubewell capacity is the maximum volume of water
        # a single tubewell can abstract in a single day. It is
        # a function of tubewell horsepower and groundwater
        # depth. Hence we need to compute the average capacity
        # during the growing season (see Tubewells class).
        max_tubewell_capacity = 1000.  # FIXME
        
        # Only allow one additional tubewell per farm per year
        require_additional_tubewell = (
            total_mean_unmet_irrigation_demand > 0
        ).astype(np.int64)
        # OLD:
        # required_additional_tubewells = (
        #     total_mean_unmet_irrigation_demand
        #     / max_tubewell_capacity
        # )
        # required_additional_tubewells = np.ceil(required_additional_tubewells)

        # TODO: refine this
        return_on_investment = self.compute_return_on_investment()
        positive_benefit = (return_on_investment > 0)
        installation_cost = (
            self.var.TubewellInstallationCost
            + self.var.PumpCost  # TODO: include maintenance cost
        )
        installation_cost = np.broadcast_to(
            installation_cost[None,...],
            (self.var.nFarm, self.var.nCell)
        )

        # 'SavingsAccount' represents the savings of the
        # subcategory as a whole. The use of subcategories
        # means that the savings rate has been effectively
        # normalised for variability of farm size and
        # tubewell ownership. However, it obviously still
        # varies amongst farmers in the category, and we
        # need to take that into account here. First we
        # compute the mean savings per farm, then assume
        # a [log-]normal distribution with standard
        # deviation... ??? 
        mean_savings_per_farm = np.divide(
            self.var.SavingsAccount,
            self.var.num_farms_per_subcategory,
            out=np.zeros((self.var.nFarm, self.var.nCell)),
            where=self.var.num_farms_per_subcategory>0
        )

        # probability of mean savings per farm exceeding the cost of installing a tubewell
        cond = mean_savings_per_farm > 0
        probability_farm_can_afford_tubewell = np.zeros((self.var.nFarm, self.var.nCell))
        probability_farm_can_afford_tubewell[cond] = (
            1.
            - scipy.stats.lognorm.cdf(
                installation_cost[cond],
                s=np.log(mean_savings_per_farm[cond])/10,  # TODO: - calibration?
                scale=mean_savings_per_farm[cond]
            )
        )
        # print installation_cost.shape
        # print probability_farm_can_afford_tubewell.shape
        num_farms_to_install_tubewell = np.floor(
            self.var.num_farms_per_subcategory
            * probability_farm_can_afford_tubewell
        )

        max_num_tubewells = self.var.max_num_tubewells[self.var.farm_index]
        allow_tubewell_installation = (
            self.var.num_tubewell_per_subcategory
            < self.var.max_num_tubewells[self.var.farm_index][:,None]
        )
        
        num_farms_to_install_tubewell[np.logical_not(allow_tubewell_installation)] = 0
        num_farms_to_install_tubewell = np.minimum(
            num_farms_to_install_tubewell,
            self.var.num_farms_per_subcategory
        )

        num_farms_to_remove_from_category = num_farms_to_install_tubewell.copy()
        num_farms_to_add_to_category = np.concatenate(
            [np.zeros((2, self.var.nCell)),
             num_farms_to_install_tubewell[:-2,...]
            ],
            axis=0
        )

        self.var.num_farms_per_subcategory += num_farms_to_add_to_category
        self.var.num_farms_per_subcategory -= num_farms_to_remove_from_category
        
        # TODO: tubewells to uninstall because they are no longer required

        # Update savings account by multiplying the number of farms to remove 
        self.var.SavingsAccount -= (num_farms_to_install_tubewell * installation_cost)
        
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
        
