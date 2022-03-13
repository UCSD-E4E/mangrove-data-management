import os
import shutil
import hashlib
import time
import math
from glob import glob
from tkinter import messagebox
from shutil import which
from subprocess import Popen
from typing import Callable, Tuple
from .caf import Caffine

class CopyManager:
    def __init__(self, source: str, target: str):
        self._caf = Caffine()
        self._caf_id: int = None
        self._source = source
        self._target = target

    def copy_files(self, callback: Callable[[float, int, float], None]):
        request_id = self._caf.request()

        source_files = glob(os.path.join(
            self._source,
            '**/*'
        ))

        target_files = [os.path.join(self._target, os.path.basename(f)) for f in source_files]
        existing_target_files = [f for f in target_files if os.path.exists(f)]

        if existing_target_files:
            messagebox.showerror(
                title='This process would overwrite some files.',
                message='This process cannot overwrite files.  Please manually remove the files from the target folder.')
            file_path = which('explorer')
            Popen([file_path, self._target])
            self._caf.release(request_id)
            return False

        total_count = len(source_files)

        start = time.perf_counter()
        for i, file in enumerate(source_files):
            file_name = os.path.basename(file)
            shutil.copyfile(file, os.path.join(self._target, file_name))

            elapsed = time.perf_counter() - start
            time_per_item = elapsed / (float(i) + 1.0)
            total_time = time_per_item * len(source_files)
            time_remaining = total_time - time_per_item
            minutes_remaing = math.floor(time_remaining / 60)
            seconds_remaining = time_remaining - minutes_remaing * 60

            callback(float(i + 1) / float(total_count), minutes_remaing, seconds_remaining)

        self._caf.release(request_id)

        return True

    def _validate_file(self, source_file, target_file):
        with open(source_file, 'rb') as f:
            source_data = f.read()
            source_checksum = hashlib.md5(source_data).hexdigest()

        with open(target_file, 'rb') as f:
            target_data = f.read()
            target_checksum = hashlib.md5(target_data).hexdigest()

        return source_checksum == target_checksum

    def validate_files(self, callback: Callable[[float, int, float], None]):
        request_id = self._caf.request()

        source_files = glob(os.path.join(
            self._source,
            '**/*'
        ))
        file_set = [(f, os.path.join(self._target, os.path.basename(f))) for f in source_files]

        total_count = len(source_files)

        start = time.perf_counter()
        for i, (source, target) in enumerate(file_set):
            if not self._validate_file(source, target):
                return False
            
            elapsed = time.perf_counter() - start
            time_per_item = elapsed / (float(i) + 1.0)
            total_time = time_per_item * len(source_files)
            time_remaining = total_time - time_per_item
            minutes_remaing = math.floor(time_remaining / 60)
            seconds_remaining = time_remaining - minutes_remaing * 60

            callback(float(i + 1) / float(total_count), minutes_remaing, seconds_remaining)

        self._caf.release(request_id)

        return True