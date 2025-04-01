import sys
from PyQt5.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
                            QTableWidgetItem, QComboBox, QDateEdit, QPushButton,
                            QLabel)
from PyQt5.QtCore import Qt, QDate
import os
from datetime import datetime

class LogDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("日志查询")
        self.setGeometry(200, 200, 800, 600)
        self.setupUI()
        
    def setupUI(self):
        layout = QVBoxLayout()
        
        # 查询条件区域
        query_layout = QHBoxLayout()
        
        # 任务选择下拉框
        self.task_combo = QComboBox()
        self.task_combo.addItems(["所有任务"])  # 后续从任务列表加载
        query_layout.addWidget(QLabel("任务:"))
        query_layout.addWidget(self.task_combo)
        
        # 日期选择
        self.date_select = QDateEdit()
        self.date_select.setDate(QDate.currentDate())
        self.date_select.setCalendarPopup(True)
        query_layout.addWidget(QLabel("日期:"))
        query_layout.addWidget(self.date_select)
        
        # 查询按钮
        self.query_btn = QPushButton("查询")
        self.query_btn.clicked.connect(self.perform_query)
        query_layout.addWidget(self.query_btn)
        
        query_layout.addStretch()
        layout.addLayout(query_layout)
        
        # 日志列表
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(4)
        self.log_table.setHorizontalHeaderLabels(["发送时间", "文件名", "文件大小", "重试次数"])
        self.log_table.setColumnWidth(0, 150)  # 发送时间列宽
        self.log_table.setColumnWidth(1, 350)  # 文件名列宽
        self.log_table.setColumnWidth(2, 100)  # 文件大小列宽
        self.log_table.setColumnWidth(3, 100)  # 重试次数列宽
        layout.addWidget(self.log_table)
        
        # 统计信息
        self.stats_label = QLabel()
        layout.addWidget(self.stats_label)
        
        self.setLayout(layout)

    def perform_query(self):
        """执行日志查询"""
        selected_date = self.date_select.date().toString("yyyyMM")
        selected_task = self.task_combo.currentText()
        
        # 清空现有数据
        self.log_table.setRowCount(0)
        
        # 读取日志文件
        log_dir = os.path.join("logs", selected_date)
        if not os.path.exists(log_dir):
            return
        
        total_files = 0
        for log_file in os.listdir(log_dir):
            if not log_file.endswith(".log"):
                continue
                
            with open(os.path.join(log_dir, log_file), "r", encoding="utf-8") as f:
                for line in f:
                    # 解析日志行
                    try:
                        log_data = self.parse_log_line(line)
                        if selected_task != "所有任务" and log_data["task"] != selected_task:
                            continue
                            
                        row = self.log_table.rowCount()
                        self.log_table.insertRow(row)
                        self.log_table.setItem(row, 0, QTableWidgetItem(log_data["time"]))
                        self.log_table.setItem(row, 1, QTableWidgetItem(log_data["filename"]))
                        self.log_table.setItem(row, 2, QTableWidgetItem(log_data["size"]))
                        self.log_table.setItem(row, 3, QTableWidgetItem(str(log_data["retries"])))
                        total_files += 1
                    except:
                        continue
        
        # 更新统计信息
        self.stats_label.setText(f"总计发送文件数: {total_files}")

    def parse_log_line(self, line):
        """解析日志行内容"""
        # 示例日志格式：[2024-03-31 10:30:15] [TaskName] filename.txt (1.5MB) Retries: 2
        # 实际项目中需要根据真实的日志格式进行解析
        parts = line.strip().split("] ")
        time = parts[0][1:]
        task = parts[1][1:]
        remaining = parts[2].split(" ")
        
        return {
            "time": time,
            "task": task,
            "filename": remaining[0],
            "size": remaining[1].strip("()"),
            "retries": int(remaining[3])
        }

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = LogDialog()
    dialog.exec_()