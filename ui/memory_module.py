"""
模块5：内存管理界面
包含动态内存分配和页面置换算法演示
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QGroupBox, QLabel, QComboBox, QSpinBox,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QMessageBox, QScrollArea, QSplitter, QTabWidget,
                             QTextEdit, QLineEdit)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.memory import (MemoryAllocator, PageReplacer, MemoryRequest,
                        AllocationAlgorithm, PageReplacementAlgorithm)
from visualization.memory_view import (MemoryBlockWidget, PageFrameWidget,
                                       PageAccessHistoryWidget)


class MemoryModule(QWidget):
    """内存管理模块"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 使用标签页分隔两个功能
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_allocation_tab(), "动态内存分配")
        self.tabs.addTab(self._create_page_replacement_tab(), "页面置换算法")

        layout.addWidget(self.tabs)

    def _create_allocation_tab(self) -> QWidget:
        """创建动态内存分配标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)

        # 初始化分配器
        self.allocator = MemoryAllocator(1024)

        # 顶部控制区
        top_panel = QWidget()
        top_layout = QHBoxLayout(top_panel)

        # 内存设置
        mem_group = QGroupBox("内存设置")
        mem_layout = QHBoxLayout(mem_group)

        mem_layout.addWidget(QLabel("总内存(KB):"))
        self.mem_size_spin = QSpinBox()
        self.mem_size_spin.setRange(128, 4096)
        self.mem_size_spin.setValue(1024)
        self.mem_size_spin.setSingleStep(128)
        mem_layout.addWidget(self.mem_size_spin)

        init_btn = QPushButton("初始化")
        init_btn.clicked.connect(self._init_memory)
        init_btn.setStyleSheet("background-color: #607D8B; color: white;")
        mem_layout.addWidget(init_btn)

        top_layout.addWidget(mem_group)

        # 分配请求
        alloc_group = QGroupBox("分配请求")
        alloc_layout = QHBoxLayout(alloc_group)

        alloc_layout.addWidget(QLabel("进程名:"))
        self.process_name_input = QComboBox()
        self.process_name_input.setEditable(True)
        self.process_name_input.addItems(["P1", "P2", "P3", "P4", "P5"])
        self.process_name_input.setMaximumWidth(80)
        alloc_layout.addWidget(self.process_name_input)

        alloc_layout.addWidget(QLabel("大小(KB):"))
        self.alloc_size_spin = QSpinBox()
        self.alloc_size_spin.setRange(1, 1024)
        self.alloc_size_spin.setValue(100)
        alloc_layout.addWidget(self.alloc_size_spin)

        alloc_layout.addWidget(QLabel("算法:"))
        self.alloc_algo_combo = QComboBox()
        self.alloc_algo_combo.addItems([
            "首次适应 (First Fit)",
            "最佳适应 (Best Fit)",
            "最坏适应 (Worst Fit)",
            "循环首次适应 (Next Fit)"
        ])
        alloc_layout.addWidget(self.alloc_algo_combo)

        top_layout.addWidget(alloc_group)

        # 操作按钮
        op_group = QGroupBox("操作")
        op_layout = QHBoxLayout(op_group)

        alloc_btn = QPushButton("分配")
        alloc_btn.clicked.connect(self._allocate_memory)
        alloc_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        op_layout.addWidget(alloc_btn)

        free_btn = QPushButton("释放")
        free_btn.clicked.connect(self._free_memory)
        free_btn.setStyleSheet("background-color: #F44336; color: white;")
        op_layout.addWidget(free_btn)

        sample_btn = QPushButton("示例序列")
        sample_btn.clicked.connect(self._run_sample_allocation)
        sample_btn.setStyleSheet("background-color: #FF9800; color: white;")
        op_layout.addWidget(sample_btn)

        top_layout.addWidget(op_group)

        layout.addWidget(top_panel)

        # 中部可视化区域
        middle_splitter = QSplitter(Qt.Vertical)

        # 内存块可视化
        mem_widget = QWidget()
        mem_layout_v = QVBoxLayout(mem_widget)
        mem_layout_v.setContentsMargins(0, 0, 0, 0)

        mem_header = QLabel("内存状态可视化")
        mem_header.setStyleSheet("font-weight: bold; font-size: 12px;")
        mem_layout_v.addWidget(mem_header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.memory_view = MemoryBlockWidget()
        scroll.setWidget(self.memory_view)
        mem_layout_v.addWidget(scroll)

        middle_splitter.addWidget(mem_widget)

        # 分配表和统计
        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_widget)

        # 分配表
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        table_layout.setContentsMargins(0, 0, 0, 0)

        table_header = QLabel("内存块列表")
        table_header.setStyleSheet("font-weight: bold; font-size: 12px;")
        table_layout.addWidget(table_header)

        self.alloc_table = QTableWidget()
        self.alloc_table.setColumnCount(4)
        self.alloc_table.setHorizontalHeaderLabels(["起始地址", "大小(KB)", "状态", "进程"])
        self.alloc_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table_layout.addWidget(self.alloc_table)

        bottom_layout.addWidget(table_widget, stretch=2)

        # 统计信息
        stats_widget = QWidget()
        stats_layout = QVBoxLayout(stats_widget)
        stats_layout.setContentsMargins(0, 0, 0, 0)

        stats_header = QLabel("统计信息")
        stats_header.setStyleSheet("font-weight: bold; font-size: 12px;")
        stats_layout.addWidget(stats_header)

        self.usage_label = QLabel("内存使用率: 0%")
        stats_layout.addWidget(self.usage_label)

        self.frag_label = QLabel("外部碎片: 0KB")
        stats_layout.addWidget(self.frag_label)

        self.frag_count_label = QLabel("空闲块数: 1")
        stats_layout.addWidget(self.frag_count_label)

        stats_layout.addWidget(QLabel("操作历史:"))
        self.alloc_history = QTextEdit()
        self.alloc_history.setReadOnly(True)
        self.alloc_history.setMaximumHeight(150)
        stats_layout.addWidget(self.alloc_history)

        stats_layout.addStretch()
        bottom_layout.addWidget(stats_widget, stretch=1)

        middle_splitter.addWidget(bottom_widget)
        middle_splitter.setSizes([200, 300])

        layout.addWidget(middle_splitter)

        # 初始化显示
        self._refresh_allocation_view()

        return widget

    def _create_page_replacement_tab(self) -> QWidget:
        """创建页面置换标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)

        # 初始化页面置换器
        self.page_replacer = PageReplacer(4)

        # 顶部控制区
        top_panel = QWidget()
        top_layout = QHBoxLayout(top_panel)

        # 页框设置
        frame_group = QGroupBox("页框设置")
        frame_layout = QHBoxLayout(frame_group)

        frame_layout.addWidget(QLabel("页框数:"))
        self.frame_count_spin = QSpinBox()
        self.frame_count_spin.setRange(2, 8)
        self.frame_count_spin.setValue(4)
        self.frame_count_spin.valueChanged.connect(self._on_frame_count_changed)
        frame_layout.addWidget(self.frame_count_spin)

        top_layout.addWidget(frame_group)

        # 算法选择
        algo_group = QGroupBox("置换算法")
        algo_layout = QHBoxLayout(algo_group)

        self.page_algo_combo = QComboBox()
        self.page_algo_combo.addItems([
            "先进先出 (FIFO)",
            "最近最少使用 (LRU)",
            "最佳置换 (OPT)",
            "时钟算法 (CLOCK)"
        ])
        algo_layout.addWidget(self.page_algo_combo)

        top_layout.addWidget(algo_group)

        # 页面访问序列
        seq_group = QGroupBox("页面访问序列")
        seq_layout = QHBoxLayout(seq_group)

        self.page_seq_input = QLineEdit()
        self.page_seq_input.setPlaceholderText("输入页面序列，用逗号分隔，如: 1,2,3,4,1,2,5")
        self.page_seq_input.setText("7,0,1,2,0,3,0,4,2,3,0,3,2,1,2,0,1,7,0,1")
        seq_layout.addWidget(self.page_seq_input)

        top_layout.addWidget(seq_group, stretch=2)

        # 操作按钮
        op_group = QGroupBox("操作")
        op_layout = QHBoxLayout(op_group)

        run_btn = QPushButton("执行")
        run_btn.clicked.connect(self._run_page_replacement)
        run_btn.setStyleSheet("background-color: #2196F3; color: white;")
        op_layout.addWidget(run_btn)

        self.animate_btn = QPushButton("动画演示")
        self.animate_btn.clicked.connect(self._animate_page_replacement)
        self.animate_btn.setStyleSheet("background-color: #FF9800; color: white;")
        op_layout.addWidget(self.animate_btn)

        reset_btn = QPushButton("重置")
        reset_btn.clicked.connect(self._reset_page_replacement)
        op_layout.addWidget(reset_btn)

        top_layout.addWidget(op_group)

        layout.addWidget(top_panel)

        # 中部可视化区域
        middle_widget = QWidget()
        middle_layout = QVBoxLayout(middle_widget)

        # 当前页框状态
        frame_widget = QWidget()
        frame_layout_v = QVBoxLayout(frame_widget)
        frame_layout_v.setContentsMargins(0, 0, 0, 0)

        frame_header = QLabel("当前页框状态")
        frame_header.setStyleSheet("font-weight: bold; font-size: 12px;")
        frame_layout_v.addWidget(frame_header)

        self.page_frame_view = PageFrameWidget()
        frame_layout_v.addWidget(self.page_frame_view)

        middle_layout.addWidget(frame_widget)

        # 访问历史表格
        history_widget = QWidget()
        history_layout = QVBoxLayout(history_widget)
        history_layout.setContentsMargins(0, 0, 0, 0)

        history_header = QLabel("页面访问历史")
        history_header.setStyleSheet("font-weight: bold; font-size: 12px;")
        history_layout.addWidget(history_header)

        history_scroll = QScrollArea()
        history_scroll.setWidgetResizable(True)
        history_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.page_history_view = PageAccessHistoryWidget()
        history_scroll.setWidget(self.page_history_view)
        history_layout.addWidget(history_scroll)

        middle_layout.addWidget(history_widget, stretch=2)

        layout.addWidget(middle_widget, stretch=2)

        # 底部统计
        stats_group = QGroupBox("性能统计")
        stats_layout = QHBoxLayout(stats_group)

        self.page_fault_label = QLabel("缺页次数: 0")
        self.page_fault_label.setStyleSheet("font-size: 14px;")
        stats_layout.addWidget(self.page_fault_label)

        self.page_hit_label = QLabel("命中次数: 0")
        self.page_hit_label.setStyleSheet("font-size: 14px;")
        stats_layout.addWidget(self.page_hit_label)

        self.hit_rate_label = QLabel("命中率: 0%")
        self.hit_rate_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        stats_layout.addWidget(self.hit_rate_label)

        self.fault_rate_label = QLabel("缺页率: 0%")
        self.fault_rate_label.setStyleSheet("font-size: 14px;")
        stats_layout.addWidget(self.fault_rate_label)

        stats_layout.addStretch()

        layout.addWidget(stats_group)

        # 动画相关
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._animation_step)
        self.animation_steps = []
        self.current_animation_step = 0

        return widget

    # ========== 动态内存分配相关方法 ==========

    def _init_memory(self):
        """初始化内存"""
        size = self.mem_size_spin.value()
        self.allocator = MemoryAllocator(size)
        self.memory_view.process_colors = {}
        self.memory_view.color_index = 0
        self._refresh_allocation_view()
        self.alloc_history.clear()
        self.alloc_history.append("内存初始化完成，总大小: {}KB".format(size))

    def _allocate_memory(self):
        """分配内存"""
        process_name = self.process_name_input.currentText()
        size = self.alloc_size_spin.value()
        algo_index = self.alloc_algo_combo.currentIndex()

        algorithms = [
            AllocationAlgorithm.FIRST_FIT,
            AllocationAlgorithm.BEST_FIT,
            AllocationAlgorithm.WORST_FIT,
            AllocationAlgorithm.NEXT_FIT
        ]
        algorithm = algorithms[algo_index]

        request = MemoryRequest(process_name, size)
        success = self.allocator.allocate(request, algorithm)

        if success:
            self.alloc_history.append(
                f"[成功] 为进程 {process_name} 分配 {size}KB ({algorithm.value})"
            )
            # 自动递增进程名
            try:
                prefix = ''.join(filter(str.isalpha, process_name))
                num = int(''.join(filter(str.isdigit, process_name))) + 1
                self.process_name_input.setCurrentText(f"{prefix}{num}")
            except:
                pass
        else:
            self.alloc_history.append(
                f"[失败] 无法为进程 {process_name} 分配 {size}KB - 内存不足"
            )
            QMessageBox.warning(self, "分配失败", f"无法为进程 {process_name} 分配 {size}KB 内存")

        self._refresh_allocation_view()

    def _free_memory(self):
        """释放内存"""
        # 从表格获取选中的进程
        selected = self.alloc_table.selectedItems()
        if not selected:
            # 使用输入框中的进程名
            process_name = self.process_name_input.currentText()
        else:
            row = selected[0].row()
            process_item = self.alloc_table.item(row, 3)
            if process_item:
                process_name = process_item.text()
            else:
                return

        if not process_name:
            return

        success = self.allocator.deallocate(process_name)
        if success:
            self.alloc_history.append(f"[释放] 进程 {process_name} 的内存已释放")
        else:
            self.alloc_history.append(f"[失败] 进程 {process_name} 未找到")

        self._refresh_allocation_view()

    def _run_sample_allocation(self):
        """运行示例分配序列"""
        self._init_memory()

        # 示例序列
        operations = [
            ("allocate", "P1", 200),
            ("allocate", "P2", 150),
            ("allocate", "P3", 300),
            ("free", "P2", 0),
            ("allocate", "P4", 100),
            ("allocate", "P5", 180),
            ("free", "P1", 0),
            ("allocate", "P6", 150),
        ]

        algo_index = self.alloc_algo_combo.currentIndex()
        algorithms = [
            AllocationAlgorithm.FIRST_FIT,
            AllocationAlgorithm.BEST_FIT,
            AllocationAlgorithm.WORST_FIT,
            AllocationAlgorithm.NEXT_FIT
        ]
        algorithm = algorithms[algo_index]

        for op, name, size in operations:
            if op == "allocate":
                request = MemoryRequest(name, size)
                success = self.allocator.allocate(request, algorithm)
                status = "成功" if success else "失败"
                self.alloc_history.append(f"[{status}] 分配 {name}: {size}KB")
            else:
                self.allocator.deallocate(name)
                self.alloc_history.append(f"[释放] {name}")

        self._refresh_allocation_view()

    def _refresh_allocation_view(self):
        """刷新分配视图"""
        # 更新内存块可视化
        self.memory_view.set_data(self.allocator.blocks, self.allocator.total_size)

        # 更新表格
        self.alloc_table.setRowCount(len(self.allocator.blocks))
        for row, block in enumerate(self.allocator.blocks):
            self.alloc_table.setItem(row, 0, QTableWidgetItem(str(block.start)))
            self.alloc_table.setItem(row, 1, QTableWidgetItem(str(block.size)))
            status = "空闲" if block.is_free else "已分配"
            self.alloc_table.setItem(row, 2, QTableWidgetItem(status))
            self.alloc_table.setItem(row, 3, QTableWidgetItem(block.process_name))

            # 设置行背景色
            color = QColor("#E8E8E8") if block.is_free else QColor("#C8E6C9")
            for col in range(4):
                item = self.alloc_table.item(row, col)
                if item:
                    item.setBackground(color)

        # 更新统计
        usage = self.allocator.get_usage()
        frag, frag_count = self.allocator.get_fragmentation()

        self.usage_label.setText(f"内存使用率: {usage:.1f}%")
        self.frag_label.setText(f"外部碎片: {frag}KB")
        self.frag_count_label.setText(f"空闲块数: {frag_count}")

    # ========== 页面置换相关方法 ==========

    def _on_frame_count_changed(self, value: int):
        """页框数变化"""
        self.page_replacer = PageReplacer(value)
        self._refresh_page_view()

    def _run_page_replacement(self):
        """执行页面置换"""
        # 解析页面序列
        try:
            seq_text = self.page_seq_input.text().strip()
            page_sequence = [int(x.strip()) for x in seq_text.split(',') if x.strip()]
        except ValueError:
            QMessageBox.warning(self, "错误", "页面序列格式错误，请输入用逗号分隔的数字")
            return

        if not page_sequence:
            QMessageBox.warning(self, "错误", "请输入页面序列")
            return

        # 获取算法
        algo_index = self.page_algo_combo.currentIndex()
        algorithms = [
            PageReplacementAlgorithm.FIFO,
            PageReplacementAlgorithm.LRU,
            PageReplacementAlgorithm.OPT,
            PageReplacementAlgorithm.CLOCK
        ]
        algorithm = algorithms[algo_index]

        # 执行
        self.page_replacer = PageReplacer(self.frame_count_spin.value())
        steps = self.page_replacer.run_sequence(page_sequence, algorithm)

        # 显示结果
        self.page_history_view.set_data(steps)
        if steps:
            last_step = steps[-1]
            self.page_frame_view.set_data(last_step['frame_state'])

        self._update_page_stats()

    def _animate_page_replacement(self):
        """动画演示页面置换"""
        # 解析页面序列
        try:
            seq_text = self.page_seq_input.text().strip()
            page_sequence = [int(x.strip()) for x in seq_text.split(',') if x.strip()]
        except ValueError:
            QMessageBox.warning(self, "错误", "页面序列格式错误")
            return

        if not page_sequence:
            return

        # 获取算法
        algo_index = self.page_algo_combo.currentIndex()
        algorithms = [
            PageReplacementAlgorithm.FIFO,
            PageReplacementAlgorithm.LRU,
            PageReplacementAlgorithm.OPT,
            PageReplacementAlgorithm.CLOCK
        ]
        algorithm = algorithms[algo_index]

        # 准备动画
        self.page_replacer = PageReplacer(self.frame_count_spin.value())
        self.animation_steps = self.page_replacer.run_sequence(page_sequence, algorithm)
        self.current_animation_step = 0

        # 禁用按钮
        self.animate_btn.setEnabled(False)
        self.animate_btn.setText("演示中...")

        # 开始动画
        self.animation_timer.start(800)

    def _animation_step(self):
        """动画步骤"""
        if self.current_animation_step >= len(self.animation_steps):
            self.animation_timer.stop()
            self.animate_btn.setEnabled(True)
            self.animate_btn.setText("动画演示")
            return

        step = self.animation_steps[self.current_animation_step]

        # 更新页框视图
        clock_pointer = -1
        ref_bits = {}
        if self.page_algo_combo.currentIndex() == 3:  # CLOCK
            clock_pointer = self.page_replacer.clock_pointer
            ref_bits = self.page_replacer.reference_bits

        self.page_frame_view.set_data(
            step['frame_state'],
            step['page'],
            step['hit'],
            step['replaced'],
            clock_pointer,
            ref_bits
        )

        # 更新历史视图
        self.page_history_view.set_data(
            self.animation_steps[:self.current_animation_step + 1],
            self.current_animation_step
        )

        # 更新统计
        self.page_fault_label.setText(f"缺页次数: {step['page_faults']}")
        self.page_hit_label.setText(f"命中次数: {step['page_hits']}")

        total = step['page_faults'] + step['page_hits']
        if total > 0:
            hit_rate = step['page_hits'] / total * 100
            fault_rate = step['page_faults'] / total * 100
            self.hit_rate_label.setText(f"命中率: {hit_rate:.1f}%")
            self.fault_rate_label.setText(f"缺页率: {fault_rate:.1f}%")

        self.current_animation_step += 1

    def _reset_page_replacement(self):
        """重置页面置换"""
        self.animation_timer.stop()
        self.page_replacer = PageReplacer(self.frame_count_spin.value())
        self.page_frame_view.set_data([])
        self.page_history_view.set_data([])
        self.animate_btn.setEnabled(True)
        self.animate_btn.setText("动画演示")

        self.page_fault_label.setText("缺页次数: 0")
        self.page_hit_label.setText("命中次数: 0")
        self.hit_rate_label.setText("命中率: 0%")
        self.fault_rate_label.setText("缺页率: 0%")

    def _refresh_page_view(self):
        """刷新页面视图"""
        self.page_frame_view.set_data(self.page_replacer.get_frame_state())

    def _update_page_stats(self):
        """更新页面统计"""
        faults = self.page_replacer.page_faults
        hits = self.page_replacer.page_hits
        total = faults + hits

        self.page_fault_label.setText(f"缺页次数: {faults}")
        self.page_hit_label.setText(f"命中次数: {hits}")

        if total > 0:
            hit_rate = hits / total * 100
            fault_rate = faults / total * 100
            self.hit_rate_label.setText(f"命中率: {hit_rate:.1f}%")
            self.fault_rate_label.setText(f"缺页率: {fault_rate:.1f}%")
