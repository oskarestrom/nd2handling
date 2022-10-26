#Dependencies:
from pims import ND2_Reader
from nd2reader import ND2Reader
import os
import pandas as pd
import numpy as np
import time

import warnings
warnings.filterwarnings('ignore', '.*ND2_Reader*', )

def read_nd2_file(file_path, frame_range=[0,0]):
    """[Loads a full or part of an nd2 file. Set the frame range you want to load]

    Args:
        file_path ([string or os.path]): [File path]
        frame_range (list, optional): [E.g. range(0,100) or range(0,1000) depending on what you like]. Defaults to [0,0] which will load all the frames available. 

    Returns:
        [type]: [description]
    """
    tic = time.perf_counter()
    str_split = file_path.split('\\')
    file_name = str_split[-1]
    folder_name = str_split[-2]
    print(f"\tReading file "+file_name+' in folder '+folder_name)

    #If the selected frames to read are all set to 0, read the full range in all dimensions. Otherwise, read only the selected range of dimensions.
    if not np.any(frame_range):
        obj_nd2 = ND2_Reader(file_path)
        img = np.array(obj_nd2[:])
        n_frames = obj_nd2.metadata['sequence_count']
    else:
        obj_nd2 = ND2_Reader(file_path)
        img = np.array(obj_nd2[frame_range])
        n_frames = len(frame_range)
    toc = time.perf_counter()
    print(f'\tRead {n_frames} {img.dtype} frame(s) from '+file_name+f' in {toc - tic:0.2f} seconds')    
    return img

def get_avg_exposure_time_using_ND2Reader(file_path):
    """[Averages the exposure times of all the acquisitions in the image stack of the given file.]

    Args:
        file_path ([type]): [description]

    Returns:
        [type]: [description]
    """
    avg_exposure_time = np.nan
    try:    
        with ND2Reader(file_path) as img:
            exposure_times = img.parser._raw_metadata.camera_exposure_time
            avg_exposure_time = np.round(np.mean(exposure_times),2)
        return avg_exposure_time
    except:
        print(f'module ND2Reader caught an error for the file (ignoring this file)\n\t{file_path}\n\t Exposure time will not be extracted')

def find_conc_in_name(file_name):
    """
    Finds the concentration in the file name if it is within the naming convention of Oskar:
    '_XXngul_' where XX is a numeric
    """
    file_name_info = file_name.split('_')
    substring = 'ngul'
    strings_with_substring = [s for s in file_name_info if substring in s]
    if len(strings_with_substring) > 0:
        conc = float(strings_with_substring[0].split(substring)[0])
        return conc
    else:
        return np.nan
def find_light_source_and_intensity_in_file_name(file_name):
    """
    Finds the right light source and intensity in the file name 
    if it is within the naming convention of Oskar:
        '_yyXX_' where yy is the short name of the camera and XX is a numeric denoting the light source intensity in [%]
    """
    file_name_info = file_name.split('_')
    substring1 = 'sola'
    sola_string = [s for s in file_name_info if substring1 in s]
    substring2 = 'solis'
    solis_string = [s for s in file_name_info if substring2 in s]
    
    if len(sola_string) > 0:
        light_source_name = 'sola'
        I = float(sola_string[0].split(substring1)[1])
    elif len(solis_string) > 0:
        light_source_name = 'solis'
        I_str = solis_string[0].split(substring2)[1]
        try:
            I = float(I_str)  
        except ValueError:           
            if I_str[-1] == '%':
                I = float(I_str[:-1]) 
            else:
                print(f'Could not extract the lamp intensity from the file name. ({I_str})')
                I=-1
    else:
        light_source_name = ''
        I = np.nan
    return [light_source_name, I]

def get_device_type(dir):
    "Example dir is '2022-02-03_400nguL_lambda_hex'"
    sub_list = dir.split('_')
    # print('Folder name: ', dir)
    device_type = ''    
    for s in sub_list:
        if 'hex' in s:
            device_type = 'H'
        if 'quad' in s:
            device_type = 'Q'
        if 'rand' in s:
            device_type = 'R'
        if ('control' in s) or ('sparse' in s):
            device_type = 'C'
    return device_type

def read_info_from_file_name(file_name):
    """[Reads a file name based on the file naming convention of Oskar: 
    - The information has to be separated with an underscore, e.g: '10x_100mbar_sola100_001.tif'
    - The file name has to end with a file number, e.g. '_001.tif']

    Args:
        file_name ([type]): [description]

    Returns:
        [info]: [A dictionary with the file number and if they exist also the pressure difference and magnification]
    """
    file_name0 = file_name.split('.')[0] #File name without extension
    file_name_info = file_name0.split('_')
    info = {}

    #Add magnification and pressure info
    for f in file_name_info:
        if f.endswith('mbar') or f.endswith('mBar'):
            p = f.split('mbar')[0]
            info['p'] = p
        if f in ['10x', '20x', '100x', '100xOil', '100xoil', '1x', '2x', '4x', '40x']:
            mag = f.split('x')[0]+'x'
            info['mag'] = mag

    if not 'p' in info:
        info['p'] = 'NaN'
        
    #Add about file number
    file_nbr = file_name_info[-1]
    if not file_nbr.isnumeric():
        print(f'File naming error: Could not extract the file number from the file {file_name}')
        file_nbr = np.nan
    info['file_nbr'] = file_nbr

    #Add light source info
    light_source_info = find_light_source_and_intensity_in_file_name(file_name)
    if len(light_source_info[0]) != 0:
        info['light_source'] = light_source_info[0]
        info['light_source_intensity'] = light_source_info[1]
    
    #Add DNA Conc info
    DNA_conc = find_conc_in_name(file_name)
    if not np.isnan(DNA_conc):
        info['DNA_conc_ngul'] = DNA_conc
    return info

def read_pims_ND2_reader_metadata(file_path, read_time_steps=False, read_xy_pos=False):
    """
    Using the ND2_reader module from the pims library, the metadata is read and added to a dictionary.
    It is optional to read the time steps and the xy-positions.
    
    This function could be extended to add more metadata. Could also use the other library called 'nd2reader'.

    see https://pypi.org/project/pims-nd2/
    """
    dic_pims = {}
    try:        
        img_pims = ND2_Reader(file_path)
        if not 'frame_rate' in img_pims.metadata:
            raise ValueError(f'COULD NOT find frame rate in item {file_path}')
        frame_rate = np.round(img_pims.metadata['frame_rate'],2)
        bit_depth = img_pims.metadata['bitsize_memory'] 
        frame_height = img_pims.metadata['height'] 
        frame_width = img_pims.metadata['width'] 
        time_start = img_pims.metadata['time_start']
        n_frames = img_pims.metadata['sequence_count']
        shape = (n_frames,frame_height,frame_width)
        time_s = np.round(n_frames/frame_rate)
        x_um_frame0 = img_pims[0].metadata['x_um']
        y_um_frame0 = img_pims[0].metadata['y_um']
        dic_pims = {'frame_rate': frame_rate, 'time_start': time_start, 'bit_depth':bit_depth, 'width': frame_width, 'height':frame_height, 'n_frames':n_frames, 'shape':shape, 'time_s':time_s, 'x_um_frame0': x_um_frame0, 'y_um_frame0':y_um_frame0}            
        if read_time_steps:
            t_ms = [f.metadata['t_ms'] for f in img_pims]
            dic_pims = {**dic_pims, 't_ms': t_ms}
        if read_xy_pos:
            x = [f.metadata['x'] for f in img_pims]
            y = [f.metadata['y'] for f in img_pims]
            dic_pims = {**dic_pims, 'x': x, 'y':y}
        img_pims.close()
    except:
        print(f'pims ND2 reader caught an error for file (ignoring this file)\n\t{file_path}')
    finally:
        return dic_pims

def get_nd2_info(file_path, read_time_steps=False, read_xy_pos=False, read_file_name_info=False):
    """
    Adds the metadata and the information from the file name into a list d
    """
    dic = {}
    dir_name = os.path.split(file_path)[0].split('\\')[-1]
    file_name = os.path.split(file_path)[1]
    if file_path.endswith('.nd2'):      

        if read_file_name_info:
            #Read info from file name
            file_info_dict = read_info_from_file_name(file_name)
        else:
            file_info_dict = {}
        #Read metadata using pims ND2_Reader
        dic_pims = read_pims_ND2_reader_metadata(file_path, read_time_steps, read_xy_pos)        

        #Read average exposure time
        avg_exposure_time = get_avg_exposure_time_using_ND2Reader(file_path)

        #Add all the above properties into a single dictionary
        dic =  {**{'file_name': file_name, 'parent_folder':dir_name, 'file_path': file_path, 'avg_exposure_time_ms':avg_exposure_time}, **file_info_dict, **dic_pims}
    else:
        raise ValueError(f'The file is not an nd2-file. File: {file_path}')
    return dic

def list_all_files_in_folder_tree(dir_path, suffix):
    """
    Lists all the files in the folder tree with a specific extention.
    """
    r = []
    for root, dirs, files in os.walk(dir_path):
        for name in files:
            if name.endswith(suffix):
                r.append(os.path.join(root, name))
    return r

def get_z_projection_info_from_file(file_path):
    """[Acquires the mean value, standard deviation from the pixel values of the file in x, y and z-dimensions.
    Note that this function takes a long time to execute]

    Args:
        file_path ([os.path or string]): [Path to the nd2-file]

    Returns:
        [dictionary]: [Dictionary containing the mean and standard deviation]
    """
    print('\tGetting z-projections from file')
    img = read_nd2_file(file_path, frame_range=[0,0])
    mean_img = np.mean(img)
    std_img = np.std(img)
    d = {'mean val':mean_img,
        'std':std_img
    }
    return d

def get_pos_from_file_name(file_name):
    """Get the FoV location 'pos' from the file name.
    Only valid for DNA DLD movies """
    file_name0 = file_name.split('.')[0] #File name without extension
    file_name_info = file_name0.split('_')

    #Find the position and possibly the filter channel (red 'r' or blue 'b')
    filter_ch = '' #Filter channel
    pos = '' #Position
    for f in file_name_info:
        if 'in' in f:
           pos = f
        elif 'out' in f:
            pos = f
        if f == 'b':
           filter_ch = 'b'
        elif f == 'r':
            filter_ch = 'r'
    if len(filter_ch) > 0:
        pos = pos + '-' + filter_ch
    return pos
def nd2_file_infos_to_spreadsheet(dir_path, display_info=False, read_time_steps=False, read_xy_pos=False, read_file_name_info=False, waves_data=True, get_z_projection_info=False, DLD_data=False):
    """[Lists all the meta data and information given in the file name for an experiment folder treein an excel spreadsheet]
        It is optional to read the time steps and the xy-positions.
        
        This function could be extended to add more metadata. Could also use more of the other library called 'nd2reader'.
    Args:
        display_info (bool, optional): [Display information of the function processing such as time taken per file]. Defaults to False.
        get_z_projection_info (bool, optional): [Open all files and extract their mean value and standard deviation and add to the spreadsheet. Makes the function significantly longer, 1 file could take up to 40s to open and process.]. Defaults to False.
        dir_path ([string]): [directory of the experiment]
        read_time_steps (bool, optional): [Read the time points of each frame or not?]. Defaults to False.
        read_xy_pos (bool, optional): [Read the xy-locations of each frame or not?]. Defaults to False.
    """

    print('Initiating nd2_file_infos_to_spreadsheet()')
    tic = time.perf_counter()
    d = [] #Create the list that will be converted to a pandas data frame with all the info.

    # Find all the .nd2 files in the folder tree
    file_list = list_all_files_in_folder_tree(dir_path, '.nd2')
    
    #Iterate the list of files and add the metadata and the information from the file name into a list d
    for i,file_path in enumerate(file_list):
        dic = get_nd2_info(file_path, read_time_steps, read_xy_pos, read_file_name_info)
        if get_z_projection_info:
            dic_z = get_z_projection_info_from_file(file_path)
            dic = {**dic, **dic_z}
        
        d.append(dic)
        if display_info:
            toc = time.perf_counter()
            print(f'\tFile {i+1}/{len(file_list)}: {os.path.basename(file_path)} complete at {toc - tic:0.2f} seconds')       

    #Convert list to data frame
    df = pd.DataFrame(d) 
    #specific to wave analysis
    if waves_data:
        wave_anal_columns = ['group', 'mask_file_nbr', 'comment', 'angle', 'area_min_factor', 'factor_local_otsu', 'otsu_radius_mask_gen', 'dist_max']
        for col in wave_anal_columns:
            df[col] = ' '
        df['exp_ID'] = os.path.split(dir_path)[-1]
        device_type = get_device_type(os.path.split(dir_path)[-1])
        #Look at one step up in the folder tree to see if the device type is specified there
        if len(device_type) == 0:
            device_type = get_device_type(os.path.split(dir_path)[-2])
        df['device_type'] = device_type
        df['order'] = 1
        df['frame_to_display'] = 0
        df['crop_area'] = 'none'
        cols_waves_first = ['group', 'exp_ID','device_type']
        cols_waves_last = ['frame_to_display','crop_area','angle', 'order','mask_file_nbr','area_min_factor', 'factor_local_otsu', 'otsu_radius_mask_gen', 'dist_max']
    #specific for DNA DLD analysis
    elif DLD_data:
        DLD_columns = ['group', 'comment', 'angle', 'x1', 'y1', 'crop_array_imageJ_bg_wall', 'Q_ng_per_h', 'Q_ng_per_h', 'sample_Q_uL_per_h', 'Q_uL_per_h', 'Q_uL_per_min', 'u_um_per_s']
        for col in DLD_columns:
            df[col] = ' '
        df['device_type'] = 'DLD'
        df['order'] = 1
        df['frame_to_display'] = 0
        df['crop_area'] = 'none'
        df['pos'] = df.apply(lambda row: get_pos_from_file_name(row.file_name), axis=1)        
        cols_DLD_first = ['device_type', 'pos', 'order']
        cols_DLD_last = ['frame_to_display','crop_area','angle','x1','y1', 'crop_array_imageJ_bg_wall', 'Q_ng_per_h', 'Q_ng_per_h', 'sample_Q_uL_per_h', 'Q_uL_per_h', 'Q_uL_per_min', 'u_um_per_s']
    
    #Re-order columns
    file_name_info_cols = ['file_nbr','mag']
    cols_reordered = ['comment', 'frame_rate', 'time_s', 'n_frames', 'width', 'height', 'time_start', 'bit_depth', 'avg_exposure_time_ms', 'file_name', 'file_path', 'parent_folder', 'x_um_frame0', 'y_um_frame0']
 
    if 'p' in df.columns:
        cols_reordered.insert(0,'p')

    if read_file_name_info:
        cols_reordered = [*file_name_info_cols, *cols_reordered]
    
    if get_z_projection_info:
        cols_reordered = [*cols_reordered, 'mean val', 'std']

    if waves_data:
        cols_reordered = [*cols_waves_first, *cols_reordered, *cols_waves_last]
    elif DLD_data:
        cols_reordered = [*cols_DLD_first, *cols_reordered, *cols_DLD_last]

    df = df[[*cols_reordered]]
    #Sort the rows by the time the video was recorded
    df.sort_values(by=['time_start'], inplace=True)
    
    #Write to spreadsheet in the folder
    dir_name = os.path.split(dir_path)[-1] #Name of the directory
    spreadsheet_name = 'nd2_file_list_'+dir_name+'.xlsx'
    spreadsheet_path = os.path.join(dir_path, spreadsheet_name)
    df.to_excel(spreadsheet_path, index=False)
    if display_info:
        toc = time.perf_counter()
        print(f'\Function complete after {toc - tic:0.2f} seconds')       

    #Open the directory of the saved spreadsheet in your OS
    os.startfile(dir_path)


def get_nd2_lists_for_all_subfolders(dir_main, read_time_steps=False, read_xy_pos=False, read_file_name_info=False):
    """
    Applies the function nd2_file_infos_to_spreadsheet() for all subdirectories.
    """
    exp_lists = os.listdir(dir_main)
    for f in exp_lists:
        dir_path = os.path.join(dir_main, f)
        print(f'Handling {f}')
        nd2_file_infos_to_spreadsheet(dir_path, read_time_steps=read_time_steps, read_xy_pos=read_xy_pos, read_file_name_info=read_file_name_info)

class Video:
    """
    A class containing information about a tiff image stack. This is supposed to be the "mother" class. 
    For specific projects, inherit this class, see e.g. the class 'Video_DNA_waves(Video)'
    """
    def __init__(self,file_path, camera_pixel_size_um=16, read_img_directly=False, frame_range = [0,0], read_file_name_info=True):
        """[summary]

        Args:
            file_path (str): [Path to the file]. Defaults to ''.
            camera_pixel_size_um (int, optional): [The pixel size of the camera]. Defaults to 16.
            read_img_directly (bool, optional): [Read the image directly into this class instance?]. Defaults to False.
            frame_range (list, optional): [E.g. range(0,100) or range(0,1000) depending on what you like]. Defaults to [0,0] which will load all the frames available. 
        """
        self.file_path = file_path #Set file path
        self.dir_file = os.path.dirname(file_path) #The directory path of the file
        self.file_name = os.path.basename(file_path)
        self.file_name0 = self.file_name.split('.')[0] #File name without extension
        self.str_contains_img = '(empty)' #Does the object contain an image file? Not yet. This is only a string for the __str__ function.
        #Read dictionary containing the file information and convert to attribtes of the class
        if read_file_name_info:
            dic = get_nd2_info(file_path, read_time_steps=False, read_xy_pos=False, read_file_name_info=read_file_name_info)
            for k, v in dic.items():
                setattr(self, k, v)

        if hasattr(self,'scale_pix_per_um'):
            self.scale_pix_per_um = float(self.mag.split('x')[0])/camera_pixel_size_um

        if read_img_directly:
            self.read_img(frame_range=frame_range)

    def read_img(self, frame_range = [0,0]):
        """[Read the image stack, based on the frame range given]

        Args:
            frame_range (list, optional): [E.g. range(0,100) or range(0,1000) depending on what you like]. Defaults to [0,0] which will load all the frames available. 
        """
        self.img = read_nd2_file(self.file_path, frame_range)
        self.str_contains_img = str(self.img.shape)
        
    def __str__(self):
        #Print all attributes
        dic = {key:value for key, value in self.__dict__.items() if not key.startswith('__') and not callable(key) and not key == 'img' and not key == 'kymo'}
        return 'Video'+self.str_contains_img+':\n\t- '+'\n\t- '.join([str(key)+': '+str(value) for key, value in dic.items()])