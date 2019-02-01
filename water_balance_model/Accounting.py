#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
import VirtualOS as vos

import logging
logger = logging.getLogger(__name__)

class Accounting(object):

    def __init__(self, Accounting_variable):
        self.var = Accounting_variable        
        
    def initial(self):
        # TODO: estimate realistic initial values
        self.var.SavingsAccount = np.zeros((self.var.nFarm, self.var.nCell))
        self.var.CurrentAccount = (
            np.ones((self.var.nFarm, self.var.nCell))
            * 5000.
            * self.var.num_farms_per_subcategory
        )
    
    def update_farm_accounts(self):

        # Treat savings account as 'potential investment'        
        positive_balance = self.var.CurrentAccount > 0
        savings_rate = 0.01 # ***TODO*** calibration factor to account for costs we do not consider
        if self.var.IsLastDayOfYear:
            self.var.CurrentAccount[positive_balance] *= savings_rate
            self.var.SavingsAccount[positive_balance] += self.var.CurrentAccount[positive_balance]
            self.var.CurrentAccount[positive_balance] = 0.
            self.var.CurrentAccount += self.var.AnnualIncome
            
    def dynamic(self):
        self.update_farm_accounts()
        
