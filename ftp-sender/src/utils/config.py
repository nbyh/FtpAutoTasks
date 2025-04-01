import json
import os
from utils.encryption import encrypt_password, decrypt_password

import logging
# 修改相对导入为绝对导入
# 设置系统日志记录器
system_logger = logging.getLogger("system_logger")
system_logger.setLevel(logging.ERROR)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
system_logger.addHandler(handler)

class ConfigManager:
    def __init__(self):
        self.config_file = "config/tasks.json"
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

    def load_tasks(self):
        """加载任务配置"""
        if not os.path.exists(self.config_file):
            return {"tasks": []}
            
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # 处理每个任务的数据
            tasks = []
            for task_data in config.get("tasks", []):
                # 解密密码
                if task_data.get("password"):
                    task_data["password"] = decrypt_password(task_data["password"])
                tasks.append(task_data)
                
            return {"tasks": tasks}
        except Exception as e:
            raise Exception(f"读取配置文件失败: {str(e)}")

    def save_tasks(self, tasks):
        """保存任务配置"""
        try:
            # 加密密码
            config_copy = {"tasks": []}
            for task in tasks["tasks"]:
                task_copy = task.copy()
                # 移除运行时状态字段
                task_copy.pop("status", None)
                task_copy.pop("last_error", None)
                task_copy.pop("last_run_time", None)
                
                # 加密密码
                if task_copy.get("password"):
                    task_copy["password"] = encrypt_password(task_copy["password"])
                    
                config_copy["tasks"].append(task_copy)
                
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_copy, f, indent=2, ensure_ascii=False)
        except Exception as e:
            system_logger.error(f"保存任务配置失败: {str(e)}")
            raise