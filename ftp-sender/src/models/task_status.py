from enum import Enum

class TaskStatus(Enum):
    UNKNOWN = "unknown"
    DISABLED = "disabled"
    ENABLED = "enabled"
    RUNNING = "running" 
    ERROR = "error"
    SUCCESS = "success"

    @classmethod
    def get_display_name(cls, status):
        display_names = {
            cls.UNKNOWN: "未知",
            cls.DISABLED: "已禁用",
            cls.ENABLED: "已启用",
            cls.RUNNING: "运行中",
            cls.ERROR: "错误",
            cls.SUCCESS: "成功"
        }
        return display_names.get(status, str(status))