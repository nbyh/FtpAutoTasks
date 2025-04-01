import sys
from PyQt5.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QHeaderView, QMessageBox,
                             QFileDialog, QMenu, QListWidget, QListWidgetItem)  # 添加 QListWidgetItem
from PyQt5.QtCore import Qt
import json
from models.task import FTPTask
from ui.task_edit_dialog import TaskEditDialog
from utils.config import ConfigManager  # 添加导入

class ConfigDialog(QDialog):
    def __init__(self, parent=None, tasks=None):
        super().__init__(parent)
        self.config_manager = ConfigManager()
        
        # 如果没有传入任务列表，则从配置文件加载
        if tasks is None:
            try:
                config = self.config_manager.load_tasks()
                self.tasks = [FTPTask.from_dict(task_data) for task_data in config.get('tasks', [])]
            except Exception as e:
                QMessageBox.warning(self, "错误", f"加载配置失败: {str(e)}")
                self.tasks = []
        else:
            self.tasks = tasks.copy() if tasks else []
            
        self.setWindowTitle("FTP任务配置")
        self.setMinimumSize(800, 600)
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        
        # 工具栏
        toolbar = QHBoxLayout()
        self.add_btn = QPushButton("添加任务")
        self.edit_btn = QPushButton("编辑任务")
        self.delete_btn = QPushButton("删除任务")
        self.import_btn = QPushButton("导入配置")
        self.export_btn = QPushButton("导出配置")
        
        self.add_btn.clicked.connect(self.add_task)
        self.edit_btn.clicked.connect(self.edit_task)
        self.delete_btn.clicked.connect(self.delete_task)
        self.import_btn.clicked.connect(self.import_config)
        self.export_btn.clicked.connect(self.export_config)
        
        toolbar.addWidget(self.add_btn)
        toolbar.addWidget(self.edit_btn)
        toolbar.addWidget(self.delete_btn)
        toolbar.addStretch()
        toolbar.addWidget(self.import_btn)
        toolbar.addWidget(self.export_btn)
        
        layout.addLayout(toolbar)
        
        # 任务列表表格
        self.task_table = QTableWidget()
        self.task_table.setColumnCount(7)
        self.task_table.setHorizontalHeaderLabels([
            "任务名称", "状态", "FTP地址", "远程目录", 
            "本地目录", "文件类型", "发送模式"
        ])
        
        # 设置表格为只读
        self.task_table.setEditTriggers(QTableWidget.NoEditTriggers)
        # 设置整行选择
        self.task_table.setSelectionBehavior(QTableWidget.SelectRows)
        # 设置单行选择
        self.task_table.setSelectionMode(QTableWidget.SingleSelection)
        
        # 设置列宽
        self.task_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.task_table.horizontalHeader().setStretchLastSection(True)
        # 双击编辑
        self.task_table.doubleClicked.connect(self.edit_task)
        # 右键菜单
        self.task_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.task_table.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.task_table)
        
        # 底部按钮
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        cancel_btn = QPushButton("取消")
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        
        # 加载任务数据
        self.load_tasks()
        
    def load_tasks(self):
        """加载任务到表格"""
        self.task_table.setRowCount(len(self.tasks))
        for row, task in enumerate(self.tasks):
            self.task_table.setItem(row, 0, QTableWidgetItem(task.name))
            self.task_table.setItem(row, 1, QTableWidgetItem("启用" if task.enabled else "禁用"))
            self.task_table.setItem(row, 2, QTableWidgetItem(task.ftp_address))
            self.task_table.setItem(row, 3, QTableWidgetItem(task.remote_dir))
            self.task_table.setItem(row, 4, QTableWidgetItem(task.local_dir))
            self.task_table.setItem(row, 5, QTableWidgetItem(";".join(task.file_types)))
            self.task_table.setItem(row, 6, QTableWidgetItem(
                "定时发送" if task.send_mode == "scheduled" else "立即发送"
            ))
            
    def add_task(self):
        """添加新任务"""
        dialog = TaskEditDialog(None, self)
        if dialog.exec_():
            task_data = dialog.get_task_data()
            new_task = FTPTask(**task_data)
            self.tasks.append(new_task)
            self.load_tasks()
            
    def edit_task(self):
        """编辑选中的任务"""
        current_row = self.task_table.currentRow()
        if current_row < 0:
            return
            
        task = self.tasks[current_row]
        dialog = TaskEditDialog(task, self)
        if dialog.exec_():
            task_data = dialog.get_task_data()
            for key, value in task_data.items():
                setattr(task, key, value)
            self.load_tasks()
            
    def delete_task(self):
        """删除选中的任务"""
        current_row = self.task_table.currentRow()
        if current_row < 0:
            return
            
        reply = QMessageBox.question(
            self, 
            '确认删除', 
            "确定要删除选中的任务吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.tasks.pop(current_row)
            self.load_tasks()
            
    def import_config(self):
        """导入任务配置"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择配置文件",
            "",
            "JSON files (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                new_tasks = []
                for task_data in data.get('tasks', []):
                    new_tasks.append(FTPTask(**task_data))
                self.tasks = new_tasks
                self.load_tasks()
                QMessageBox.information(self, "成功", "配置导入成功")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"导入失败: {str(e)}")
                
    def export_config(self):
        """导出任务配置"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存配置文件",
            "",
            "JSON files (*.json)"
        )
        
        if file_path:
            try:
                tasks_data = []
                for task in self.tasks:
                    task_dict = task.__dict__.copy()
                    task_dict.pop('_password', None)  # 移除敏感信息
                    tasks_data.append(task_dict)
                    
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump({'tasks': tasks_data}, f, indent=2, ensure_ascii=False)
                QMessageBox.information(self, "成功", "配置导出成功")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"导出失败: {str(e)}")
                
    def show_context_menu(self, pos):
        """显示右键菜单"""
        menu = QMenu(self)
        menu.addAction("编辑任务", self.edit_task)
        menu.addAction("删除任务", self.delete_task)
        menu.addSeparator()
        menu.addAction("启用任务", lambda: self.toggle_task_state(True))
        menu.addAction("禁用任务", lambda: self.toggle_task_state(False))
        menu.exec_(self.task_table.viewport().mapToGlobal(pos))
        
    def toggle_task_state(self, enabled):
        """切换任务状态"""
        current_row = self.task_table.currentRow()
        if current_row >= 0:
            self.tasks[current_row].enabled = enabled
            self.load_tasks()
            
    def get_tasks(self):
        """获取修改后的任务列表"""
        return self.tasks

    def accept(self):
        """保存按钮点击处理"""
        try:
            # 保存任务配置
            self.config_manager.save_tasks({"tasks": [
                task.to_dict() for task in self.tasks
            ]})
            QMessageBox.information(self, "成功", "任务配置已保存")
            super().accept()  # 调用父类的 accept 方法关闭对话框
        except Exception as e:
            QMessageBox.warning(self, "错误", f"保存失败: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    tasks = []  # 初始化任务列表
    dialog = ConfigDialog(tasks=tasks)
    dialog.exec_()