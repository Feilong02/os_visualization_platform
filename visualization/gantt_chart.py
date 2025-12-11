"""
甘特图可视化组件
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QScrollArea
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont
from PyQt5.QtCore import Qt, QRectF, QTimer
from typing import List
import sys
sys.path.append('..')
from core.scheduler import GanttBlock


class GanttChartWidget(QWidget):
    """甘特图可视化组件"""

    # 进程颜色调色板
    COLORS = [
        QColor(100, 180, 220),   # 蓝色
        QColor(220, 150, 100),   # 橙色
        QColor(100, 200, 150),   # 绿色
        QColor(200, 100, 150),   # 粉色
        QColor(180, 180, 100),   # 黄色
        QColor(150, 100, 200),   # 紫色
        QColor(100, 180, 180),   # 青色
        QColor(200, 150, 180),   # 浅粉
        QColor(150, 200, 100),   # 浅绿
        QColor(180, 120, 120),   # 浅红
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 200)
        self.gantt_blocks: List[GanttBlock] = []
        self.time_scale = 30  # 每个时间单位的像素宽度
        self.row_height = 40
        self.margin_left = 80
        self.margin_top = 40
        self.margin_bottom = 30

        # 动画相关
        self._current_time = 0
        self._animation_timer = QTimer()
        self._animation_timer.timeout.connect(self._animate_step)
        self._animating = False

    def set_data(self, blocks: List[GanttBlock]):
        """设置甘特图数据"""
        self.gantt_blocks = blocks
        self._current_time = max([b.end_time for b in blocks]) if blocks else 0
        self._animating = False
        self._animation_timer.stop()
        self.update()
        self._update_size()

    def _update_size(self):
        """更新组件大小"""
        if not self.gantt_blocks:
            return
        max_time = max([b.end_time for b in self.gantt_blocks])
        width = int(self.margin_left + max_time * self.time_scale + 50)
        height = int(self.margin_top + self.row_height + self.margin_bottom + 30)
        self.setMinimumWidth(width)
        self.setMinimumHeight(height)

    def start_animation(self, blocks: List[GanttBlock], speed: float = 0.5):
        """启动动画播放"""
        self.gantt_blocks = blocks
        self._current_time = 0
        self._animating = True
        self._animation_timer.start(int(speed * 1000))
        self._update_size()

    def stop_animation(self):
        """停止动画"""
        self._animating = False
        self._animation_timer.stop()
        if self.gantt_blocks:
            self._current_time = max([b.end_time for b in self.gantt_blocks])
        self.update()

    def _animate_step(self):
        """动画步进"""
        if not self.gantt_blocks:
            return

        max_time = max([b.end_time for b in self.gantt_blocks])
        self._current_time += 1

        if self._current_time > max_time:
            self.stop_animation()
            return

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if not self.gantt_blocks:
            painter.setPen(QPen(QColor(150, 150, 150)))
            painter.setFont(QFont("Microsoft YaHei", 12))
            painter.drawText(self.rect(), Qt.AlignCenter, "暂无调度数据")
            return

        # 绘制背景网格
        self._draw_grid(painter)

        # 绘制甘特图块
        self._draw_blocks(painter)

        # 绘制时间轴
        self._draw_time_axis(painter)

        # 绘制进程标签
        self._draw_labels(painter)

        # 绘制当前时间指示线（动画时）
        if self._animating:
            self._draw_time_indicator(painter)

    def _draw_grid(self, painter: QPainter):
        """绘制背景网格"""
        if not self.gantt_blocks:
            return

        max_time = max([b.end_time for b in self.gantt_blocks])
        painter.setPen(QPen(QColor(230, 230, 230), 1, Qt.DashLine))

        # 绘制垂直网格线
        for t in range(int(max_time) + 1):
            x = self.margin_left + t * self.time_scale
            painter.drawLine(int(x), self.margin_top, int(x),
                           self.margin_top + self.row_height)

    def _draw_blocks(self, painter: QPainter):
        """绘制甘特图块"""
        y = self.margin_top

        for block in self.gantt_blocks:
            # 动画时只显示当前时间之前的部分
            if self._animating:
                if block.start_time >= self._current_time:
                    continue
                end_time = min(block.end_time, self._current_time)
            else:
                end_time = block.end_time

            x = self.margin_left + block.start_time * self.time_scale
            width = (end_time - block.start_time) * self.time_scale

            # 获取颜色
            color = self.COLORS[block.color_index % len(self.COLORS)]

            # 绘制矩形
            painter.setPen(QPen(color.darker(120), 1))
            painter.setBrush(QBrush(color))
            rect = QRectF(x, y + 5, width, self.row_height - 10)
            painter.drawRoundedRect(rect, 3, 3)

            # 绘制进程名称（如果块足够宽）
            if width > 30:
                painter.setPen(QPen(QColor(255, 255, 255)))
                font = QFont("Microsoft YaHei", 9, QFont.Bold)
                painter.setFont(font)
                painter.drawText(rect, Qt.AlignCenter, block.name)

    def _draw_time_axis(self, painter: QPainter):
        """绘制时间轴"""
        if not self.gantt_blocks:
            return

        max_time = max([b.end_time for b in self.gantt_blocks])
        y = self.margin_top + self.row_height + 10

        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.drawLine(self.margin_left, y,
                        int(self.margin_left + max_time * self.time_scale), y)

        # 绘制刻度
        font = QFont("Microsoft YaHei", 8)
        painter.setFont(font)
        for t in range(int(max_time) + 1):
            x = self.margin_left + t * self.time_scale
            painter.drawLine(int(x), y - 3, int(x), y + 3)
            painter.drawText(int(x - 10), y + 18, str(t))

    def _draw_labels(self, painter: QPainter):
        """绘制进程标签"""
        painter.setPen(QPen(QColor(80, 80, 80)))
        font = QFont("Microsoft YaHei", 10)
        painter.setFont(font)
        painter.drawText(10, self.margin_top + self.row_height // 2 + 5, "CPU")

    def _draw_time_indicator(self, painter: QPainter):
        """绘制当前时间指示线"""
        x = self.margin_left + self._current_time * self.time_scale
        painter.setPen(QPen(QColor(255, 50, 50), 2))
        painter.drawLine(int(x), self.margin_top - 10,
                        int(x), self.margin_top + self.row_height + 10)

        # 绘制时间标签
        painter.setFont(QFont("Microsoft YaHei", 9, QFont.Bold))
        painter.drawText(int(x - 15), self.margin_top - 15, f"T={self._current_time}")

    def set_time_scale(self, scale: int):
        """设置时间刻度"""
        self.time_scale = scale
        self._update_size()
        self.update()

    def clear(self):
        """清空甘特图"""
        self.gantt_blocks = []
        self._current_time = 0
        self._animating = False
        self._animation_timer.stop()
        self.update()
