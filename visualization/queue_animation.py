"""
进程队列动画组件
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont
from PyQt5.QtCore import Qt, QRectF, QPropertyAnimation, QEasingCurve, pyqtProperty
from typing import List, Optional
import sys
sys.path.append('..')
from core.process import Process, ProcessState


class ProcessBlock(QWidget):
    """进程块组件"""

    STATE_COLORS = {
        ProcessState.CREATED: QColor(150, 150, 150),
        ProcessState.READY: QColor(100, 180, 100),
        ProcessState.RUNNING: QColor(100, 150, 220),
        ProcessState.BLOCKED: QColor(220, 180, 100),
        ProcessState.TERMINATED: QColor(180, 100, 100),
    }

    def __init__(self, process: Process, parent=None):
        super().__init__(parent)
        self.process = process
        self.setFixedSize(60, 50)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 获取状态颜色
        color = self.STATE_COLORS.get(self.process.state, QColor(150, 150, 150))

        # 绘制圆角矩形
        painter.setPen(QPen(color.darker(120), 2))
        painter.setBrush(QBrush(color))
        rect = QRectF(2, 2, self.width() - 4, self.height() - 4)
        painter.drawRoundedRect(rect, 5, 5)

        # 绘制进程信息
        painter.setPen(QPen(QColor(255, 255, 255)))
        font = QFont("Microsoft YaHei", 8, QFont.Bold)
        painter.setFont(font)

        # PID
        painter.drawText(rect.adjusted(0, 5, 0, 0), Qt.AlignHCenter | Qt.AlignTop,
                        f"P{self.process.pid}")
        # 名称（简化）
        name = self.process.name[:4] if len(self.process.name) > 4 else self.process.name
        painter.drawText(rect.adjusted(0, 0, 0, -5), Qt.AlignHCenter | Qt.AlignBottom, name)


class QueueWidget(QWidget):
    """单个队列组件"""

    def __init__(self, title: str, color: QColor, parent=None):
        super().__init__(parent)
        self.title = title
        self.color = color
        self.processes: List[Process] = []

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # 标题
        self.title_label = QLabel(self.title)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet(f"""
            QLabel {{
                background-color: {self.color.name()};
                color: white;
                font-weight: bold;
                padding: 5px;
                border-radius: 3px;
            }}
        """)
        layout.addWidget(self.title_label)

        # 进程容器
        self.process_container = QWidget()
        self.process_layout = QHBoxLayout(self.process_container)
        self.process_layout.setContentsMargins(5, 5, 5, 5)
        self.process_layout.setSpacing(5)
        self.process_layout.addStretch()

        # 边框
        self.process_container.setStyleSheet("""
            QWidget {
                border: 2px dashed #ccc;
                border-radius: 5px;
                min-height: 70px;
            }
        """)
        layout.addWidget(self.process_container)

    def set_processes(self, processes: List[Process]):
        """设置进程列表"""
        self.processes = processes

        # 清除现有组件
        while self.process_layout.count() > 1:
            item = self.process_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 添加新的进程块
        for process in processes:
            block = ProcessBlock(process)
            self.process_layout.insertWidget(self.process_layout.count() - 1, block)

        # 更新标题
        self.title_label.setText(f"{self.title} ({len(processes)})")


class QueueAnimationWidget(QWidget):
    """进程队列动画组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # 运行队列（单个进程）
        self.running_queue = QueueWidget("运行中", QColor(100, 150, 220))
        layout.addWidget(self.running_queue)

        # 就绪队列
        self.ready_queue = QueueWidget("就绪队列", QColor(100, 180, 100))
        layout.addWidget(self.ready_queue)

        # 阻塞队列
        self.blocked_queue = QueueWidget("阻塞队列", QColor(220, 180, 100))
        layout.addWidget(self.blocked_queue)

        layout.addStretch()

    def update_queues(self, running: Optional[Process],
                      ready: List[Process], blocked: List[Process]):
        """更新所有队列"""
        self.running_queue.set_processes([running] if running else [])
        self.ready_queue.set_processes(ready)
        self.blocked_queue.set_processes(blocked)

    def set_running(self, process: Optional[Process]):
        """设置运行中的进程"""
        self.running_queue.set_processes([process] if process else [])

    def set_ready_queue(self, processes: List[Process]):
        """设置就绪队列"""
        self.ready_queue.set_processes(processes)

    def set_blocked_queue(self, processes: List[Process]):
        """设置阻塞队列"""
        self.blocked_queue.set_processes(processes)
