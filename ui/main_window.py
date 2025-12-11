"""
主窗口
"""
from PyQt5.QtWidgets import (QMainWindow, QTabWidget, QWidget, QVBoxLayout,
                             QMenuBar, QMenu, QAction, QMessageBox, QStatusBar,
                             QLabel)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QFont
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("操作系统原理可视化实验展示平台")
        self.setGeometry(100, 100, 1200, 800)

        # 模块实例（延迟加载）
        self._modules = {}
        self._module_loaded = [False] * 6

        self._init_ui()
        self._init_menu()
        self._init_statusbar()

    def _init_ui(self):
        """初始化UI"""
        # 中央标签页
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ccc;
                background: white;
            }
            QTabBar::tab {
                background: #e0e0e0;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom: 2px solid #2196F3;
            }
            QTabBar::tab:hover {
                background: #f0f0f0;
            }
        """)

        # 创建占位符页面（延迟加载实际模块）
        self._placeholders = []
        tab_names = [
            "1. 进程管理", "2. 进程通信", "3. 进程同步",
            "4. CPU调度", "5. 内存管理", "6. 任务管理器"
        ]

        for i, name in enumerate(tab_names):
            placeholder = QWidget()
            layout = QVBoxLayout(placeholder)
            loading_label = QLabel("正在加载...")
            loading_label.setAlignment(Qt.AlignCenter)
            loading_label.setStyleSheet("font-size: 16px; color: #666;")
            layout.addWidget(loading_label)
            self._placeholders.append(placeholder)
            self.tabs.addTab(placeholder, name)

        # 连接标签页切换信号
        self.tabs.currentChanged.connect(self._on_tab_changed)

        self.setCentralWidget(self.tabs)

        # 延迟加载第一个模块
        QTimer.singleShot(100, lambda: self._load_module(0))

    def _load_module(self, index: int):
        """延迟加载模块"""
        if self._module_loaded[index]:
            return

        self._module_loaded[index] = True

        # 动态导入并创建模块
        module = None
        if index == 0:
            from ui.process_module import ProcessModule
            module = ProcessModule()
            self._modules['process'] = module
        elif index == 1:
            from ui.ipc_module import IPCModule
            module = IPCModule()
            self._modules['ipc'] = module
        elif index == 2:
            from ui.sync_module import SyncModule
            module = SyncModule()
            self._modules['sync'] = module
        elif index == 3:
            from ui.scheduler_module import SchedulerModule
            module = SchedulerModule()
            self._modules['scheduler'] = module
        elif index == 4:
            from ui.memory_module import MemoryModule
            module = MemoryModule()
            self._modules['memory'] = module
        elif index == 5:
            from ui.task_manager_module import TaskManagerModule
            module = TaskManagerModule()
            self._modules['task_manager'] = module

        if module:
            # 替换占位符
            self.tabs.removeTab(index)
            self.tabs.insertTab(index, module, self.tabs.tabText(index) if index < self.tabs.count() else "")
            # 恢复标签名
            tab_names = [
                "1. 进程管理", "2. 进程通信", "3. 进程同步",
                "4. CPU调度", "5. 内存管理", "6. 任务管理器"
            ]
            self.tabs.setTabText(index, tab_names[index])
            self.tabs.setCurrentIndex(index)

    def _on_tab_changed(self, index: int):
        """标签页切换时加载模块并管理定时器"""
        # 加载新模块
        if not self._module_loaded[index]:
            self._load_module(index)

        # 暂停任务管理器定时器（当不在该标签页时）
        if 'task_manager' in self._modules:
            task_manager = self._modules['task_manager']
            if index == 5:
                # 切换到任务管理器，启动刷新
                if hasattr(task_manager, 'refresh_timer') and not task_manager.refresh_timer.isActive():
                    task_manager.refresh_timer.start(task_manager.refresh_interval)
                    task_manager._refresh_all()
            else:
                # 离开任务管理器，暂停刷新
                if hasattr(task_manager, 'refresh_timer'):
                    task_manager.refresh_timer.stop()

    def _init_menu(self):
        """初始化菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")

        exit_action = QAction("退出(&Q)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 视图菜单
        view_menu = menubar.addMenu("视图(&V)")

        process_action = QAction("进程管理", self)
        process_action.triggered.connect(lambda: self.tabs.setCurrentIndex(0))
        view_menu.addAction(process_action)

        ipc_action = QAction("进程通信", self)
        ipc_action.triggered.connect(lambda: self.tabs.setCurrentIndex(1))
        view_menu.addAction(ipc_action)

        sync_action = QAction("进程同步", self)
        sync_action.triggered.connect(lambda: self.tabs.setCurrentIndex(2))
        view_menu.addAction(sync_action)

        scheduler_action = QAction("CPU调度", self)
        scheduler_action.triggered.connect(lambda: self.tabs.setCurrentIndex(3))
        view_menu.addAction(scheduler_action)

        memory_action = QAction("内存管理", self)
        memory_action.triggered.connect(lambda: self.tabs.setCurrentIndex(4))
        view_menu.addAction(memory_action)

        taskman_action = QAction("任务管理器", self)
        taskman_action.triggered.connect(lambda: self.tabs.setCurrentIndex(5))
        view_menu.addAction(taskman_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")

        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

        usage_action = QAction("使用说明(&U)", self)
        usage_action.triggered.connect(self._show_usage)
        help_menu.addAction(usage_action)

    def _init_statusbar(self):
        """初始化状态栏"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        self.status_label = QLabel("就绪")
        self.statusbar.addWidget(self.status_label)

        # 版本信息
        version_label = QLabel("v2.2.0")
        self.statusbar.addPermanentWidget(version_label)

    def _show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于",
            """<h2>操作系统原理可视化实验展示平台</h2>
            <p>版本: 2.2.0</p>
            <p>本平台用于展示操作系统核心原理：</p>
            <ul>
                <li>进程与线程的创建与管理</li>
                <li>进程间通信（IPC）机制</li>
                <li>基于信号量的进程同步</li>
                <li>CPU调度算法</li>
                <li>动态内存分配与页面置换</li>
                <li>系统任务管理器</li>
            </ul>
            <p>技术栈: Python + PyQt5</p>
            """
        )

    def _show_usage(self):
        """显示使用说明"""
        QMessageBox.information(
            self,
            "使用说明",
            """<h3>模块说明</h3>

<b>1. 进程管理</b>
- 创建、删除进程
- 观察进程状态转换（创建→就绪→运行→阻塞→终止）
- 查看进程队列变化

<b>2. 进程通信</b>
- 生产者-消费者模型演示
- 添加/移除生产者和消费者
- 调整生产/消费速率
- 观察共享缓冲区变化

<b>3. 进程同步</b>
- 哲学家就餐问题演示
- P/V操作可视化
- 信号量状态监控
- 死锁预防机制

<b>4. CPU调度</b>
- FCFS、RR、SJF、优先级调度
- 甘特图动态展示
- 性能指标计算

<b>5. 内存管理（扩展）</b>
- 动态内存分配（首次/最佳/最坏适应）
- 页面置换算法（FIFO/LRU/OPT/CLOCK）
- 内存碎片可视化

<b>6. 任务管理器（扩展）</b>
- 实时系统监控
- CPU/内存使用率图表
- 进程列表与排序
"""
        )

    def closeEvent(self, event):
        """关闭事件"""
        # 停止所有已加载模块的线程和定时器
        if 'ipc' in self._modules:
            self._modules['ipc'].closeEvent(event)
        if 'sync' in self._modules:
            self._modules['sync'].closeEvent(event)
        if 'task_manager' in self._modules:
            self._modules['task_manager'].closeEvent(event)
        super().closeEvent(event)
