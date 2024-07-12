import arcpy, os, sys, requests, logging, errno, datetime, time, argparse, pathlib
from datetime import datetime

arcpy.SetProgressor('default','Initiating iterable selection by intersect tool')

arcpy.env.overwriteOutput = True

from utils import (
    paths, 
    createFolder, 
    log_message,
    dir_file, 
    log_setup,
    iter_row_set,
    spa_select_int)

target_feature = arcpy.GetParameterAsText(0)
selecting_feature = arcpy.GetParameterAsText(1)
field = arcpy.GetParameterAsText(2)
out_gdb = arcpy.GetParameterAsText(3)
append = arcpy.GetParameterAsText(4)

#Logging level specified in script configuration
directory, filename, gp_dir = dir_file(out_gdb)
log_setup(gp_dir,'Selection')

row_set = iter_row_set(selecting_feature,field)
spa_select_int(target_feature,selecting_feature,row_set,field,out_gdb,append)
