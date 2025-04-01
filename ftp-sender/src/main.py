import sys
import os
from utils.logger import system_logger
from utils.singleton import SingleInstance

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

# 确保配置和日志目录存在
if not os.path.exists('config'):
    os.makedirs('config')
if not os.path.exists('logs'):
    os.makedirs('logs')

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from ui.main_window import MainWindow

def excepthook(exctype, value, traceback):
    """全局异常处理"""
    # 记录异常到日志文件
    system_logger.log_exception(exctype, value, traceback)
    # 调用默认异常处理
    sys.__excepthook__(exctype, value, traceback)

sys.excepthook = excepthook

def main():
    # 单例检查
    with SingleInstance():
        app = QApplication(sys.argv)
        
        # 设置应用程序图标
        icon_path = os.path.join(current_dir, 'resources', 'icons', 'app.png')
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
        
        mainWin = MainWindow()
        # 确保程序退出时清理资源
        app.aboutToQuit.connect(mainWin.cleanup)
        mainWin.show()
        sys.exit(app.exec_())

if __name__ == "__main__":
    main()