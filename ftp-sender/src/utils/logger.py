import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List

class Logger:
    def __init__(self):
        self.base_dir = "logs"
        self.current_month = datetime.now().strftime("%Y%m")
        self.log_dir = os.path.join(self.base_dir, self.current_month)
        os.makedirs(self.log_dir, exist_ok=True)
        self.send_records: Dict[str, List[dict]] = {}

    def log_success(self, task_name: str, filename: str, retries: int = 0):
        """记录成功发送的文件"""
        log_entry = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "filename": filename,
            "size": self._get_file_size(filename),
            "retries": retries,
            "status": "success"
        }
        self._write_log(task_name, log_entry)
        self._update_send_records(task_name, log_entry)

    def log_error(self, task_name: str, filename: str, error_msg: str):
        """记录发送失败的文件"""
        log_entry = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "filename": filename,
            "error": error_msg,
            "status": "error"
        }
        self._write_log(task_name, log_entry)

    def _write_log(self, task_name: str, log_entry: dict):
        """写入日志文件"""
        log_file = os.path.join(self.log_dir, f"{task_name}.log")
        with open(log_file, "a", encoding="utf-8") as f:
            json.dump(log_entry, f, ensure_ascii=False)
            f.write("\n")

    def _update_send_records(self, task_name: str, log_entry: dict):
        """更新发送记录"""
        if task_name not in self.send_records:
            self.send_records[task_name] = []
        self.send_records[task_name].append(log_entry)
        
        # 清理超过1小时的记录
        current_time = datetime.now()
        self.send_records[task_name] = [
            record for record in self.send_records[task_name]
            if (current_time - datetime.strptime(record["time"], "%Y-%m-%d %H:%M:%S")) <= timedelta(hours=1)
        ]

    def get_recent_send_count(self) -> int:
        """获取过去1小时发送文件总数"""
        total_count = 0
        for task_records in self.send_records.values():
            total_count += len(task_records)
        return total_count

    def get_task_logs(self, task_name: str, date: str) -> List[dict]:
        """获取指定任务指定日期的日志记录"""
        log_file = os.path.join(self.base_dir, date[:6], f"{task_name}.log")
        if not os.path.exists(log_file):
            return []

        logs = []
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    log_entry = json.loads(line.strip())
                    if log_entry["time"].startswith(date):
                        logs.append(log_entry)
                except:
                    continue
        return logs

    def _get_file_size(self, filename: str) -> str:
        """获取文件大小的友好显示"""
        try:
            size = os.path.getsize(filename)
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024:
                    return f"{size:.2f}{unit}"
                size /= 1024
            return f"{size:.2f}TB"
        except:
            return "0B"

class SystemLogger:
    def __init__(self):
        self.logger = logging.getLogger('FTPAutoTasks')
        self.logger.setLevel(logging.DEBUG)
        
        # 创建日志目录
        log_dir = os.path.join('logs', 'system')
        os.makedirs(log_dir, exist_ok=True)
        
        # 设置日志文件名（按日期）
        log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y%m%d')}.log")
        
        # 文件处理器
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # 格式化器
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)

    def log_exception(self, exctype, value, tb):
        """记录异常信息"""
        import traceback
        exc_info = ''.join(traceback.format_exception(exctype, value, tb))
        self.logger.error(f"未捕获的异常:\n{exc_info}")

system_logger = SystemLogger()