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

target_feature = r'C:\Users\USMC714671\WSP O365\Durham Hazard Mitigation - HMP GIS Tools\HMP_Tools\Templates\Template_Data\iRisk_tables.gdb\NC_RISK_DBO_S_BUILDING_FP'
selecting_feature = r'C:\Project_Files\GIS\Library\GIS_Data\NC\Geography\NC_County_Boundary_NAD83_NC_Stateplane.shp'
field = 'NAME'
out_gdb = r'C:\Users\USMC714671\OneDrive - WSP O365\OneDrive - Development Folders\Dev_Apps\HMP_Tools\HMP_Tools\work.gdb'
append = True

#Logging level specified in script configuration
directory, filename, gp_dir = dir_file(out_gdb)
log_setup(gp_dir,'Selection')

row_set = iter_row_set(selecting_feature,field)
spa_select_int(target_feature,selecting_feature,row_set,field,out_gdb,append)
