#!/usr/bin/env python
# -*- coding: utf-8 -*-

# AquaCrop crop growth model

# The purpose of this file is to parse the configuration file

from configparser import ConfigParser, ExtendedInterpolation
import os
import sys
import string
from hydro_model_builder import VirtualOS as vos
import time
import datetime
import shutil
import glob
import warnings
from aquacrop.Messages import *
import logging
logger = logging.getLogger(__name__)

class Configuration(object):

    def __init__(self, iniFileName, debug_mode = False, no_modification = True, system_arguments = None, relative_ini_meteo_paths = False):
        object.__init__(self)
        if iniFileName is None:
            msg = 'Error: No configuration file specified'
            raise AQError(msg)
        
        self._timestamp = datetime.datetime.now()
        self.iniFileName = os.path.abspath(iniFileName)
        self.debug_mode = debug_mode
        self.parse_configuration_file(self.iniFileName)
        if no_modification: self.set_configuration(system_arguments)
        self.main_output_directory = self.globalOptions['outputDir']

    def set_configuration(self, system_arguments = None):

        self.repair_ini_key_names()
        
        # set all paths
        # self.set_input_files()
        self.set_clone_map()
        self.create_output_directories()
        self.create_coupling_directories()
        
        self.initialize_logging("Default", system_arguments)
        self.backup_configuration()

    def initialize_logging(self, log_file_location = "Default", system_arguments = None):
        """Initialize logging. Prints to both the console and a log 
        file, at configurable levels
        """

        # set root logger to debug level        
        logging.getLogger().setLevel(logging.DEBUG)

        # logging format 
        formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')

        # default logging levels
        log_level_console    = "INFO"
        log_level_file       = "INFO"
        # order: DEBUG, INFO, WARNING, ERROR, CRITICAL
        
        # log level based on ini/configuration file:
        if "log_level_console" in self.globalOptions.keys():
            log_level_console = self.globalOptions['log_level_console']        
        if "log_level_file" in self.globalOptions.keys():
            log_level_file = self.globalOptions['log_level_file']        

        # log level for debug mode:
        if self.debug_mode == True: 
            log_level_console = "DEBUG"
            log_level_file    = "DEBUG"

        console_level = getattr(logging, log_level_console.upper(), logging.INFO)
        if not isinstance(console_level, int):
            raise ValueError('Invalid log level: %s', log_level_console)
        
        # create handler, add to root logger
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(console_level)
        logging.getLogger().addHandler(console_handler)

        # log file name (and location)
        if log_file_location != "Default":  self.logFileDir = log_file_location
        log_filename = self.logFileDir + os.path.basename(self.iniFileName) + '_' + str(self._timestamp.isoformat()).replace(":",".") + '.log'

        file_level = getattr(logging, log_level_file.upper(), logging.DEBUG)
        if not isinstance(console_level, int):
            raise ValueError('Invalid log level: %s', log_level_file)

        # create handler, add to root logger
        file_handler = logging.FileHandler(log_filename)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(file_level)
        logging.getLogger().addHandler(file_handler)
        
        # file name for debug log 
        dbg_filename = self.logFileDir + os.path.basename(self.iniFileName) + '_' +  str(self._timestamp.isoformat()).replace(":",".") + '.dbg'

        # create handler, add to root logger
        debug_handler = logging.FileHandler(dbg_filename)
        debug_handler.setFormatter(formatter)
        debug_handler.setLevel(logging.DEBUG)
        logging.getLogger().addHandler(debug_handler)

        # # print disclaimer
        # disclaimer.print_disclaimer(with_logger = True)
        
        logger.info('Model run started at %s', self._timestamp)
        logger.info('Logging output to %s', log_filename)
        logger.info('Debugging output to %s', dbg_filename)
        
        if system_arguments != None:
            logger.info('The system arguments given to execute this run: %s', system_arguments)
        

    def backup_configuration(self):
        """Function to copy ini file to log directory"""
        shutil.copy(self.iniFileName,
                    self.logFileDir
                    + os.path.basename(self.iniFileName)
                    + '_'
                    + str(self._timestamp.isoformat()).replace(":",".") + '.ini')
        
    def parse_configuration_file(self, modelFileName):
        config = ConfigParser(interpolation=ExtendedInterpolation())
        config.optionxform = str
        config.read(modelFileName)

        # sections in configuration file
        self.allSections = config.sections()

        # read all sections
        for section in self.allSections:
            vars(self)[section] = {}
            options = config.options(section)
            for option in options:
                val = config.get(section, option)
                self.__getattribute__(section)[option] = val

    # # def set_input_files(self):
    # #     self.set_clone_map()
    # #     # self.set_initial_condition_file()
    # #     # self.set_meteo_files()
    # #     # # self.set_co2_input_file()
    # #     # self.set_groundwater_input_file()
    # #     # self.set_groundwater_initial_value_file()
    # #     # # self.set_canal_input_file()
    # #     # self.set_soil_parameter_input_file()
    # #     # self.set_crop_input_files()
    # #     # self.set_farm_input_files()
    # #     # self.set_irrigation_management_input_files()
    # #     # self.set_field_management_input_files()
    # #     # # self.set_price_input_files()
        
    def set_clone_map(self):
        self.cloneMap = vos.getFullPath(
            self.globalOptions['cloneMap'],
            self.globalOptions['inputDir'])

    # # def set_initial_condition_file(self):
    # #     if self.globalOptions['initialConditionNC'] != "None":
    # #         self.globalOptions['initialConditionNC'] = vos.getFullPath(self.globalOptions['initialConditionNC'], self.globalOptions['inputDir'])

    # # def set_meteo_files(self):
    # #     meteoInputFiles = ['precipitationNC','minDailyTemperatureNC','maxDailyTemperatureNC','refETPotFileNC']
    # #     for item in meteoInputFiles:
    # #         if self.meteoOptions[item] != "None":
    # #             self.meteoOptions[item] = vos.getFullPath(self.meteoOptions[item], self.globalOptions['inputDir'])

    # # def set_co2_input_file(self):
    # #     co2InputFiles = ['carbonDioxideNC']
    # #     for item in co2InputFiles:
    # #         if self.carbonDioxideOptions[item] != "None":                
    # #             self.carbonDioxideOptions[item] = vos.getFullPath(self.carbonDioxideOptions[item], self.globalOptions['inputDir'])

    # # def set_groundwater_input_file(self):
    # #     item = 'groundwaterNC'
    # #     if item in self.groundwaterOptions.keys() and self.groundwaterOptions[item] != "None":
    # #         self.groundwaterOptions[item] = vos.getFullPath(self.groundwaterOptions[item], self.groundwaterOptions['groundwaterInputDir'])

    # # def set_groundwater_initial_value_file(self):
    # #     item = 'initialGroundwaterLevelNC'
    # #     if item in self.groundwaterOptions.keys() and self.groundwaterOptions[item] != "None":
    # #         self.groundwaterOptions[item] = vos.getFullPath(self.groundwaterOptions[item], self.globalOptions['inputDir'])

    # # def set_canal_input_file(self):
    # #     # canal input file
    # #     item = 'canalSupplyNC'
    # #     if item in self.canalOptions.keys() and self.canalOptions[item] != "None":
    # #         self.canalOptions[item] = vos.getFullPath(self.canalOptions[item], self.canalOptions['canalSupplyInputDir'])

    # # def set_soil_parameter_input_file(self):
    # #     item = 'soilAndTopoNC'
    # #     if self.soilOptions[item] != "None":
    # #         self.soilOptions[item] = vos.getFullPath(self.soilOptions[item], self.globalOptions['inputDir'])

    # # def set_crop_input_files(self):
    # #     cropInputFiles = ['cropParameterNC','croplandAreaNC','cropAreaNC','PotYieldNC']
    # #     for item in cropInputFiles:
    # #         if item in self.cropOptions:
    # #             if self.cropOptions[item] != "None":
    # #                 self.cropOptions[item] = vos.getFullPath(self.cropOptions[item], self.globalOptions['inputDir'])

    # # def set_farm_input_files(self):
    # #     farmInputFiles = ['farmAreaNC','farmCategoryNC','farmCategoryAreaNC','initialCanalAccessNC','initialTubewellCapacityNC','initialSavingsAccountNC','initialTubewellOwnershipNC']
    # #     for item in farmInputFiles:
    # #         if item in self.farmOptions:
    # #             if self.farmOptions[item] != "None":
    # #                 self.farmOptions[item] = vos.getFullPath(self.farmOptions[item], self.globalOptions['inputDir'])

    # # def set_irrigation_management_input_files(self):
    # #     irrMgmtInputFiles = ['irrMgmtParameterNC']
    # #     for item in irrMgmtInputFiles:
    # #         if self.irrMgmtOptions[item] != "None":
    # #             self.irrMgmtOptions[item] = vos.getFullPath(self.irrMgmtOptions[item], self.globalOptions['inputDir'])

    # # def set_field_management_input_files(self):
    # #     item = 'fieldMgmtParameterNC'
    # #     if self.fieldMgmtOptions[item] != "None":
    # #         self.fieldMgmtOptions[item] = vos.getFullPath(self.fieldMgmtOptions[item], self.globalOptions['inputDir'])

    # # def set_price_input_files(self):
    # #     priceInputFiles = ['cropPriceNC','NitrogenPriceNC','PhosphorusPriceNC','PotassiumPriceNC','dieselPriceNC']
    # #     for item in priceInputFiles:
    # #         if self.priceOptions[item] != "None":
    # #             self.priceOptions[item] = vos.getFullPath(self.priceOptions[item], self.globalOptions['inputDir'])
            
    def create_output_directories(self):

        cleanOutputDir = False
        if cleanOutputDir:
            try:
                shutil.rmtree(self.globalOptions['outputDir'])
            except:
                pass

        try:
            os.makedirs(self.globalOptions['outputDir'])
        except:
            pass

        # make temp directory
        self.tmpDir = vos.getFullPath("tmp/", self.globalOptions['outputDir'])

        if os.path.exists(self.tmpDir):
            shutil.rmtree(self.tmpDir)
        os.makedirs(self.tmpDir)

        # make netcdf directory
        self.outNCDir = vos.getFullPath("netcdf/", self.globalOptions['outputDir'])
        
        if os.path.exists(self.outNCDir):
            shutil.rmtree(self.outNCDir)
        os.makedirs(self.outNCDir)

        # make and populate backup directory for Python scripts
        self.scriptDir = vos.getFullPath("scripts/", self.globalOptions['outputDir'])

        if os.path.exists(self.scriptDir):
            shutil.rmtree(self.scriptDir)
        os.makedirs(self.scriptDir)

        # working/starting directory where all Python scripts are located
        path_of_this_module = os.path.abspath(os.path.dirname(__file__))
        self.starting_directory = path_of_this_module
        
        all_files = glob.glob(os.path.join(path_of_this_module, '*.py'))
        for filename in all_files:
            shutil.copy(filename, self.scriptDir)

        # make log directory
        self.logFileDir = vos.getFullPath("log/", self.globalOptions['outputDir'])

        cleanLogDir = True
        if os.path.exists(self.logFileDir) and cleanLogDir:
            shutil.rmtree(self.logFileDir)
        os.makedirs(self.logFileDir)

        # make end state directory
        self.endStateDir = vos.getFullPath("states/", self.globalOptions['outputDir'])

        if os.path.exists(self.endStateDir):
            shutil.rmtree(self.endStateDir)
        os.makedirs(self.endStateDir)

    def create_coupling_directories(self):
        pass
    
    def repair_ini_key_names(self):
        """This function is used to change or modify key names of
        options, to check the validity of options and to infill 
        missing keys"""
        self.repair_global_options()
        
    def repair_global_options(self):
        if 'globalOptions' not in self.allSections:
            self.globalOptions = {}  # TODO: raise error
        self.repair_timestep()
        
    def repair_timestep(self):
        self.timeStep = 1.0
        self.timeStepUnit = "day"
        if ('timeStep' in self.globalOptions.keys()
            and 'timeStepUnit'in self.globalOptions.keys()):

            if (float(self.globalOptions['timeStep']) != 1.0
                or self.globalOptions['timeStepUnit'] != "day"):
                
                logger.error('The model runs only on daily time step. Please check your ini/configuration file')
                self.timeStep     = None
                self.timeStepUnit = None

