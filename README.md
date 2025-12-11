# 操作系统原理可视化实验展示平台

基于 Python + PyQt5 开发的操作系统核心原理可视化教学平台。

## 功能模块

### 1. 进程管理
- 进程生命周期管理（创建、就绪、运行、阻塞、终止）
- 进程状态转换可视化（状态机图）
- 进程队列动态展示（就绪队列、阻塞队列）
- 线程管理（创建、状态切换、终止）

### 2. 进程通信 (IPC)
- 生产者-消费者模型
- 共享缓冲区可视化
- 动态添加/移除生产者和消费者
- 生产/消费速率调节

### 3. 进程同步
- 哲学家就餐问题可视化
- 信号量机制（P/V 操作）
- 死锁检测与预防
- 叉子状态实时显示

### 4. CPU 调度
- 先来先服务 (FCFS)
- 时间片轮转 (RR)
- 最短作业优先 (SJF)
- 优先级调度
- 甘特图动态展示
- 性能指标计算

### 5. 内存管理
**动态内存分配**
- 首次适应 (First Fit)
- 最佳适应 (Best Fit)
- 最坏适应 (Worst Fit)
- 循环首次适应 (Next Fit)
- 内存碎片可视化

**页面置换**
- 先进先出 (FIFO)
- 最近最少使用 (LRU)
- 最佳置换 (OPT)
- 时钟算法 (CLOCK)
- 缺页率统计

### 6. 系统任务管理器
- 实时 CPU 使用率监控
- 内存使用率图表
- 每核心 CPU 使用率
- 系统进程列表
- 多种排序方式

## 环境要求

- Python 3.9.25
- PyQt5
- psutil（任务管理器模块需要）

## 安装

```bash
pip install -r requirements.txt
```

## 运行

```bash
python main.py
```

## 项目结构

```
os_visualization_platform/
├── main.py                 # 程序入口
├── core/                   # 核心逻辑
│   ├── process.py          # 进程与线程管理
│   ├── ipc.py              # 进程间通信
│   ├── synchronization.py  # 进程同步（信号量）
│   ├── scheduler.py        # CPU调度算法
│   ├── memory.py           # 内存管理算法
│   └── system_monitor.py   # 系统监控
├── ui/                     # 界面模块
│   ├── main_window.py      # 主窗口
│   ├── process_module.py   # 进程管理界面
│   ├── ipc_module.py       # 进程通信界面
│   ├── sync_module.py      # 进程同步界面
│   ├── scheduler_module.py # CPU调度界面
│   ├── memory_module.py    # 内存管理界面
│   └── task_manager_module.py  # 任务管理器界面
└── visualization/          # 可视化组件
    ├── state_machine.py    # 状态机可视化
    ├── queue_animation.py  # 队列动画
    ├── buffer_animation.py # 缓冲区动画
    ├── gantt_chart.py      # 甘特图
    ├── memory_view.py      # 内存视图
    └── philosopher_table.py # 哲学家餐桌
```

## 技术栈

- **GUI 框架**: PyQt5
- **系统监控**: psutil
- **多线程**: Python threading
- **数据结构**: dataclasses

## 版本

v2.2.0
