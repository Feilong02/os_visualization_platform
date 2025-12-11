"""
模块3：基于信号量的进程同步界面
哲学家就餐问题可视化
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QGroupBox, QLabel, QSlider, QCheckBox, QTextEdit,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QSpinBox, QSizePolicy, QScrollArea, QFrame)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QColor, QTextCursor
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.synchronization import DiningPhilosophers, PhilosopherState, SemaphoreLog
from visualization.philosopher_table import PhilosopherTableWidget


class SignalBridge(QObject):
    """信号桥接器"""
    state_changed = pyqtSignal(int, object)
    log_received = pyqtSignal(object)
    fork_changed = pyqtSignal(list)
    deadlock_detected = pyqtSignal()


class SyncModule(QWidget):
    """进程同步模块"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.dining = DiningPhilosophers(5)

        # 信号桥接
        self.signal_bridge = SignalBridge()
        self.signal_bridge.state_changed.connect(self._on_state_changed)
        self.signal_bridge.log_received.connect(self._on_log)
        self.signal_bridge.fork_changed.connect(self._on_fork_changed)

        # 设置回调
        self.dining.set_state_callback(self._state_callback)
        self.dining.set_log_callback(self._log_callback)
        self.dining.set_fork_state_callback(self._fork_callback)

        # 死锁检测定时器
        self.deadlock_timer = QTimer()
        self.deadlock_timer.timeout.connect(self._check_deadlock)
        self.signal_bridge.deadlock_detected.connect(self._on_deadlock_detected)
        self._deadlock_warned = False

        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # 左侧控制面板
        left_panel = QWidget()
        left_panel.setMaximumWidth(350)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(6)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # 控制按钮
        control_group = QGroupBox("控制")
        control_layout = QVBoxLayout(control_group)
        control_layout.setSpacing(5)
        control_layout.setContentsMargins(8, 12, 8, 8)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(5)
        self.start_btn = QPushButton("开始")
        self.start_btn.clicked.connect(self._start)
        self.start_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        btn_layout.addWidget(self.start_btn)

        self.pause_btn = QPushButton("暂停")
        self.pause_btn.clicked.connect(self._pause)
        self.pause_btn.setEnabled(False)
        btn_layout.addWidget(self.pause_btn)

        self.stop_btn = QPushButton("停止")
        self.stop_btn.clicked.connect(self._stop)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("background-color: #f44336; color: white;")
        btn_layout.addWidget(self.stop_btn)

        control_layout.addLayout(btn_layout)

        # 死锁预防选项
        self.deadlock_check = QCheckBox("启用死锁预防")
        self.deadlock_check.setChecked(True)
        self.deadlock_check.stateChanged.connect(self._on_deadlock_option_changed)
        control_layout.addWidget(self.deadlock_check)

        left_layout.addWidget(control_group)

        # 速度控制 - 使用更紧凑的水平布局
        speed_group = QGroupBox("速度控制")
        speed_layout = QVBoxLayout(speed_group)
        speed_layout.setSpacing(3)
        speed_layout.setContentsMargins(8, 12, 8, 8)

        # 思考时间 - 水平布局
        think_layout = QHBoxLayout()
        think_layout.addWidget(QLabel("思考:"))
        self.think_slider = QSlider(Qt.Horizontal)
        self.think_slider.setRange(5, 50)
        self.think_slider.setValue(20)
        self.think_slider.valueChanged.connect(self._update_speed)
        think_layout.addWidget(self.think_slider)
        self.think_label = QLabel("2.0s")
        self.think_label.setMinimumWidth(35)
        think_layout.addWidget(self.think_label)
        speed_layout.addLayout(think_layout)

        # 进餐时间 - 水平布局
        eat_layout = QHBoxLayout()
        eat_layout.addWidget(QLabel("进餐:"))
        self.eat_slider = QSlider(Qt.Horizontal)
        self.eat_slider.setRange(5, 50)
        self.eat_slider.setValue(20)
        self.eat_slider.valueChanged.connect(self._update_speed)
        eat_layout.addWidget(self.eat_slider)
        self.eat_label = QLabel("2.0s")
        self.eat_label.setMinimumWidth(35)
        eat_layout.addWidget(self.eat_label)
        speed_layout.addLayout(eat_layout)

        left_layout.addWidget(speed_group)

        # 信号量状态表
        sem_group = QGroupBox("信号量状态 (叉子)")
        sem_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sem_layout = QVBoxLayout(sem_group)
        sem_layout.setContentsMargins(5, 10, 5, 5)
        sem_layout.setSpacing(0)

        self.sem_table = QTableWidget()
        self.sem_table.setColumnCount(3)
        self.sem_table.setHorizontalHeaderLabels(["叉子", "值", "等待队列"])
        self.sem_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.sem_table.verticalHeader().setVisible(False)
        self.sem_table.setRowCount(5)
        # 禁用滚动条
        self.sem_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.sem_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # 设置尺寸策略，防止被压缩
        self.sem_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.sem_table.setFixedHeight(230)

        for i in range(5):
            self.sem_table.setItem(i, 0, QTableWidgetItem(f"F{i}"))
            self.sem_table.setItem(i, 1, QTableWidgetItem("1"))
            self.sem_table.setItem(i, 2, QTableWidgetItem("-"))
            self.sem_table.item(i, 1).setBackground(QColor(200, 255, 200))

        sem_layout.addWidget(self.sem_table)
        left_layout.addWidget(sem_group)

        # 操作日志
        log_group = QGroupBox("P/V操作日志")
        log_layout = QVBoxLayout(log_group)
        log_layout.setContentsMargins(8, 12, 8, 8)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)

        clear_btn = QPushButton("清空日志")
        clear_btn.clicked.connect(lambda: self.log_text.clear())
        log_layout.addWidget(clear_btn)

        left_layout.addWidget(log_group, stretch=1)

        layout.addWidget(left_panel)

        # 右侧可视化区域
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        vis_group = QGroupBox("哲学家餐桌")
        vis_layout = QVBoxLayout(vis_group)

        self.table_widget = PhilosopherTableWidget(5)
        vis_layout.addWidget(self.table_widget, stretch=1)

        # 图例说明 - 哲学家状态
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(12)
        legend_items = [
            ("思考", "#3498db"),
            ("饥饿", "#f39c12"),
            ("进餐", "#27ae60"),
        ]
        for text, color in legend_items:
            item_layout = QHBoxLayout()
            item_layout.setSpacing(3)
            color_box = QLabel()
            color_box.setFixedSize(14, 14)
            color_box.setStyleSheet(f"background-color: {color}; border-radius: 3px;")
            item_layout.addWidget(color_box)
            item_layout.addWidget(QLabel(text))
            legend_layout.addLayout(item_layout)

        # 叉子状态图例
        legend_layout.addSpacing(15)
        fork_items = [
            ("叉子可用", "#c0c0c0"),
            ("叉子占用", "#dc5050"),
        ]
        for text, color in fork_items:
            item_layout = QHBoxLayout()
            item_layout.setSpacing(3)
            color_box = QLabel()
            color_box.setFixedSize(14, 14)
            color_box.setStyleSheet(f"background-color: {color}; border-radius: 3px;")
            item_layout.addWidget(color_box)
            item_layout.addWidget(QLabel(text))
            legend_layout.addLayout(item_layout)

        legend_layout.addStretch()
        vis_layout.addLayout(legend_layout)

        # 问题说明
        problem_label = QLabel(
            "哲学家就餐问题：5位哲学家围坐圆桌，每人需要同时拿起左右两把叉子才能进餐。"
        )
        problem_label.setWordWrap(True)
        problem_label.setStyleSheet("color: #666; padding: 5px;")
        vis_layout.addWidget(problem_label)

        # 参数说明
        param_label = QLabel(
            "参数说明：思考时间越短，哲学家越快进入饥饿状态争抢叉子；"
            "进餐时间越长，叉子被占用时间越久，其他哲学家等待越长。"
        )
        param_label.setWordWrap(True)
        param_label.setStyleSheet("color: #888; padding: 3px; font-size: 11px;")
        vis_layout.addWidget(param_label)

        # 死锁预防说明（默认显示）
        self.prevention_label = QLabel(
            "【死锁预防策略】打破循环等待条件：\n"
            "让最后一位哲学家(P4)先拿右边的叉子再拿左边的叉子，\n"
            "而其他哲学家都是先拿左边再拿右边。\n"
            "这样就打破了循环等待，避免了死锁的发生。"
        )
        self.prevention_label.setWordWrap(True)
        self.prevention_label.setStyleSheet("""
            QLabel {
                color: #155724;
                background-color: #d4edda;
                border: 1px solid #c3e6cb;
                padding: 10px;
                border-radius: 5px;
            }
        """)
        vis_layout.addWidget(self.prevention_label)

        # 死锁原因说明（默认隐藏）
        self.deadlock_cause_label = QLabel(
            "【死锁产生条件】当所有哲学家同时拿起左边的叉子时：\n"
            "1. 互斥条件：每把叉子只能被一个哲学家持有\n"
            "2. 持有并等待：每人持有左叉子，等待右叉子\n"
            "3. 不可剥夺：已持有的叉子不能被强制拿走\n"
            "4. 循环等待：P0等P1的叉子，P1等P2的...P4等P0的"
        )
        self.deadlock_cause_label.setWordWrap(True)
        self.deadlock_cause_label.setStyleSheet("""
            QLabel {
                color: #856404;
                background-color: #fff3cd;
                border: 1px solid #ffeeba;
                padding: 10px;
                border-radius: 5px;
            }
        """)
        self.deadlock_cause_label.hide()
        vis_layout.addWidget(self.deadlock_cause_label)

        # 死锁警告标签
        self.deadlock_label = QLabel("")
        self.deadlock_label.setWordWrap(True)
        self.deadlock_label.setStyleSheet("""
            QLabel {
                color: white;
                background-color: #e74c3c;
                padding: 12px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 13px;
            }
        """)
        self.deadlock_label.setAlignment(Qt.AlignCenter)
        self.deadlock_label.hide()
        vis_layout.addWidget(self.deadlock_label)

        right_layout.addWidget(vis_group)

        layout.addWidget(right_panel, stretch=1)

    def _state_callback(self, philosopher_id: int, state: PhilosopherState):
        """哲学家状态变化回调（线程安全）"""
        self.signal_bridge.state_changed.emit(philosopher_id, state)

    def _log_callback(self, log: SemaphoreLog):
        """日志回调（线程安全）"""
        self.signal_bridge.log_received.emit(log)

    def _fork_callback(self, fork_states: list):
        """叉子状态回调（线程安全）"""
        self.signal_bridge.fork_changed.emit(fork_states)

    def _on_state_changed(self, philosopher_id: int, state: PhilosopherState):
        """处理状态变化"""
        self.table_widget.set_philosopher_state(philosopher_id, state)

    def _on_log(self, log: SemaphoreLog):
        """处理日志"""
        color = "#27ae60" if log.operation == "V" else "#e74c3c"
        if log.result == "blocked":
            color = "#f39c12"

        msg = (f"<span style='color:{color}'>"
               f"[{log.operation}] {log.process_name} -> {log.semaphore_name} "
               f"({log.old_value}→{log.new_value}) [{log.result}]"
               f"</span>")
        self.log_text.append(msg)

        # 自动滚动
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_text.setTextCursor(cursor)

    def _on_fork_changed(self, fork_states: list):
        """处理叉子状态变化"""
        self.table_widget.set_fork_states(fork_states)

        # 更新信号量表
        for state in fork_states:
            row = state["id"]
            value = state.get("value", 1 if state["available"] else 0)
            waiting = ", ".join(state["waiting"]) if state["waiting"] else "-"

            self.sem_table.setItem(row, 1, QTableWidgetItem(str(value)))
            self.sem_table.setItem(row, 2, QTableWidgetItem(waiting))

            # 设置颜色
            value_item = self.sem_table.item(row, 1)
            if value > 0:
                value_item.setBackground(QColor(200, 255, 200))
            elif value == 0:
                value_item.setBackground(QColor(255, 255, 200))
            else:
                value_item.setBackground(QColor(255, 200, 200))

    def _on_deadlock_option_changed(self, state: int):
        """死锁预防选项变化"""
        self.dining.set_deadlock_prevention(state == Qt.Checked)
        if state == Qt.Checked:
            # 启用死锁预防：显示预防策略，隐藏死锁原因
            self.prevention_label.show()
            self.deadlock_cause_label.hide()
        else:
            # 关闭死锁预防：隐藏预防策略，显示死锁原因
            self.prevention_label.hide()
            self.deadlock_cause_label.show()

    def _update_speed(self):
        """更新速度"""
        think_time = self.think_slider.value() / 10.0
        eat_time = self.eat_slider.value() / 10.0

        self.think_label.setText(f"{think_time:.1f}s")
        self.eat_label.setText(f"{eat_time:.1f}s")

        self.dining.set_speed(think_time, eat_time)

    def _start(self):
        """开始模拟"""
        self.dining.start()
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.deadlock_check.setEnabled(False)
        self.table_widget.start_animation()
        self.log_text.append("<b>--- 模拟开始 ---</b>")
        self._deadlock_warned = False
        self.deadlock_label.hide()
        self.deadlock_timer.start(500)

    def _pause(self):
        """暂停/恢复"""
        if self.pause_btn.text() == "暂停":
            self.dining.pause()
            self.pause_btn.setText("继续")
            self.log_text.append("<i>--- 模拟暂停 ---</i>")
        else:
            self.dining.resume()
            self.pause_btn.setText("暂停")
            self.log_text.append("<i>--- 模拟继续 ---</i>")

    def _stop(self):
        """停止模拟"""
        self.deadlock_timer.stop()
        self.dining.stop()
        self.table_widget.stop_animation()
        self.table_widget.reset()
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.pause_btn.setText("暂停")
        self.stop_btn.setEnabled(False)
        self.deadlock_check.setEnabled(True)

        # 重置信号量表
        for i in range(5):
            self.sem_table.setItem(i, 1, QTableWidgetItem("1"))
            self.sem_table.setItem(i, 2, QTableWidgetItem("-"))
            self.sem_table.item(i, 1).setBackground(QColor(200, 255, 200))

        self.deadlock_label.hide()
        self._deadlock_warned = False

        self.log_text.append("<b>--- 模拟停止 ---</b>")

    def _check_deadlock(self):
        """定时检测死锁"""
        if self.dining.check_deadlock() and not self._deadlock_warned:
            self.signal_bridge.deadlock_detected.emit()

    def _on_deadlock_detected(self):
        """处理死锁检测"""
        if self._deadlock_warned:
            return
        self._deadlock_warned = True
        self.deadlock_label.setText(
            "检测到死锁！所有哲学家都拿起了左边的叉子，等待右边的叉子，形成循环等待。\n"
            "请点击「停止」并启用「死锁预防」后重试。"
        )
        self.deadlock_label.show()
        self.log_text.append(
            "<span style='color:#e74c3c; font-weight:bold;'>"
            "检测到死锁！系统陷入死锁状态。"
            "</span>"
        )

    def closeEvent(self, event):
        """关闭时停止线程"""
        self.deadlock_timer.stop()
        self.dining.stop()
        super().closeEvent(event)
