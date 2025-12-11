"""
进程状态机可视化组件
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath
from PyQt5.QtCore import Qt, QRectF, QPointF, QTimer
import math


class StateMachineWidget(QWidget):
    """进程状态机可视化组件"""

    # 状态颜色映射
    STATE_COLORS = {
        "创建": QColor(150, 150, 150),    # 灰色
        "就绪": QColor(100, 180, 100),    # 绿色
        "运行": QColor(100, 150, 220),    # 蓝色
        "阻塞": QColor(220, 180, 100),    # 黄色
        "终止": QColor(180, 100, 100),    # 红色
    }

    # 状态位置（相对于中心）
    STATE_POSITIONS = {
        "创建": (-180, -80),
        "就绪": (-60, -80),
        "运行": (100, -80),
        "阻塞": (100, 80),
        "终止": (-60, 80),
    }

    # 状态转换关系
    TRANSITIONS = [
        ("创建", "就绪", "admit"),
        ("就绪", "运行", "dispatch"),
        ("运行", "就绪", "timeout"),
        ("运行", "阻塞", "wait"),
        ("阻塞", "就绪", "signal"),
        ("运行", "终止", "exit"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(450, 280)
        self.current_state = None
        self._highlight_transition = None
        self._animation_timer = QTimer()
        self._animation_timer.timeout.connect(self._clear_highlight)

    def set_current_state(self, state_name: str):
        """设置当前高亮状态"""
        self.current_state = state_name
        self.update()

    def highlight_transition(self, from_state: str, to_state: str):
        """高亮状态转换"""
        self._highlight_transition = (from_state, to_state)
        self.update()
        self._animation_timer.start(1000)

    def _clear_highlight(self):
        """清除高亮"""
        self._highlight_transition = None
        self._animation_timer.stop()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 计算中心点
        center_x = self.width() // 2
        center_y = self.height() // 2

        # 绘制状态转换箭头
        self._draw_transitions(painter, center_x, center_y)

        # 绘制状态节点
        self._draw_states(painter, center_x, center_y)

    def _draw_states(self, painter: QPainter, center_x: int, center_y: int):
        """绘制状态节点"""
        node_radius = 35
        font = QFont("Microsoft YaHei", 10, QFont.Bold)
        painter.setFont(font)

        for state_name, (dx, dy) in self.STATE_POSITIONS.items():
            x = center_x + dx
            y = center_y + dy

            # 设置颜色
            color = self.STATE_COLORS.get(state_name, QColor(150, 150, 150))

            # 当前状态高亮
            if state_name == self.current_state:
                painter.setPen(QPen(QColor(255, 100, 100), 4))
                painter.setBrush(QBrush(color.lighter(120)))
            else:
                painter.setPen(QPen(QColor(60, 60, 60), 2))
                painter.setBrush(QBrush(color))

            # 绘制圆形节点
            painter.drawEllipse(QPointF(x, y), node_radius, node_radius)

            # 绘制状态名称
            painter.setPen(QPen(QColor(255, 255, 255)))
            rect = QRectF(x - node_radius, y - node_radius, node_radius * 2, node_radius * 2)
            painter.drawText(rect, Qt.AlignCenter, state_name)

    def _draw_transitions(self, painter: QPainter, center_x: int, center_y: int):
        """绘制状态转换箭头"""
        for from_state, to_state, label in self.TRANSITIONS:
            from_pos = self.STATE_POSITIONS[from_state]
            to_pos = self.STATE_POSITIONS[to_state]

            x1 = center_x + from_pos[0]
            y1 = center_y + from_pos[1]
            x2 = center_x + to_pos[0]
            y2 = center_y + to_pos[1]

            # 检查是否高亮
            is_highlight = (self._highlight_transition and
                           self._highlight_transition[0] == from_state and
                           self._highlight_transition[1] == to_state)

            if is_highlight:
                painter.setPen(QPen(QColor(255, 100, 100), 3))
            else:
                painter.setPen(QPen(QColor(100, 100, 100), 2))

            # 计算箭头方向
            dx = x2 - x1
            dy = y2 - y1
            length = math.sqrt(dx * dx + dy * dy)
            if length == 0:
                continue

            # 标准化方向向量
            dx /= length
            dy /= length

            # 调整起点和终点（避开圆形节点）
            node_radius = 38
            start_x = x1 + dx * node_radius
            start_y = y1 + dy * node_radius
            end_x = x2 - dx * node_radius
            end_y = y2 - dy * node_radius

            # 绘制线段
            painter.drawLine(int(start_x), int(start_y), int(end_x), int(end_y))

            # 绘制箭头头部
            arrow_size = 10
            angle = math.atan2(dy, dx)
            arrow_p1_x = end_x - arrow_size * math.cos(angle - math.pi / 6)
            arrow_p1_y = end_y - arrow_size * math.sin(angle - math.pi / 6)
            arrow_p2_x = end_x - arrow_size * math.cos(angle + math.pi / 6)
            arrow_p2_y = end_y - arrow_size * math.sin(angle + math.pi / 6)

            path = QPainterPath()
            path.moveTo(end_x, end_y)
            path.lineTo(arrow_p1_x, arrow_p1_y)
            path.lineTo(arrow_p2_x, arrow_p2_y)
            path.closeSubpath()

            if is_highlight:
                painter.setBrush(QBrush(QColor(255, 100, 100)))
            else:
                painter.setBrush(QBrush(QColor(100, 100, 100)))
            painter.drawPath(path)

            # 绘制标签
            mid_x = (start_x + end_x) / 2
            mid_y = (start_y + end_y) / 2
            painter.setPen(QPen(QColor(80, 80, 80)))
            font = QFont("Microsoft YaHei", 8)
            painter.setFont(font)

            # 偏移标签位置
            offset_x = -dy * 15
            offset_y = dx * 15
            painter.drawText(int(mid_x + offset_x - 25), int(mid_y + offset_y + 5), label)
