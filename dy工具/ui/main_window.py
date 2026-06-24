"""
主窗口布局 - 参考新媒体数据工具风格
"""
import os
from datetime import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QTextCursor
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QProgressBar,
    QSpinBox, QGroupBox, QFileDialog, QMessageBox, QStatusBar,
    QApplication, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView,
)

import config
from core.exporter import export_to_excel, get_default_output_path
from ui.worker import ScrapeWorker
from ui.styles import MAIN_STYLE


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self._worker = None
        self._comments = []
        self._init_ui()

    def _init_ui(self):
        """初始化界面"""
        self.setWindowTitle("抖音评论抓取工具")
        self.setMinimumSize(900, 660)
        self.resize(960, 700)
        self.setStyleSheet(MAIN_STYLE)

        # 中央部件
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(6)
        main_layout.setContentsMargins(10, 8, 10, 6)

        # === 标题栏 ===
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(4, 0, 4, 0)

        title = QLabel("抖音评论抓取工具")
        title.setFont(QFont("Microsoft YaHei UI", 14, QFont.Bold))
        title.setStyleSheet("color: #212529;")
        header_layout.addWidget(title)

        subtitle = QLabel("  支持抖音视频链接 / 分享文本")
        subtitle.setFont(QFont("Microsoft YaHei UI", 9))
        subtitle.setStyleSheet("color: #6c757d;")
        header_layout.addWidget(subtitle)
        header_layout.addStretch()

        main_layout.addWidget(header)

        # === 链接输入区（多行） ===
        input_group = QGroupBox(" 链接输入（支持粘贴分享文本）")
        input_layout = QVBoxLayout(input_group)
        input_layout.setContentsMargins(8, 14, 8, 8)

        self.url_input = QTextEdit()
        self.url_input.setPlaceholderText("粘贴抖音视频链接或分享文本...\n支持格式: https://v.douyin.com/xxx 或分享口令")
        self.url_input.setMaximumHeight(80)
        self.url_input.setFont(QFont("Microsoft YaHei UI", 10))
        input_layout.addWidget(self.url_input)

        main_layout.addWidget(input_group)

        # === 按钮工具栏 ===
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(4, 2, 4, 2)
        toolbar_layout.setSpacing(8)

        # 粘贴按钮
        self.paste_btn = QPushButton("📋 粘贴")
        self.paste_btn.setFixedHeight(30)
        self.paste_btn.setCursor(Qt.PointingHandCursor)
        self.paste_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: 1px solid #6c757d;
                border-radius: 4px;
                padding: 6px 14px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #5c636a;
                border-color: #565e64;
            }
        """)
        self.paste_btn.clicked.connect(self._paste_url)
        toolbar_layout.addWidget(self.paste_btn)

        # 分隔
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.VLine)
        sep1.setStyleSheet("color: #dee2e6;")
        toolbar_layout.addWidget(sep1)

        # 目标数量
        count_label = QLabel("目标数量:")
        count_label.setStyleSheet("font-size: 12px; color: #495057;")
        toolbar_layout.addWidget(count_label)

        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 100000)
        self.count_spin.setValue(config.DEFAULT_TARGET_COUNT)
        self.count_spin.setSingleStep(50)
        self.count_spin.setFixedWidth(100)
        self.count_spin.setFixedHeight(30)
        toolbar_layout.addWidget(self.count_spin)

        # 快捷按钮
        for count in [50, 100, 200, 500]:
            btn = QPushButton(f"{count}")
            btn.setObjectName("quickBtn")
            btn.setFixedSize(46, 28)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, c=count: self.count_spin.setValue(c))
            toolbar_layout.addWidget(btn)

        toolbar_layout.addSpacing(8)

        # 分隔
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.VLine)
        sep2.setStyleSheet("color: #dee2e6;")
        toolbar_layout.addWidget(sep2)

        # 确认登录按钮（默认隐藏）
        self.confirm_login_btn = QPushButton("✅ 确认登录")
        self.confirm_login_btn.setFixedHeight(30)
        self.confirm_login_btn.setCursor(Qt.PointingHandCursor)
        self.confirm_login_btn.setStyleSheet("""
            QPushButton {
                background-color: #fd7e14;
                color: white;
                border: 1px solid #fd7e14;
                border-radius: 4px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e8690a;
            }
            QPushButton:disabled {
                background-color: #f8d7a5;
                border-color: #f8d7a5;
                color: white;
            }
        """)
        self.confirm_login_btn.setVisible(False)
        self.confirm_login_btn.clicked.connect(self._confirm_login)
        toolbar_layout.addWidget(self.confirm_login_btn)

        # 开始按钮
        self.start_btn = QPushButton("▶ 开始抓取")
        self.start_btn.setObjectName("startBtn")
        self.start_btn.setFixedHeight(30)
        self.start_btn.setMinimumWidth(100)
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.clicked.connect(self._start_scrape)
        toolbar_layout.addWidget(self.start_btn)

        # 停止按钮
        self.stop_btn = QPushButton("⏹ 停止")
        self.stop_btn.setObjectName("stopBtn")
        self.stop_btn.setFixedHeight(30)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setCursor(Qt.PointingHandCursor)
        self.stop_btn.clicked.connect(self._stop_scrape)
        toolbar_layout.addWidget(self.stop_btn)

        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #6c757d; font-size: 11px;")
        toolbar_layout.addWidget(self.status_label)

        toolbar_layout.addStretch()

        main_layout.addWidget(toolbar)

        # === 进度条 ===
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setFixedHeight(18)
        main_layout.addWidget(self.progress_bar)

        # === 日志区 ===
        log_group = QGroupBox(" 运行日志")
        log_layout = QVBoxLayout(log_group)
        log_layout.setContentsMargins(8, 14, 8, 8)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(110)
        self.log_text.setFont(QFont("Consolas", 9))
        log_layout.addWidget(self.log_text)
        main_layout.addWidget(log_group)

        # === 结果表格 ===
        table_group = QGroupBox(" 采集结果")
        table_layout = QVBoxLayout(table_group)
        table_layout.setContentsMargins(8, 14, 8, 8)

        self.result_table = QTableWidget()
        self.result_table.setColumnCount(7)
        self.result_table.setHorizontalHeaderLabels([
            "序号", "用户昵称", "评论内容", "点赞", "回复", "发布时间", "评论ID"
        ])
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.result_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.result_table.horizontalHeader().setStretchLastSection(False)
        self.result_table.verticalHeader().setVisible(False)

        # 列宽设置
        header_view = self.result_table.horizontalHeader()
        header_view.resizeSection(0, 45)   # 序号
        header_view.resizeSection(1, 100)  # 用户昵称
        header_view.resizeSection(2, 380)  # 评论内容
        header_view.resizeSection(3, 60)   # 点赞
        header_view.resizeSection(4, 60)   # 回复
        header_view.resizeSection(5, 130)  # 发布时间
        header_view.resizeSection(6, 100)  # 评论ID
        header_view.setSectionResizeMode(2, QHeaderView.Stretch)

        table_layout.addWidget(self.result_table)
        main_layout.addWidget(table_group, stretch=1)

        # === 底部操作栏 ===
        bottom = QWidget()
        bottom_layout = QHBoxLayout(bottom)
        bottom_layout.setContentsMargins(4, 2, 4, 2)

        # 导出路径
        path_label = QLabel("导出路径:")
        path_label.setStyleSheet("font-size: 11px; color: #6c757d;")
        bottom_layout.addWidget(path_label)

        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("默认保存到桌面...")
        self.path_input.setFixedHeight(28)
        self.path_input.setMaximumWidth(400)
        bottom_layout.addWidget(self.path_input)

        browse_btn = QPushButton("浏览")
        browse_btn.setObjectName("browseBtn")
        browse_btn.setFixedHeight(28)
        browse_btn.setFixedWidth(60)
        browse_btn.setCursor(Qt.PointingHandCursor)
        browse_btn.clicked.connect(self._browse_path)
        bottom_layout.addWidget(browse_btn)

        bottom_layout.addSpacing(12)

        # 导出按钮
        self.export_btn = QPushButton("📊 导出 Excel")
        self.export_btn.setObjectName("exportBtn")
        self.export_btn.setFixedHeight(30)
        self.export_btn.setMinimumWidth(110)
        self.export_btn.setEnabled(False)
        self.export_btn.setCursor(Qt.PointingHandCursor)
        self.export_btn.clicked.connect(self._export_excel)
        bottom_layout.addWidget(self.export_btn)

        bottom_layout.addStretch()

        # 统计标签
        self.count_label = QLabel("共 0 条评论")
        self.count_label.setStyleSheet("color: #6c757d; font-size: 11px;")
        bottom_layout.addWidget(self.count_label)

        main_layout.addWidget(bottom)

        # === 状态栏 ===
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self._update_status_bar()

    def _paste_url(self):
        """粘贴按钮"""
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            self.url_input.setPlainText(text.strip())
            self._log("已粘贴链接")

    def _browse_path(self):
        """选择导出路径"""
        default_path = get_default_output_path()
        path, _ = QFileDialog.getSaveFileName(
            self, "选择导出路径", default_path, "Excel 文件 (*.xlsx)"
        )
        if path:
            self.path_input.setText(path)

    def _get_output_path(self) -> str:
        """获取输出路径"""
        path = self.path_input.text().strip()
        if not path:
            path = get_default_output_path()
        if not path.endswith(".xlsx"):
            path += ".xlsx"
        return path

    def _start_scrape(self):
        """开始抓取"""
        url = self.url_input.toPlainText().strip()
        if not url:
            QMessageBox.warning(self, "提示", "请先粘贴视频链接！")
            self.url_input.setFocus()
            return

        target_count = self.count_spin.value()
        cookies_exist = os.path.exists(config.COOKIE_FILE)

        # 重置状态
        self._comments = []
        self.export_btn.setEnabled(False)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.confirm_login_btn.setVisible(False)
        self.progress_bar.setValue(0)
        self.result_table.setRowCount(0)
        self.log_text.clear()
        self.count_label.setText("共 0 条评论")
        self.status_label.setText("启动中...")

        # 创建工作线程
        self._worker = ScrapeWorker(
            video_url=url,
            target_count=target_count,
            cookies_exist=cookies_exist,
        )
        self._worker.log_message.connect(self._log)
        self._worker.progress_update.connect(self._update_progress)
        self._worker.finished.connect(self._on_scrape_finished)
        self._worker.error.connect(self._on_scrape_error)
        self._worker.login_ready.connect(self._on_login_ready)
        self._worker.login_done.connect(self._on_login_done)
        self._worker.start()

    def _on_login_ready(self):
        """浏览器已打开，等待用户扫码登录"""
        self.status_label.setText("等待登录...")
        self.confirm_login_btn.setVisible(True)
        self.confirm_login_btn.setEnabled(True)
        self._log("请在弹出的浏览器窗口中扫码登录")
        self._log("登录完成后，点击右侧「确认登录」按钮")

    def _on_login_done(self):
        """登录成功"""
        self.confirm_login_btn.setVisible(False)
        self.status_label.setText("登录成功，开始抓取...")
        self._log("✅ 登录成功")

    def _confirm_login(self):
        """用户确认已完成登录"""
        self.confirm_login_btn.setEnabled(False)
        self.confirm_login_btn.setText("登录中...")
        self._log("已确认登录，正在保存 Cookie...")
        if self._worker:
            self._worker.confirm_login()

    def _stop_scrape(self):
        """停止抓取"""
        if self._worker:
            self._worker.stop()
            self._log("正在停止...")
            self.status_label.setText("正在停止...")

    def _on_scrape_finished(self, comments: list):
        """抓取完成"""
        self._comments = comments
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.confirm_login_btn.setVisible(False)
        self.export_btn.setEnabled(len(comments) > 0)

        count = len(comments)
        self.status_label.setText(f"完成！成功 {count} 条")
        self.count_label.setText(f"共 {count} 条评论")
        self._log(f"{'='*40}")
        self._log(f"抓取完成！共获取 {count} 条评论")

        # 填充表格
        self._fill_table(comments)
        self._worker = None

    def _on_scrape_error(self, error_msg: str):
        """抓取出错"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.confirm_login_btn.setVisible(False)
        self.progress_bar.setValue(0)
        self.status_label.setText("采集失败")
        self._log(f"❌ 错误: {error_msg}")
        QMessageBox.critical(self, "抓取失败", f"发生错误:\n\n{error_msg[:500]}")
        self._worker = None

    def _fill_table(self, comments: list):
        """填充结果表格"""
        self.result_table.setRowCount(len(comments))
        for row, c in enumerate(comments):
            items = [
                str(row + 1),
                c.get("user_name", ""),
                c.get("comment_text", ""),
                str(c.get("like_count", 0)),
                str(c.get("reply_count", 0)),
                c.get("publish_time", ""),
                c.get("comment_id", ""),
            ]
            for col, text in enumerate(items):
                item = QTableWidgetItem(text)
                if col in (0, 3, 4):
                    item.setTextAlignment(Qt.AlignCenter)
                self.result_table.setItem(row, col, item)

    def _export_excel(self):
        """导出 Excel"""
        if not self._comments:
            QMessageBox.warning(self, "提示", "没有可导出的评论数据！")
            return

        output_path = self._get_output_path()
        try:
            video_url = self.url_input.toPlainText().strip().split("\n")[0]
            actual_path = export_to_excel(self._comments, output_path, video_url)
            self._log(f"✅ 已导出到: {actual_path}")

            reply = QMessageBox.information(
                self, "导出成功",
                f"评论已导出到:\n{actual_path}\n\n是否打开文件所在目录？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if reply == QMessageBox.Yes:
                import subprocess
                subprocess.Popen(f'explorer /select,"{actual_path}"')
        except Exception as e:
            self._log(f"❌ 导出失败: {e}")
            QMessageBox.critical(self, "导出失败", f"导出 Excel 失败:\n{e}")

    def _update_progress(self, current: int, total: int):
        """更新进度条"""
        if total > 0:
            pct = min(int(current / total * 100), 100)
            self.progress_bar.setValue(pct)
            self.progress_bar.setFormat(f"{current}/{total} ({pct}%)")

    def _log(self, message: str):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_text.setTextCursor(cursor)

    def _update_status_bar(self):
        """更新状态栏"""
        if os.path.exists(config.COOKIE_FILE):
            self.status_bar.showMessage("就绪 | Cookie 已保存，可免登录")
        else:
            self.status_bar.showMessage("就绪 | 首次使用需要扫码登录")

    def closeEvent(self, event):
        """关闭窗口时清理资源"""
        if self._worker and self._worker.isRunning():
            self._worker.stop()
            self._worker.wait(3000)
        event.accept()
