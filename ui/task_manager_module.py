"""
模块6：系统任务管理器界面
展示系统真实的进程、CPU、内存信息
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QGroupBox, QLabel, QComboBox, QSpinBox,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QMessageBox, QProgressBar, QSplitter, QTabWidget,
                             QFrame)
from PyQt5.QtCore import Qt, QTimer, QRectF, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QPen, QBrush, QFont, QPainterPath
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.system_monitor import create_monitor, SystemInfo


class ProcessFetchThread(QThread):
    """后台获取进程列表的线程"""
    finished_signal = pyqtSignal(list)

    def __init__(self, monitor, sort_by="cpu", parent=None):
        super().__init__(parent)
        self.monitor = monitor
        self.sort_by = sort_by

    def run(self):
        processes = self.monitor.get_process_list(sort_by=self.sort_by, limit=100)
        self.finished_signal.emit(processes)


class UsageGraphWidget(QWidget):
    """使用率图表组件"""

    def __init__(self, title: str = "CPU", color: str = "#2196F3", parent=None):
        super().__init__(parent)
        self.title = title
        self.color = QColor(color)
        self.history: list = []
        self.max_points = 60
        self.current_value = 0
        self.setMinimumHeight(120)
        self.setMinimumWidth(200)

    def set_data(self, history: list, current: float):
        """设置数据"""
        self.history = history[-self.max_points:]
        self.current_value = current
        self.update()

    def paintEvent(self, event):
        """绘制图表"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()

        # 绘制背景
        painter.fillRect(0, 0, width, height, QColor("#1E1E1E"))

        # 绘制边框
        painter.setPen(QPen(QColor("#333"), 1))
        painter.drawRect(0, 0, width - 1, height - 1)

        # 绘制网格线
        painter.setPen(QPen(QColor("#333"), 1, Qt.DotLine))
        for i in range(1, 4):
            y = height * i // 4
            painter.drawLine(0, y, width, y)

        # 绘制刻度
        painter.setPen(QPen(QColor("#666")))
        painter.setFont(QFont("Microsoft YaHei", 7))
        painter.drawText(5, 12, "100%")
        painter.drawText(5, height // 2, "50%")
        painter.drawText(5, height - 5, "0%")

        # 绘制标题
        painter.setFont(QFont("Microsoft YaHei", 9, QFont.Bold))
        painter.setPen(QPen(self.color))
        painter.drawText(width - 100, 15, f"{self.title}: {self.current_value:.1f}%")

        # 绘制曲线
        if len(self.history) > 1:
            graph_left = 35
            graph_width = width - graph_left - 10
            graph_height = height - 20

            # 创建路径
            path = QPainterPath()

            # 填充区域
            fill_path = QPainterPath()

            point_spacing = graph_width / (self.max_points - 1)

            for i, value in enumerate(self.history):
                x = graph_left + i * point_spacing
                y = height - 10 - (value / 100.0) * graph_height

                if i == 0:
                    path.moveTo(x, y)
                    fill_path.moveTo(x, height - 10)
                    fill_path.lineTo(x, y)
                else:
                    path.lineTo(x, y)
                    fill_path.lineTo(x, y)

            # 闭合填充路径
            if self.history:
                last_x = graph_left + (len(self.history) - 1) * point_spacing
                fill_path.lineTo(last_x, height - 10)
                fill_path.closeSubpath()

            # 绘制填充
            fill_color = QColor(self.color)
            fill_color.setAlpha(50)
            painter.fillPath(fill_path, QBrush(fill_color))

            # 绘制线条
            painter.setPen(QPen(self.color, 2))
            painter.drawPath(path)


class CpuCoreWidget(QWidget):
    """CPU核心使用率组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.core_usage: list = []
        self.setMinimumHeight(60)

    def set_data(self, usage: list):
        """设置数据"""
        self.core_usage = usage
        self.update()

    def paintEvent(self, event):
        """绘制CPU核心"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if not self.core_usage:
            return

        width = self.width()
        height = self.height()
        n = len(self.core_usage)

        bar_width = min(30, (width - 20) // n - 5)
        spacing = 5
        total_width = n * (bar_width + spacing) - spacing
        start_x = (width - total_width) // 2

        for i, usage in enumerate(self.core_usage):
            x = start_x + i * (bar_width + spacing)
            bar_height = height - 25

            # 背景条
            painter.setBrush(QBrush(QColor("#333")))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(x, 5, bar_width, bar_height, 3, 3)

            # 使用率条
            used_height = int((usage / 100.0) * bar_height)
            if usage > 80:
                color = QColor("#F44336")
            elif usage > 50:
                color = QColor("#FF9800")
            else:
                color = QColor("#4CAF50")

            painter.setBrush(QBrush(color))
            painter.drawRoundedRect(x, 5 + bar_height - used_height,
                                   bar_width, used_height, 3, 3)

            # 标签
            painter.setPen(QPen(QColor("#999")))
            painter.setFont(QFont("Microsoft YaHei", 7))
            painter.drawText(QRectF(x, height - 18, bar_width, 15),
                           Qt.AlignCenter, f"C{i}")


class TaskManagerModule(QWidget):
    """系统任务管理器模块"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.monitor = create_monitor()
        self.refresh_interval = 1000  # 1秒刷新
        self._process_thread = None
        self._init_ui()
        # 不立即启动刷新，等待主窗口切换到此标签时启动

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # 顶部系统概览
        overview_group = QGroupBox("系统概览")
        overview_layout = QHBoxLayout(overview_group)

        # CPU使用率图
        self.cpu_graph = UsageGraphWidget("CPU", "#2196F3")
        overview_layout.addWidget(self.cpu_graph)

        # 内存使用率图
        self.memory_graph = UsageGraphWidget("内存", "#4CAF50")
        overview_layout.addWidget(self.memory_graph)

        layout.addWidget(overview_group)

        # 中部区域
        middle_splitter = QSplitter(Qt.Vertical)

        # 系统信息和CPU核心
        info_widget = QWidget()
        info_layout = QHBoxLayout(info_widget)

        # 系统信息
        sys_info_group = QGroupBox("系统信息")
        sys_info_layout = QVBoxLayout(sys_info_group)

        self.cpu_info_label = QLabel("CPU: -")
        sys_info_layout.addWidget(self.cpu_info_label)

        self.memory_info_label = QLabel("内存: - / - GB")
        sys_info_layout.addWidget(self.memory_info_label)

        self.disk_info_label = QLabel("磁盘: - / - GB")
        sys_info_layout.addWidget(self.disk_info_label)

        self.boot_time_label = QLabel("启动时间: -")
        sys_info_layout.addWidget(self.boot_time_label)

        self.process_count_label = QLabel("进程数: -")
        sys_info_layout.addWidget(self.process_count_label)

        sys_info_layout.addStretch()
        info_layout.addWidget(sys_info_group)

        # CPU核心
        cpu_core_group = QGroupBox("CPU核心使用率")
        cpu_core_layout = QVBoxLayout(cpu_core_group)
        self.cpu_core_widget = CpuCoreWidget()
        cpu_core_layout.addWidget(self.cpu_core_widget)
        info_layout.addWidget(cpu_core_group, stretch=2)

        middle_splitter.addWidget(info_widget)

        # 进程列表
        process_widget = QWidget()
        process_layout = QVBoxLayout(process_widget)
        process_layout.setContentsMargins(0, 0, 0, 0)

        # 进程列表头部
        process_header = QWidget()
        process_header_layout = QHBoxLayout(process_header)
        process_header_layout.setContentsMargins(0, 0, 0, 0)

        process_title = QLabel("进程列表")
        process_title.setStyleSheet("font-weight: bold; font-size: 12px;")
        process_header_layout.addWidget(process_title)

        process_header_layout.addWidget(QLabel("排序:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["CPU使用率", "内存使用率", "PID", "名称"])
        self.sort_combo.currentIndexChanged.connect(self._refresh_process_list)
        process_header_layout.addWidget(self.sort_combo)

        process_header_layout.addWidget(QLabel("刷新间隔:"))
        self.refresh_spin = QSpinBox()
        self.refresh_spin.setRange(500, 5000)
        self.refresh_spin.setValue(1000)
        self.refresh_spin.setSuffix(" ms")
        self.refresh_spin.setSingleStep(500)
        self.refresh_spin.valueChanged.connect(self._on_refresh_changed)
        process_header_layout.addWidget(self.refresh_spin)

        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self._refresh_all)
        process_header_layout.addWidget(refresh_btn)

        process_header_layout.addStretch()

        process_layout.addWidget(process_header)

        # 进程表格
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(8)
        self.process_table.setHorizontalHeaderLabels([
            "PID", "名称", "状态", "CPU%", "内存%", "内存(MB)", "线程数", "用户"
        ])
        self.process_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.process_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.process_table.setAlternatingRowColors(True)
        self.process_table.setStyleSheet("""
            QTableWidget {
                alternate-background-color: #f5f5f5;
            }
        """)
        process_layout.addWidget(self.process_table)

        middle_splitter.addWidget(process_widget)
        middle_splitter.setSizes([150, 400])

        layout.addWidget(middle_splitter, stretch=1)

        # 底部状态
        status_group = QGroupBox("状态")
        status_layout = QHBoxLayout(status_group)

        if not self.monitor.is_available():
            status_label = QLabel("注意: psutil未安装，显示的是模拟数据。请运行 pip install psutil 安装依赖。")
            status_label.setStyleSheet("color: #FF9800;")
        else:
            status_label = QLabel("正在监控系统状态...")
            status_label.setStyleSheet("color: #4CAF50;")

        status_layout.addWidget(status_label)
        status_layout.addStretch()

        self.last_update_label = QLabel("最后更新: -")
        status_layout.addWidget(self.last_update_label)

        layout.addWidget(status_group)

        # 刷新定时器
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._refresh_all)

    def _start_refresh(self):
        """开始刷新"""
        self.refresh_timer.start(self.refresh_interval)
        self._refresh_all()

    def _on_refresh_changed(self, value: int):
        """刷新间隔改变"""
        self.refresh_interval = value
        self.refresh_timer.setInterval(value)

    def _refresh_all(self):
        """刷新所有数据"""
        # 更新时间
        from datetime import datetime
        self.last_update_label.setText(
            f"最后更新: {datetime.now().strftime('%H:%M:%S')}"
        )

        # 刷新系统信息（快速，同步执行）
        self._refresh_system_info()

        # 刷新进程列表（慢，后台线程执行）
        self._refresh_process_list()

    def _refresh_system_info(self):
        """刷新系统信息"""
        info = self.monitor.get_system_info()
        if not info:
            return

        # 更新图表
        cpu_history = self.monitor.get_cpu_history()
        memory_history = self.monitor.get_memory_history()

        self.cpu_graph.set_data(cpu_history, info.cpu_percent)
        self.memory_graph.set_data(memory_history, info.memory_percent)

        # 更新CPU核心
        core_usage = self.monitor.get_cpu_per_core()
        self.cpu_core_widget.set_data(core_usage)

        # 更新文本信息
        self.cpu_info_label.setText(
            f"CPU: {info.cpu_count}核 @ {info.cpu_freq:.0f}MHz ({info.cpu_percent:.1f}%)"
        )
        self.memory_info_label.setText(
            f"内存: {info.memory_used:.1f} / {info.memory_total:.1f} GB ({info.memory_percent:.1f}%)"
        )
        self.disk_info_label.setText(
            f"磁盘: {info.disk_used:.1f} / {info.disk_total:.1f} GB ({info.disk_percent:.1f}%)"
        )
        self.boot_time_label.setText(f"启动时间: {info.boot_time}")
        self.process_count_label.setText(f"进程数: {info.process_count}")

    def _refresh_process_list(self):
        """刷新进程列表（后台线程）"""
        # 如果上一个线程还在运行，跳过
        if self._process_thread and self._process_thread.isRunning():
            return

        sort_options = ["cpu", "memory", "pid", "name"]
        sort_by = sort_options[self.sort_combo.currentIndex()]

        self._process_thread = ProcessFetchThread(self.monitor, sort_by)
        self._process_thread.finished_signal.connect(self._on_process_list_ready)
        self._process_thread.start()

    def _on_process_list_ready(self, processes):
        """进程列表获取完成"""
        self.process_table.setRowCount(len(processes))

        for row, proc in enumerate(processes):
            self.process_table.setItem(row, 0, QTableWidgetItem(str(proc.pid)))
            self.process_table.setItem(row, 1, QTableWidgetItem(proc.name))
            self.process_table.setItem(row, 2, QTableWidgetItem(proc.status))

            cpu_item = QTableWidgetItem(f"{proc.cpu_percent:.1f}")
            if proc.cpu_percent > 50:
                cpu_item.setBackground(QColor("#FFCDD2"))
            self.process_table.setItem(row, 3, cpu_item)

            mem_item = QTableWidgetItem(f"{proc.memory_percent:.1f}")
            if proc.memory_percent > 10:
                mem_item.setBackground(QColor("#FFECB3"))
            self.process_table.setItem(row, 4, mem_item)

            self.process_table.setItem(row, 5, QTableWidgetItem(f"{proc.memory_mb:.1f}"))
            self.process_table.setItem(row, 6, QTableWidgetItem(str(proc.threads)))
            self.process_table.setItem(row, 7, QTableWidgetItem(proc.username))

    def closeEvent(self, event):
        """关闭事件"""
        self.refresh_timer.stop()
        if self._process_thread and self._process_thread.isRunning():
            self._process_thread.wait(1000)
        super().closeEvent(event)
