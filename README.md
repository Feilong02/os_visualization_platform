# 操作系统原理可视化实验展示平台

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green.svg)](https://pypi.org/project/PyQt5/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

一个基于 Python + PyQt5 开发的操作系统核心原理可视化教学平台，通过交互式动画演示进程管理、CPU调度、内存管理等操作系统核心概念。

## 项目背景

操作系统课程是计算机相关专业的核心基础课程，但其概念（如进程状态转换、调度算法、死锁等）较为抽象。本项目旨在通过**可视化**的方式，将这些抽象概念具象化，帮助学习者更直观地理解操作系统的工作原理。

## 功能特性

### 核心模块

| 模块 | 功能描述 |
|------|----------|
| **进程管理** | 进程生命周期管理、状态机可视化、线程管理、就绪/阻塞队列展示 |
| **进程通信** | 生产者-消费者模型、共享缓冲区可视化、动态速率调节 |
| **进程同步** | 哲学家就餐问题、信号量 P/V 操作、死锁检测与预防 |
| **CPU 调度** | FCFS、RR、SJF、优先级调度，甘特图动态演示，性能指标计算 |
| **内存管理** | 动态分配（首次/最佳/最坏/循环适应）、页面置换（FIFO/LRU/OPT/CLOCK） |
| **任务管理器** | 实时系统监控、CPU/内存使用率图表、进程列表管理 |

### 详细功能

<details>
<summary><b>1. 进程管理</b></summary>

- 五状态进程模型（新建、就绪、运行、阻塞、终止）
- 进程状态转换动画与状态机图
- 就绪队列、阻塞队列动态展示
- 支持在进程下创建线程
- 状态转换合法性自动验证

</details>

<details>
<summary><b>2. 进程间通信 (IPC)</b></summary>

- 经典生产者-消费者模型
- 有界缓冲区可视化（环形队列）
- 支持动态添加/移除生产者和消费者
- 生产/消费速率实时调节
- 同步机制演示（信号量控制）

</details>

<details>
<summary><b>3. 进程同步</b></summary>

- 哲学家就餐问题动画演示
- 信号量 P/V 操作可视化
- 死锁检测算法（资源分配图环检测）
- 死锁预防策略演示（奇偶策略）
- 叉子状态、哲学家状态实时显示

</details>

<details>
<summary><b>4. CPU 调度</b></summary>

- **FCFS**（先来先服务）：按到达顺序调度
- **RR**（时间片轮转）：支持自定义时间片大小
- **SJF**（最短作业优先）：选择剩余时间最短的进程
- **Priority**（优先级调度）：支持自定义优先级
- 甘特图动态演示调度过程
- 性能指标：平均等待时间、平均周转时间

</details>

<details>
<summary><b>5. 内存管理</b></summary>

**动态内存分配**
- 首次适应（First Fit）
- 最佳适应（Best Fit）
- 最坏适应（Worst Fit）
- 循环首次适应（Next Fit）
- 内存碎片可视化

**页面置换算法**
- FIFO（先进先出）
- LRU（最近最少使用）
- OPT（最佳置换，理论最优）
- CLOCK（时钟算法）
- 缺页率统计与对比

</details>

<details>
<summary><b>6. 任务管理器</b></summary>

- 实时 CPU 使用率监控（曲线图）
- 内存使用率图表
- 各 CPU 核心独立使用率显示
- 系统进程列表（PID、名称、CPU%、内存%）
- 多种排序方式
- 刷新间隔可调节

</details>

## 快速开始

### 环境要求

- Python 3.8 或更高版本
- 支持的操作系统：Windows、macOS、Linux

### 安装

1. **克隆项目**

```bash
git clone https://github.com/Feilong02/os_visualization_platform.git
cd os_visualization_platform
```

2. **安装依赖**

```bash
pip install -r requirements.txt
```

或手动安装：

```bash
pip install PyQt5 psutil
```

### 运行

```bash
python main.py
```

## 项目结构

```
os_visualization_platform/
├── main.py                      # 程序入口
├── requirements.txt             # 项目依赖
├── README.md                    # 项目说明
│
├── core/                        # 核心逻辑层（Model）
│   ├── process.py               # 进程与线程管理
│   ├── scheduler.py             # CPU 调度算法
│   ├── synchronization.py       # 信号量与哲学家问题
│   ├── ipc.py                   # 进程间通信
│   ├── memory.py                # 内存管理算法
│   └── system_monitor.py        # 系统监控
│
├── ui/                          # 界面控制层（Controller）
│   ├── main_window.py           # 主窗口
│   ├── process_module.py        # 进程管理界面
│   ├── ipc_module.py            # 进程通信界面
│   ├── sync_module.py           # 进程同步界面
│   ├── scheduler_module.py      # CPU 调度界面
│   ├── memory_module.py         # 内存管理界面
│   └── task_manager_module.py   # 任务管理器界面
│
└── visualization/               # 可视化组件层（View）
    ├── state_machine.py         # 进程状态机动画
    ├── gantt_chart.py           # 甘特图组件
    ├── queue_animation.py       # 队列动画
    ├── buffer_animation.py      # 缓冲区动画
    ├── memory_view.py           # 内存块可视化
    └── philosopher_table.py     # 哲学家餐桌动画
```

## 技术架构

### 技术栈

| 技术 | 用途 |
|------|------|
| Python 3.8+ | 主要开发语言 |
| PyQt5 | GUI 图形界面框架 |
| psutil | 系统监控（CPU、内存、进程信息） |
| threading | 多线程支持 |
| dataclasses | 数据类定义 |

### 架构模式

采用 **MVC 分层架构**：

```
┌─────────────────────────────────────────────────┐
│              UI 层 (Controller)                  │
│         界面交互与业务协调                        │
├─────────────────────────────────────────────────┤
│           可视化组件层 (View)                     │
│         动画绘制与图形展示                        │
├─────────────────────────────────────────────────┤
│            核心逻辑层 (Model)                     │
│         算法实现与数据处理                        │
└─────────────────────────────────────────────────┘
```

### 数据流向

```
用户操作 → UI层接收事件 → 调用Core层算法 → 返回计算结果 → 更新Visualization层 → 界面刷新
```

## 算法说明

### CPU 调度算法

| 算法 | 时间复杂度 | 特点 |
|------|-----------|------|
| FCFS | O(n) | 简单公平，但可能产生"护航效应" |
| RR | O(n) | 响应时间短，适合交互式系统 |
| SJF | O(n log n) | 平均等待时间最优，但可能饥饿 |
| Priority | O(n log n) | 灵活，但低优先级可能饥饿 |

### 页面置换算法

| 算法 | 缺页率 | 实现复杂度 | 备注 |
|------|--------|-----------|------|
| FIFO | 较高 | 简单 | 可能出现 Belady 异常 |
| LRU | 较低 | 较复杂 | 需要记录访问时间 |
| OPT | 最低 | 不可实现 | 理论最优，用于对比 |
| CLOCK | 接近LRU | 中等 | LRU 的近似，开销小 |

## 文档

- [技术文档与使用手册](技术文档与使用手册.md) - 详细的技术实现与操作指南
- [PPT大纲](PPT大纲.md) - 项目展示 PPT 大纲

## 版本历史

- **v2.2.0** - 当前版本
  - 新增任务管理器模块
  - 完善死锁检测算法
  - 优化 UI 交互体验

- **v2.0.0**
  - 新增内存管理模块（动态分配 + 页面置换）
  - 优化可视化效果

- **v1.0.0**
  - 初始版本，实现四大核心模块
  - 进程管理、进程通信、进程同步、CPU 调度

## 许可证

本项目采用 [MIT License](LICENSE) 开源许可证。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 致谢

感谢操作系统课程的指导老师！

---

*如有问题或建议，请在 [Issues](https://github.com/Feilong02/os_visualization_platform/issues) 中反馈。*
