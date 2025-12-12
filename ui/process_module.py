"""
模块1：进程与线程的创建与管理界面
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QGroupBox, QLabel,
                             QLineEdit, QMessageBox, QHeaderView,
                             QSplitter, QComboBox, QTabWidget, QTextEdit)
from PyQt5.QtCore import Qt, QTimer, QDateTime
from PyQt5.QtGui import QColor
import sys
import os
import random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.process import Process, ProcessState, ProcessManager, Thread, ThreadState
from visualization.state_machine import StateMachineWidget
from visualization.queue_animation import QueueAnimationWidget


class ProcessModule(QWidget):
    """进程与线程管理模块"""

    STATE_COLORS = {
        ProcessState.CREATED: QColor(150, 150, 150),
        ProcessState.READY: QColor(100, 180, 100),
        ProcessState.RUNNING: QColor(100, 150, 220),
        ProcessState.BLOCKED: QColor(220, 180, 100),
        ProcessState.TERMINATED: QColor(180, 100, 100),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.process_manager = ProcessManager()
        self.process_manager.add_state_change_callback(self._on_state_change)
        self.process_manager.add_thread_state_change_callback(self._on_thread_state_change)
        self._init_ui()
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._refresh_display)
        self._update_timer.start(500)

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(15)

        # 左侧：控制面板和进程/线程列表
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # ========== 进程控制区域 ==========
        process_group = QGroupBox("进程管理")
        process_layout = QVBoxLayout(process_group)

        # 创建进程控制
        create_process_layout = QHBoxLayout()
        create_process_layout.addWidget(QLabel("进程名称:"))
        self.process_name_input = QLineEdit("Process")
        self.process_name_input.setMaximumWidth(100)
        create_process_layout.addWidget(self.process_name_input)

        create_process_btn = QPushButton("创建进程")
        create_process_btn.clicked.connect(self._create_process)
        create_process_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        create_process_layout.addWidget(create_process_btn)
        create_process_layout.addStretch()
        process_layout.addLayout(create_process_layout)

        # 进程列表
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(3)
        self.process_table.setHorizontalHeaderLabels(["PID", "名称", "状态"])
        self.process_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.process_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.process_table.setSelectionMode(QTableWidget.SingleSelection)
        self.process_table.setMaximumHeight(150)
        process_layout.addWidget(self.process_table)

        # 进程状态转换控制
        process_control_layout = QHBoxLayout()

        self.ready_btn = QPushButton("就绪")
        self.ready_btn.clicked.connect(lambda: self._change_process_state("ready"))
        self.ready_btn.setStyleSheet("background-color: #66BB6A;")
        process_control_layout.addWidget(self.ready_btn)

        self.run_btn = QPushButton("运行")
        self.run_btn.clicked.connect(lambda: self._change_process_state("run"))
        self.run_btn.setStyleSheet("background-color: #42A5F5;")
        process_control_layout.addWidget(self.run_btn)

        self.block_btn = QPushButton("阻塞")
        self.block_btn.clicked.connect(lambda: self._change_process_state("block"))
        self.block_btn.setStyleSheet("background-color: #FFA726;")
        process_control_layout.addWidget(self.block_btn)

        self.terminate_btn = QPushButton("终止")
        self.terminate_btn.clicked.connect(lambda: self._change_process_state("terminate"))
        self.terminate_btn.setStyleSheet("background-color: #EF5350; color: white;")
        process_control_layout.addWidget(self.terminate_btn)

        self.delete_process_btn = QPushButton("删除")
        self.delete_process_btn.clicked.connect(self._delete_process)
        self.delete_process_btn.setStyleSheet("background-color: #B71C1C; color: white;")
        process_control_layout.addWidget(self.delete_process_btn)

        process_layout.addLayout(process_control_layout)
        left_layout.addWidget(process_group)

        # ========== 线程控制区域 ==========
        thread_group = QGroupBox("线程管理")
        thread_layout = QVBoxLayout(thread_group)

        # 创建线程控制
        create_thread_layout = QHBoxLayout()
        create_thread_layout.addWidget(QLabel("线程名称:"))
        self.thread_name_input = QLineEdit("Thread")
        self.thread_name_input.setMaximumWidth(100)
        create_thread_layout.addWidget(self.thread_name_input)

        create_thread_btn = QPushButton("在选中进程下创建线程")
        create_thread_btn.clicked.connect(self._create_thread)
        create_thread_btn.setStyleSheet("background-color: #2196F3; color: white;")
        create_thread_layout.addWidget(create_thread_btn)
        create_thread_layout.addStretch()
        thread_layout.addLayout(create_thread_layout)

        # 线程列表
        self.thread_table = QTableWidget()
        self.thread_table.setColumnCount(3)
        self.thread_table.setHorizontalHeaderLabels(["TID", "所属PID", "名称"])
        self.thread_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.thread_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.thread_table.setSelectionMode(QTableWidget.SingleSelection)
        self.thread_table.setMaximumHeight(150)
        thread_layout.addWidget(self.thread_table)

        # 线程删除按钮
        thread_control_layout = QHBoxLayout()

        self.delete_thread_btn = QPushButton("删除线程")
        self.delete_thread_btn.clicked.connect(self._delete_thread)
        self.delete_thread_btn.setStyleSheet("background-color: #B71C1C; color: white;")
        thread_control_layout.addWidget(self.delete_thread_btn)
        thread_control_layout.addStretch()

        thread_layout.addLayout(thread_control_layout)
        left_layout.addWidget(thread_group)

        # 批量操作
        batch_group = QGroupBox("批量操作")
        batch_layout = QHBoxLayout(batch_group)

        batch_create_btn = QPushButton("批量创建(3进程各2线程)")
        batch_create_btn.clicked.connect(self._batch_create)
        batch_layout.addWidget(batch_create_btn)

        reset_btn = QPushButton("重置全部")
        reset_btn.clicked.connect(self._reset_all)
        batch_layout.addWidget(reset_btn)

        left_layout.addWidget(batch_group)

        layout.addWidget(left_panel, stretch=1)

        # 右侧：可视化区域
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # 状态机图
        state_group = QGroupBox("进程状态机")
        state_layout = QVBoxLayout(state_group)
        self.state_machine = StateMachineWidget()
        state_layout.addWidget(self.state_machine)
        right_layout.addWidget(state_group)

        # 队列可视化
        queue_group = QGroupBox("进程队列")
        queue_layout = QVBoxLayout(queue_group)
        self.queue_widget = QueueAnimationWidget()
        queue_layout.addWidget(self.queue_widget)
        right_layout.addWidget(queue_group)

        # 操作日志
        log_group = QGroupBox("操作日志")
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)

        clear_log_btn = QPushButton("清空日志")
        clear_log_btn.clicked.connect(lambda: self.log_text.clear())
        log_layout.addWidget(clear_log_btn)
        right_layout.addWidget(log_group)

        layout.addWidget(right_panel, stretch=1)

    def _create_process(self):
        """创建新进程"""
        name = self.process_name_input.text() or "Process"
        process = self.process_manager.create_process(name)
        self._refresh_display()

    def _create_thread(self):
        """在选中进程下创建新线程"""
        pid = self._get_selected_pid()
        if pid < 0:
            QMessageBox.warning(self, "提示", "请先选择一个进程")
            return

        process = self.process_manager.get_process(pid)
        if not process:
            return

        if process.state != ProcessState.RUNNING:
            QMessageBox.warning(self, "提示", "只有运行态的进程才能创建线程")
            return

        name = self.thread_name_input.text() or "Thread"
        thread = self.process_manager.create_thread(pid, name)
        if thread:
            self._refresh_display()
        else:
            QMessageBox.warning(self, "创建失败", "无法创建线程")

    def _batch_create(self):
        """批量创建进程和线程"""
        for i in range(3):
            process = self.process_manager.create_process(f"P{i+1}")
            # 进程需先转为就绪态，再转为运行态才能创建线程
            self.process_manager.ready(process.pid)
            self.process_manager.run(process.pid)
            # 在每个进程下创建2个线程
            for j in range(2):
                self.process_manager.create_thread(process.pid, f"T{i+1}-{j+1}")
            # 创建完线程后，随机进入就绪态或阻塞态
            if random.choice([True, False]):
                self.process_manager.block(process.pid)
            else:
                self.process_manager.ready(process.pid)
        self._refresh_display()

    def _get_selected_pid(self) -> int:
        """获取选中的进程PID"""
        selected = self.process_table.selectedItems()
        if not selected:
            return -1
        row = selected[0].row()
        pid_item = self.process_table.item(row, 0)
        return int(pid_item.text()) if pid_item else -1

    def _get_selected_tid(self) -> int:
        """获取选中的线程TID"""
        selected = self.thread_table.selectedItems()
        if not selected:
            return -1
        row = selected[0].row()
        tid_item = self.thread_table.item(row, 0)
        return int(tid_item.text()) if tid_item else -1

    def _change_process_state(self, action: str):
        """改变进程状态"""
        pid = self._get_selected_pid()
        if pid < 0:
            QMessageBox.warning(self, "提示", "请先选择一个进程")
            return

        process = self.process_manager.get_process(pid)
        if not process:
            return

        old_state = process.state
        success = False

        if action == "ready":
            success = self.process_manager.ready(pid)
        elif action == "run":
            success = self.process_manager.run(pid)
        elif action == "block":
            success = self.process_manager.block(pid)
        elif action == "terminate":
            success = self.process_manager.terminate(pid)

        if not success:
            QMessageBox.warning(self, "操作失败",
                               f"无法将进程从 {old_state.value} 转换到目标状态")

    def _delete_process(self):
        """删除进程"""
        pid = self._get_selected_pid()
        if pid < 0:
            QMessageBox.warning(self, "提示", "请先选择一个进程")
            return

        # 删除进程下的所有线程
        process = self.process_manager.get_process(pid)
        if process:
            process_name = process.name
            for tid in process.threads.copy():
                thread = self.process_manager.get_thread(tid)
                if thread:
                    self._log(f"  └─ 线程 {thread.name}(TID={tid}) 被删除")
                self.process_manager.delete_thread(tid)

            self.process_manager.delete_process(pid)
            self._log(f"进程 {process_name}(PID={pid}) 被删除")
        self._refresh_display()

    def _delete_thread(self):
        """删除线程"""
        tid = self._get_selected_tid()
        if tid < 0:
            QMessageBox.warning(self, "提示", "请先选择一个线程")
            return

        thread = self.process_manager.get_thread(tid)
        if thread:
            self._log(f"线程 {thread.name}(TID={tid}) 被删除")
        self.process_manager.delete_thread(tid)
        self._refresh_display()

    def _reset_all(self):
        """重置所有进程和线程"""
        self.process_manager.reset()
        self._log("系统重置，清空所有进程和线程")
        self._refresh_display()

    def _log(self, message: str):
        """添加日志"""
        time_str = QDateTime.currentDateTime().toString("hh:mm:ss")
        self.log_text.append(f"[{time_str}] {message}")
        # 滚动到底部
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    def _on_state_change(self, process: Process, old_state: ProcessState,
                        new_state: ProcessState):
        """进程状态变化回调"""
        # 记录日志
        if old_state is None:
            self._log(f"进程 {process.name}(PID={process.pid}) 创建")
        else:
            self._log(f"进程 {process.name}(PID={process.pid}): {old_state.value} → {new_state.value}")

        self._refresh_display()

        # 更新状态机显示
        self.state_machine.set_current_state(new_state.value)

        # 高亮状态转换
        if old_state:
            self.state_machine.highlight_transition(old_state.value, new_state.value)

    def _on_thread_state_change(self, thread: Thread, old_state: ThreadState,
                                new_state: ThreadState):
        """线程状态变化回调"""
        # 记录日志
        if old_state is None:
            self._log(f"  └─ 线程 {thread.name}(TID={thread.tid}) 在进程 PID={thread.pid} 下创建")

        self._refresh_display()

    def _refresh_display(self):
        """刷新显示"""
        # 更新进程表格
        processes = self.process_manager.get_all_processes()
        self.process_table.setRowCount(len(processes))

        for row, process in enumerate(processes):
            self.process_table.setItem(row, 0, QTableWidgetItem(str(process.pid)))
            self.process_table.setItem(row, 1, QTableWidgetItem(process.name))

            state_item = QTableWidgetItem(process.state.value)
            color = self.STATE_COLORS.get(process.state)
            if color:
                state_item.setBackground(color)
                state_item.setForeground(QColor(255, 255, 255))
            self.process_table.setItem(row, 2, state_item)

        # 更新线程表格
        threads = self.process_manager.get_all_threads()
        self.thread_table.setRowCount(len(threads))

        for row, thread in enumerate(threads):
            self.thread_table.setItem(row, 0, QTableWidgetItem(str(thread.tid)))
            self.thread_table.setItem(row, 1, QTableWidgetItem(str(thread.pid)))
            self.thread_table.setItem(row, 2, QTableWidgetItem(thread.name))

        # 更新队列显示
        running = self.process_manager.get_running_process()
        ready = self.process_manager.get_ready_queue()
        blocked = self.process_manager.get_blocked_queue()
        self.queue_widget.update_queues(running, ready, blocked)
