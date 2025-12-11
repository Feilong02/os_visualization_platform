"""
哲学家就餐问题可视化组件
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath
from PyQt5.QtCore import Qt, QPointF, QRectF, QTimer
import math
from typing import List, Optional
import sys
sys.path.append('..')
from core.synchronization import PhilosopherState


class PhilosopherTableWidget(QWidget):
    """哲学家餐桌可视化组件"""

    # 状态颜色 - 与UI保持一致
    STATE_COLORS = {
        PhilosopherState.THINKING: QColor(52, 152, 219),    # 蓝色 - 思考
        PhilosopherState.HUNGRY: QColor(243, 156, 18),      # 橙色 - 饥饿
        PhilosopherState.EATING: QColor(39, 174, 96),       # 绿色 - 进餐
    }

    def __init__(self, num_philosophers: int = 5, parent=None):
        super().__init__(parent)
        self.num_philosophers = num_philosophers
        self.setMinimumSize(400, 400)

        # 哲学家状态
        self.philosopher_states: List[PhilosopherState] = [
            PhilosopherState.THINKING] * num_philosophers

        # 叉子状态：True表示可用
        self.fork_available: List[bool] = [True] * num_philosophers

        # 信号量值
        self.semaphore_values: List[int] = [1] * num_philosophers

        # 动画定时器
        self._timer = QTimer()
        self._timer.timeout.connect(self.update)

    def set_philosopher_state(self, philosopher_id: int, state: PhilosopherState):
        """设置哲学家状态"""
        if 0 <= philosopher_id < self.num_philosophers:
            self.philosopher_states[philosopher_id] = state
            self.update()

    def set_fork_state(self, fork_id: int, available: bool):
        """设置叉子状态"""
        if 0 <= fork_id < self.num_philosophers:
            self.fork_available[fork_id] = available
            self.update()

    def set_all_states(self, states: List[PhilosopherState]):
        """设置所有哲学家状态"""
        self.philosopher_states = states[:self.num_philosophers]
        self.update()

    def set_fork_states(self, states: List[dict]):
        """设置所有叉子状态"""
        for state in states:
            fork_id = state.get("id", 0)
            available = state.get("available", True)
            if 0 <= fork_id < self.num_philosophers:
                self.fork_available[fork_id] = available
        self.update()

    def set_semaphore_values(self, values: List[int]):
        """设置信号量值"""
        self.semaphore_values = values[:self.num_philosophers]
        self.update()

    def start_animation(self):
        """启动刷新动画"""
        self._timer.start(100)

    def stop_animation(self):
        """停止刷新动画"""
        self._timer.stop()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 计算中心和半径
        center_x = self.width() // 2
        center_y = self.height() // 2
        table_radius = min(center_x, center_y) - 80
        philosopher_radius = 30
        fork_length = 25

        # 绘制桌子
        self._draw_table(painter, center_x, center_y, table_radius)

        # 绘制叉子
        self._draw_forks(painter, center_x, center_y, table_radius, fork_length)

        # 绘制哲学家
        self._draw_philosophers(painter, center_x, center_y, table_radius + 50, philosopher_radius)

    def _draw_table(self, painter: QPainter, cx: int, cy: int, radius: int):
        """绘制圆桌"""
        painter.setPen(QPen(QColor(139, 90, 43), 4))
        painter.setBrush(QBrush(QColor(205, 133, 63)))
        painter.drawEllipse(QPointF(cx, cy), radius, radius)

    def _draw_philosophers(self, painter: QPainter, cx: int, cy: int,
                           radius: int, p_radius: int):
        """绘制哲学家"""
        font = QFont("Microsoft YaHei", 9, QFont.Bold)
        painter.setFont(font)

        for i in range(self.num_philosophers):
            # 计算位置（从顶部开始顺时针）
            angle = -math.pi / 2 + 2 * math.pi * i / self.num_philosophers
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)

            # 获取状态颜色
            state = self.philosopher_states[i] if i < len(self.philosopher_states) else PhilosopherState.THINKING
            color = self.STATE_COLORS.get(state, QColor(150, 150, 150))

            # 绘制圆形（哲学家）
            painter.setPen(QPen(color.darker(120), 2))
            painter.setBrush(QBrush(color))
            painter.drawEllipse(QPointF(x, y), p_radius, p_radius)

            # 绘制编号
            painter.setPen(QPen(QColor(255, 255, 255)))
            rect = QRectF(x - p_radius, y - p_radius, p_radius * 2, p_radius * 2)
            painter.drawText(rect, Qt.AlignCenter, f"P{i}")

            # 绘制状态文字
            painter.setPen(QPen(QColor(60, 60, 60)))
            state_text = state.value if state else "思考"
            text_rect = QRectF(x - 25, y + p_radius + 5, 50, 20)
            painter.drawText(text_rect, Qt.AlignCenter, state_text)

    def _draw_forks(self, painter: QPainter, cx: int, cy: int,
                    table_radius: int, fork_length: int):
        """绘制叉子"""
        for i in range(self.num_philosophers):
            # 叉子位置在两个哲学家之间
            angle = -math.pi / 2 + 2 * math.pi * (i + 0.5) / self.num_philosophers
            x = cx + (table_radius - 20) * math.cos(angle)
            y = cy + (table_radius - 20) * math.sin(angle)

            # 叉子是否可用
            available = self.fork_available[i] if i < len(self.fork_available) else True

            if available:
                color = QColor(192, 192, 192)  # 银色 - 可用
            else:
                color = QColor(220, 80, 80)    # 红色 - 被占用

            # 绘制叉子（简化为线条+圆点）
            painter.setPen(QPen(color, 3))

            # 叉子柄
            end_x = x + fork_length * math.cos(angle)
            end_y = y + fork_length * math.sin(angle)
            painter.drawLine(int(x), int(y), int(end_x), int(end_y))

            # 叉子齿
            for offset in [-0.3, 0, 0.3]:
                tooth_angle = angle + offset
                tooth_x = end_x + 8 * math.cos(tooth_angle)
                tooth_y = end_y + 8 * math.sin(tooth_angle)
                painter.drawLine(int(end_x), int(end_y), int(tooth_x), int(tooth_y))

            # 绘制叉子编号
            painter.setPen(QPen(QColor(60, 60, 60)))
            font = QFont("Microsoft YaHei", 7)
            painter.setFont(font)
            num_x = x - 15 * math.cos(angle)
            num_y = y - 15 * math.sin(angle)
            painter.drawText(int(num_x - 8), int(num_y + 4), f"F{i}")

    def reset(self):
        """重置状态"""
        self.philosopher_states = [PhilosopherState.THINKING] * self.num_philosophers
        self.fork_available = [True] * self.num_philosophers
        self.semaphore_values = [1] * self.num_philosophers
        self.update()
