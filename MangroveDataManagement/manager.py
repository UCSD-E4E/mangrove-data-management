from queue import Empty
from time import sleep
from typing import Any, Dict, List
import os
import pathlib
import pickle
from tkinter import messagebox
from glob import glob
import shutil
from shutil import which
from subprocess import Popen
import json
import argparse
from multiprocessing import Process, Queue
import tkinter

FONT_NAME = 'Segoe UI'
FONT_SIZE = 18
FONT = (FONT_NAME, FONT_SIZE)

from .main_window import MainWindow
from .copy_manager import CopyManager
from .drive_manager import MockDriveManager, PhysicalDriveManager
from .utils import create_directories

def write_metadata(config: Dict[str, Any], path: str):
    with open(os.path.join(
        path,
        'metadata.json'
    ), 'w') as f:
        json.dump(config, f, default=str, indent=4, sort_keys=True)

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

def copy(config: Dict[str, Any], message_queue: Queue):
    def update_progress_callback(percent: float, minutes: int, seconds: float, message: str):
        message_queue.put((percent, minutes, seconds, message))

    base_target_path, _ = config['target_drive'].split('(')
    base_target_path = base_target_path.strip()
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
    if not copy_manager.copy_files(lambda p, m, s: update_progress_callback(p, m, s, 'Copying files')):
        return
    write_metadata(config, copy_path)

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

    if not copy_manager.validate_files(lambda p, m, s: update_progress_callback(p, m, s, 'Validating files')):
        messagebox.showerror(title='An error during copy occurred.', message='One or more files failed the checksum check.')
        return

    sd_card_path = os.path.join(
        config['source_drive'],
        F"{config['country']}_{config['region']}",
        F"{config['date'].strftime('%Y-%m-%d')}",
        config['site'],
        config['flight'])
    create_directories(sd_card_path)
    target_dcim = os.path.join(
        sd_card_path,
        'DCIM')
    shutil.move(os.path.join(
        config['source_drive'],
        'DCIM'
    ), target_dcim)
    write_metadata(config, target_dcim)

    message_queue.put(-1)

    # Launch explorer.
    file_path = which('explorer')
    Popen([file_path, copy_path])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mock", action="store_true")
    args = parser.parse_args()
    if args.mock:
        drive_manager = MockDriveManager()
    else:
        drive_manager = PhysicalDriveManager()

    # Only run if a removable drive is attached.
    removable_drives = drive_manager.get_removable_drives()
    if not removable_drives:
        messagebox.showerror(title='No removable drives attached', message='Check that your SD card is plugged in and try again.')
        return

    fixed_drives = drive_manager.get_fixed_drives()
    if not fixed_drives:
        messagebox.showerror(title='No fixed drives attached', message='Check that your portable HDD is plugged in and try again.')
        return

    config = load_config()

    def copy_callback(root: MainWindow, config):
        root.disable_copy()

        progress_win = tkinter.Toplevel()
        progress_win.geometry('500x100')
        progress_win.config(bg='black')

        progress = tkinter.ttk.Progressbar(progress_win)
        progress.pack(fill='x', ipady=10, ipadx=10, expand=True)
        progress.config(length=100)

        message_label = tkinter.Label(progress_win)
        message_label.pack(fill='x')
        message_label.config(bg='black', fg='white', font=FONT)

        remaining_time = tkinter.Label(progress_win)
        remaining_time.pack(fill='x')
        remaining_time.config(bg='black', fg='white', font=FONT)

        message_queue = Queue()
        save_config(config)
        process = Process(target=copy, args=(config, message_queue))
        process.start()

        while message_queue:
            try:
                message = message_queue.get(block=False)

                if message == -1:
                    progress_win.destroy()
                    root.enable_copy()
                    break

                percent, minutes_remaing, seconds_remaining, message_str = message
                message_label.config(text=message_str)
                progress['value'] = round(percent * 100)
                remaining_time.config(text=F'{minutes_remaing}:{round(seconds_remaining * 1000) / 1000} remaining')
            except Empty:
                root.update()
    
    root = MainWindow(config, removable_drives, fixed_drives, copy_callback)
    root.mainloop()

if __name__ == '__main__':
    main()