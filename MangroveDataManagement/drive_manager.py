from typing import List
from abc import ABC, abstractmethod
import os
import wmi
import win32api
import win32file
from .utils import create_directories


class DriveManager(ABC):
    @abstractmethod
    def get_removable_drives(self) -> List[str]:
        pass

    @abstractmethod
    def get_fixed_drives(self) -> List[str]:
        pass

class MockDriveManager(DriveManager):
    def get_fixed_drives(self) -> List[str]:
        return [F"{create_directories('./mock_data/fixed_drive_mock')} (Mock)"]

    def get_removable_drives(self) -> List[str]:
        return [create_directories('./mock_data/removable_drive_mock')]

class PhysicalDriveManager(DriveManager):
    def _has_files(self, drive: str):
        return os.path.exists(os.path.join(drive, 'DCIM'))

    def get_removable_drives(self):
        return [d for d in win32api.GetLogicalDriveStrings().split('\x00')[:-1] if win32file.GetDriveType(d) == win32file.DRIVE_REMOVABLE and self._has_files(d)]

    def get_fixed_drives(self):
        c = wmi.WMI()
        logical_disk2partition_query = c.query('SELECT * FROM Win32_LogicalDiskToPartition')
        logical_disk2partition_map = {l2p.Antecedent.DeviceID:l2p.Dependent for l2p in logical_disk2partition_query}
        disk_drive2disk_partition_query = c.query('SELECT * FROM Win32_DiskDriveToDiskPartition')

        disk_drive2disk_partition_filter = [(d2p.Antecedent, d2p.Dependent) for d2p in disk_drive2disk_partition_query if d2p.Antecedent.MediaType == 'External hard disk media']
        logical_disks = [F'{logical_disk2partition_map[p.DeviceID].DeviceID}\\ ({d.Model})' for d, p in disk_drive2disk_partition_filter if p.DeviceID in logical_disk2partition_map]
        
        return logical_disks