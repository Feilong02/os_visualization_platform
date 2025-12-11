#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
操作系统原理可视化实验展示平台
主程序入口
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ui.main_window import MainWindow


def main():
    """主函数"""
    # 高DPI支持
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)

    # 设置应用程序信息
    app.setApplicationName("操作系统原理可视化实验展示平台")
    app.setApplicationVersion("2.2.0")
    app.setOrganizationName("OS Visualization")

    # 设置默认字体
    font = QFont("Microsoft YaHei", 9)
    app.setFont(font)

    # 设置全局样式
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f5f5f5;
        }
        QGroupBox {
            font-weight: bold;
            border: 1px solid #ccc;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
        QPushButton {
            padding: 5px 15px;
            border-radius: 3px;
            border: 1px solid #ccc;
            background-color: #f0f0f0;
        }
        QPushButton:hover {
            background-color: #e0e0e0;
        }
        QPushButton:pressed {
            background-color: #d0d0d0;
        }
        QTableWidget {
            border: 1px solid #ccc;
            gridline-color: #eee;
        }
        QTableWidget::item:selected {
            background-color: #2196F3;
            color: white;
        }
        QHeaderView::section {
            background-color: #e0e0e0;
            padding: 5px;
            border: 1px solid #ccc;
            font-weight: bold;
        }
        QSlider::groove:horizontal {
            border: 1px solid #ccc;
            height: 8px;
            background: #e0e0e0;
            border-radius: 4px;
        }
        QSlider::handle:horizontal {
            background: #2196F3;
            border: 1px solid #1976D2;
            width: 18px;
            margin: -5px 0;
            border-radius: 9px;
        }
        QTextEdit {
            border: 1px solid #ccc;
            border-radius: 3px;
        }
        QListWidget {
            border: 1px solid #ccc;
            border-radius: 3px;
        }
        QSpinBox, QDoubleSpinBox, QComboBox {
            padding: 3px;
            border: 1px solid #ccc;
            border-radius: 3px;
        }
    """)

    # 创建并显示主窗口
    window = MainWindow()
    window.show()

    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
