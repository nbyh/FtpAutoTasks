import sys
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QPushButton, 
                            QVBoxLayout, QHBoxLayout, QWidget, QLabel, QTextEdit,
                            QMessageBox, QStatusBar, QSystemTrayIcon, QMenu, QProgressBar, QHeaderView)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QIcon
import os
import logging
# 修改相对导入为绝对导入
# 设置系统日志记录器
system_logger = logging.getLogger("system_logger")
system_logger.setLevel(logging.ERROR)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
system_logger.addHandler(handler)
# 修改相对导入为绝对导入
from core.task_manager import FTPTaskManager
from models.task import FTPTask
from utils.config import ConfigManager
from ui.config_dialog import ConfigDialog
from ui.log_dialog import LogDialog
import queue

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FTP Auto Sender")
        self.setGeometry(100, 100, 800, 600)
        self.tasks = []  # 初始化任务列表
        self.task_manager = FTPTaskManager()
        self.config_manager = ConfigManager()
        self.initUI()
        self.setupTrayIcon()
        self.setupTimer()
        self.load_tasks()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_send_count)
        self.update_timer.start(60000)  # 每分钟更新一次发送计数

    def initUI(self):
        # 创建中心部件
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        self.setCentralWidget(central_widget)
        central_widget.setLayout(main_layout)
        
        # 第一行：任务列表
        self.task_table = QTableWidget()
        self.task_table.setColumnCount(5)
        self.task_table.setHorizontalHeaderLabels([
            "任务名称", "FTP地址", "文件类型", "最近发送时间", "最近发送文件"
        ])
        # 设置表格为只读
        self.task_table.setEditTriggers(QTableWidget.NoEditTriggers)
        # 设置整行选择
        self.task_table.setSelectionBehavior(QTableWidget.SelectRows)
        # 设置单行选择
        self.task_table.setSelectionMode(QTableWidget.SingleSelection)
        
        header = self.task_table.horizontalHeader()
        for i in range(5):
            header.setSectionResizeMode(i, QHeaderView.Stretch)
        main_layout.addWidget(self.task_table, stretch=4)
        
        # 第二行：按钮组
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        # 设置按钮组居中显示
        button_layout.setAlignment(Qt.AlignCenter)
        # 增加按钮组的上下边距
        button_layout.setContentsMargins(0, 10, 0, 10)
        
        # 定义按钮样式
        button_style = """
            QPushButton {
                min-width: 150px;
                min-height: 35px;
                font-size: 14px;
                padding: 5px;
                margin: 0 10px;
            }
        """
        
        self.start_button = QPushButton("全部开始")
        self.stop_button = QPushButton("全部停止")
        self.config_button = QPushButton("任务配置")
        self.exit_button = QPushButton("退出程序")
        
        for btn in [self.start_button, self.stop_button, self.config_button, self.exit_button]:
            btn.setStyleSheet(button_style)
            button_layout.addWidget(btn)
        
        main_layout.addWidget(button_widget, stretch=1)
        
        # 第三行：发送记录
        self.send_log = QTextEdit()
        self.send_log.setReadOnly(True)
        main_layout.addWidget(self.send_log, stretch=3)
        
        # 第四行：状态栏
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        
        self.files_count_label = QLabel("过去1小时发送文件数: 0")
        self.files_count_label.setMinimumWidth(200)
        status_bar.addWidget(self.files_count_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(500)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("")
        status_bar.addWidget(self.progress_bar)
        
        self.datetime_label = QLabel()
        status_bar.addPermanentWidget(self.datetime_label)
        
        # 连接信号
        self.setup_connections()

    def setup_connections(self):
        """设置信号连接"""
        self.start_button.clicked.connect(self.start_tasks)
        self.stop_button.clicked.connect(self.stop_tasks)
        self.config_button.clicked.connect(self.open_config_dialog)
        self.exit_button.clicked.connect(self.handle_exit)

    def setupTimer(self):
        # 更新时间的定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateDateTime)
        self.timer.start(1000)  # 每秒更新一次
        
        # 添加定时器更新进度和网络状态
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(1000)  # 每秒更新

    def setupTrayIcon(self):
        """设置系统托盘图标"""
        # 系统托盘
        tray_icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                 'resources', 'icons', 'tray.png')
        icon = QIcon(tray_icon_path) if os.path.exists(tray_icon_path) else QIcon()
        
        self.tray_icon = QSystemTrayIcon(icon, self)
        
        # 设置托盘菜单
        tray_menu = QMenu()
        show_action = tray_menu.addAction("显示主窗口")
        show_action.triggered.connect(self.show_main_window)
        tray_menu.addSeparator()
        quit_action = tray_menu.addAction("退出程序")
        quit_action.triggered.connect(self.handle_exit)
        self.tray_icon.setContextMenu(tray_menu)
        
        # 连接双击信号
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        
        self.tray_icon.show()

    def on_tray_icon_activated(self, reason):
        """处理托盘图标激活事件"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_main_window()

    def show_main_window(self):
        """显示主窗口"""
        self.show()
        self.activateWindow()  # 激活窗口
        self.raise_()  # 将窗口置于最前

    def updateDateTime(self):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.datetime_label.setText(current_time)

    def load_tasks(self):
        """加载任务配置"""
        try:
            tasks_config = self.config_manager.load_tasks()
            for task_data in tasks_config["tasks"]:
                # 处理密码字段
                if "_password" in task_data:
                    password = task_data.pop("_password")
                    task_data["password"] = password
                
                task = FTPTask(**task_data)
                self.tasks.append(task)

            self.updateTaskList()
        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载任务配置失败: {str(e)}")
            # 记录详细错误信息到日志
            system_logger.error(f"加载任务配置失败: {str(e)}", exc_info=True)

    def start_tasks(self):
        """启动所有已启用的任务"""
        for task in self.tasks:
            if task.enabled:
                try:
                    self.task_manager.start_task(task.name)
                    self.add_send_log(f"任务 '{task.name}' 已启动")
                except Exception as e:
                    self.add_send_log(f"任务 '{task.name}' 启动失败: {str(e)}")
        self.updateTaskList()

    def stop_tasks(self):
        """停止所有任务"""
        for task in self.tasks:
            try:
                self.task_manager.stop_task(task.name)
                self.add_send_log(f"任务 '{task.name}' 已停止")
            except Exception as e:
                self.add_send_log(f"任务 '{task.name}' 停止失败: {str(e)}")
        self.updateTaskList()

    def update_send_count(self):
        """更新过去1小时发送文件数"""
        try:
            count = self.task_manager.get_recent_send_count()
            self.files_count_label.setText(f"过去1小时发送文件数: {count}")
        except Exception as e:
            print(f"更新发送计数失败: {str(e)}")

    def update_status(self):
        """更新进度显示"""
        try:
            # 更新传输进度
            while not self.task_manager.progress_queue.empty():
                progress_data = self.task_manager.progress_queue.get_nowait()
                task_name = progress_data['task_name']
                progress = progress_data['progress']
                
                # 更新进度条
                self.progress_bar.setValue(progress['percentage'])
                self.progress_bar.setFormat(
                    f"{task_name}: {progress['filename']} - {progress['percentage']}%"
                )
                
                # 当传输完成时清空进度条
                if progress['percentage'] == 100:
                    QTimer.singleShot(2000, self.reset_progress_bar)
                    
        except queue.Empty:
            pass
        except Exception as e:
            print(f"更新进度显示时出错: {str(e)}")

    def reset_progress_bar(self):
        """重置进度条"""
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("")

    def updateTaskList(self):
        """更新任务列表显示"""
        self.task_table.setRowCount(0)
        for task in self.tasks:
            row = self.task_table.rowCount()
            self.task_table.insertRow(row)
            
            # 设置任务信息
            items = [
                QTableWidgetItem(task.name),
                QTableWidgetItem(task.ftp_address),
                QTableWidgetItem(", ".join(task.file_types)),
                QTableWidgetItem(task.last_send_time if hasattr(task, 'last_send_time') else ""),
                QTableWidgetItem(task.last_file if hasattr(task, 'last_file') else "")
            ]
            
            # 设置颜色
            color = QColor('black')
            if not task.enabled:
                color = QColor('gray')
            elif task.status == 'running':
                color = QColor('blue')
            elif task.status == 'error':
                color = QColor('red')
            elif task.status == 'enabled':
                color = QColor('green')
            
            # 应用颜色和提示信息
            for col, item in enumerate(items):
                item.setForeground(color)
                if task.last_error:
                    item.setToolTip(f"最后错误: {task.last_error}")
                self.task_table.setItem(row, col, item)

    def closeEvent(self, event):
        """窗口关闭事件处理"""
        if self.tray_icon.isVisible():
            self.hide()
            self.tray_icon.showMessage(
                "FTP自动发送程序",
                "程序已最小化到系统托盘",
                QSystemTrayIcon.Information,
                2000
            )
            event.ignore()
        else:
            self.handle_exit()

    def handle_exit(self):
        """处理退出程序"""
        reply = QMessageBox.question(
            self, 
            '确认退出',
            "是否确认退出程序？\n这将停止所有正在运行的任务。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 停止所有任务
            self.stop_tasks()
            # 调用清理方法
            self.cleanup()
            # 退出程序
            QApplication.quit()

    def cleanup(self):
        """程序退出时清理资源"""
        try:
            # 停止所有任务
            self.stop_tasks()
            
            # 停止所有定时器
            if hasattr(self, 'update_timer'):
                self.update_timer.stop()
            
            # 关闭任务管理器
            if hasattr(self, 'task_manager'):
                self.task_manager.cleanup()
                
            # 关闭日志文件
            if hasattr(self, 'logger'):
                self.logger.close()
                
        except Exception as e:
            print(f"清理资源时出错: {str(e)}")

    def open_config_dialog(self):
        """打开任务配置对话框"""
        dialog = ConfigDialog(self, tasks=self.tasks)
        if dialog.exec_():
            # 更新任务列表
            self.tasks = dialog.get_tasks()
            # 更新任务管理器
            self.task_manager.update_tasks(self.tasks)
            # 更新界面显示
            self.updateTaskList()

    def open_log_dialog(self):
        dialog = LogDialog(self)
        dialog.exec_()

    def add_send_log(self, message: str):
        """添加发送日志到界面"""
        current_time = datetime.now().strftime("%yy-%m-%d %H:%M:%S")
        self.send_log.append(f"[{current_time}] {message}")
        # 限制显示最新的1000条记录
        if self.send_log.document().lineCount() > 1000:
            cursor = self.send_log.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.movePosition(cursor.Down, cursor.KeepAnchor)
            cursor.removeSelectedText()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())