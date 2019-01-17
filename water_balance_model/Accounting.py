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
        self.var.SavingsAccount = np.ones((self.var.nFarm, self.var.nCell)) * 5000.
        self.var.CurrentAccount = np.ones((self.var.nFarm, self.var.nCell)) * 5000.
    
    def update_farm_accounts(self):

        # Treat savings account as 'potential investment'
        
        positive_balance = self.var.CurrentAccount > 0
        if self.var.IsLastDayOfYear:
            self.var.SavingsAccount[positive_balance] += self.var.CurrentAccount[positive_balance]
            self.var.CurrentAccount[positive_balance] = 0.
            self.var.CurrentAccount += self.var.AnnualIncome            
        # print np.max(self.var.CurrentAccount)
        # print np.max(self.var.SavingsAccount)
    def dynamic(self):
        self.update_farm_accounts()
