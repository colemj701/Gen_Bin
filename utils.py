import arcpy, os, sys, requests, logging, errno, datetime, time, argparse, pathlib
from datetime import datetime

##################-------------------------------------------------------------------------------------##################
                                                 # Project Setup Functions
##################-------------------------------------------------------------------------------------##################

env_settings_list = [
    "compression",
    "resamplingMethod",
    "nodata",
    "cellSize",
    "cellSizeProjectionMethod",
    "cellAlignment",
    "pyramid",
    "snapRaster"
]

def env(x):
    arcpy.env.workspace = x
    return arcpy.env.workspace

def paths(x,y):
    path = os.path.join(x,y)
    return path

def log_message(mes):
    arcpy.AddMessage(mes)
    logging.info(mes)

def createFolder(folderPath):
    if not os.path.exists(folderPath):
        try:
            os.makedirs(folderPath)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

#Logging level specified in script configuration
def dir_file(out_ras):
    directory, filename = os.path.split(out_ras)

    if directory.endswith('.gdb'):
        gp_dir = os.path.abspath(os.path.dirname(directory))
    else:
        gp_dir = directory

    return directory, filename, gp_dir

def list_shp(root_fld):
    shps = []
    for root, dirs, files in os.walk(root_fld):
        shps_add = [file for file in files if file.endswith('.shp')]
        shps.extend(shps_add)
        return shps
    
def log_setup(dir,Name):
    # Close and reinitialize logging handlers to release file handles
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    log_folder = paths(dir,'GeoProcess_Logs')
    createFolder(log_folder)
    log_file_name = Name+'_Logs_'+str(datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    log_file_path = paths(log_folder,log_file_name)
    log_set = logging.basicConfig(filename=log_file_path, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    return log_set

def gp_env(snap):
    arcpy.env.compression = 'LZW'
    arcpy.env.resamplingMethod = 'BILINEAR'
    arcpy.env.snapRaster = snap
    arcpy.env.nodata = 'NONE'
    arcpy.env.cellAlignment = 'DEFAULT'
    arcpy.env.cellSize = 'MAXOF'
    arcpy.env.pyramid = 'PYRAMIDS -1 BILINEAR DEFAULT 75 NO_SKIP'
    arcpy.env.cellSizeProjectionMethod = 'CONVERT_UNITS'

    return

##################-------------------------------------------------------------------------------------##################
                                             # Working with feature rows
##################-------------------------------------------------------------------------------------##################

def iter_row_set(in_feat, field):
    '''
    This function is used to iterate through a single field and return a set of the values existing in the table rows

    in_feat = the input feature
    field = the field to be iterated
    
    '''


    arcpy.SetProgressor('default', 'Initiating Iterate Row Set Module...')
    log_message('Building Row Value Set{0}'.format('  ::  ' + str(datetime.now().strftime("%Y-%m-%d @ %H:%M:%S"))))
    row_set = set()
    
    # Reading feature class data into a pandas DataFrame
    with arcpy.da.SearchCursor(in_feat, field) as cursor:
        for row in cursor:
            value = row[0]
            row_set.add(value)

    log_message(f'Input feature contains {len(row_set)} total row values')
    log_message('Row Value Set Built{0}\n------------------------------------------------'.format('  ::  '+str(datetime.now().strftime("%Y-%m-%d @ %H:%M:%S"))))

    return row_set

##################-------------------------------------------------------------------------------------##################
                                             # Working with spatial selections
##################-------------------------------------------------------------------------------------##################

def spa_select_int(target_feat,select_feat,def_query,field,out_gdb,Append):
    """
    This function is meant to be used to execute a variety of select by location workflows utilizing the 'INTERSECT' method
    
    This function allows you to pass a definition query in the form of a list, set, float, integer, or string data type. The appropriate workflow is implemented for the type of def query passed to the function.
    The selected features will be exported to the user defined output workspace.

    If no def querry is being passed to the function the user must use NONE as the input parameter for 'def_query' and 'field'.

    target feature = the feature to be selected
    select_feature = the selecting feature
    def_query = the user should develope a set, list, or single value that is to be queried and pass it to the function for the parameter
    field = the field containing the def_query value(s)
    out_gdb = the target output geodatabase
    append = a boolean that will indicate whether or not to append the target fc name to the output selection

    """
    arcpy.SetProgressor('default', 'Initiating Intersect Selection Module...')
    log_message('Initiating Intersect Selection Module{0}'.format('  ::  ' + str(datetime.now().strftime("%Y-%m-%d @ %H:%M:%S"))))

    if def_query:
        arcpy.SetProgressor('default', 'Definition Query Provided...')
        log_message('Definition Query Provided{0}'.format('  ::  ' + str(datetime.now().strftime("%Y-%m-%d @ %H:%M:%S"))))
        data_type = type(def_query)
        if data_type == dict or data_type == range or data_type == frozenset or data_type == bool or data_type == None:
            pass
        elif data_type == set or data_type == list:
            q_num = len(def_query)
            arcpy.SetProgressor('step','Selecting Features...',0,1,q_num)
            for query in def_query:
                log_message("Processing '{0}' Spatial Selection{1}".format(query,'  ::  ' + str(datetime.now().strftime("%Y-%m-%d @ %H:%M:%S"))))
                arcpy.SetProgressorLabel("Processing '{0}' Spatial Selection".format(query))
                q = str(query)
                dq = f"{field} = '{q}'"
                if Append:
                    desc = arcpy.Describe(target_feat)
                    desc_name = desc.name
                    q_r = q.replace(' ','_').replace('-','_').replace('.','_')
                    q_app = q_r + '_' + desc_name
                    out_fc_path = paths(out_gdb,q_app)
                else:
                    q_final = q.replace(' ','_').replace('-','_').replace('.','_')
                    out_fc_path = paths(out_gdb,q_final)

                try:
                    sel_fl = arcpy.MakeFeatureLayer_management(
                        in_features=select_feat, out_layer='sel_fl', where_clause=dq)
                
                    selection = arcpy.management.SelectLayerByLocation(
                        in_layer=target_feat,
                        overlap_type='INTERSECT',
                        select_features=sel_fl)
                
                    out_fc = arcpy.management.CopyFeatures(
                        in_features=selection, 
                        out_feature_class=out_fc_path)

                except (Exception, OSError) as e:
                    log_message("A process error occurred{0} \n{1}".format('  ::  '+str(datetime.now().strftime("%Y-%m-%d @ %H:%M:%S")),e))
                    arcpy.AddWarning("An unexpected error occurred: {}".format(e))

                log_message("Completed '{0}' Spatial Selection{1}".format(query,'  ::  '+str(datetime.now().strftime("%Y-%m-%d @ %H:%M:%S"))))
                arcpy.SetProgressorPosition()
        else:
            log_message("Processing '{0}' Spatial Selection{1}".format(def_query,'  ::  ' + str(datetime.now().strftime("%Y-%m-%d @ %H:%M:%S"))))
            arcpy.SetProgressor("default","Processing '{0}' Spatial Selection".format(def_query))

            q = str(def_query)
            dq = f"{field} = '{q}'"
            if Append:
                desc = arcpy.Describe(target_feat)
                desc_name = desc.name
                q_r = q.replace(' ','_').replace('-','_').replace('.','_')
                q_app = q_r + '_' + desc_name
                out_fc_path = paths(out_gdb,q_app)
            else:
                q_app = 'Selection_' + desc_name
                out_fc_path = paths(out_gdb,q_app)

            try:
                sel_fl = arcpy.MakeFeatureLayer_management(
                    in_features=select_feat, out_layer='sel_fl', where_clause=dq)
                
                selection = arcpy.management.SelectLayerByLocation(
                    in_layer=target_feat,
                    overlap_type='INTERSECT',
                    select_features=sel_fl)
                
                out_fc = arcpy.management.CopyFeatures(
                        in_features=selection, 
                        out_feature_class=out_fc_path)
                
            except (Exception, OSError) as e:
                    log_message("A process error occurred{0} \n{1}".format('  ::  '+str(datetime.now().strftime("%Y-%m-%d @ %H:%M:%S")),e))
                    arcpy.AddWarning("An unexpected error occurred: {}".format(e))

            log_message("Completed '{0}' Spatial Selection{1}".format(query,'  ::  '+str(datetime.now().strftime("%Y-%m-%d @ %H:%M:%S"))))
            arcpy.SetProgressorPosition()
            
    else:
        log_message("Processing Spatial Selection{1}".format('  ::  ' + str(datetime.now().strftime("%Y-%m-%d @ %H:%M:%S"))))
        arcpy.SetProgressor("default","Processing Spatial Selection")

        desc = arcpy.Describe(target_feat)
        desc_name = desc.name
        q_app = 'Selection_' + desc_name
        out_fc_path = paths(out_gdb,q_app)
        
        selection = arcpy.management.SelectLayerByLocation(
                    in_layer=target_feat,
                    overlap_type='INTERSECT',
                    select_features=select_feat)
                
        out_fc = arcpy.management.CopyFeatures(
                        in_features=selection, 
                        out_feature_class=out_fc_path)
        
        log_message("Completed Spatial Selection{1}".format('  ::  '+str(datetime.now().strftime("%Y-%m-%d @ %H:%M:%S"))))
        arcpy.SetProgressorPosition()
        
    return out_fc