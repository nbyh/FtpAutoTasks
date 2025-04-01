import os
import time
import json
import socket
from datetime import datetime, timedelta
import ftplib
import threading
import queue
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from utils.logger import Logger
from models.task import FTPTask
from models.task_status import TaskStatus

class FTPTaskManager:
    def __init__(self):
        self.tasks = {}
        self.observers = {}
        self.timers = {}
        self.logger = Logger()
        self.running = False
        self.task_statuses = {}
        self.last_send_times = {}
        self.transfer_progress = {}  # 存储传输进度
        self.network_status = True   # 网络状态标志
        self.progress_queue = queue.Queue()  # 进度更新队列
        
        # 启动网络监控
        self.network_monitor = threading.Thread(target=self._monitor_network)
        self.network_monitor.daemon = True
        self.network_monitor.start()
        
        # 启动清理定时器
        self.cleanup_timer = threading.Timer(3600, self._cleanup_old_records)
        self.cleanup_timer.daemon = True
        self.cleanup_timer.start()
        
    def add_task(self, task: FTPTask):
        """添加任务"""
        self.tasks[task.name] = task
        if task.enabled:
            self.start_task(task.name)
            
    def start_task(self, task_name):
        """启动任务"""
        task = self.tasks.get(task_name)
        if not task or not task.enabled:
            return
            
        if task.send_mode == "scheduled":
            # 定时发送模式
            timer = threading.Timer(task.schedule_interval * 60, 
                                 self._scheduled_send, 
                                 args=(task_name,))
            timer.daemon = True
            timer.start()
            self.timers[task_name] = timer
        else:
            # 即时发送模式
            observer = Observer()
            event_handler = FileChangeHandler(self, task)
            observer.schedule(event_handler, task.local_dir, recursive=False)
            observer.start()
            self.observers[task_name] = observer
            
    def stop_task(self, task_name):
        """停止任务"""
        if task_name in self.observers:
            self.observers[task_name].stop()
            self.observers[task_name].join()
            del self.observers[task_name]
            
        if task_name in self.timers:
            self.timers[task_name].cancel()
            del self.timers[task_name]
            
    def pause_task(self, task_name):
        """暂停任务但保持启用状态"""
        task = self.tasks.get(task_name)
        if not task:
            return
        
        self.stop_task(task_name)
        task.enabled = True
        self.update_task_status(task_name, TaskStatus.ENABLED)

    def resume_task(self, task_name):
        """恢复暂停的任务"""
        task = self.tasks.get(task_name)
        if not task or not task.enabled:
            return
            
        self.start_task(task_name)

    def restart_task(self, task_name):
        """重启任务"""
        self.stop_task(task_name)
        self.start_task(task_name)

    def check_task_health(self, task_name):
        """检查任务健康状态"""
        task = self.tasks.get(task_name)
        if not task:
            return False
            
        status = self.get_task_status(task_name)
        
        # 检查最后更新时间
        if 'last_update' in status:
            last_update = datetime.strptime(status['last_update'], "%Y-%m-%d %H:%M:%S")
            if datetime.now() - last_update > timedelta(hours=1):
                self.update_task_status(task_name, TaskStatus.ERROR, "任务可能已停止响应")
                return False
                
        # 检查错误次数
        error_count = status.get('error_count', 0)
        if error_count > 10:  # 连续错误超过10次
            self.update_task_status(task_name, TaskStatus.ERROR, "错误次数过多")
            return False
            
        return True

    def handle_task_error(self, task_name, error):
        """处理任务错误"""
        status = self.get_task_status(task_name)
        current_errors = status.get('error_count', 0)
        
        self.task_statuses[task_name].update({
            'error_count': current_errors + 1,
            'last_error': str(error),
            'last_error_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        # 如果错误次数过多，暂停任务
        if current_errors + 1 >= 10:
            self.pause_task(task_name)
            self.logger.log_error(task_name, "task_paused", "错误次数过多，任务已暂停")

    def get_task_statistics(self, task_name):
        """获取任务统计信息"""
        task = self.tasks.get(task_name)
        if not task:
            return {}
            
        status = self.get_task_status(task_name)
        return {
            'status': status.get('status', TaskStatus.UNKNOWN.value),
            'total_files': status.get('total_files', 0),
            'success_count': status.get('success_count', 0),
            'error_count': status.get('error_count', 0),
            'last_success': status.get('last_success'),
            'last_error': status.get('last_error'),
            'last_error_time': status.get('last_error_time')
        }

    def _scheduled_send(self, task_name):
        """定时发送处理"""
        task = self.tasks.get(task_name)
        if not task:
            return
            
        # 扫描目录下的文件
        for filename in os.listdir(task.local_dir):
            if any(filename.endswith(ext) for ext in task.file_types):
                self._send_file(task, filename)
                
        # 重新启动定时器
        self.start_task(task_name)
        
    def _send_file(self, task: FTPTask, filename: str):
        """发送文件，添加进度显示"""
        try:
            local_path = os.path.join(task.local_dir, filename)
            total_size = os.path.getsize(local_path)
            self.transfer_progress[task.name] = {
                'filename': filename,
                'total_size': total_size,
                'transferred': 0,
                'percentage': 0
            }

            def progress_callback(transferred):
                self.transfer_progress[task.name].update({
                    'transferred': transferred,
                    'percentage': int((transferred / total_size) * 100)
                })
                self.progress_queue.put({
                    'task_name': task.name,
                    'progress': self.transfer_progress[task.name]
                })

            retries = 0
            
            # 检查文件是否存在
            if not os.path.exists(local_path):
                self.update_task_status(task.name, 'error', f"文件不存在: {filename}")
                return False
            
            while retries < task.retry_count:
                try:
                    # 检查文件是否被占用
                    if self._is_file_locked(local_path):
                        time.sleep(1)
                        continue
                    
                    # 检查文件大小是否为0
                    if os.path.getsize(local_path) == 0:
                        raise Exception("文件大小为0，可能未完成写入")
                        
                    # 连接FTP
                    with ftplib.FTP(task.ftp_address) as ftp:
                        try:
                            ftp.login(task.username, task.password)
                        except ftplib.error_perm as e:
                            raise Exception(f"FTP登录失败: {str(e)}")
                            
                        try:
                            ftp.cwd(task.remote_dir)
                        except ftplib.error_perm as e:
                            raise Exception(f"切换远程目录失败: {str(e)}")
                        
                        # 上传文件
                        with open(local_path, 'rb') as f:
                            ftp.storbinary(f'STOR {filename}', f, callback=progress_callback)
                            
                    # 记录成功状态
                    self.update_task_status(task.name, 'success')
                    self.last_send_times[task.name] = datetime.now()
                    self.logger.log_success(task.name, filename, retries)
                    self.transfer_progress.pop(task.name, None)
                    return True
                    
                except Exception as e:
                    retries += 1
                    error_msg = f"发送失败 (第{retries}次尝试): {str(e)}"
                    self.update_task_status(task.name, 'error', error_msg)
                    self.logger.log_error(task.name, filename, error_msg)
                    
                    if retries < task.retry_count:
                        time.sleep(task.retry_interval)
                        
            return False
            
        except Exception as e:
            self.logger.log_error(task.name, filename, str(e))
            raise

    def _is_file_locked(self, filepath):
        """检查文件是否被占用"""
        try:
            with open(filepath, 'rb') as f:
                return False
        except:
            return True

    def _cleanup_old_records(self):
        """清理旧的记录"""
        try:
            # 清理24小时前的状态记录
            cutoff_time = datetime.now() - timedelta(hours=24)
            for task_name in list(self.task_statuses.keys()):
                status = self.task_statuses[task_name]
                if 'last_update' in status:
                    last_update = datetime.strptime(status['last_update'], "%Y-%m-%d %H:%M:%S")
                    if last_update < cutoff_time:
                        del self.task_statuses[task_name]
                        
            # 清理1小时前的发送时间记录
            one_hour_ago = datetime.now() - timedelta(hours=1)
            for task_name in list(self.last_send_times.keys()):
                if self.last_send_times[task_name] < one_hour_ago:
                    del self.last_send_times[task_name]
                    
        finally:
            # 重新启动清理定时器
            self.cleanup_timer = threading.Timer(3600, self._cleanup_old_records)
            self.cleanup_timer.daemon = True
            self.cleanup_timer.start()

    def get_task_status(self, task_name):
        """获取任务状态信息"""
        return self.task_statuses.get(task_name, {
            'status': 'unknown',
            'last_error': None,
            'last_success': None,
            'retry_count': 0
        })

    def update_task_status(self, task_name, status, error=None):
        """更新任务状态"""
        if task_name not in self.task_statuses:
            self.task_statuses[task_name] = {}
        
        self.task_statuses[task_name].update({
            'status': status,
            'last_update': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        if error:
            self.task_statuses[task_name]['last_error'] = str(error)
        elif status == 'success':
            self.task_statuses[task_name]['last_success'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def get_recent_send_count(self) -> int:
        """获取过去1小时的发送文件总数"""
        one_hour_ago = datetime.now() - timedelta(hours=1)
        count = 0
        for task_name, last_time in self.last_send_times.items():
            if last_time > one_hour_ago:
                count += 1
        return count

    def get_task_errors(self, task_name):
        """获取任务错误信息"""
        status = self.get_task_status(task_name)
        return {
            'last_error': status.get('last_error'),
            'last_error_time': status.get('last_update') if status.get('status') == 'error' else None
        }

    def get_transfer_progress(self, task_name):
        """获取文件传输进度"""
        return self.transfer_progress.get(task_name)

    def is_network_available(self):
        """获取网络状态"""
        return self.network_status

    def export_tasks(self, filepath):
        """导出任务配置到JSON文件"""
        try:
            tasks_data = []
            for task in self.tasks.values():
                task_dict = task.__dict__.copy()
                task_dict.pop('_password', None)  # 移除敏感信息
                tasks_data.append(task_dict)
                
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({'tasks': tasks_data}, f, indent=2, ensure_ascii=False)
            return True, "导出成功"
        except Exception as e:
            return False, f"导出失败: {str(e)}"

    def import_tasks(self, filepath):
        """从JSON文件导入任务配置"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            imported_count = 0
            for task_data in data.get('tasks', []):
                try:
                    task = FTPTask(**task_data)
                    self.add_task(task)
                    imported_count += 1
                except Exception as e:
                    self.logger.log_error("import", f"导入任务失败: {str(e)}")
                    
            return True, f"成功导入 {imported_count} 个任务"
        except Exception as e:
            return False, f"导入失败: {str(e)}"

    def batch_config(self, task_names, config_updates):
        """批量更新任务配置"""
        try:
            updated_count = 0
            for task_name in task_names:
                if task_name in self.tasks:
                    task = self.tasks[task_name]
                    for key, value in config_updates.items():
                        if hasattr(task, key):
                            setattr(task, key, value)
                    updated_count += 1
            return True, f"已更新 {updated_count} 个任务"
        except Exception as e:
            return False, f"批量配置失败: {str(e)}"

    def update_tasks(self, tasks):
        """更新任务列表"""
        # 停止所有现有任务
        for task_name in list(self.tasks.keys()):
            self.stop_task(task_name)
        
        # 清空现有任务
        self.tasks.clear()
        
        # 添加新任务
        for task in tasks:
            self.add_task(task)

    def cleanup(self):
        """清理任务管理器资源"""
        try:
            # 停止所有观察器
            for observer in self.observers.values():
                observer.stop()
                observer.join()
            
            # 取消所有定时器
            for timer in self.timers.values():
                timer.cancel()
            
            # 停止网络监控线程
            if hasattr(self, 'network_monitor'):
                self.running = False
                self.network_monitor.join(timeout=1)
            
            # 停止清理定时器
            if hasattr(self, 'cleanup_timer'):
                self.cleanup_timer.cancel()
            
        except Exception as e:
            print(f"清理任务管理器资源时出错: {str(e)}")

    def _monitor_network(self):
        """监控网络连接状态"""
        while True:
            try:
                # 测试与FTP服务器的连接
                for task in self.tasks.values():
                    if task.enabled:
                        socket.create_connection((task.ftp_address, 21), timeout=5)
                self.network_status = True
            except:
                self.network_status = False
            time.sleep(60)  # 每分钟检查一次

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, manager, task):
        self.manager = manager
        self.task = task
        
    def on_created(self, event):
        if event.is_directory:
            return
            
        filename = os.path.basename(event.src_path)
        if any(filename.endswith(ext) for ext in self.task.file_types):
            # 延迟发送
            if self.task.delay_after_generation:
                time.sleep(self.task.delay_after_generation)
            self.manager._send_file(self.task, filename)