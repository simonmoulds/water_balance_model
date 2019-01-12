#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import xml.dom.minidom
# import datetime
# import time as xtime
import os
import sys

class ModelError(Exception):
    def __init__(self, msg):        
        sys.tracebacklimit = 0 # don't show the error code, lines etc.
        header = "\n\n =========================== MODEL ERROR =============================\n"
        try:
           self._msg = header + msg +"\n" +  sys.exc_info()[1].message
        except:
           self._msg = header + msg +"\n"
           
    def __str__(self):
        return self._msg

class ModelFileError(ModelError):
    def __init__(self, filename,msg="",sname = ""):        
        sys.tracebacklimit = 0 # don't show the error code, lines etc.
        path,name = os.path.split(filename)
        if os.path.exists(path):
            text1 = "In  \"" + sname + "\"\n"
            text1 += "path: "+ path + " exists\nbut filename: "+name+ " does not\n"
            text1 += "file name extension can be .nc4 or .nc\n"
        else:
            text1 = " In  \""+ sname +"\"\n"
            text1 += "searching: \""+filename+"\""
            text1 += "\npath: "+ path + " does not exists\n"

        header = "\n\n ========================= MODEL FILE ERROR ==========================\n"
        self._msg = header + msg + text1

class ModelWarning(Warning):    
    def __init__(self, msg):
        sys.tracebacklimit = 0 # don't show the error code, lines etc.
        header = "\n\n ========================== MODEL WARNING ============================\n"
        self._msg = header + msg
        sys.tracebacklimit = 1
    def __str__(self):
        return self._msg

# class ModelRunInfo(Warning):
#     """
#     prints out an error

#     Warning
#         warning given with a header and a message from the subroutine
#     """
#     def __init__(self, outputDir, Steps = 1, ensMembers=1, Cores=1):
#         header = "\nCWATM Simulation Information and Setting\n"
#         msg = "The simulation output as specified in the settings file: " + sys.argv[1] + " can be found in "+str(outputDir)+"\n"
#         self._msg = header + msg
#     def __str__(self):
#         return self._msg

