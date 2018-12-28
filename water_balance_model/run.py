#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

from pcraster.framework import DynamicModel
from pcraster.framework import DynamicFramework

from hydro_model_builder.DeterministicRunner import DeterministicRunner
from hydro_model_builder.ModelTime import ModelTime
from hydro_model_builder.Reporting import Reporting
from hydro_model_builder import disclaimer

# from FAO66_behaviour import FAO66_behaviour
from LandSurface import LandSurface
from Configuration import Configuration
import variable_list

import logging
logger = logging.getLogger(__name__)

def main():

    # disclaimer.print_disclaimer()

    # get the full path of the config file provided as system argument
    iniFileName = os.path.abspath(sys.argv[1])
    debug_mode = False
    if len(sys.argv) > 2:
        if (sys.argv[2] == "debug"):
            debug_mode = True

    configuration = Configuration(iniFileName=iniFileName, debug_mode=debug_mode)
    currTimeStep = ModelTime()
    initial_state = None
    currTimeStep.getStartEndTimeSteps(
        configuration.globalOptions['startTime'],
        configuration.globalOptions['endTime'])
    currTimeStep.update(1)    
    logger.info('Transient simulation run has started')
    deterministic_runner = DeterministicRunner(
        # FAO66_behaviour,
        LandSurface,
        configuration,
        currTimeStep,
        variable_list,
        initial_state)
    dynamic_framework = DynamicFramework(deterministic_runner, currTimeStep.nrOfTimeSteps)
    dynamic_framework.setQuiet(True)
    dynamic_framework.run()

if __name__ == '__main__':
    disclaimer.print_disclaimer(with_logger = True)
    sys.exit(main())
