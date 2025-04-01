import os
import datetime

class LogEntry:
    def __init__(self, task_name, file_name, status, retry_count):
        self.timestamp = datetime.datetime.now()
        self.task_name = task_name
        self.file_name = file_name
        self.status = status
        self.retry_count = retry_count

    def __str__(self):
        return f"{self.timestamp} - Task: {self.task_name}, File: {self.file_name}, Status: {self.status}, Retries: {self.retry_count}"

class Logger:
    def __init__(self, log_directory):
        self.log_directory = log_directory
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)

    def log(self, log_entry):
        log_file_path = os.path.join(self.log_directory, f"{log_entry.timestamp.strftime('%Y%m')}.log")
        with open(log_file_path, 'a') as log_file:
            log_file.write(str(log_entry) + '\n')

    def get_logs(self, task_name):
        log_file_path = os.path.join(self.log_directory, f"{datetime.datetime.now().strftime('%Y%m')}.log")
        if not os.path.exists(log_file_path):
            return []

        with open(log_file_path, 'r') as log_file:
            return [line for line in log_file if task_name in line]