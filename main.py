from typing import Any, Dict, List
import win32api
import win32file
import tkinter
import tkcalendar
import os
import pathlib
import pickle
from tkinter import messagebox
from glob import glob
import shutil
import wmi

def has_files(drive: str):
    return os.path.exists(os.path.join(drive, 'DCIM'))

def get_removable_drives():
    return [d for d in win32api.GetLogicalDriveStrings().split('\x00')[:-1] if win32file.GetDriveType(d) == win32file.DRIVE_REMOVABLE and has_files(d)]

def get_fixed_drives():
    c = wmi.WMI()
    logical_disk2partition_query = c.query('SELECT * FROM Win32_LogicalDiskToPartition')
    logical_disk2partition_map = {l2p.Antecedent.DeviceID:l2p.Dependent for l2p in logical_disk2partition_query}
    disk_drive2disk_partition_query = c.query('SELECT * FROM Win32_DiskDriveToDiskPartition')

    partitions = [d2p.Dependent for d2p in disk_drive2disk_partition_query if d2p.Antecedent.MediaType == 'External hard disk media']
    logical_disks = [F'{logical_disk2partition_map[p.DeviceID].DeviceID}\\' for p in partitions if p.DeviceID in logical_disk2partition_map]
    
    return ['Desktop'] + logical_disks

def add_dropdown(root: tkinter.Tk, label: str, row: int, data: List[str], default=None):
    label = tkinter.Label(root, text=label)
    label.grid(row=row, column=0)

    variable = tkinter.StringVar()
    if default and default in data:
        variable.set(default)
    elif data:
        variable.set(data[0])

    dropdown = tkinter.OptionMenu(root, variable, *data)
    dropdown.grid(row=row, column=1)

    return label, dropdown, variable

def add_entry(root: tkinter.Tk, label: str, row: int, default=None):
    label = tkinter.Label(root, text=label)
    label.grid(row=row, column=0)

    entry = tkinter.Entry(root)
    entry.grid(row=row, column=1)

    if default:
        entry.insert(0, default)

    return label, entry

def add_date(root: tkinter.Tk, label: str, row: int, default=None):
    label = tkinter.Label(root, text=label)
    label.grid(row=row, column=0)

    date = tkcalendar.DateEntry(root, selectmode='day')
    date.grid(row=row, column=1)

    if default:
        date.set_date(default)

    return label, date

def add_checkbox(root: tkinter.Tk, label: str, row:int, default=None):
    variable = tkinter.BooleanVar()
    if default:
        variable.set(default)

    checkbox = tkinter.Checkbutton(root, text=label,variable=variable, onvalue=True, offvalue=False)
    checkbox.grid(row=row, column=0)

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

def copy(config: Dict[str, Any]):
    base_target_path = config['target_drive']
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

    for file in source_files:
        file_name = os.path.basename(file)
        shutil.copyfile(file, os.path.join(copy_path, file_name))

    if config['delete_files']:
        shutil.rmtree(os.path.join(
            config['source_drive'],
            'DCIM'
        ))

    messagebox.showinfo(title='Copy completed', message='Copy completed')

def get_value_or_default(config: Dict[str, Any], key: str, default=None):
    return config[key] if key in config else default

def fix_input(input: str):
    return input.lower().replace(' ', '-')

def main():
    removable_drives = get_removable_drives()
    if not removable_drives:
        messagebox.showerror(title='No removable drives attached', message='Check that your SD card is plugged in and try again.')
        return

    root = tkinter.Tk()
    root.title('Data Organizer')

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
        copy(config)

    copy_button = tkinter.Button(root, text='Copy', command=copy_command)
    copy_button.grid(row=8, column=1)

    root.mainloop()

if __name__ == '__main__':
    main()