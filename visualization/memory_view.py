"""
内存可视化组件
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer, QRectF
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QFont, QFontMetrics
from typing import List
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.memory import MemoryBlock


# 进程颜色映射
PROCESS_COLORS = [
    "#FF6B6B",  # 红
    "#4ECDC4",  # 青
    "#45B7D1",  # 蓝
    "#96CEB4",  # 绿
    "#FFEAA7",  # 黄
    "#DDA0DD",  # 紫
    "#98D8C8",  # 薄荷
    "#F7DC6F",  # 金
    "#BB8FCE",  # 淡紫
    "#85C1E9",  # 天蓝
]


class MemoryBlockWidget(QWidget):
    """内存块可视化组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.blocks: List[MemoryBlock] = []
        self.total_size = 1024
        self.process_colors = {}
        self.color_index = 0
        self.setMinimumHeight(100)
        self.setMinimumWidth(600)

    def set_data(self, blocks: List[MemoryBlock], total_size: int):
        """设置数据"""
        self.blocks = blocks
        self.total_size = total_size
        self._assign_colors()
        self.update()

    def _assign_colors(self):
        """为进程分配颜色"""
        for block in self.blocks:
            if not block.is_free and block.process_name not in self.process_colors:
                self.process_colors[block.process_name] = PROCESS_COLORS[
                    self.color_index % len(PROCESS_COLORS)
                ]
                self.color_index += 1

    def paintEvent(self, event):
        """绘制内存块"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width() - 20
        height = self.height() - 40
        start_x = 10
        start_y = 20

        # 绘制边框
        painter.setPen(QPen(QColor("#333"), 2))
        painter.drawRect(start_x, start_y, width, height)

        # 绘制每个内存块
        for block in self.blocks:
            x = start_x + (block.start / self.total_size) * width
            w = (block.size / self.total_size) * width

            if block.is_free:
                color = QColor("#E8E8E8")
            else:
                color = QColor(self.process_colors.get(block.process_name, "#999"))

            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor("#666"), 1))
            painter.drawRect(int(x), start_y, int(w), height)

            # 绘制文字
            font = QFont("Microsoft YaHei", 8)
            painter.setFont(font)
            painter.setPen(QPen(QColor("#333")))

            text = "空闲" if block.is_free else block.process_name
            size_text = f"{block.size}KB"

            fm = QFontMetrics(font)
            if w > fm.horizontalAdvance(text) + 10:
                painter.drawText(
                    QRectF(x, start_y, w, height / 2),
                    Qt.AlignCenter,
                    text
                )
                painter.drawText(
                    QRectF(x, start_y + height / 2, w, height / 2),
                    Qt.AlignCenter,
                    size_text
                )

        # 绘制地址刻度
        painter.setFont(QFont("Microsoft YaHei", 7))
        painter.setPen(QPen(QColor("#666")))

        for i in range(0, self.total_size + 1, self.total_size // 8):
            x = start_x + (i / self.total_size) * width
            painter.drawLine(int(x), start_y + height, int(x), start_y + height + 5)
            painter.drawText(int(x - 15), start_y + height + 15, f"{i}")


class PageFrameWidget(QWidget):
    """页框可视化组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.frames: List[int] = []  # 页号列表
        self.frame_count = 4
        self.current_page = -1
        self.is_hit = False
        self.replaced_page = -1
        self.clock_pointer = -1
        self.reference_bits = {}
        self.setMinimumHeight(120)
        self.setMinimumWidth(400)

    def set_data(self, frames: List[int], current_page: int = -1,
                 is_hit: bool = False, replaced: int = -1,
                 clock_pointer: int = -1, reference_bits: dict = None):
        """设置数据"""
        self.frames = frames
        self.frame_count = len(frames)
        self.current_page = current_page
        self.is_hit = is_hit
        self.replaced_page = replaced
        self.clock_pointer = clock_pointer
        self.reference_bits = reference_bits or {}
        self.update()

    def paintEvent(self, event):
        """绘制页框"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if not self.frames:
            return

        frame_width = min(80, (self.width() - 40) // self.frame_count)
        frame_height = 60
        start_x = (self.width() - frame_width * self.frame_count) // 2
        start_y = 30

        font = QFont("Microsoft YaHei", 10, QFont.Bold)
        painter.setFont(font)

        for i, page_id in enumerate(self.frames):
            x = start_x + i * frame_width
            rect = QRectF(x, start_y, frame_width - 5, frame_height)

            # 确定颜色
            if page_id == -1:
                color = QColor("#E8E8E8")
            elif page_id == self.current_page:
                if self.is_hit:
                    color = QColor("#4CAF50")  # 命中 - 绿色
                else:
                    color = QColor("#2196F3")  # 新加入 - 蓝色
            elif page_id == self.replaced_page:
                color = QColor("#F44336")  # 被替换 - 红色
            else:
                color = QColor("#FFD700")  # 普通页 - 金色

            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor("#333"), 2))
            painter.drawRoundedRect(rect, 5, 5)

            # 绘制页号
            painter.setPen(QPen(QColor("#333" if page_id != -1 else "#999")))
            text = str(page_id) if page_id != -1 else "-"
            painter.drawText(rect, Qt.AlignCenter, text)

            # 绘制帧号标签
            painter.setFont(QFont("Microsoft YaHei", 8))
            painter.setPen(QPen(QColor("#666")))
            painter.drawText(
                QRectF(x, start_y - 20, frame_width - 5, 20),
                Qt.AlignCenter,
                f"帧{i}"
            )

            # 绘制引用位（如果有）
            if page_id in self.reference_bits:
                ref_bit = self.reference_bits[page_id]
                painter.drawText(
                    QRectF(x, start_y + frame_height + 2, frame_width - 5, 15),
                    Qt.AlignCenter,
                    f"R={ref_bit}"
                )

            # 绘制时钟指针
            if self.clock_pointer == i:
                painter.setPen(QPen(QColor("#E91E63"), 2))
                painter.drawText(
                    QRectF(x, start_y + frame_height + 15, frame_width - 5, 20),
                    Qt.AlignCenter,
                    "^"
                )

            painter.setFont(font)


class PageAccessHistoryWidget(QWidget):
    """页面访问历史可视化"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.history: List[dict] = []
        self.current_step = -1
        self.setMinimumHeight(150)

    def set_data(self, history: List[dict], current_step: int = -1):
        """设置数据"""
        self.history = history
        self.current_step = current_step
        # 动态调整宽度
        self.setMinimumWidth(max(600, len(history) * 50 + 100))
        self.update()

    def paintEvent(self, event):
        """绘制访问历史"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if not self.history:
            return

        cell_width = 45
        cell_height = 25
        start_x = 60
        start_y = 30

        font = QFont("Microsoft YaHei", 9)
        painter.setFont(font)

        # 获取帧数
        if self.history:
            frame_count = len(self.history[0]['frame_state'])
        else:
            frame_count = 4

        # 绘制列标题（页面访问序列）
        painter.setPen(QPen(QColor("#333")))
        for i, step in enumerate(self.history):
            x = start_x + i * cell_width
            rect = QRectF(x, 5, cell_width, 20)

            # 高亮当前步骤
            if i == self.current_step:
                painter.setBrush(QBrush(QColor("#2196F3")))
                painter.drawRect(rect)
                painter.setPen(QPen(QColor("#FFF")))
            else:
                painter.setPen(QPen(QColor("#333")))

            painter.drawText(rect, Qt.AlignCenter, str(step['page']))

        # 绘制行标题（帧号）
        painter.setPen(QPen(QColor("#333")))
        for i in range(frame_count):
            y = start_y + i * cell_height
            painter.drawText(QRectF(5, y, 50, cell_height), Qt.AlignVCenter, f"帧 {i}")

        # 绘制表格内容
        for col, step in enumerate(self.history):
            x = start_x + col * cell_width

            for row, page_id in enumerate(step['frame_state']):
                y = start_y + row * cell_height
                rect = QRectF(x, y, cell_width - 2, cell_height - 2)

                # 确定背景色
                if page_id == -1:
                    bg_color = QColor("#F5F5F5")
                elif page_id == step['page']:
                    if step['hit']:
                        bg_color = QColor("#C8E6C9")  # 命中 - 浅绿
                    else:
                        bg_color = QColor("#BBDEFB")  # 调入 - 浅蓝
                elif page_id == step.get('replaced', -1):
                    bg_color = QColor("#FFCDD2")  # 被替换 - 浅红
                else:
                    bg_color = QColor("#FFF9C4")  # 普通 - 浅黄

                painter.setBrush(QBrush(bg_color))
                painter.setPen(QPen(QColor("#CCC")))
                painter.drawRect(rect)

                # 绘制页号
                painter.setPen(QPen(QColor("#333")))
                text = str(page_id) if page_id != -1 else ""
                painter.drawText(rect, Qt.AlignCenter, text)

        # 绘制命中/缺失标记
        y = start_y + frame_count * cell_height + 5
        for col, step in enumerate(self.history):
            x = start_x + col * cell_width
            rect = QRectF(x, y, cell_width - 2, 20)

            if step['hit']:
                painter.setPen(QPen(QColor("#4CAF50")))
                text = "H"
            else:
                painter.setPen(QPen(QColor("#F44336")))
                text = "M"

            painter.drawText(rect, Qt.AlignCenter, text)

        # 图例
        painter.setFont(QFont("Microsoft YaHei", 8))
        painter.setPen(QPen(QColor("#333")))
        legend_y = start_y + frame_count * cell_height + 30
        painter.drawText(10, legend_y, "H: 命中  M: 缺失")
