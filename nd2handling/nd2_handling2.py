import os
import pandas as pd
import numpy as np

#My modules
import nd2_handling
import file_processing as fp
import tiff_image_manipulation as ti
import fun_array_pixel as ap
import fun_wave_general as wg

class Video_waves(nd2_handling.Video):
    def __init__(self,file_path, camera_pixel_size_um=16, read_img_directly=False, frame_range = [0,0], dir_exp='', mode='normal', subtract_bg=True):
        super().__init__(file_path, camera_pixel_size_um,read_img_directly,frame_range)

        #Create a folder for the file in the current file directory
        self.dir_path_file_folder = os.path.join(self.dir_file, self.file_name0) 
        if not os.path.exists(self.dir_path_file_folder):
            os.mkdir(self.dir_path_file_folder)

        #Create a sub folder where to save image analyzed files (pixelated)
        self.dir_pixelated_files =  os.path.join(self.dir_path_file_folder, 'pixelated_'+self.p+'mbar')
        if not os.path.exists(self.dir_pixelated_files):
            os.mkdir(self.dir_pixelated_files)

        #Create a sub folder where to save kymographs
        self.dir_kymos =  os.path.join(self.dir_path_file_folder, 'kymographs'+self.p+'mbar')
        if not os.path.exists(self.dir_kymos):
            os.mkdir(self.dir_kymos)

        if mode == 'polarization':
        #Create a sub folder where to save hsv images
            self.dir_hsv =  os.path.join(self.dir_path_file_folder, 'hsv images'+self.p+'mbar')
            if not os.path.exists(self.dir_hsv):
                os.mkdir(self.dir_hsv)

       #Create a sub folder where to save hsv images
        self.dir_img_no_posts =  os.path.join(self.dir_path_file_folder, 'img_posts_masked_out'+self.p+'mbar')
        if not os.path.exists(self.dir_img_no_posts):
            os.mkdir(self.dir_img_no_posts)

       #Create a sub folder where to save videos
        self.dir_video_files =  os.path.join(self.dir_path_file_folder, 'video_files_'+self.p+'mbar')
        if not os.path.exists(self.dir_video_files):
            os.mkdir(self.dir_video_files)
       #Create a sub folder where to save 2D FFT spectra
        self.dir_2D_FFT =  os.path.join(self.dir_path_file_folder, '2D_FFT')
        if not os.path.exists(self.dir_2D_FFT):
            os.mkdir(self.dir_2D_FFT)

        if len(dir_exp) == 0:
            print('Did not add the bg directory to the wave video class')
            self.frame_to_display = 0 #Default frame to display
            print('Setting the frame to display as 0')
        else:
            self.dir_exp = dir_exp 
            if subtract_bg:                           
                dir_bg_file = os.path.join(dir_exp, 'bg', self.mag)
                file_name_bg = fp.find_file_name(dir_bg_file, prefix='MED', file_ending = 'tif')
                if file_name_bg == -1:
                    raise ValueError(f'Could not find the bg tiff file in \n{dir_bg_file}')
                self.file_path_bg = os.path.join(dir_bg_file, file_name_bg)

            #Create a sub folder where to save bg-subtracted videos
            self.dir_bg_subtracted_vid =  os.path.join(self.dir_path_file_folder, 'bg_subtracted_vid_'+self.p+'mbar')
            if not os.path.exists(self.dir_bg_subtracted_vid):
                os.mkdir(self.dir_bg_subtracted_vid)

            self.frame_to_display = 0 #Default frame to display
        #Create a sub folder where to save videos
            self.figures_shared =  os.path.join(self.dir_exp, 'figures_shared')
            if not os.path.exists(self.figures_shared):
                os.mkdir(self.figures_shared)            
        if ',' in self.p:
            self.p = self.p.replace(',','.')

import sys
def update_v_from_nd2_spreadsheet_if_pims_could_not_extract_metadata(v, df_vid, settings_general):
    frame_to_display = int(df_vid.frame_to_display.values[0])
    if settings_general['frame_range'][-1] != 0:
        if frame_to_display < settings_general['frame_range'][-1]:
            v.frame_to_display = frame_to_display
    else:
        v.frame_to_display = frame_to_display
    if not hasattr(v,'n_frames'):
        v.n_frames = int(df_vid.n_frames.values[0])
    if not hasattr(v,'frame_rate'):
        v.frame_rate = df_vid.frame_rate.values[0]
    if not hasattr(v,'time_s'):
        v.time_s = df_vid.time_s.values[0]
    if not hasattr(v,'time_start'):
        v.time_start = df_vid.time_start.values[0]   
    if not hasattr(v,'avg_exposure_time_ms'):
        v.avg_exposure_time_ms = df_vid.avg_exposure_time_ms.values[0] 
    if not hasattr(v,'width'):
        v.width = df_vid.width.values[0] 
    if not hasattr(v,'height'):
        v.height = df_vid.height.values[0] 
    if (not hasattr(v,'pixel_width')) & ('pixel_width' in df_vid.columns):
        v.pixel_width = df_vid.pixel_width.values[0] 
    if not hasattr(v,'bit_depth'):
        v.bit_depth = df_vid.bit_depth.values[0]     
    if not hasattr(v,'y_um_frame0'):
        v.y_um_frame0 = df_vid.y_um_frame0.values[0]    
    if not hasattr(v,'x_um_frame0'):
        v.x_um_frame0 = df_vid.x_um_frame0.values[0]  
    if (not hasattr(v,'Q_uL_per_min_mean')) & ('Q_uL_per_min_mean' in df_vid.columns):
        v.Q_uL_per_min_mean = df_vid.Q_uL_per_min_mean.values[0]    
    if (not hasattr(v,'Q_uL_per_min_std')) & ('Q_uL_per_min_std' in df_vid.columns):
        v.Q_uL_per_min_std = df_vid.Q_uL_per_min_std.values[0]   
    if (not hasattr(v,'U_m_per_s_mean')) & ('U_m_per_s_mean' in df_vid.columns):
        v.U_m_per_s_mean = df_vid.U_m_per_s_mean.values[0]   
    if (not hasattr(v,'u_um_per_s')) & ('u_um_per_s' in df_vid.columns):
        v.u_um_per_s = df_vid.u_um_per_s.values[0]    
    if (not hasattr(v,'Q_uL_per_h')) & ('Q_uL_per_h' in df_vid.columns):
        v.Q_uL_per_h = df_vid.Q_uL_per_h.values[0]    
    if (not hasattr(v,'Q_ng_per_h')) & ('Q_ng_per_h' in df_vid.columns):
        v.Q_ng_per_h = df_vid.Q_ng_per_h.values[0]    
    if (not hasattr(v,'C_ng_per_uL')) & ('C_ng_per_uL' in df_vid.columns):
        v.C_ng_per_uL = df_vid.C_ng_per_uL.values[0]    
    if (not hasattr(v,'U_m_per_s_std')) & ('U_m_per_s_std' in df_vid.columns):
        v.U_m_per_s_std = df_vid.U_m_per_s_std.values[0]  
    if (not hasattr(v,'Wi_low')) & ('Wi_low' in df_vid.columns):
        v.Wi_low = df_vid.Wi_low.values[0]              
    v.crop = ap.extract_crop_values_From_df(df_vid)                     
    return v    

def get_exp_list_df(dir_main):
    """[Get the data frame based on the excel document generated with the module nd2_handling 
    (the excel document file name always contains 'nd2_file_list'.)
    If the excel document does not exist, it is generated.
    ]

    Args:
        dir_main ([string or os.path]): [Directory of the excel document]

    Returns:
        [pandas data frame]: [Data frame containing the data from the excel document]
    """
    file_path = fp.find_file_name_v2(dir_main, sub_string='_nd2_file_list', prefix='', file_ending = 'xlsx', return_path = True)
    
    #If it can't find the excel sheet, make it.
    if len(file_path) == 0: 
        print('\tCould not find the spreadsheet with the file list, creating it...')
        nd2_handling.nd2_file_infos_to_spreadsheet(dir_main, read_time_steps=False, read_xy_pos=False, read_file_name_info=True)
        file_path = fp.find_file_name_v2(dir_main, sub_string='nd2_file_list', prefix='', file_ending = 'xlsx', return_path = True)

    # df = pd.read_excel(file_path, dtype={'exp_ID':str, 'pressures':list, 'device_type':str, 'experiment_type':str, 'pressures_to_ignore':float})
    df = pd.read_excel(file_path, dtype={'file_nbr':str})
    print(f'\t Found data frame {os.path.basename(file_path)}')
    return df

def get_v_from_exp_ID(exp_ID, file_nbr, settings_general, read_img_directly=False, frame_range = [0,0]):
    pressures=np.array([-1])
    df = ap.get_exp_list_df()
    df_exp = wg.create_exp_df(exp_ID, df, settings_general)
    pressures = wg.update_pressures(df, exp_ID, pressures)
    df_vid = wg.make_subset_of_df_exp(df_exp, settings_general, file_nbr=file_nbr)
    file_path = df_vid.file_path.values[0]
    v = Video_waves(file_path, read_img_directly=read_img_directly, dir_exp=df_vid.dir_exp.values[0])
    return v

def get_Video(dir_exp, file_nbr, read_img_directly=True, frame_range = [0,0], settings_get_video={}):
    """[Returns a Video class object (see nd2_handling) depending on the parent directory and the input variables
    Requires the spreadsheet with the list to start with the prefix '_nd2_file_list', note the initial underscore.

    if tiff-files are to be loaded, specify the file ending and prefix in the dictionary settings_get_video
    ]

    Args:
        dir_path ([type]): [description]
        file_nbr ([type]): [description]

    Returns:
        [type]: [description]
    """
    df = get_exp_list_df(dir_exp)
    file_path_df = df[df['file_nbr'] == file_nbr].file_path
    if len(file_path_df) != 0:
        path_file = file_path_df.values[0]
    else:
        raise ValueError(f'Could not find file #{file_nbr} in the excel document in \n folder: {dir_exp}')

    if len(settings_get_video) > 0:
        if 'video_prefix' in settings_get_video:
            path_dir = os.path.dirname(path_file)
            prefix = settings_get_video['video_prefix']
            path_file = fp.find_file_name_v2(path_dir, sub_string='', prefix=prefix, file_ending = 'tiff', return_path = True)
            if len(path_file) == 0:
                 raise ValueError(f'Could not find file #{file_nbr} with the prefix {prefix} in \n folder: {dir_exp}')

        if 'file_ending' in settings_get_video:
            if settings_get_video['file_ending'] == 'tiff':
                path_file_nd2 = file_path_df.values[0]
                v = nd2_handling.Video(path_file_nd2, read_img_directly=False, frame_range=frame_range)
                print('tiff path: ', path_file)
                v.img = ti.read_tif_file(path_file, frame_range=frame_range)
    else:      
        if read_img_directly==False:
            #Set the nd2 file as path if the image is not being read, e.g. if you want just want to read the info about the nd2 file
            path_file = file_path_df.values[0]
        v = nd2_handling.Video(path_file, read_img_directly=read_img_directly, frame_range=frame_range)
    return v