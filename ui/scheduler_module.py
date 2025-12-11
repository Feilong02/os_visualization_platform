"""
模块4：CPU调度算法界面
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QGroupBox, QLabel, QComboBox, QSpinBox, QDoubleSpinBox,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QMessageBox, QScrollArea, QSplitter, QSlider)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.scheduler import Scheduler, SchedulerAlgorithm, GanttBlock
from visualization.gantt_chart import GanttChartWidget


class SchedulerModule(QWidget):
    """CPU调度模块"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scheduler = Scheduler()
        self._init_ui()
        self._load_sample_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # 顶部控制区
        top_panel = QWidget()
        top_layout = QHBoxLayout(top_panel)

        # 进程输入
        input_group = QGroupBox("添加进程")
        input_layout = QHBoxLayout(input_group)

        input_layout.addWidget(QLabel("名称:"))
        self.name_input = QComboBox()
        self.name_input.setEditable(True)
        self.name_input.addItems(["P1", "P2", "P3", "P4", "P5"])
        self.name_input.setCurrentText("P1")
        self.name_input.setMaximumWidth(80)
        input_layout.addWidget(self.name_input)

        input_layout.addWidget(QLabel("到达:"))
        self.arrival_spin = QSpinBox()
        self.arrival_spin.setRange(0, 100)
        self.arrival_spin.setValue(0)
        input_layout.addWidget(self.arrival_spin)

        input_layout.addWidget(QLabel("执行:"))
        self.burst_spin = QSpinBox()
        self.burst_spin.setRange(1, 50)
        self.burst_spin.setValue(5)
        input_layout.addWidget(self.burst_spin)

        input_layout.addWidget(QLabel("优先级:"))
        self.priority_spin = QSpinBox()
        self.priority_spin.setRange(1, 10)
        self.priority_spin.setValue(1)
        input_layout.addWidget(self.priority_spin)

        add_btn = QPushButton("添加")
        add_btn.clicked.connect(self._add_process)
        add_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        input_layout.addWidget(add_btn)

        top_layout.addWidget(input_group)

        # 算法选择
        algo_group = QGroupBox("调度算法")
        algo_layout = QHBoxLayout(algo_group)

        self.algo_combo = QComboBox()
        self.algo_combo.addItems([
            "先来先服务 (FCFS)",
            "时间片轮转 (RR)",
            "最短作业优先 (SJF)",
            "优先级调度"
        ])
        self.algo_combo.currentIndexChanged.connect(self._on_algo_changed)
        algo_layout.addWidget(self.algo_combo)

        algo_layout.addWidget(QLabel("时间片:"))
        self.timeslice_spin = QSpinBox()
        self.timeslice_spin.setRange(1, 10)
        self.timeslice_spin.setValue(2)
        self.timeslice_spin.setEnabled(False)
        algo_layout.addWidget(self.timeslice_spin)

        top_layout.addWidget(algo_group)

        # 执行按钮
        exec_group = QGroupBox("执行")
        exec_layout = QHBoxLayout(exec_group)

        self.run_btn = QPushButton("执行调度")
        self.run_btn.clicked.connect(self._run_scheduling)
        self.run_btn.setStyleSheet("background-color: #2196F3; color: white;")
        exec_layout.addWidget(self.run_btn)

        self.animate_btn = QPushButton("动画演示")
        self.animate_btn.clicked.connect(self._run_animation)
        self.animate_btn.setStyleSheet("background-color: #FF9800; color: white;")
        exec_layout.addWidget(self.animate_btn)

        self.clear_btn = QPushButton("清空")
        self.clear_btn.clicked.connect(self._clear_all)
        exec_layout.addWidget(self.clear_btn)

        self.sample_btn = QPushButton("示例数据")
        self.sample_btn.clicked.connect(self._load_sample_data)
        exec_layout.addWidget(self.sample_btn)

        top_layout.addWidget(exec_group)

        layout.addWidget(top_panel)

        # 中部区域（进程表 + 甘特图）
        splitter = QSplitter(Qt.Vertical)

        # 进程表格
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        table_layout.setContentsMargins(0, 0, 0, 0)

        table_header = QLabel("进程列表")
        table_header.setStyleSheet("font-weight: bold; font-size: 12px;")
        table_layout.addWidget(table_header)

        self.process_table = QTableWidget()
        self.process_table.setColumnCount(7)
        self.process_table.setHorizontalHeaderLabels([
            "进程", "到达时间", "执行时间", "优先级",
            "开始时间", "完成时间", "等待时间"
        ])
        self.process_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table_layout.addWidget(self.process_table)

        # 删除进程按钮
        del_btn = QPushButton("删除选中进程")
        del_btn.clicked.connect(self._delete_process)
        table_layout.addWidget(del_btn)

        splitter.addWidget(table_widget)

        # 甘特图区域
        gantt_widget = QWidget()
        gantt_layout = QVBoxLayout(gantt_widget)
        gantt_layout.setContentsMargins(0, 0, 0, 0)

        gantt_header_layout = QHBoxLayout()
        gantt_header = QLabel("甘特图")
        gantt_header.setStyleSheet("font-weight: bold; font-size: 12px;")
        gantt_header_layout.addWidget(gantt_header)

        gantt_header_layout.addWidget(QLabel("缩放:"))
        self.scale_slider = QSlider(Qt.Horizontal)
        self.scale_slider.setRange(15, 60)
        self.scale_slider.setValue(30)
        self.scale_slider.setMaximumWidth(150)
        self.scale_slider.valueChanged.connect(self._on_scale_changed)
        gantt_header_layout.addWidget(self.scale_slider)
        gantt_header_layout.addStretch()

        gantt_layout.addLayout(gantt_header_layout)

        # 甘特图放在滚动区域中
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.gantt_chart = GanttChartWidget()
        scroll_area.setWidget(self.gantt_chart)

        gantt_layout.addWidget(scroll_area)

        splitter.addWidget(gantt_widget)
        splitter.setSizes([200, 300])

        layout.addWidget(splitter, stretch=2)

        # 底部统计区
        stats_group = QGroupBox("性能指标")
        stats_layout = QHBoxLayout(stats_group)

        self.avg_waiting_label = QLabel("平均等待时间: -")
        self.avg_waiting_label.setStyleSheet("font-size: 14px;")
        stats_layout.addWidget(self.avg_waiting_label)

        self.avg_turnaround_label = QLabel("平均周转时间: -")
        self.avg_turnaround_label.setStyleSheet("font-size: 14px;")
        stats_layout.addWidget(self.avg_turnaround_label)

        self.total_time_label = QLabel("总执行时间: -")
        self.total_time_label.setStyleSheet("font-size: 14px;")
        stats_layout.addWidget(self.total_time_label)

        stats_layout.addStretch()

        layout.addWidget(stats_group)

    def _on_algo_changed(self, index: int):
        """算法选择变化"""
        # 只有时间片轮转算法需要设置时间片
        self.timeslice_spin.setEnabled(index == 1)

    def _on_scale_changed(self, value: int):
        """缩放变化"""
        self.gantt_chart.set_time_scale(value)

    def _add_process(self):
        """添加进程"""
        name = self.name_input.currentText()
        arrival = self.arrival_spin.value()
        burst = self.burst_spin.value()
        priority = self.priority_spin.value()

        # 检查是否已存在同名进程
        for p in self.scheduler.processes:
            if p.name == name:
                QMessageBox.warning(self, "提示", f"进程 {name} 已存在")
                return

        pid = len(self.scheduler.processes) + 1
        self.scheduler.add_process(pid, name, arrival, burst, priority)

        self._refresh_table()

        # 自动递增进程名
        try:
            prefix = ''.join(filter(str.isalpha, name))
            num = int(''.join(filter(str.isdigit, name))) + 1
            self.name_input.setCurrentText(f"{prefix}{num}")
        except:
            pass

    def _delete_process(self):
        """删除选中的进程"""
        selected = self.process_table.selectedItems()
        if not selected:
            return

        row = selected[0].row()
        if row < len(self.scheduler.processes):
            del self.scheduler.processes[row]
            self._refresh_table()

    def _refresh_table(self):
        """刷新进程表格"""
        self.process_table.setRowCount(len(self.scheduler.processes))

        for row, process in enumerate(self.scheduler.processes):
            self.process_table.setItem(row, 0, QTableWidgetItem(process.name))
            self.process_table.setItem(row, 1, QTableWidgetItem(str(int(process.arrival_time))))
            self.process_table.setItem(row, 2, QTableWidgetItem(str(int(process.burst_time))))
            self.process_table.setItem(row, 3, QTableWidgetItem(str(process.priority)))

            # 结果列（如果已计算）
            if process.start_time >= 0:
                self.process_table.setItem(row, 4, QTableWidgetItem(str(int(process.start_time))))
                self.process_table.setItem(row, 5, QTableWidgetItem(str(int(process.finish_time))))
                self.process_table.setItem(row, 6, QTableWidgetItem(str(int(process.waiting_time))))
            else:
                self.process_table.setItem(row, 4, QTableWidgetItem("-"))
                self.process_table.setItem(row, 5, QTableWidgetItem("-"))
                self.process_table.setItem(row, 6, QTableWidgetItem("-"))

    def _run_scheduling(self):
        """执行调度算法"""
        if not self.scheduler.processes:
            QMessageBox.warning(self, "提示", "请先添加进程")
            return

        algo_index = self.algo_combo.currentIndex()

        if algo_index == 0:  # FCFS
            blocks, _ = self.scheduler.fcfs()
        elif algo_index == 1:  # RR
            time_slice = self.timeslice_spin.value()
            blocks, _ = self.scheduler.round_robin(time_slice)
        elif algo_index == 2:  # SJF
            blocks, _ = self.scheduler.sjf()
        elif algo_index == 3:  # Priority
            blocks, _ = self.scheduler.priority_scheduling()

        # 更新显示
        self.gantt_chart.set_data(blocks)
        self._refresh_table()
        self._update_metrics()

    def _run_animation(self):
        """运行动画演示"""
        if not self.scheduler.processes:
            QMessageBox.warning(self, "提示", "请先添加进程")
            return

        # 先执行调度
        algo_index = self.algo_combo.currentIndex()

        if algo_index == 0:
            blocks, _ = self.scheduler.fcfs()
        elif algo_index == 1:
            time_slice = self.timeslice_spin.value()
            blocks, _ = self.scheduler.round_robin(time_slice)
        elif algo_index == 2:
            blocks, _ = self.scheduler.sjf()
        elif algo_index == 3:
            blocks, _ = self.scheduler.priority_scheduling()

        # 启动动画
        self.gantt_chart.start_animation(blocks, speed=0.3)
        self._refresh_table()
        self._update_metrics()

    def _update_metrics(self):
        """更新性能指标"""
        metrics = self.scheduler.get_metrics()
        if metrics:
            self.avg_waiting_label.setText(
                f"平均等待时间: {metrics['avg_waiting_time']}")
            self.avg_turnaround_label.setText(
                f"平均周转时间: {metrics['avg_turnaround_time']}")
            self.total_time_label.setText(
                f"总执行时间: {metrics['total_time']}")

    def _clear_all(self):
        """清空所有"""
        self.scheduler.clear_processes()
        self.gantt_chart.clear()
        self._refresh_table()
        self.avg_waiting_label.setText("平均等待时间: -")
        self.avg_turnaround_label.setText("平均周转时间: -")
        self.total_time_label.setText("总执行时间: -")

    def _load_sample_data(self):
        """加载示例数据"""
        self._clear_all()

        # 添加示例进程
        sample_data = [
            (1, "P1", 0, 5, 3),
            (2, "P2", 1, 3, 1),
            (3, "P3", 2, 8, 4),
            (4, "P4", 3, 2, 2),
            (5, "P5", 4, 4, 5),
        ]

        for pid, name, arrival, burst, priority in sample_data:
            self.scheduler.add_process(pid, name, arrival, burst, priority)

        self._refresh_table()
