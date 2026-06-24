"""
抖音评论抓取工具 - 入口文件
"""
import sys
import traceback

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtGui import QFont


def excepthook(exc_type, exc_value, exc_tb):
    """全局异常兜底，防止静默崩溃"""
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    try:
        QMessageBox.critical(None, "未处理的异常", f"程序遇到未处理的异常:\n\n{tb[:1000]}")
    except Exception:
        pass
    print(f"[FATAL] {tb}", file=sys.stderr)


sys.excepthook = excepthook


def main():
    app = QApplication(sys.argv)

    # 设置全局字体
    font = QFont("Microsoft YaHei UI", 10)
    app.setFont(font)

    # 设置应用程序属性
    app.setApplicationName("抖音评论抓取工具")
    app.setApplicationVersion("1.0.0")

    # 创建主窗口
    from ui.main_window import MainWindow
    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
