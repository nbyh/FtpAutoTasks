import win32event
import win32api
import winerror
import sys
from typing import Optional

class SingleInstance:
    """ 确保应用程序只运行一个实例 """
    
    def __init__(self):
        self.mutexname = "FTPAutoTasks_{D0E858DF-985E-4907-B7FB-8D732C3FC3B9}"
        self.mutex: Optional[int] = None
        
    def __enter__(self):
        self.mutex = win32event.CreateMutex(None, False, self.mutexname)
        if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
            self.mutex = None
            # 找到已运行的实例窗口并激活
            self._activate_existing_window()
            sys.exit(1)
        return self
        
    def __exit__(self, *args):
        if self.mutex:
            win32api.CloseHandle(self.mutex)
            
    def _activate_existing_window(self):
        """查找并激活已运行的程序窗口"""
        try:
            from win32gui import FindWindow, ShowWindow, SetForegroundWindow, SW_SHOW
            other_window = FindWindow(None, "FTP自动发送工具")
            if other_window:
                ShowWindow(other_window, SW_SHOW)
                SetForegroundWindow(other_window)
        except:
            pass