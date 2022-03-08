from typing import Any, Dict, List
import win32api
import win32file
import tkinter
import tkinter.ttk
import tkcalendar
import os
import pathlib
import pickle
from tkinter import messagebox
from glob import glob
import shutil
import wmi
from .caf import Caffine
from shutil import which
from subprocess import Popen
import time
import math

FONT_NAME = 'Segoe UI'
FONT_SIZE = 18
FONT = (FONT_NAME, FONT_SIZE)

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

def add_dropdown(root: tkinter.Tk, label: str, row: int, data: List[str], default=None):
    label = tkinter.Label(root, text=label)
    label.grid(row=row, column=0)
    label.config(bg='black', fg='white', font=FONT)

    variable = tkinter.StringVar()
    if default and default in data:
        variable.set(default)
    elif data:
        variable.set(data[0])

    dropdown = tkinter.OptionMenu(root, variable, *data)
    dropdown.grid(row=row, column=1, sticky='we', pady=(10, 10))
    dropdown.config(bg='black', fg='white', font=FONT)

    return label, dropdown, variable

def add_entry(root: tkinter.Tk, label: str, row: int, default=None):
    label = tkinter.Label(root, text=label)
    label.grid(row=row, column=0)
    label.config(bg='black', fg='white', font=FONT)

    entry = tkinter.Entry(root)
    entry.grid(row=row, column=1, sticky='we', pady=(10, 10))
    entry.config(bg='black', fg='white', insertbackground='white', font=FONT)

    if default:
        entry.insert(0, default)

    return label, entry

def add_date(root: tkinter.Tk, label: str, row: int, default=None):
    label = tkinter.Label(root, text=label)
    label.grid(row=row, column=0)
    label.config(bg='black', fg='white', font=FONT)

    date = tkcalendar.DateEntry(root, selectmode='day')
    date.grid(row=row, column=1, sticky='we', pady=(10, 10))
    date.config(font=FONT)

    if default:
        date.set_date(default)

    return label, date

def add_checkbox(root: tkinter.Tk, label: str, row:int, default=None):
    variable = tkinter.BooleanVar()
    if default:
        variable.set(default)

    checkbox = tkinter.Checkbutton(root, text=label,variable=variable, onvalue=True, offvalue=False)
    checkbox.grid(row=row, column=0, pady=(10, 10))
    checkbox.config(bg='black', fg='white', selectcolor='black', activebackground='black', activeforeground='white', font=FONT)

    return checkbox, variable

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

def copy(root: tkinter.Tk, config: Dict[str, Any]):
    caf = Caffine()
    request_id = caf.request()

    progress_win = tkinter.Toplevel()
    progress_win.geometry('500x100')
    progress_win.config(bg='black')

    progress = tkinter.ttk.Progressbar(progress_win)
    progress.pack(fill='x', ipady=10, expand=True)

    remaining_time = tkinter.Label(progress_win)
    remaining_time.pack(fill='x')
    remaining_time.config(bg='black', fg='white', font=FONT)

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

    source_files = glob(os.path.join(
        config['source_drive'],
        'DCIM',
        '**/*'
    ))

    progress.config(length=len(source_files))

    target_files = [os.path.join(copy_path, os.path.basename(f)) for f in source_files]
    existing_target_files = [f for f in target_files if os.path.exists(f)]

    if existing_target_files:
        messagebox.showerror(
            title='This process would overwrite some files.',
            message='This process cannot overwrite files.  Please manually remove the files from the target folder.')
        file_path = which('explorer')
        Popen([file_path, copy_path])
        caf.release(request_id)
        return

    start = time.perf_counter()
    for i, file in enumerate(source_files):
        file_name = os.path.basename(file)
        shutil.copyfile(file, os.path.join(copy_path, file_name))
        elapsed = time.perf_counter() - start
        time_per_item = elapsed / (float(i) + 1.0)
        total_time = time_per_item * len(source_files)
        time_remaining = total_time - time_per_item
        minutes_remaing = math.floor(time_remaining / 60)
        seconds_remaining = time_remaining - minutes_remaing * 60
        progress['value'] = (float(i) + 1.0) * 100.0 / float(len(source_files))
        remaining_time.config(text=F'{minutes_remaing}:{round(seconds_remaining * 1000) / 1000} remaining')

    if config['delete_files']:
        folder_to_delete = os.path.join(
            config['source_drive'],
            'DCIM'
        )

        try:
            shutil.rmtree(folder_to_delete)
        except OSError:
            messagebox.showerror(
                title='An error has occurred while trying to delete the DCIM folder.',
                message='Please delete the DCIM folder manually')
            file_path = which('explorer')
            Popen([file_path, folder_to_delete])

    caf.release(request_id)
    progress_win.destroy()

    # Launch explorer.
    file_path = which('explorer')
    Popen([file_path, copy_path])

def get_value_or_default(config: Dict[str, Any], key: str, default=None):
    return config[key] if key in config else default

def fix_input(input: str):
    return input.lower().replace(' ', '-')

def main():
    # Only run if a removable drive is attached.
    removable_drives = get_removable_drives()
    if not removable_drives:
        messagebox.showerror(title='No removable drives attached', message='Check that your SD card is plugged in and try again.')
        return

    root = tkinter.Tk()
    root.title('Data Organizer')
    root.config(bg='black')
    root.grid_columnconfigure(1, weight=1)

    config = load_config()

    source_drive_label, source_drive_dropdown, source_drive_variable = add_dropdown(root, 'Source Drive', 0, removable_drives, default=get_value_or_default(config, 'source_drive'))
    target_drive_label, target_drive_dropdown, target_drive_variable = add_dropdown(root, 'Target Drive', 1, get_fixed_drives(), default=get_value_or_default(config, 'target_drive'))
    country_label, country_entry = add_entry(root, 'Country', 2, default=get_value_or_default(config, 'country'))
    region_label, region_entry = add_entry(root, 'Region', 3, default=get_value_or_default(config, 'region'))
    date_label, date_entry = add_date(root, 'Flight Date', 4)
    site_label, site_entry = add_entry(root, 'Site', 5)
    flight_label, flight_entry = add_entry(root, 'Flight', 6)
    delete_checkbox, delete_variable = add_checkbox(root, 'Delete Files', 7, default=get_value_or_default(config, 'delete_files'))

    def copy_command():
        config['source_drive'] = source_drive_variable.get()
        config['target_drive'] = target_drive_variable.get()
        config['country'] = fix_input(country_entry.get())
        config['region'] = fix_input(region_entry.get())
        config['date'] = date_entry.get_date()
        config['site'] = fix_input(site_entry.get())
        config['flight'] = fix_input(flight_entry.get())
        config['delete_files'] = delete_variable.get()

        if not config['country'] or not config['region'] or not config['date'] or not config['site'] or not config['flight']:
            messagebox.showerror(title='Missing data', message='Please ensure all fields have been filled out and try again.')
            return

        save_config(config)
        copy(root, config)

    copy_button = tkinter.Button(root, text='Copy', command=copy_command)
    copy_button.grid(row=8, column=1, pady=(10, 10))
    copy_button.config(bg='black', fg='white', font=FONT)

    root.mainloop()

if __name__ == '__main__':
    main()