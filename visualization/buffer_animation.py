"""
共享缓冲区动画组件（用于生产者-消费者模型）
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QLinearGradient
from PyQt5.QtCore import Qt, QRectF, QTimer, QPropertyAnimation, QEasingCurve
from typing import List, Optional
import sys
sys.path.append('..')
from core.ipc import BufferItem


class BufferSlotWidget(QWidget):
    """缓冲区槽位组件"""

    def __init__(self, index: int, parent=None):
        super().__init__(parent)
        self.index = index
        self.item: Optional[BufferItem] = None
        self.setFixedSize(50, 50)

    def set_item(self, item: Optional[BufferItem]):
        """设置槽位中的项"""
        self.item = item
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(2, 2, self.width() - 4, self.height() - 4)

        if self.item:
            # 有数据 - 显示填充状态
            gradient = QLinearGradient(0, 0, 0, self.height())
            gradient.setColorAt(0, QColor(100, 180, 220))
            gradient.setColorAt(1, QColor(60, 140, 180))

            painter.setPen(QPen(QColor(60, 140, 180), 2))
            painter.setBrush(QBrush(gradient))
            painter.drawRoundedRect(rect, 5, 5)

            # 显示数据ID
            painter.setPen(QPen(QColor(255, 255, 255)))
            font = QFont("Microsoft YaHei", 8, QFont.Bold)
            painter.setFont(font)
            painter.drawText(rect, Qt.AlignCenter, f"{self.item.id}")
        else:
            # 空槽位
            painter.setPen(QPen(QColor(180, 180, 180), 2, Qt.DashLine))
            painter.setBrush(QBrush(QColor(240, 240, 240)))
            painter.drawRoundedRect(rect, 5, 5)


class BufferAnimationWidget(QWidget):
    """共享缓冲区动画组件"""

    def __init__(self, capacity: int = 10, parent=None):
        super().__init__(parent)
        self.capacity = capacity
        self.slots: List[BufferSlotWidget] = []
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # 标题
        title = QLabel("共享缓冲区")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #333;
            }
        """)
        layout.addWidget(title)

        # 缓冲区容器
        buffer_container = QWidget()
        buffer_layout = QHBoxLayout(buffer_container)
        buffer_layout.setSpacing(5)
        buffer_layout.setContentsMargins(10, 10, 10, 10)

        # 创建槽位
        for i in range(self.capacity):
            slot = BufferSlotWidget(i)
            self.slots.append(slot)
            buffer_layout.addWidget(slot)

        buffer_container.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                border: 2px solid #ccc;
                border-radius: 8px;
            }
        """)
        layout.addWidget(buffer_container)

        # 状态信息
        self.status_label = QLabel("容量: 0 / " + str(self.capacity))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #666;")
        layout.addWidget(self.status_label)

    def update_buffer(self, items: List[BufferItem], capacity: int):
        """更新缓冲区显示"""
        # 更新容量（如果变化）
        if capacity != self.capacity:
            self._resize_slots(capacity)

        # 更新槽位内容
        for i, slot in enumerate(self.slots):
            if i < len(items):
                slot.set_item(items[i])
            else:
                slot.set_item(None)

        # 更新状态
        self.status_label.setText(f"容量: {len(items)} / {self.capacity}")

        # 根据填充程度改变状态颜色
        fill_ratio = len(items) / self.capacity if self.capacity > 0 else 0
        if fill_ratio >= 0.9:
            color = "#e74c3c"  # 红色 - 接近满
        elif fill_ratio >= 0.7:
            color = "#f39c12"  # 橙色 - 较多
        elif fill_ratio <= 0.1:
            color = "#3498db"  # 蓝色 - 较少
        else:
            color = "#27ae60"  # 绿色 - 正常

        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold;")

    def _resize_slots(self, new_capacity: int):
        """调整槽位数量"""
        self.capacity = new_capacity

        # 获取布局
        container = self.slots[0].parent() if self.slots else None
        if not container:
            return

        layout = container.layout()

        # 移除多余槽位
        while len(self.slots) > new_capacity:
            slot = self.slots.pop()
            layout.removeWidget(slot)
            slot.deleteLater()

        # 添加新槽位
        while len(self.slots) < new_capacity:
            slot = BufferSlotWidget(len(self.slots))
            self.slots.append(slot)
            layout.addWidget(slot)

    def set_capacity(self, capacity: int):
        """设置缓冲区容量"""
        self._resize_slots(capacity)
        self.update_buffer([], capacity)

    def clear(self):
        """清空缓冲区显示"""
        for slot in self.slots:
            slot.set_item(None)
        self.status_label.setText(f"容量: 0 / {self.capacity}")


class ProducerConsumerWidget(QWidget):
    """生产者-消费者完整可视化组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(20)

        # 生产者区域
        self.producer_frame = self._create_actor_frame("生产者", QColor(100, 200, 100))
        layout.addWidget(self.producer_frame)

        # 缓冲区
        self.buffer_widget = BufferAnimationWidget(10)
        layout.addWidget(self.buffer_widget, stretch=2)

        # 消费者区域
        self.consumer_frame = self._create_actor_frame("消费者", QColor(100, 150, 220))
        layout.addWidget(self.consumer_frame)

    def _create_actor_frame(self, title: str, color: QColor) -> QFrame:
        """创建生产者/消费者框架"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {color.lighter(150).name()};
                border: 2px solid {color.name()};
                border-radius: 8px;
                min-width: 100px;
            }}
        """)

        layout = QVBoxLayout(frame)

        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                font-weight: bold;
                color: {color.darker(120).name()};
                padding: 5px;
            }}
        """)
        layout.addWidget(title_label)

        self.actor_list = QVBoxLayout()
        layout.addLayout(self.actor_list)
        layout.addStretch()

        return frame

    def update_buffer(self, items: List[BufferItem], capacity: int):
        """更新缓冲区"""
        self.buffer_widget.update_buffer(items, capacity)

    def set_buffer_capacity(self, capacity: int):
        """设置缓冲区容量"""
        self.buffer_widget.set_capacity(capacity)
