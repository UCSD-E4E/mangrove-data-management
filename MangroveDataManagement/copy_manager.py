import os
import shutil
import hashlib
from glob import glob
from tkinter import messagebox
from shutil import which
from subprocess import Popen
from .caf import Caffine

class CopyManager:
    def __init__(self, source: str, target: str):
        self._caf = Caffine()
        self._caf_id: int = None
        self._source = source
        self._target = target

    def copy_files(self):
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
            return

        for file in source_files:
            file_name = os.path.basename(file)
            shutil.copyfile(file, os.path.join(self._target, file_name))

        self._caf.release(request_id)

    def _validate_file(self, source_file, target_file):
        with open(source_file, 'rb') as f:
            source_data = f.read()
            source_checksum = hashlib.md5(source_data).hexdigest()

        with open(target_file, 'rb') as f:
            target_data = f.read()
            target_checksum = hashlib.md5(target_data).hexdigest()

        return source_checksum == target_checksum

    def validate_files(self):
        request_id = self._caf.request()

        source_files = glob(os.path.join(
            self._source,
            '**/*'
        ))
        file_set = [(f, os.path.join(self._target, os.path.basename(f))) for f in source_files]

        result = all(self._validate_file(s, t,) for s, t in file_set)
        self._caf.release(request_id)

        return result