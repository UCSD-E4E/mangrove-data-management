import os
import pathlib

def create_directories(path: str):
    path_obj = pathlib.Path(path)
    if not os.path.exists(path_obj.absolute()):
        path_obj.mkdir(parents=True)

    return path_obj.absolute()