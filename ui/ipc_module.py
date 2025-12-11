"""
模块2：进程间通信（IPC）机制界面
生产者-消费者模型可视化
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QGroupBox, QLabel, QSlider, QSpinBox, QTextEdit,
                             QListWidget, QListWidgetItem, QSplitter, QFrame)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QColor, QTextCursor
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.ipc import IPCManager, IPCEvent, IPCEventType, BufferItem
from visualization.buffer_animation import BufferAnimationWidget
from typing import List


class SignalBridge(QObject):
    """信号桥接器（用于线程安全的UI更新）"""
    buffer_changed = pyqtSignal(list, int)
    event_occurred = pyqtSignal(object)


class IPCModule(QWidget):
    """进程间通信模块"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ipc_manager = IPCManager(buffer_capacity=10)

        # 信号桥接
        self.signal_bridge = SignalBridge()
        self.signal_bridge.buffer_changed.connect(self._on_buffer_changed)
        self.signal_bridge.event_occurred.connect(self._on_event)

        # 设置回调
        self.ipc_manager.set_buffer_change_callback(self._buffer_callback)
        self.ipc_manager.set_event_callback(self._event_callback)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # 顶部控制区
        top_panel = QWidget()
        top_layout = QHBoxLayout(top_panel)

        # 缓冲区设置
        buffer_group = QGroupBox("缓冲区设置")
        buffer_layout = QHBoxLayout(buffer_group)

        buffer_layout.addWidget(QLabel("容量:"))
        self.capacity_spin = QSpinBox()
        self.capacity_spin.setRange(5, 20)
        self.capacity_spin.setValue(10)
        self.capacity_spin.valueChanged.connect(self._on_capacity_changed)
        buffer_layout.addWidget(self.capacity_spin)

        buffer_layout.addStretch()
        top_layout.addWidget(buffer_group)

        # 控制按钮
        control_group = QGroupBox("控制")
        control_layout = QHBoxLayout(control_group)

        self.start_btn = QPushButton("开始")
        self.start_btn.clicked.connect(self._start)
        self.start_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        control_layout.addWidget(self.start_btn)

        self.pause_btn = QPushButton("暂停")
        self.pause_btn.clicked.connect(self._pause)
        self.pause_btn.setEnabled(False)
        control_layout.addWidget(self.pause_btn)

        self.stop_btn = QPushButton("停止")
        self.stop_btn.clicked.connect(self._stop)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("background-color: #f44336; color: white;")
        control_layout.addWidget(self.stop_btn)

        self.reset_btn = QPushButton("重置")
        self.reset_btn.clicked.connect(self._reset)
        control_layout.addWidget(self.reset_btn)

        top_layout.addWidget(control_group)
        layout.addWidget(top_panel)

        # 中部可视化区域
        middle_panel = QWidget()
        middle_layout = QHBoxLayout(middle_panel)

        # 生产者控制
        producer_group = QGroupBox("生产者")
        producer_layout = QVBoxLayout(producer_group)

        add_producer_btn = QPushButton("+ 添加生产者")
        add_producer_btn.clicked.connect(self._add_producer)
        add_producer_btn.setStyleSheet("background-color: #66BB6A;")
        producer_layout.addWidget(add_producer_btn)

        producer_layout.addWidget(QLabel("生产速率:"))
        self.producer_rate_slider = QSlider(Qt.Horizontal)
        self.producer_rate_slider.setRange(1, 30)
        self.producer_rate_slider.setValue(10)
        self.producer_rate_slider.valueChanged.connect(self._update_producer_rate)
        producer_layout.addWidget(self.producer_rate_slider)
        self.producer_rate_label = QLabel("1.0 秒/个")
        producer_layout.addWidget(self.producer_rate_label)

        self.producer_list = QListWidget()
        producer_layout.addWidget(self.producer_list)

        remove_producer_btn = QPushButton("- 移除选中")
        remove_producer_btn.clicked.connect(self._remove_producer)
        producer_layout.addWidget(remove_producer_btn)

        middle_layout.addWidget(producer_group)

        # 缓冲区可视化
        buffer_group = QGroupBox("共享缓冲区")
        buffer_layout = QVBoxLayout(buffer_group)
        self.buffer_widget = BufferAnimationWidget(10)
        buffer_layout.addWidget(self.buffer_widget)
        middle_layout.addWidget(buffer_group, stretch=2)

        # 消费者控制
        consumer_group = QGroupBox("消费者")
        consumer_layout = QVBoxLayout(consumer_group)

        add_consumer_btn = QPushButton("+ 添加消费者")
        add_consumer_btn.clicked.connect(self._add_consumer)
        add_consumer_btn.setStyleSheet("background-color: #42A5F5;")
        consumer_layout.addWidget(add_consumer_btn)

        consumer_layout.addWidget(QLabel("消费速率:"))
        self.consumer_rate_slider = QSlider(Qt.Horizontal)
        self.consumer_rate_slider.setRange(1, 30)
        self.consumer_rate_slider.setValue(15)
        self.consumer_rate_slider.valueChanged.connect(self._update_consumer_rate)
        consumer_layout.addWidget(self.consumer_rate_slider)
        self.consumer_rate_label = QLabel("1.5 秒/个")
        consumer_layout.addWidget(self.consumer_rate_label)

        self.consumer_list = QListWidget()
        consumer_layout.addWidget(self.consumer_list)

        remove_consumer_btn = QPushButton("- 移除选中")
        remove_consumer_btn.clicked.connect(self._remove_consumer)
        consumer_layout.addWidget(remove_consumer_btn)

        middle_layout.addWidget(consumer_group)

        layout.addWidget(middle_panel, stretch=2)

        # 底部日志区域
        log_group = QGroupBox("事件日志")
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)

        clear_log_btn = QPushButton("清空日志")
        clear_log_btn.clicked.connect(lambda: self.log_text.clear())
        log_layout.addWidget(clear_log_btn)

        layout.addWidget(log_group)

        # 初始化一个生产者和消费者
        self._add_producer()
        self._add_consumer()

    def _buffer_callback(self, items: List[BufferItem], capacity: int):
        """缓冲区变化回调（线程安全）"""
        self.signal_bridge.buffer_changed.emit(items, capacity)

    def _event_callback(self, event: IPCEvent):
        """事件回调（线程安全）"""
        self.signal_bridge.event_occurred.emit(event)

    def _on_buffer_changed(self, items: List[BufferItem], capacity: int):
        """处理缓冲区变化"""
        self.buffer_widget.update_buffer(items, capacity)

    def _on_event(self, event: IPCEvent):
        """处理事件"""
        color_map = {
            IPCEventType.PRODUCE: "#27ae60",
            IPCEventType.CONSUME: "#3498db",
            IPCEventType.WAIT_FULL: "#e74c3c",
            IPCEventType.WAIT_EMPTY: "#f39c12",
            IPCEventType.WAKE_UP: "#9b59b6",
        }
        color = color_map.get(event.event_type, "#333")

        item_info = f" [{event.item.value}]" if event.item else ""
        msg = f"<span style='color:{color}'>[{event.event_type.value}] {event.actor_name}{item_info} (缓冲区: {event.buffer_size})</span>"
        self.log_text.append(msg)

        # 自动滚动到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_text.setTextCursor(cursor)

    def _on_capacity_changed(self, value: int):
        """缓冲区容量变化"""
        self.ipc_manager.buffer.capacity = value
        self.buffer_widget.set_capacity(value)

    def _add_producer(self):
        """添加生产者"""
        rate = self.producer_rate_slider.value() / 10.0
        producer = self.ipc_manager.add_producer(rate)
        item = QListWidgetItem(f"生产者{producer.producer_id} (速率: {rate}s)")
        item.setData(Qt.UserRole, producer.producer_id)
        self.producer_list.addItem(item)

    def _add_consumer(self):
        """添加消费者"""
        rate = self.consumer_rate_slider.value() / 10.0
        consumer = self.ipc_manager.add_consumer(rate)
        item = QListWidgetItem(f"消费者{consumer.consumer_id} (速率: {rate}s)")
        item.setData(Qt.UserRole, consumer.consumer_id)
        self.consumer_list.addItem(item)

    def _remove_producer(self):
        """移除选中的生产者"""
        selected = self.producer_list.currentItem()
        if selected:
            producer_id = selected.data(Qt.UserRole)
            if self.ipc_manager.remove_producer(producer_id):
                self.producer_list.takeItem(self.producer_list.row(selected))

    def _remove_consumer(self):
        """移除选中的消费者"""
        selected = self.consumer_list.currentItem()
        if selected:
            consumer_id = selected.data(Qt.UserRole)
            if self.ipc_manager.remove_consumer(consumer_id):
                self.consumer_list.takeItem(self.consumer_list.row(selected))

    def _update_producer_rate(self, value: int):
        """更新生产速率显示"""
        rate = value / 10.0
        self.producer_rate_label.setText(f"{rate:.1f} 秒/个")
        # 更新所有生产者的速率
        for producer in self.ipc_manager.producers:
            producer.set_rate(rate)

    def _update_consumer_rate(self, value: int):
        """更新消费速率显示"""
        rate = value / 10.0
        self.consumer_rate_label.setText(f"{rate:.1f} 秒/个")
        # 更新所有消费者的速率
        for consumer in self.ipc_manager.consumers:
            consumer.set_rate(rate)

    def _start(self):
        """开始模拟"""
        self.ipc_manager.start()
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.capacity_spin.setEnabled(False)
        self.log_text.append("<b>--- 模拟开始 ---</b>")

    def _pause(self):
        """暂停/恢复"""
        if self.pause_btn.text() == "暂停":
            self.ipc_manager.pause()
            self.pause_btn.setText("继续")
            self.log_text.append("<i>--- 模拟暂停 ---</i>")
        else:
            self.ipc_manager.resume()
            self.pause_btn.setText("暂停")
            self.log_text.append("<i>--- 模拟继续 ---</i>")

    def _stop(self):
        """停止模拟"""
        self.ipc_manager.stop()
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.pause_btn.setText("暂停")
        self.stop_btn.setEnabled(False)
        self.capacity_spin.setEnabled(True)
        self.log_text.append("<b>--- 模拟停止 ---</b>")

    def _reset(self):
        """重置"""
        self._stop()
        self.ipc_manager.reset()
        self.producer_list.clear()
        self.consumer_list.clear()
        self.buffer_widget.clear()
        self.log_text.clear()

        # 重新添加默认的生产者和消费者
        self._add_producer()
        self._add_consumer()

    def closeEvent(self, event):
        """关闭时停止线程"""
        self.ipc_manager.stop()
        super().closeEvent(event)
