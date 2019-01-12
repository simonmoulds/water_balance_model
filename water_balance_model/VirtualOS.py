#!/usr/bin/env python
# -*- coding: utf-8 -*-

import shutil
import subprocess
import datetime
import random
import os
import gc
import re
import math
import operator
import sys
import types
import calendar
import glob
import time

import netCDF4 as nc
import numpy as np
import numpy.ma as ma
import pcraster as pcr
import string

from Messages import *

import logging
logger = logging.getLogger(__name__)

# file cache to minimize/reduce opening/closing files.  
filecache = dict()

# Global variables:
MV = 1e20
smallNumber = 1E-39

# Tuple of netcdf file suffixes (extensions) that can be used:
netcdf_suffixes = ('.nc4','.nc')

# def getFileList(inputDir, filePattern):
# 	'''creates a dictionary of	files meeting the pattern specified'''
# 	fileNameList = glob.glob(os.path.join(inputDir, filePattern))
# 	ll= {}
# 	for fileName in fileNameList:
# 		ll[os.path.split(fileName)[-1]]= fileName
# 	return ll

# def check_time_format_args(format_args):
#     """Function to check whether the correct format arguments
#     are provided in input filenames.
#     """
#     res = True
#     if len(format_args) > 0:
#         if 'day' in format_args:
#             if 'month' not in format_args or 'year' not in format_args:
#                 res = False
#         elif 'month' in format_args:
#             if 'year' not in format_args:
#                 res = False
#     return res

def gdal_warp(input_filename, output_filename, minx, miny, maxx, maxy):
    """This function is necessary because the python gdal bindings seem
    unreliable
    """
    cmd = ('gdalwarp -overwrite -te '
           + str(minx) + ' ' + str(miny) + ' ' + str(maxx) + ' ' + str(maxy) + ' '
           + str(input_filename) + ' '
           + str(output_filename))
    subprocess.check_output(cmd, shell=True)
    # os.system(cmd)

def get_clone_map_extent(cloneMapFileName):
    cloneAtt = getMapAttributesALL(cloneMapFileName)
    xmin = cloneAtt['xUL']
    ymin = cloneAtt['yUL'] - cloneAtt['rows']*cloneAtt['cellsize']
    xmax = cloneAtt['xUL'] + cloneAtt['cols']*cloneAtt['cellsize']
    ymax = cloneAtt['yUL']
    return (xmin, ymin, xmax, ymax)
    
def get_format_args(x):
    """Function to get format arguments from a string. This is
    useful to work out whether input data files are provided
    on a monthly or yearly basis
    """
    format_args = [tup[1] for tup in string.Formatter().parse(x) if tup[1] is not None]
    return format_args

def any_duplicates(lst):
    return len(lst) != len(set(lst))

def check_format_args_ok(format_args, allowable_args, allow_duplicates=True):
    format_args_ok = all([arg in allowable_args for arg in format_args])
    if format_args_ok and not allow_duplicates:
        format_args_ok = not any_duplicates(format_args)
    return format_args_ok

def check_if_nc_variable_has_dimension(ncFile, varname, dimname):
    if ncFile in filecache.keys():
        f = filecache[ncFile]
    else:
        try:
            f = nc.Dataset(ncFile)
        except:
            AQFileError(ncFile)
        filecache[ncFile] = f
    res = False
    try:
        res = (dimname in f.variables[varname].dimensions)
    except:
        pass
    return res

def checkVariableInNC(ncFile,varName):
    logger.debug('Check whether the variable: '+str(varName)+' is defined in the file: '+str(ncFile))    
    if ncFile in filecache.keys():
        f = filecache[ncFile]
    else:
        try:
            f = nc.Dataset(ncFile)
        except:
            ModelFileError(ncFile)
        filecache[ncFile] = f

    varName = str(varName)    
    return varName in f.variables.keys()

def get_dimension_variable(ncFile,dimName):    
    if not checkVariableInNC(ncFile, dimName):            
        dimvar = None
    else:
        if ncFile in filecache.keys():
            f = filecache[ncFile]
        else:
            try:
                f = nc.Dataset(ncFile)
            except:
                ModelFileError(ncFile)
            filecache[ncFile] = f
    
        dimName = str(dimName)
        dimvar = f.variables[dimName][:]    
    return dimvar

# def get_time_index(ncFile, date, useDoy):

#     # Get netCDF file and variable name:
#     if ncFile in filecache.keys():
#         f = filecache[ncFile]
#     else:
#         try:
#             f = nc.Dataset(ncFile)
#         except:
#             ModelFileError(ncFile)
#         filecache[ncFile] = f
        
#     if useDoy == "Yes": 
#         logger.debug('Finding the date based on the given climatology doy index (1 to 366, or index 0 to 365)')
#         idx = int(dateInput) - 1
#     elif useDoy == "month":  
#         logger.debug('Finding the date based on the given climatology month index (1 to 12, or index 0 to 11)')
#         # make sure that date is in the correct format
#         if isinstance(date, str) == True: date = \
#                         datetime.datetime.strptime(str(date),'%Y-%m-%d') 
#         idx = int(date.month) - 1
#     else:
#         # make sure that date is in the correct format
#         if isinstance(date, str) == True:
#             date = datetime.datetime.strptime(str(date),'%Y-%m-%d')
            
#         date = datetime.datetime(date.year,date.month,date.day)

#         if useDoy == "yearly":
#             date  = datetime.datetime(date.year,int(1),int(1))

#         if useDoy == "monthly":
#             date = datetime.datetime(date.year,date.month,int(1))

#         if useDoy == "yearly" or useDoy == "monthly" or useDoy == "daily_seasonal":
#             # if the desired year is not available, use the first year or the last year that is available
#             first_year_in_nc_file = findFirstYearInNCTime(f.variables['time'])
#             last_year_in_nc_file  =  findLastYearInNCTime(f.variables['time'])
            
#             if date.year < first_year_in_nc_file:  
#                 if date.day == 29 and date.month == 2 and calendar.isleap(date.year) and calendar.isleap(first_year_in_nc_file) == False:
#                     date = datetime.datetime(first_year_in_nc_file, date.month, 28)
#                 else:
#                     date = datetime.datetime(first_year_in_nc_file, date.month, date.day)
#                 msg  = "\n"
#                 msg += "WARNING related to the netcdf file: "+str(ncFile)+" ; variable: "+str(varName)+" !!!!!!"+"\n"
#                 msg += "The date "+str(dateInput)+" is NOT available. "
#                 msg += "The date "+str(date.year)+"-"+str(date.month)+"-"+str(date.day)+" is used."
#                 msg += "\n"
#                 logger.warning(msg)
                
#             if date.year > last_year_in_nc_file:  
#                 if date.day == 29 and date.month == 2 and calendar.isleap(date.year) and calendar.isleap(last_year_in_nc_file) == False:
#                     date = datetime.datetime(last_year_in_nc_file, date.month, 28)
#                 else:
#                     date = datetime.datetime(last_year_in_nc_file, date.month, date.day)
#                 msg  = "\n"
#                 msg += "WARNING related to the netcdf file: "+str(ncFile)+" ; variable: "+str(varName)+" !!!!!!"+"\n"
#                 msg += "The date "+str(dateInput)+" is NOT available. "
#                 msg += "The date "+str(date.year)+"-"+str(date.month)+"-"+str(date.day)+" is used."
#                 msg += "\n"
#                 logger.warning(msg)
#         try:
#             idx = nc.date2index(date, f.variables['time'], calendar = f.variables['time'].calendar, select ='exact')
#             msg = "The date "+str(date.year)+"-"+str(date.month)+"-"+str(date.day)+" is available. The 'exact' option is used while selecting netcdf time."
#             logger.debug(msg)
#         except:
#             msg = "The date "+str(date.year)+"-"+str(date.month)+"-"+str(date.day)+" is NOT available. The 'exact' option CANNOT be used while selecting netcdf time."
#             logger.debug(msg)
#             try:                                  
#                 idx = nc.date2index(date, f.variables['time'], calendar = f.variables['time'].calendar, select = 'before')
#                 msg  = "\n"
#                 msg += "WARNING related to the netcdf file: "+str(ncFile)+" ; variable: "+str(varName)+" !!!!!!"+"\n"
#                 msg += "The date "+str(date.year)+"-"+str(date.month)+"-"+str(date.day)+" is NOT available. The 'before' option is used while selecting netcdf time."
#                 msg += "\n"
#             except:
#                 idx = nc.date2index(date, f.variables['time'], calendar = f.variables['time'].calendar, \
#                                     select = 'after')
#                 msg  = "\n"
#                 msg += "WARNING related to the netcdf file: "+str(ncFile)+" ; variable: "+str(varName)+" !!!!!!"+"\n"
#                 msg += "The date "+str(date.year)+"-"+str(date.month)+"-"+str(date.day)+" is NOT available. The 'after' option is used while selecting netcdf time."
#                 msg += "\n"
#             logger.warning(msg)

#     idx = int(idx)                                                  
#     logger.debug('Using the date index '+str(idx))
#     return(idx)

# def netcdfDim2NumPy(ncFile, dimName, absolutePath = None):
#     if absolutePath != None: ncFile = getFullPath(ncFile, absolutePath)
#     if ncFile in filecache.keys():
#         f = filecache[ncFile]
#     else:
#         try:
#             f = nc.Dataset(ncFile)
#         except:
#             ModelFileError(ncFile)
#         filecache[ncFile] = f
        
#     dimName = str(dimName)
#     var = f.variables[dimName][:]
#     return var
    
# def netcdf2PCRobjCloneWithoutTime(ncFile, varName,
#                                   cloneMapFileName  = None,\
#                                   LatitudeLongitude = True,\
#                                   specificFillValue = None,\
#                                   absolutePath = None):
    
#     if absolutePath != None: ncFile = getFullPath(ncFile, absolutePath)    
#     logger.debug('reading variable: '+str(varName)+' from the file: '+str(ncFile))
    
#     # EHS (19 APR 2013): To convert netCDF (tss) file to PCR file.
#     # --- with clone checking
#     #     Only works if cells are 'square'.
#     #     Only works if cellsizeClone <= cellsizeInput
#     # Get netCDF file and variable name:
#     if ncFile in filecache.keys():
#         f = filecache[ncFile]
#     else:
#         try:
#             f = nc.Dataset(ncFile)
#         except:
#             raise ModelFileError(ncFile)
#         filecache[ncFile] = f
    
#     varName = str(varName)    
#     if LatitudeLongitude == True:
#         try:
#             f.variables['lat'] = f.variables['latitude']
#             f.variables['lon'] = f.variables['longitude']
#         except:
#             pass
    
#     sameClone = True
#     # check whether clone and input maps have the same attributes:
#     if cloneMapFileName != None:
#         # get the attributes of cloneMap
#         attributeClone = getMapAttributesALL(cloneMapFileName)
#         cellsizeClone = attributeClone['cellsize']
#         rowsClone = attributeClone['rows']
#         colsClone = attributeClone['cols']
#         xULClone = attributeClone['xUL']
#         yULClone = attributeClone['yUL']
#         # get the attributes of input (netCDF) 
#         cellsizeInput = f.variables['lat'][0]- f.variables['lat'][1]
#         cellsizeInput = float(cellsizeInput)
#         rowsInput = len(f.variables['lat'])
#         colsInput = len(f.variables['lon'])
#         xULInput = f.variables['lon'][0]-0.5*cellsizeInput
#         yULInput = f.variables['lat'][0]+0.5*cellsizeInput
#         # check whether both maps have the same attributes 
#         if cellsizeClone != cellsizeInput: sameClone = False
#         if rowsClone != rowsInput: sameClone = False
#         if colsClone != colsInput: sameClone = False
#         if xULClone != xULInput: sameClone = False
#         if yULClone != yULInput: sameClone = False

#     cropData = f.variables[varName][:,:]       # still original data    
#     factor = 1                                 # needed in regridData2FinerGrid
#     if sameClone == False:
#         # crop to cloneMap:
#         minX    = min(abs(f.variables['lon'][:] - (xULClone + 0.5*cellsizeInput)))
#         xIdxSta = int(np.where(abs(f.variables['lon'][:] - (xULClone + 0.5*cellsizeInput)) == minX)[0])
#         xIdxEnd = int(math.ceil(xIdxSta + colsClone /(cellsizeInput/cellsizeClone)))
#         minY    = min(abs(f.variables['lat'][:] - (yULClone - 0.5*cellsizeInput)))
#         yIdxSta = int(np.where(abs(f.variables['lat'][:] - (yULClone - 0.5*cellsizeInput)) == minY)[0])
#         yIdxEnd = int(math.ceil(yIdxSta + rowsClone /(cellsizeInput/cellsizeClone)))
#         if len(cropData.shape) > 2:
#             cropData = f.variables[varName][...,yIdxSta:yIdxEnd,xIdxSta:xIdxEnd]
#         else:
#             cropData = f.variables[varName][yIdxSta:yIdxEnd,xIdxSta:xIdxEnd]
#         factor = int(round(float(cellsizeInput)/float(cellsizeClone)))
#         if factor > 1: logger.debug('Resample: input cell size = '+str(float(cellsizeInput))+' ; output/clone cell size = '+str(float(cellsizeClone)))

#     # numpy array
#     outnp = regridData2FinerGrid(factor,cropData,MV)
#     f = None
#     cropData = None 
#     return (outnp)

def read_netCDF(ncFile):
    if ncFile in filecache.keys():
        f = filecache[ncFile]
    else:
        f = nc.Dataset(ncFile)
        filecache[ncFile] = f
    return f

def rename_latlong_dims(f, LatitudeLongitude):
    if LatitudeLongitude == True:
        try:
            f.variables['lat'] = f.variables['latitude']
            f.variables['lon'] = f.variables['longitude']
        except:
            pass
    return f

def get_time_dimension_name(f):
    dimnames = f.dimensions.keys()
    time_dimension_name = None
    if 'time' in dimnames:
        time_dimension_name = 'time'
    elif 'tstep' in dimnames:
        time_dimension_name = 'tstep'
    else:
        pass
    
    return time_dimension_name
        
def get_time_variable_name(f):
    time_variable_name = None
    if 'time' in f.variables:
        time_variable_name = 'time'
    elif 'timestp' in f.variables:
        time_variable_name = 'timestp'
    else:
        pass    
    return time_variable_name

# def rename_time_dims(f):
#     if 'timestp' in f.variables and 'time' not in f.variables:
#         try:
#             f.variables['time'] = f.variables['timestp']
#         except:
#             pass
#     return f

def get_time_units(nctime):
    return repair_time_string(nctime.units)

def get_time_calendar(nctime):
    try:
        calendar = nctime.calendar
    except:
        calendar = 'standard'
    return calendar

# def format_date(date):
#     if isinstance(date, str) == True:
#         date = datetime.datetime.strptime(str(date),'%Y-%m-%d')
#     return date

# def compare_clone(input_latitudes, input_longitudes, clone_attributes):
#     sameClone = True
#     cellsizeClone = clone_attributes['cellsize']
#     rowsClone = clone_attributes['rows']
#     colsClone = clone_attributes['cols']
#     xULClone = clone_attributes['xUL']
#     yULClone = clone_attributes['yUL']

#     # get the attributes of input (netCDF)
#     cellsizeInput = float(abs(input_latitudes[0] - input_latitudes[1]))
#     rowsInput = len(input_latitudes)
#     colsInput = len(input_longitudes)
#     xULInput = np.min(input_longitudes) - 0.5 * cellsizeInput
#     yULInput = np.max(input_latitudes) + 0.5 * cellsizeInput

#     # check whether both maps have the same attributes 
#     # NB: the original code (PCRGLOBWB) used the following line to test
#     # equality between cellsize:
#     #     if cellsizeClone != cellsizeInput: sameClone = False
#     # but this is not sensible when dealing with decimal degrees
#     # (e.g. 5 arcminute -> 0.08333333) and netCDF files which may have
#     # varying levels of precision depending on the creation options of the
#     # user. Instead, test almost equality:
#     if abs(cellsizeClone - cellsizeInput) > 1e-8: sameClone = False
#     if rowsClone != rowsInput: sameClone = False
#     if colsClone != colsInput: sameClone = False
#     if xULClone != xULInput: sameClone = False
#     if yULClone != yULInput: sameClone = False
#     return sameClone
    
# TODO: refactor
def resample_nc_data(f, varName, cloneMapFileName, timeDimName = None, timeIndex = None):

    # TODO: https://stackoverflow.com/a/35507245 (xarray and dask)
    
    # compare spatial attributes of input map with those of clone map

    var_dims = f.variables[varName].dimensions
    slc = [slice(None)] * len(var_dims)
    if (timeIndex is not None) and (timeDimName is not None):
        time_axis = [i for i in range(len(var_dims)) if var_dims[i] == timeDimName][0]
        slc[time_axis] = timeIndex
    cropData = f.variables[varName][slc]
    
    input_latitudes = f.variables['lat'][:]
    input_longitudes = f.variables['lon'][:]
    sameClone = True
    if cloneMapFileName != None:
        attributeClone = getMapAttributesALL(cloneMapFileName)
        cellsizeClone = attributeClone['cellsize']
        rowsClone = attributeClone['rows']
        colsClone = attributeClone['cols']
        xULClone = attributeClone['xUL']
        yULClone = attributeClone['yUL']
        
        # get the attributes of input (netCDF)
        cellsizeInput = float(abs(input_latitudes[0] - input_latitudes[1]))
        rowsInput = len(input_latitudes)
        colsInput = len(input_longitudes)
        xULInput = np.min(input_longitudes) - 0.5 * cellsizeInput
        yULInput = np.max(input_latitudes) + 0.5 * cellsizeInput
        
        # check whether both maps have the same attributes 
        # NB: the original code (PCRGLOBWB) used the following line to test
        # equality between cellsize:
        #     if cellsizeClone != cellsizeInput: sameClone = False
        # but this is not sensible when dealing with decimal degrees
        # (e.g. 5 arcminute -> 0.08333333) and netCDF files which may have
        # varying levels of precision depending on the creation options of the
        # user. Instead, test almost equality:
        if abs(cellsizeClone - cellsizeInput) > 1e-8: sameClone = False
        if rowsClone != rowsInput: sameClone = False
        if colsClone != colsInput: sameClone = False
        if xULClone != xULInput: sameClone = False
        if yULClone != yULInput: sameClone = False

    netcdf_y_orientation_follow_cf_convention = (input_latitudes[0] - input_latitudes[1]) > 0
    if not netcdf_y_orientation_follow_cf_convention:
        cropData = np.flip(cropData, axis=-2)
        input_latitudes = input_latitudes[::-1]
        
    factor = 1
    if sameClone == False:
        logger.debug('Crop to the clone map with upper left corner (x,y): '+ str(xULClone) + ' , ' + str(yULClone))
        minX    = min(abs(input_longitudes[:] - (xULClone + 0.5 * cellsizeInput)))

        # longitudes are ascending (i.e. W -> E), hence we *add* half
        # the input cellsize to the clone map western boundary
        xIdxSta = int(np.where(abs(input_longitudes[:] - (xULClone + 0.5 * cellsizeInput)) == minX)[0])
        xIdxEnd = int(math.ceil(xIdxSta + colsClone / (cellsizeInput / cellsizeClone)))        
        xStep   = (xIdxEnd - xIdxSta) / abs(xIdxEnd - xIdxSta)

        # latitudes are descending (i.e. N -> S), hence we *subtract*
        # half the input cellsize from the clone map northern boundary
        minY    = min(abs(input_latitudes - (yULClone - 0.5 * cellsizeInput)))
        yIdxSta = int(np.where(abs(input_latitudes - (yULClone - 0.5 * cellsizeInput)) == minY)[0])
        yIdxEnd = int(math.ceil(yIdxSta + rowsClone / (cellsizeInput / cellsizeClone)))
        yStep   = (yIdxEnd - yIdxSta) / abs(yIdxEnd - yIdxSta)

        xSlice = slice(xIdxSta, xIdxEnd, xStep)
        ySlice = slice(yIdxSta, yIdxEnd, yStep)
        cropData = cropData[...,ySlice, xSlice]
        factor = int(round(float(cellsizeInput) / float(cellsizeClone)))
        
    if factor > 1:
        logger.debug('Resample: input cell size = '
                     + str(float(cellsizeInput))
                     + ' ; output/clone cell size = '
                     + str(float(cellsizeClone)))
    arr = regridData2FinerGrid(factor,cropData,MV)
    return arr

def netcdf2NumpyDailyTimeSlice(ncFile, varName, startDate, #endDate,
                               useDoy = None,
                               cloneMapFileName = None,
                               LatitudeLongitude = True,
                               specificFillValue = None):

    logger.debug('reading variable: ' + str(varName) + ' from the file: ' + str(ncFile))
    f = read_netCDF(ncFile)
    varName = str(varName)
    f = rename_latlong_dims(f, LatitudeLongitude)
    t_varname = get_time_variable_name(f)
    t_dimname = get_time_dimension_name(f)
    t_unit = get_time_units(f.variables[t_varname])
    t_calendar = get_time_calendar(f.variables[t_varname])
    startDate = format_date(startDate, f.variables[t_varname], useDoy)
    endDate = startDate + datetime.timedelta(days=1)
    lastDateInNC = nc.num2date(f.variables[t_varname][-1], units=t_unit, calendar=t_calendar)
    startIndex = nc.date2index(datetime.datetime(startDate.year, startDate.month, startDate.day, 0, 0, 0), f.variables[t_varname])
    if endDate <= lastDateInNC:
        endIndex = nc.date2index(datetime.datetime(endDate.year, endDate.month, endDate.day, 0, 0, 0), f.variables[t_varname])
        # print endIndex
    else:
        endIndex = f.variables[t_varname].size        
    timeIndex = np.arange(startIndex, endIndex)
    # print timeIndex
    arr = resample_nc_data(f, varName, cloneMapFileName, t_dimname, timeIndex)
    f = None
    return arr

def get_message_for_using_nearest_year(ncFile, varName, oldDate, newDate):
    msg  = "\n"
    msg += "WARNING related to the netcdf file: "+str(ncFile)+" ; variable: "+str(varName)+" !"+"\n"
    msg += "The date "+str(oldDate)+" is NOT available. "
    msg += "The date "+str(newDate.year)+"-"+str(newDate.month)+"-"+str(newDate.day)+" is used."
    msg += "\n"
    return msg

def get_nearest_date_to_year(year, date):
    # if the desired year is not available, use the first or last year that is available
    if date.day == 29 and date.month == 2 and calendar.isleap(date.year) and not calendar.isleap(year):
        date = datetime.datetime(year, date.month, 28)
    else:
        date = datetime.datetime(year, date.month, date.day)
    return date

def format_date(date, nctime, useDoy):
    if isinstance(date, str):
        date = datetime.datetime.strptime(str(date),'%Y-%m-%d')        
    date = datetime.datetime(date.year,date.month,date.day)  # currently only support daily
    if useDoy == "yearly":
        date  = datetime.datetime(date.year,int(1),int(1))
    if useDoy == "monthly":
        date = datetime.datetime(date.year,date.month,int(1))
    if useDoy == "yearly" or useDoy == "monthly" or useDoy == "daily_seasonal":
        first_year_in_nc_file = findFirstYearInNCTime(nctime)
        last_year_in_nc_file  =  findLastYearInNCTime(nctime)
        if date.year < first_year_in_nc_file:
            date = get_nearest_date_to_year(first_year_in_nc_file, date)
            msg = get_message_for_using_nearest_year(ncFile, varName, dateInput, date)
            logger.warning(msg)

        if date.year > last_year_in_nc_file:
            date = get_nearest_date_to_year(last_year_in_nc_file, date)
            msg = get_message_for_using_nearest_year(ncFile, varName, dateInput, date)
            logger.warning(msg)            

    return date

def get_date_index_exact(ncFile, date, t_varname, t_unit, t_calendar):
    datenum = nc.date2num(date, t_unit, t_calendar)
    timevar = ncFile[t_varname][:]
    idx = int(np.nonzero(timevar == datenum)[0][0])
    return idx

def get_date_index_before(ncFile, date, t_varname, t_unit, t_calendar):
    datenum = nc.date2num(date, t_unit, t_calendar)
    timevar = ncFile[t_varname][:]
    times_before_current_time = np.nonzero(timevar < datenum)
    idx = int(np.max(times_before_current_time))
    return idx

def get_date_index_after(ncFile, date, t_varname, t_unit, t_calendar):
    datenum = nc.date2num(date, t_unit, t_calendar)
    timevar = ncFile[t_varname][:]
    times_after_current_time = np.nonzero(timevar > datenum)
    idx = int(np.max(times_after_current_time))
    return idx
        
def get_date_availability_message(date, available=True):
    if available:
        msg = ("The date %s-%s-%s is available. The 'exact' option is \n"
               "used while selecting netCDF time."
               % (str(date.year), str(date.month), str(date.day)))
    else:
        msg = ("The date %s-%s-%s is NOT available. The 'exact' option \n"
               "CANNOT be used while selecting netCDF time."
               % (str(date.year), str(date.month), str(date.day)))
    return msg

def get_message_for_using_date_before_or_after(ncFile, varName, date, using_before=True):
    msg  = "\n"
    msg += "WARNING related to the netcdf file: "+str(ncFile)+" ; variable: "+str(varName)+" !"+"\n"
    if using_before:
        option = 'before'
    else:
        option = 'after'
    msg += "The date "+str(date.year)+"-"+str(date.month)+"-"+str(date.day)+" is NOT available. The '"+option+"' option is used while selecting netcdf time."
    msg += "\n"
    return msg
    
def get_time_index(ncFile, varName, date, t_varname, t_unit, t_calendar):    
    try:
        idx = get_date_index_exact(ncFile, date, t_varname, t_unit, t_calendar)
        msg = get_date_availability_message(date, available=True)
        logger.debug(msg)
    except:
        msg = get_date_availability_message(date, available=False)
        logger.debug(msg)
        try:
            idx = get_date_index_before(ncFile, date, t_varname, t_unit, t_calendar)
            msg = get_message_for_using_date_before_or_after(ncFile, varName, date, using_before=True)
        except:
            idx = get_date_index_after(ncFile, date, t_varname, t_unit, t_calendar)
            msg = get_message_for_using_date_before_or_after(ncFile, varName, date, using_before=False)
        logger.debug(msg)
    return idx
    
def netcdf2PCRobjClone(ncFile,varName,dateInput,
                       useDoy = None,
                       cloneMapFileName  = None,
                       cloneMapAttributes = None,
                       LatitudeLongitude = True,
                       specificFillValue = None):
    
    logger.debug('Reading variable: ' + str(varName) + ' from the file: ' + str(ncFile))
    f = read_netCDF(ncFile)
    varName = str(varName)
    f = rename_latlong_dims(f, LatitudeLongitude)
    t_varname = get_time_variable_name(f)
    t_dimname = get_time_dimension_name(f)
    date = format_date(dateInput, f.variables[t_varname], useDoy)
    t_unit = get_time_units(f.variables[t_varname])
    t_calendar = get_time_calendar(f.variables[t_varname])
    timeIndex = get_time_index(f, varName, date, t_varname, t_unit, t_calendar)
    logger.debug('Using date index ' + str(timeIndex))
    arr = resample_nc_data(f, varName, cloneMapFileName, t_dimname, timeIndex)
    f = None
    return arr

def netcdf2PCRobjCloneWithoutTime(
        ncFile, varName,
        cloneMapFileName  = None,
        LatitudeLongitude = True,
        specificFillValue = None,
        absolutePath = None):        
    
    logger.debug('Reading variable: ' + str(varName) + ' from the file: ' + str(ncFile))
    f = read_netCDF(ncFile)
    varName = str(varName)
    f = rename_latlong_dims(f, LatitudeLongitude)
    arr = resample_nc_data(f, varName, cloneMapFileName)
    f = None
    return arr

def netcdf2NumPyTimeSlice(ncFile,varName,startDate,endDate,
                          useDoy = None,
                          cloneMapFileName = None,
                          LatitudeLongitude = True,
                          specificFillValue = None):

    logger.debug('reading variable: ' + str(varName) + ' from the file: ' + str(ncFile))
    f = read_netCDF(ncFile)
    varName = str(varName)
    f = rename_latlong_dims(f, LatitudeLongitude)
    t_varname = get_time_variable_name(f)
    t_dimname = get_time_dimension_name(f)
    t_unit = get_time_units(f.variables[t_varname])
    t_calendar = get_time_calendar(f.variables[t_varname])
    startDate = format_date(startDate, f.variables[t_varname], useDoy)
    endDate = format_date(endDate, f.variables[t_varname], useDoy)
    lastDateInNC = nc.num2date(f.variables[t_varname][-1], units=t_unit, calendar=t_calendar)
    startIndex = nc.date2index(datetime.datetime(startDate.year, startDate.month, startDate.day, 0, 0, 0), f.variables[t_varname])
    if endDate <= lastDateInNC:
        endIndex = nc.date2index(datetime.datetime(endDate.year, endDate.month, endDate.day, 0, 0, 0), f.variables[t_varname])
        # print endIndex
    else:
        endIndex = f.variables[t_varname].size    
    timeIndex = np.arange(startIndex, endIndex + 1)
    arr = resample_nc_data(f, varName, cloneMapFileName, t_dimname, timeIndex)
    f = None
    return arr
    
    # if ncFile in filecache.keys():
    #     f = filecache[ncFile]
    # else:
    #     f = nc.Dataset(ncFile)
    #     filecache[ncFile] = f
    # varName = str(varName)

    # if LatitudeLongitude == True:
    #     try:
    #         f.variables['lat'] = f.variables['latitude']
    #         f.variables['lon'] = f.variables['longitude']
    #     except:
    #         pass

    # if varName == "evapotranspiration":        
    #     try:
    #         f.variables['evapotranspiration'] = f.variables['referencePotET']
    #     except:
    #         pass

    # # date index
    # # NB ncFile should be cached, so don't need to open it again (filecache is a global variable)
    # startidx = get_time_index(ncFile, startDate, useDoy)
    # endidx   = get_time_index(ncFile, endDate, useDoy)
    # idx = np.arange(startidx, endidx + 1)

    # # compare spatial attributes with clone map
    # sameClone = True
    # # check whether clone and input maps have the same attributes:
    # if cloneMapFileName != None:
    #     # get the attributes of cloneMap
    #     attributeClone = getMapAttributesALL(cloneMapFileName)
    #     cellsizeClone = attributeClone['cellsize']
    #     rowsClone = attributeClone['rows']
    #     colsClone = attributeClone['cols']
    #     xULClone = attributeClone['xUL']
    #     yULClone = attributeClone['yUL']
    #     # get the attributes of input (netCDF) 
    #     cellsizeInput = f.variables['lat'][0]- f.variables['lat'][1]
    #     cellsizeInput = float(cellsizeInput)
    #     rowsInput = len(f.variables['lat'])
    #     colsInput = len(f.variables['lon'])
    #     xULInput = f.variables['lon'][0]-0.5*cellsizeInput
    #     yULInput = f.variables['lat'][0]+0.5*cellsizeInput
    #     # check whether both maps have the same attributes 
    #     if cellsizeClone != cellsizeInput: sameClone = False
    #     if rowsClone != rowsInput: sameClone = False
    #     if colsClone != colsInput: sameClone = False
    #     if xULClone != xULInput: sameClone = False
    #     if yULClone != yULInput: sameClone = False

    # cropData = f.variables[varName][idx,:,:] # still original data
    # factor = 1                               # needed in regridData2FinerGrid

    # if sameClone == False:

    #     logger.debug('Crop to the clone map with lower left corner (x,y): '+str(xULClone)+' , '+str(yULClone))

    #     # crop to cloneMap:
    #     #~ xIdxSta = int(np.where(f.variables['lon'][:] == xULClone + 0.5*cellsizeInput)[0])
    #     minX    = min(abs(f.variables['lon'][:] - (xULClone + 0.5*cellsizeInput))) # ; print(minX)
    #     xIdxSta = int(np.where(abs(f.variables['lon'][:] - (xULClone + 0.5*cellsizeInput)) == minX)[0])
    #     xIdxEnd = int(math.ceil(xIdxSta + colsClone /(cellsizeInput/cellsizeClone)))
    #     #~ yIdxSta = int(np.where(f.variables['lat'][:] == yULClone - 0.5*cellsizeInput)[0])
    #     minY    = min(abs(f.variables['lat'][:] - (yULClone - 0.5*cellsizeInput))) # ; print(minY)
    #     yIdxSta = int(np.where(abs(f.variables['lat'][:] - (yULClone - 0.5*cellsizeInput)) == minY)[0])
    #     yIdxEnd = int(math.ceil(yIdxSta + rowsClone /(cellsizeInput/cellsizeClone)))
    #     cropData = f.variables[varName][idx,yIdxSta:yIdxEnd,xIdxSta:xIdxEnd]
    #     factor = int(round(float(cellsizeInput)/float(cellsizeClone)))
    #     if factor > 1: logger.debug('Resample: input cell size = '+str(float(cellsizeInput))+' ; output/clone cell size = '+str(float(cellsizeClone)))

    # # numpy array
    # outnp = regridData2FinerGrid(factor,cropData,MV)
    
    # f = None
    # cropData = None 
    # return (outnp)

def readPCRmapClone(v,cloneMapFileName,tmpDir,absolutePath=None,isLddMap=False,cover=None,isNomMap=False):
	# v: inputMapFileName or floating values
	# cloneMapFileName: If the inputMap and cloneMap have different clones,
	#                   resampling will be done.   
    logger.debug('read file/values: '+str(v))
    if v == "None":
        #~ PCRmap = str("None")
        PCRmap = None                                                   # 29 July: I made an experiment by changing the type of this object. 
    elif not re.match(r"[0-9.-]*$",v):
        if absolutePath != None: v = getFullPath(v,absolutePath)
        # print v
        # print cloneMapFileName
        sameClone = isSameClone(v,cloneMapFileName)
        if sameClone == True:
            PCRmap = pcr.readmap(v)
        else:
            # resample using GDAL:
            output = tmpDir+'temp.map'
            warp = gdalwarpPCR(v,output,cloneMapFileName,tmpDir,isLddMap,isNomMap)
            # read from temporary file and delete the temporary file:
            PCRmap = pcr.readmap(output)
            if isLddMap == True: PCRmap = pcr.ifthen(pcr.scalar(PCRmap) < 10., PCRmap)
            if isLddMap == True: PCRmap = pcr.ldd(PCRmap)
            if isNomMap == True: PCRmap = pcr.ifthen(pcr.scalar(PCRmap) >  0., PCRmap)
            if isNomMap == True: PCRmap = pcr.nominal(PCRmap)
            if os.path.isdir(tmpDir):
                shutil.rmtree(tmpDir)
            os.makedirs(tmpDir)
    else:
        PCRmap = pcr.spatial(pcr.scalar(float(v)))
    if cover != None:
        PCRmap = pcr.cover(PCRmap, cover)
    co = None; cOut = None; err = None; warp = None
    del co; del cOut; del err; del warp
    stdout = None; del stdout
    stderr = None; del stderr

    # SM: revisit this
    PCRmap = pcr.pcr2numpy(PCRmap, np.nan)
    
    return PCRmap    

# def readPCRmap(v):
# 	# v : fileName or floating values
#     if not re.match(r"[0-9.-]*$", v):
#         PCRmap = pcr.readmap(v)
#     else:
#         PCRmap = pcr.scalar(float(v))
#     return PCRmap    

def isSameClone(inputMapFileName,cloneMapFileName):    
    # reading inputMap:
    attributeInput = getMapAttributesALL(inputMapFileName)
    cellsizeInput = attributeInput['cellsize']
    rowsInput = attributeInput['rows']
    colsInput = attributeInput['cols']
    xULInput = attributeInput['xUL']
    yULInput = attributeInput['yUL']
    # reading cloneMap:
    attributeClone = getMapAttributesALL(cloneMapFileName)
    cellsizeClone = attributeClone['cellsize']
    rowsClone = attributeClone['rows']
    colsClone = attributeClone['cols']
    xULClone = attributeClone['xUL']
    yULClone = attributeClone['yUL']
    # check whether both maps have the same attributes? 
    sameClone = True
    if cellsizeClone != cellsizeInput: sameClone = False
    if rowsClone != rowsInput: sameClone = False
    if colsClone != colsInput: sameClone = False
    if xULClone != xULInput: sameClone = False
    if yULClone != yULInput: sameClone = False
    return sameClone

# def gdalwarpPCR(input,output,cloneOut,tmpDir,isLddMap=False,isNominalMap=False):
#     # 19 Mar 2013 created by Edwin H. Sutanudjaja
#     # all input maps must be in PCRaster maps
#     # 
#     # remove temporary files:
#     co = 'rm '+str(tmpDir)+'*.*'
#     cOut,err = subprocess.Popen(co, stdout=subprocess.PIPE,stderr=open(os.devnull),shell=True).communicate()
#     # 
#     # converting files to tif:
#     co = 'gdal_translate -ot Float64 '+str(input)+' '+str(tmpDir)+'tmp_inp.tif'
#     if isLddMap == True: co = 'gdal_translate -ot Int32 '+str(input)+' '+str(tmpDir)+'tmp_inp.tif'
#     if isNominalMap == True: co = 'gdal_translate -ot Int32 '+str(input)+' '+str(tmpDir)+'tmp_inp.tif'
#     cOut,err = subprocess.Popen(co, stdout=subprocess.PIPE,stderr=open(os.devnull),shell=True).communicate()
#     # 
#     # get the attributes of PCRaster map:
#     cloneAtt = getMapAttributesALL(cloneOut)
#     xmin = cloneAtt['xUL']
#     ymin = cloneAtt['yUL'] - cloneAtt['rows']*cloneAtt['cellsize']
#     xmax = cloneAtt['xUL'] + cloneAtt['cols']*cloneAtt['cellsize']
#     ymax = cloneAtt['yUL'] 
#     xres = cloneAtt['cellsize']
#     yres = cloneAtt['cellsize']
#     te = '-te '+str(xmin)+' '+str(ymin)+' '+str(xmax)+' '+str(ymax)+' '
#     tr = '-tr '+str(xres)+' '+str(yres)+' '
#     co = 'gdalwarp '+te+tr+ \
#          ' -srcnodata -3.4028234663852886e+38 -dstnodata mv '+ \
#            str(tmpDir)+'tmp_inp.tif '+ \
#            str(tmpDir)+'tmp_out.tif'
#     cOut,err = subprocess.Popen(co, stdout=subprocess.PIPE,stderr=open(os.devnull),shell=True).communicate()
#     # 
#     co = 'gdal_translate -of PCRaster '+ \
#               str(tmpDir)+'tmp_out.tif '+str(output)
#     cOut,err = subprocess.Popen(co, stdout=subprocess.PIPE,stderr=open(os.devnull),shell=True).communicate()
#     # 
#     co = 'mapattr -c '+str(cloneOut)+' '+str(output)
#     cOut,err = subprocess.Popen(co, stdout=subprocess.PIPE,stderr=open(os.devnull),shell=True).communicate()
#     # 
#     #~ co = 'aguila '+str(output)
#     #~ print(co)
#     #~ cOut,err = subprocess.Popen(co, stdout=subprocess.PIPE,stderr=open(os.devnull),shell=True).communicate()
#     # 
#     co = 'rm '+str(tmpDir)+'tmp*.*'
#     cOut,err = subprocess.Popen(co, stdout=subprocess.PIPE,stderr=open(os.devnull),shell=True).communicate()
#     co = None; cOut = None; err = None
#     del co; del cOut; del err
#     stdout = None; del stdout
#     stderr = None; del stderr
#     n = gc.collect() ; del gc.garbage[:] ; n = None ; del n

def getFullPath(inputPath,absolutePath,completeFileName = True):
    # 19 Mar 2013 created by Edwin H. Sutanudjaja
    # Function: to get the full absolute path of a folder or a file
          
    # replace all \ with /
    inputPath = str(inputPath).replace("\\", "/")
    absolutePath = str(absolutePath).replace("\\", "/")
    
    # tuple of suffixes (extensions) that can be used:

    # old:
    # suffix = ('/','_','.nc4','.map','.nc','.dat','.txt','.asc','.ldd','.tbl',\
    #           '.001','.002','.003','.004','.005','.006',\
    #           '.007','.008','.009','.010','.011','.012')
    
    # new:
    suffix = ('/','_','.nc4','.map','.nc','.dat','.txt','.asc','.ldd','.tbl',\
              '.001','.002','.003','.004','.005','.006',\
              '.007','.008','.009','.010','.011','.012',
              '.tif')
    
    if inputPath.startswith('/') or str(inputPath)[1] == ":":
        fullPath = str(inputPath)
    else:
        if absolutePath.endswith('/'): 
            absolutePath = str(absolutePath)
        else:
			absolutePath = str(absolutePath)+'/'    
        fullPath = str(absolutePath)+str(inputPath)
    
    if completeFileName:
        if fullPath.endswith(suffix): 
            fullPath = str(fullPath)
    	else:
            fullPath = str(fullPath)+'/'    

    return fullPath    		

def getMapAttributesALL(cloneMap,arcDegree=True):
    cOut,err = subprocess.Popen(str('mapattr -p %s ' %(cloneMap)), stdout=subprocess.PIPE,stderr=open(os.devnull),shell=True).communicate()
    # print cOut

    if err !=None or cOut == []:
        print "Something wrong with mattattr in VirtualOS, maybe clone Map does not exist ? "
        sys.exit()

    cellsize = float(cOut.split()[7])
    if arcDegree == True: cellsize = round(cellsize * 360000.)/360000.
    mapAttr = {'cellsize': float(cellsize)        ,\
               'rows'    : float(cOut.split()[3]) ,\
               'cols'    : float(cOut.split()[5]) ,\
               'xUL'     : float(cOut.split()[17]),\
               'yUL'     : float(cOut.split()[19])}
    co = None; cOut = None; err = None
    del co; del cOut; del err
    n = gc.collect() ; del gc.garbage[:] ; n = None ; del n
    return mapAttr 

def getLastDayOfMonth(date):
    ''' returns the last day of the month for a given date '''

    if date.month == 12:
        return date.replace(day=31)
    return date.replace(month=date.month + 1, day=1) - datetime.timedelta(days=1)

def regridData2FinerGrid(rescaleFac, coarse, MV):
    # TODO: check with >3 dimensions (only checked with 2D
    # and 3D arrays so far)    
    if rescaleFac == 1:
        return coarse

    dim = np.shape(coarse)
    ndim = len(dim)
    nr,nc = dim[-2:]
    if ndim > 2:
        othdim = dim[0:(ndim-2)]
        othdimprod = reduce(operator.mul, othdim)
        fine = np.zeros(nr * nc * rescaleFac * rescaleFac * othdimprod).reshape(othdim + (nr * rescaleFac, nc * rescaleFac)) + MV
    else:
        fine = np.zeros(nr * nc * rescaleFac * rescaleFac).reshape(nr * rescaleFac, nc * rescaleFac) + MV

    dimF = np.shape(fine)
    nrF,ncF = dimF[-2:]
    ii = -1
    for i in range(0, nrF):
        if i % rescaleFac == 0:
            ii += 1

        # repeat along space axis, which (I think!!!) should
        # always be the last dimension of coarse[...,ii,:]
        # hence, ndim - 2 (-1 to comply with Python zero
        # indexing, -1 because we select a single row and hence
        # reduce the number of dimensions by 1)
        fine[...,i,:] = coarse[...,ii,:].repeat(rescaleFac, ndim - 2)

    return fine

def findLastYearInNCFile(ncFile):
    # open a netcdf file:
    if ncFile in filecache.keys():
        f = filecache[ncFile]
    else:
        f = nc.Dataset(ncFile)
        filecache[ncFile] = f

    # last datetime
    last_datetime_year = findLastYearInNCTime(f.variables['time']) 
    
    return last_datetime_year

def repair_time_string(timestr):    
    timestr = timestr.lower()
    timestr_split = timestr.split()
    units = timestr_split[0]
    successful = False
    if timestr_split[1] == 'since':
        successful = True
    elif 'since' in timestr_split:
        time_units = timestr.split('since')[0]
        allowable_units = ['second','minute','hour','day']
        occurrences = [unit in time_units for unit in allowable_units]
        number_of_occurrences = sum(1 for occurrence in occurrences if occurrence is True)
        if number_of_occurrences == 1:
            time_unit = [unit for (unit, index) in zip(allowable_units, occurrences) if index][0]
            timestr = time_unit + ' since' + timestr.split('since')[1]
            successful = True
        else:
            msg = 'ambiguous time units'
    else:
        msg = "time string does not contain 'since'"

    if not successful:
        raise ValueError,msg
    
    return timestr
            
def findLastYearInNCTime(ncTimeVariable):    
    last_datetime = nc.num2date(
        ncTimeVariable[len(ncTimeVariable) - 1],
        repair_time_string(ncTimeVariable.units),
        # ncTimeVariable.units,
        ncTimeVariable.calendar) 
    return last_datetime.year

def findFirstYearInNCTime(ncTimeVariable):
    first_datetime = nc.num2date(
        ncTimeVariable[0],
        repair_time_string(ncTimeVariable.units),
        ncTimeVariable.calendar)    
    return first_datetime.year

# def cmd_line(command_line,using_subprocess = True):

#     msg = "Call: "+str(command_line)
#     logger.debug(msg)
    
#     co = command_line
#     if using_subprocess:
#         cOut,err = subprocess.Popen(co, stdout=subprocess.PIPE,stderr=open('/dev/null'),shell=True).communicate()
#     else:
#         os.system(co)

# def plot_variable(pcr_variable, filename = "test.map"):

#     pcr.report(pcr_variable, filename)
#     cmd = 'aguila '+str(filename)
#     os.system(cmd)
