from typing import Any, Dict, List
import win32api
import win32file
import os
import pathlib
import pickle
from tkinter import messagebox
from glob import glob
import shutil
import wmi
from shutil import which
from subprocess import Popen
import time
import math

from .main_window import MainWindow
from .copy_manager import CopyManager

def has_files(drive: str):
    return os.path.exists(os.path.join(drive, 'DCIM'))

def get_removable_drives():
    return [d for d in win32api.GetLogicalDriveStrings().split('\x00')[:-1] if win32file.GetDriveType(d) == win32file.DRIVE_REMOVABLE and has_files(d)]

def get_fixed_drives():
    c = wmi.WMI()
    logical_disk2partition_query = c.query('SELECT * FROM Win32_LogicalDiskToPartition')
    logical_disk2partition_map = {l2p.Antecedent.DeviceID:l2p.Dependent for l2p in logical_disk2partition_query}
    disk_drive2disk_partition_query = c.query('SELECT * FROM Win32_DiskDriveToDiskPartition')

    disk_drive2disk_partition_filter = [(d2p.Antecedent, d2p.Dependent) for d2p in disk_drive2disk_partition_query if d2p.Antecedent.MediaType == 'External hard disk media']
    logical_disks = [F'{logical_disk2partition_map[p.DeviceID].DeviceID}\\ ({d.Model})' for d, p in disk_drive2disk_partition_filter if p.DeviceID in logical_disk2partition_map]
    
    return [F'Desktop ({os.path.join(os.path.expanduser("~"), "Desktop")})'] + logical_disks

def create_directories(path: str):
    path_obj = pathlib.Path(path)
    if not os.path.exists(path_obj.absolute()):
        path_obj.mkdir(parents=True)

    return path_obj.absolute()

def get_config_path():
    config_path = create_directories(os.path.expandvars('%APPDATA%/E4E/Mangroves'))
    return os.path.join(config_path, 'config.pickle')

def save_config(config: Dict[str, Any]):
    with open(get_config_path(), 'wb') as f:
        pickle.dump(config, f)

def load_config() -> Dict[str, Any]:
    if os.path.exists(get_config_path()):
        with open(get_config_path(), 'rb') as f:
            return pickle.load(f)
    
    return {}

def copy(config: Dict[str, Any]):
    # progress_win = tkinter.Toplevel()
    # progress_win.geometry('500x100')
    # progress_win.config(bg='black')

    # progress = tkinter.ttk.Progressbar(progress_win)
    # progress.pack(fill='x', ipady=10, expand=True)

    # remaining_time = tkinter.Label(progress_win)
    # remaining_time.pack(fill='x')
    # remaining_time.config(bg='black', fg='white', font=FONT)

    base_target_path, _ = config['target_drive'].split(' ')
    if base_target_path == 'Desktop':
        base_target_path = os.path.expanduser('~/Desktop')

    copy_path = os.path.join(
        base_target_path,
        F"{config['country']}_{config['region']}",
        F"{config['date'].strftime('%Y-%m-%d')}",
        config['site'],
        config['flight'])
    copy_path = create_directories(copy_path)

    copy_manager = CopyManager(
        os.path.join(
            config['source_drive'],
            'DCIM'),
        copy_path)
    copy_manager.copy_files()

    # progress.config(length=len(source_files))

    # start = time.perf_counter()
    # for i, file in enumerate(source_files):
    #     file_name = os.path.basename(file)
    #     shutil.copyfile(file, os.path.join(copy_path, file_name))
    #     elapsed = time.perf_counter() - start
    #     time_per_item = elapsed / (float(i) + 1.0)
    #     total_time = time_per_item * len(source_files)
    #     time_remaining = total_time - time_per_item
    #     minutes_remaing = math.floor(time_remaining / 60)
    #     seconds_remaining = time_remaining - minutes_remaing * 60
        # progress['value'] = (float(i) + 1.0) * 100.0 / float(len(source_files))
        # remaining_time.config(text=F'{minutes_remaing}:{round(seconds_remaining * 1000) / 1000} remaining')

    if not copy_manager.validate_files():
        messagebox.showerror(title='An error during copy occurred.', message='One or more files failed the checksum check.')

    # if config['delete_files']:
    #     folder_to_delete = os.path.join(
    #         config['source_drive'],
    #         'DCIM'
    #     )

    #     try:
    #         shutil.rmtree(folder_to_delete)
    #     except OSError:
    #         messagebox.showerror(
    #             title='An error has occurred while trying to delete the DCIM folder.',
    #             message='Please delete the DCIM folder manually')
    #         file_path = which('explorer')
    #         Popen([file_path, folder_to_delete])

    # progress_win.destroy()

    # Launch explorer.
    file_path = which('explorer')
    Popen([file_path, copy_path])

def main():
    # Only run if a removable drive is attached.
    removable_drives = get_removable_drives()
    if not removable_drives:
        messagebox.showerror(title='No removable drives attached', message='Check that your SD card is plugged in and try again.')
        return

    config = load_config()

    def copy_callback(config):
        save_config(config)
        copy(root, config)
    
    root = MainWindow(config, removable_drives, get_fixed_drives(), copy_callback)
    root.mainloop()

if __name__ == '__main__':
    main()