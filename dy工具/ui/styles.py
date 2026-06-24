"""
QSS 样式表 - 简洁实用风格（参考 ttkbootstrap cosmo 主题）
"""

MAIN_STYLE = """
/* ===== 全局 ===== */
QMainWindow {
    background-color: #f8f9fa;
}

QWidget {
    font-family: "Microsoft YaHei UI", "PingFang SC", sans-serif;
    color: #212529;
}

QLabel {
    color: #495057;
    font-size: 12px;
}

/* ===== 输入框 ===== */
QLineEdit {
    background-color: #ffffff;
    color: #212529;
    border: 1px solid #ced4da;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 12px;
    selection-background-color: #0d6efd;
    selection-color: white;
}

QLineEdit:focus {
    border-color: #86b7fe;
    outline: none;
}

QLineEdit:hover {
    border-color: #adb5bd;
}

/* ===== 多行输入 ===== */
QTextEdit {
    background-color: #ffffff;
    color: #000000;
    border: 1px solid #ced4da;
    border-radius: 4px;
    padding: 6px 8px;
    font-size: 12px;
}

QTextEdit:focus {
    border-color: #86b7fe;
}

/* ===== 数字输入 ===== */
QSpinBox {
    background-color: #ffffff;
    color: #212529;
    border: 1px solid #ced4da;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}

QSpinBox:focus {
    border-color: #86b7fe;
}

/* ===== 按钮基础 ===== */
QPushButton {
    background-color: #e9ecef;
    color: #495057;
    border: 1px solid #ced4da;
    border-radius: 4px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: normal;
}

QPushButton:hover {
    background-color: #dee2e6;
    border-color: #adb5bd;
}

QPushButton:pressed {
    background-color: #ced4da;
}

QPushButton:disabled {
    background-color: #e9ecef;
    color: #adb5bd;
    border-color: #dee2e6;
}

/* ===== 主按钮 - 开始采集 ===== */
QPushButton#startBtn {
    background-color: #198754;
    color: white;
    border: 1px solid #198754;
    font-weight: bold;
}

QPushButton#startBtn:hover {
    background-color: #157347;
    border-color: #146c43;
}

QPushButton#startBtn:disabled {
    background-color: #a3cfbb;
    border-color: #a3cfbb;
    color: white;
}

/* ===== 停止按钮 ===== */
QPushButton#stopBtn {
    background-color: #dc3545;
    color: white;
    border: 1px solid #dc3545;
    font-weight: bold;
}

QPushButton#stopBtn:hover {
    background-color: #bb2d3b;
    border-color: #b02a37;
}

QPushButton#stopBtn:disabled {
    background-color: #e9a5ab;
    border-color: #e9a5ab;
    color: white;
}

/* ===== 导出按钮 ===== */
QPushButton#exportBtn {
    background-color: #0d6efd;
    color: white;
    border: 1px solid #0d6efd;
}

QPushButton#exportBtn:hover {
    background-color: #0b5ed7;
    border-color: #0a58ca;
}

QPushButton#exportBtn:disabled {
    background-color: #86b7fe;
    border-color: #86b7fe;
    color: white;
}

/* ===== 粘贴按钮 ===== */
QPushButton#pasteBtn {
    background-color: #6c757d;
    color: white;
    border: 1px solid #6c757d;
}

QPushButton#pasteBtn:hover {
    background-color: #5c636a;
    border-color: #565e64;
}

/* ===== 快捷数量按钮 ===== */
QPushButton#quickBtn {
    background-color: #ffffff;
    color: #0d6efd;
    border: 1px solid #0d6efd;
    padding: 4px 12px;
    font-size: 11px;
}

QPushButton#quickBtn:hover {
    background-color: #0d6efd;
    color: white;
}

/* ===== 浏览按钮 ===== */
QPushButton#browseBtn {
    background-color: #ffffff;
    color: #495057;
    border: 1px solid #ced4da;
}

QPushButton#browseBtn:hover {
    background-color: #e9ecef;
}

/* ===== 进度条 ===== */
QProgressBar {
    background-color: #e9ecef;
    border: none;
    border-radius: 4px;
    text-align: center;
    color: #495057;
    font-size: 11px;
    height: 20px;
}

QProgressBar::chunk {
    background-color: #0d6efd;
    border-radius: 4px;
}

/* ===== 状态栏 ===== */
QStatusBar {
    background-color: #e9ecef;
    color: #6c757d;
    font-size: 11px;
    border-top: 1px solid #dee2e6;
}

/* ===== 分组框 ===== */
QGroupBox {
    color: #495057;
    border: 1px solid #dee2e6;
    border-radius: 4px;
    margin-top: 10px;
    padding: 14px 10px 8px 10px;
    font-size: 12px;
    font-weight: bold;
    background-color: #ffffff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #495057;
}

/* ===== 表格 ===== */
QTableWidget {
    background-color: #ffffff;
    alternate-background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 4px;
    gridline-color: #dee2e6;
    font-size: 11px;
    selection-background-color: #cfe2ff;
    selection-color: #212529;
}

QTableWidget::item {
    padding: 4px 6px;
    border-bottom: 1px solid #f0f0f0;
}

QHeaderView::section {
    background-color: #e9ecef;
    color: #495057;
    border: none;
    border-bottom: 2px solid #dee2e6;
    border-right: 1px solid #dee2e6;
    padding: 6px 8px;
    font-size: 11px;
    font-weight: bold;
}

QHeaderView::section:hover {
    background-color: #dee2e6;
}

/* ===== 滚动条 ===== */
QScrollBar:vertical {
    background: #f8f9fa;
    width: 10px;
    border-radius: 5px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #ced4da;
    border-radius: 5px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: #adb5bd;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

/* ===== 下拉框 ===== */
QComboBox {
    background-color: #ffffff;
    color: #212529;
    border: 1px solid #ced4da;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}

QComboBox:hover {
    border-color: #adb5bd;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #dee2e6;
    selection-background-color: #0d6efd;
    selection-color: white;
}
"""
