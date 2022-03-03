from typing import Any, Dict
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

def has_files(drive: str):
    return os.path.exists(os.path.join(drive, 'DCIM'))

def get_removable_drives():
    return [d for d in win32api.GetLogicalDriveStrings().split('\x00')[:-1] if win32file.GetDriveType(d) == win32file.DRIVE_REMOVABLE and has_files(d)]

def get_fixed_drives():
    return [d for d in win32api.GetLogicalDriveStrings().split('\x00')[:-1] if win32file.GetDriveType(d) == win32file.DRIVE_FIXED]

def add_source_drive_dropdown(root: tkinter.Tk, row: int, default=None):
    removable_drives = get_removable_drives()

    label = tkinter.Label(root, text='Source Drive')
    label.grid(row=row, column=0)

    variable = tkinter.StringVar()
    if default and default in removable_drives:
        variable.set(default)
    elif removable_drives:
        variable.set(removable_drives[0])

    dropdown = tkinter.OptionMenu(root, variable, *removable_drives)
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
    copy_path = os.path.join(
        os.path.expanduser('~/Desktop'),
        F"{config['country']}_{config['region']}",
        F"{config['date'].strftime('%Y-%m-%d')}",
        config['site'],
        config['flight'])
    copy_path = create_directories(copy_path)

    source_files = glob(os.path.join(
        F"{config['drive']}",
        'DCIM',
        '**/*'
    ))

    for file in source_files:
        file_name = os.path.basename(file)
        shutil.copyfile(file, os.path.join(copy_path, file_name))

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

    drive_label, drive_dropdown, drive_variable = add_source_drive_dropdown(root, 0, default=get_value_or_default(config, 'drive'))
    country_label, country_entry = add_entry(root, 'Country', 1, default=get_value_or_default(config, 'country'))
    region_label, region_entry = add_entry(root, 'Region', 2, default=get_value_or_default(config, 'region'))
    date_label, date_entry = add_date(root, 'Flight Date', 3)
    site_label, site_entry = add_entry(root, 'Site', 4)
    flight_label, flight_entry = add_entry(root, 'Flight', 5)

    def copy_command():
        config['drive'] = drive_variable.get()
        config['country'] = fix_input(country_entry.get())
        config['region'] = fix_input(region_entry.get())
        config['date'] = date_entry.get_date()
        config['site'] = fix_input(site_entry.get())
        config['flight'] = fix_input(flight_entry.get())

        save_config(config)
        copy(config)

    copy_button = tkinter.Button(root, text='Copy', command=copy_command)
    copy_button.grid(row=6, column=1)

    root.mainloop()

if __name__ == '__main__':
    main()