#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

from pcraster.framework import DynamicModel
from pcraster.framework import DynamicFramework

# from Configuration import *
# from ModelTime import ModelTime
from Reporting import Reporting
# import variable_list
# from RefET import RefET

import hydro_model_builder.disclaimer
import logging
logger = logging.getLogger(__name__)

class DeterministicRunner(DynamicModel):    
    def __init__(self, model, configuration, modelTime, variable_list, initialState = None, suffix = None):
        DynamicModel.__init__(self)
        self.modelTime = modelTime
        self.model = model(configuration, modelTime, initialState)
        self.model.initial()
        self.reporting = Reporting(configuration, self.model, modelTime, variable_list, suffix)

    def initial(self):
        pass

    def dynamic(self):
        self.modelTime.update(self.currentTimeStep())
        self.model.dynamic()
        self.reporting.report()
