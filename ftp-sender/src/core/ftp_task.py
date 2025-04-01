import ftplib
import os
import time
import logging

class FTPTask:
    def __init__(self, name, ftp_address, port=21, username="", password="", 
                 remote_dir="", local_dir="", file_types=None, enabled=False, **kwargs):
        self.name = name
        self.adftp_address = ftp_address
        self.port = port
        self.username = username
        self.password = password
        self.remote_dir = remote_dir
        self.local_dir = local_dir
        self.file_types = file_types or []
        self.enabled = enabled
        self.status = 'stopped'
        self.last_error = None
        self.last_send_time = None
        self.last_file = None

    def connect(self):
        try:
            self.ftp = ftplib.FTP()
            self.ftp.connect(self.host, self.port)
            self.ftp.login(self.username, self.password)
            logging.info(f"Connected to FTP server: {self.host}:{self.port}")
        except Exception as e:
            self.last_error = str(e)
            logging.error(f"Failed to connect to FTP server: {e}")

    def upload_file(self, file_path):
        try:
            with open(file_path, 'rb') as file:
                self.ftp.storbinary(f'STOR {self.remote_dir}/{os.path.basename(file_path)}', file)
                self.last_file = file_path
                self.last_send_time = time.time()
                logging.info(f"Uploaded file: {file_path}")
        except Exception as e:
            self.last_error = str(e)
            logging.error(f"Failed to upload file {file_path}: {e}")

    def execute(self):
        if not self.enabled:
            logging.info(f"Task {self.name} is not enabled.")
            return

        self.connect()
        if self.ftp is None:
            return

        for file_name in os.listdir(self.local_dir):
            if any(file_name.endswith(ext) for ext in self.file_types):
                file_path = os.path.join(self.local_dir, file_name)
                for attempt in range(3):  # Default retry count set to 3
                    self.upload_file(file_path)
                    time.sleep(5)  # Default retry interval set to 5 seconds
                logging.info(f"Completed processing for file: {file_name}")

    def close(self):
        if self.ftp:
            self.ftp.quit()
            logging.info("Disconnected from FTP server.")