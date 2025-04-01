class FTPTask:
    def __init__(self, name, enabled=True, ftp_address='', username='', password='',
                 remote_dir='', local_dir='', file_types=None,
                 send_mode='immediate', schedule_interval=None, 
                 delay_after_generation=None, retry_count=3, retry_interval=60,
                 status='enabled', last_error=None, last_run_time=None):  # 添加新参数
        self.name = name
        self.enabled = enabled
        self.ftp_address = ftp_address
        self.username = username
        self._password = password  # 使用下划线前缀表示这是私有属性
        self.remote_dir = remote_dir
        self.local_dir = local_dir
        self.file_types = file_types or ['*.*']
        self.send_mode = send_mode  # 'immediate' or 'scheduled'
        self.schedule_interval = schedule_interval  # 定时发送间隔（分钟）
        self.delay_after_generation = delay_after_generation  # 立即发送时的延迟时间（秒）
        self.retry_count = retry_count
        self.retry_interval = retry_interval  # 重试间隔（秒）
        self.status = status  # 任务状态
        self.last_error = last_error  # 最后错误信息
        self.last_run_time = last_run_time  # 最后运行时间

    @property
    def password(self):
        """密码属性getter"""
        return self._password

    @password.setter
    def password(self, value):
        """密码属性setter"""
        self._password = value

    @classmethod
    def from_dict(cls, data):
        """从字典创建任务实例"""
        # 处理密码字段
        if '_password' in data:
            data['password'] = data.pop('_password')
        return cls(**data)

    def to_dict(self):
        """转换为字典，用于序列化"""
        return {
            'name': self.name,
            'enabled': self.enabled,
            'ftp_address': self.ftp_address,
            'username': self.username,
            'password': self._password,  # 注意这里使用 password 而不是 _password
            'remote_dir': self.remote_dir,
            'local_dir': self.local_dir,
            'file_types': self.file_types,
            'send_mode': self.send_mode,
            'schedule_interval': self.schedule_interval,
            'delay_after_generation': self.delay_after_generation,
            'retry_count': self.retry_count,
            'retry_interval': self.retry_interval,
            'status': self.status,
            'last_error': self.last_error,
            'last_run_time': self.last_run_time
        }

    def validate(self):
        """验证任务配置的有效性"""
        if not self.name:
            raise ValueError("任务名称不能为空")
        if not self.ftp_address:
            raise ValueError("FTP地址不能为空")
        if not self.username:
            raise ValueError("用户名不能为空")
        if not self.remote_dir:
            raise ValueError("远程目录不能为空")
        if not self.local_dir:
            raise ValueError("本地目录不能为空")
        if not self.file_types:
            raise ValueError("文件类型不能为空")
        if self.send_mode == 'scheduled' and not self.schedule_interval:
            raise ValueError("定时发送模式必须设置时间间隔")
        if self.retry_count < 0:
            raise ValueError("重试次数不能为负数")
        if self.retry_interval < 0:
            raise ValueError("重试间隔不能为负数")