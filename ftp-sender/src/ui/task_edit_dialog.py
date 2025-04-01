from PyQt5.QtWidgets import (QDialog, QLineEdit, QCheckBox, QComboBox, QSpinBox,
                           QLabel, QGridLayout, QHBoxLayout, QPushButton,
                           QFileDialog, QWidget)

class TaskEditDialog(QDialog):
    def __init__(self, task=None, parent=None):
        super().__init__(parent)
        self.task = task
        self.setWindowTitle("编辑任务" if task else "新建任务")
        self.setMinimumWidth(500)
        self.init_ui()
        if task:
            self.load_task_data()

    def init_ui(self):
        layout = QGridLayout()
        row = 0

        # 基本信息
        layout.addWidget(QLabel("启用任务:"), row, 0)
        self.enabled_cb = QCheckBox()
        self.enabled_cb.setChecked(True)
        layout.addWidget(self.enabled_cb, row, 1)
        row += 1

        layout.addWidget(QLabel("任务名称:"), row, 0)
        self.name_edit = QLineEdit()
        layout.addWidget(self.name_edit, row, 1)
        row += 1

        # FTP配置
        layout.addWidget(QLabel("FTP地址:"), row, 0)
        self.ftp_address_edit = QLineEdit()
        layout.addWidget(self.ftp_address_edit, row, 1)
        row += 1

        layout.addWidget(QLabel("用户名:"), row, 0)
        self.username_edit = QLineEdit()
        layout.addWidget(self.username_edit, row, 1)
        row += 1

        layout.addWidget(QLabel("密码:"), row, 0)
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_edit, row, 1)
        row += 1

        # 目录配置
        layout.addWidget(QLabel("远程目录:"), row, 0)
        self.remote_dir_edit = QLineEdit()
        layout.addWidget(self.remote_dir_edit, row, 1)
        row += 1

        layout.addWidget(QLabel("本地目录:"), row, 0)
        local_dir_layout = QHBoxLayout()
        self.local_dir_edit = QLineEdit()
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.clicked.connect(self.browse_local_dir)
        local_dir_layout.addWidget(self.local_dir_edit)
        local_dir_layout.addWidget(self.browse_btn)
        layout.addLayout(local_dir_layout, row, 1)
        row += 1

        # 文件类型
        layout.addWidget(QLabel("文件类型:"), row, 0)
        self.file_types_edit = QLineEdit()
        self.file_types_edit.setPlaceholderText("示例: *.txt;*.jpg;*.pdf")
        layout.addWidget(self.file_types_edit, row, 1)
        row += 1

        # 发送模式
        layout.addWidget(QLabel("发送模式:"), row, 0)
        self.send_mode_combo = QComboBox()
        self.send_mode_combo.addItems(["立即发送", "定时发送"])
        self.send_mode_combo.currentTextChanged.connect(self.on_send_mode_changed)
        layout.addWidget(self.send_mode_combo, row, 1)
        row += 1

        # 定时发送配置
        self.scheduled_widget = QWidget()
        scheduled_layout = QHBoxLayout()
        scheduled_layout.addWidget(QLabel("定时间隔(分钟):"))
        self.schedule_interval_spin = QSpinBox()
        self.schedule_interval_spin.setRange(1, 1440)  # 1分钟到24小时
        self.schedule_interval_spin.setValue(60)
        scheduled_layout.addWidget(self.schedule_interval_spin)
        scheduled_layout.addStretch()
        self.scheduled_widget.setLayout(scheduled_layout)
        layout.addWidget(self.scheduled_widget, row, 1)
        row += 1

        # 立即发送配置
        self.immediate_widget = QWidget()
        immediate_layout = QHBoxLayout()
        immediate_layout.addWidget(QLabel("延迟发送(秒):"))
        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(0, 3600)  # 0-3600秒
        immediate_layout.addWidget(self.delay_spin)
        immediate_layout.addStretch()
        self.immediate_widget.setLayout(immediate_layout)
        layout.addWidget(self.immediate_widget, row, 1)
        row += 1

        # 重试设置
        retry_layout = QHBoxLayout()
        retry_layout.addWidget(QLabel("重试次数:"))
        self.retry_count_spin = QSpinBox()
        self.retry_count_spin.setRange(0, 10)
        retry_layout.addWidget(self.retry_count_spin)
        retry_layout.addWidget(QLabel("重试间隔(秒):"))
        self.retry_interval_spin = QSpinBox()
        self.retry_interval_spin.setRange(1, 3600)
        retry_layout.addWidget(self.retry_interval_spin)
        retry_layout.addStretch()
        layout.addLayout(retry_layout, row, 1)
        row += 1

        # 确定取消按钮
        button_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        cancel_btn = QPushButton("取消")
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout, row, 0, 1, 2)

        self.setLayout(layout)
        self.on_send_mode_changed(self.send_mode_combo.currentText())

    def browse_local_dir(self):
        """选择本地目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择本地目录")
        if dir_path:
            self.local_dir_edit.setText(dir_path)

    def on_send_mode_changed(self, mode):
        """发送模式切换处理"""
        is_scheduled = mode == "定时发送"
        self.scheduled_widget.setVisible(is_scheduled)
        self.immediate_widget.setVisible(not is_scheduled)

    def load_task_data(self):
        """加载任务数据到界面"""
        self.name_edit.setText(self.task.name)
        self.enabled_cb.setChecked(self.task.enabled)
        self.ftp_address_edit.setText(self.task.ftp_address)
        self.username_edit.setText(self.task.username)
        self.password_edit.setText(self.task.password)
        self.remote_dir_edit.setText(self.task.remote_dir)
        self.local_dir_edit.setText(self.task.local_dir)
        self.file_types_edit.setText(";".join(self.task.file_types))
        
        is_scheduled = self.task.send_mode == "scheduled"
        self.send_mode_combo.setCurrentText("定时发送" if is_scheduled else "立即发送")
        
        if is_scheduled and self.task.schedule_interval:
            self.schedule_interval_spin.setValue(self.task.schedule_interval)
        elif not is_scheduled and self.task.delay_after_generation:
            self.delay_spin.setValue(self.task.delay_after_generation)
            
        self.retry_count_spin.setValue(self.task.retry_count)
        self.retry_interval_spin.setValue(self.task.retry_interval)

    def get_task_data(self):
        """获取界面数据"""
        file_types = [x.strip() for x in self.file_types_edit.text().split(";") if x.strip()]
        is_scheduled = self.send_mode_combo.currentText() == "定时发送"
        
        return {
            "name": self.name_edit.text(),
            "enabled": self.enabled_cb.isChecked(),
            "ftp_address": self.ftp_address_edit.text(),
            "username": self.username_edit.text(),
            "password": self.password_edit.text(),
            "remote_dir": self.remote_dir_edit.text(),
            "local_dir": self.local_dir_edit.text(),
            "file_types": file_types,
            "send_mode": "scheduled" if is_scheduled else "immediate",
            "schedule_interval": self.schedule_interval_spin.value() if is_scheduled else None,
            "delay_after_generation": self.delay_spin.value() if not is_scheduled else None,
            "retry_count": self.retry_count_spin.value(),
            "retry_interval": self.retry_interval_spin.value()
        }