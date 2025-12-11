"""
系统监控模块
获取系统真实的进程、CPU、内存信息
"""
import os
import time
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


@dataclass
class SystemProcessInfo:
    """系统进程信息"""
    pid: int
    name: str
    status: str
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    threads: int
    username: str
    create_time: str


@dataclass
class SystemInfo:
    """系统信息"""
    cpu_percent: float
    cpu_count: int
    cpu_freq: float
    memory_total: float  # GB
    memory_used: float   # GB
    memory_percent: float
    disk_total: float    # GB
    disk_used: float     # GB
    disk_percent: float
    boot_time: str
    process_count: int


class SystemMonitor:
    """系统监控器"""

    def __init__(self):
        self.available = PSUTIL_AVAILABLE
        self._cpu_history: List[float] = []
        self._memory_history: List[float] = []
        self._max_history = 60  # 保存60个数据点

    def is_available(self) -> bool:
        """检查psutil是否可用"""
        return self.available

    def get_system_info(self) -> Optional[SystemInfo]:
        """获取系统信息"""
        if not self.available:
            return None

        try:
            # CPU信息（非阻塞方式）
            cpu_percent = psutil.cpu_percent(interval=None)
            cpu_count = psutil.cpu_count()
            try:
                cpu_freq = psutil.cpu_freq().current if psutil.cpu_freq() else 0
            except:
                cpu_freq = 0

            # 内存信息
            memory = psutil.virtual_memory()
            memory_total = memory.total / (1024 ** 3)
            memory_used = memory.used / (1024 ** 3)
            memory_percent = memory.percent

            # 磁盘信息（兼容Windows和Linux）
            try:
                import platform
                if platform.system() == 'Windows':
                    disk = psutil.disk_usage('C:/')
                else:
                    disk = psutil.disk_usage('/')
                disk_total = disk.total / (1024 ** 3)
                disk_used = disk.used / (1024 ** 3)
                disk_percent = disk.percent
            except:
                disk_total = disk_used = disk_percent = 0

            # 启动时间
            boot_time = datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")

            # 进程数
            process_count = len(psutil.pids())

            # 更新历史
            self._cpu_history.append(cpu_percent)
            self._memory_history.append(memory_percent)
            if len(self._cpu_history) > self._max_history:
                self._cpu_history.pop(0)
            if len(self._memory_history) > self._max_history:
                self._memory_history.pop(0)

            return SystemInfo(
                cpu_percent=cpu_percent,
                cpu_count=cpu_count,
                cpu_freq=cpu_freq,
                memory_total=memory_total,
                memory_used=memory_used,
                memory_percent=memory_percent,
                disk_total=disk_total,
                disk_used=disk_used,
                disk_percent=disk_percent,
                boot_time=boot_time,
                process_count=process_count
            )
        except Exception as e:
            print(f"获取系统信息失败: {e}")
            return None

    def get_cpu_history(self) -> List[float]:
        """获取CPU使用率历史"""
        return self._cpu_history.copy()

    def get_memory_history(self) -> List[float]:
        """获取内存使用率历史"""
        return self._memory_history.copy()

    def get_process_list(self, sort_by: str = "cpu", limit: int = 50) -> List[SystemProcessInfo]:
        """
        获取进程列表
        sort_by: cpu, memory, pid, name
        """
        if not self.available:
            return []

        processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent',
                                             'memory_percent', 'memory_info',
                                             'num_threads', 'username', 'create_time']):
                try:
                    info = proc.info
                    memory_mb = info['memory_info'].rss / (1024 * 1024) if info['memory_info'] else 0

                    try:
                        create_time = datetime.fromtimestamp(info['create_time']).strftime("%H:%M:%S")
                    except:
                        create_time = "-"

                    processes.append(SystemProcessInfo(
                        pid=info['pid'],
                        name=info['name'] or "Unknown",
                        status=info['status'] or "unknown",
                        cpu_percent=info['cpu_percent'] or 0,
                        memory_percent=info['memory_percent'] or 0,
                        memory_mb=memory_mb,
                        threads=info['num_threads'] or 0,
                        username=info['username'] or "-",
                        create_time=create_time
                    ))
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

            # 排序
            if sort_by == "cpu":
                processes.sort(key=lambda x: x.cpu_percent, reverse=True)
            elif sort_by == "memory":
                processes.sort(key=lambda x: x.memory_percent, reverse=True)
            elif sort_by == "pid":
                processes.sort(key=lambda x: x.pid)
            elif sort_by == "name":
                processes.sort(key=lambda x: x.name.lower())

            return processes[:limit]
        except Exception as e:
            print(f"获取进程列表失败: {e}")
            return []

    def get_cpu_per_core(self) -> List[float]:
        """获取每个CPU核心的使用率"""
        if not self.available:
            return []
        try:
            # 非阻塞方式
            return psutil.cpu_percent(interval=None, percpu=True)
        except:
            return []

    def kill_process(self, pid: int) -> bool:
        """终止进程"""
        if not self.available:
            return False
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            return True
        except:
            return False


# 模拟数据（当psutil不可用时）
class MockSystemMonitor:
    """模拟系统监控器（用于演示）"""

    def __init__(self):
        self.available = True
        self._cpu_history: List[float] = []
        self._memory_history: List[float] = []
        self._max_history = 60
        import random
        self._random = random

    def is_available(self) -> bool:
        return True

    def get_system_info(self) -> SystemInfo:
        cpu = self._random.uniform(10, 60)
        mem = self._random.uniform(40, 70)

        self._cpu_history.append(cpu)
        self._memory_history.append(mem)
        if len(self._cpu_history) > self._max_history:
            self._cpu_history.pop(0)
        if len(self._memory_history) > self._max_history:
            self._memory_history.pop(0)

        return SystemInfo(
            cpu_percent=cpu,
            cpu_count=8,
            cpu_freq=3200,
            memory_total=16.0,
            memory_used=16.0 * mem / 100,
            memory_percent=mem,
            disk_total=500.0,
            disk_used=250.0,
            disk_percent=50.0,
            boot_time="2024-01-01 08:00:00",
            process_count=self._random.randint(100, 200)
        )

    def get_cpu_history(self) -> List[float]:
        return self._cpu_history.copy()

    def get_memory_history(self) -> List[float]:
        return self._memory_history.copy()

    def get_process_list(self, sort_by: str = "cpu", limit: int = 50) -> List[SystemProcessInfo]:
        processes = []
        sample_names = [
            "System", "svchost.exe", "chrome.exe", "python.exe", "explorer.exe",
            "code.exe", "node.exe", "firefox.exe", "WindowsTerminal.exe", "notepad.exe"
        ]

        for i in range(min(limit, 20)):
            processes.append(SystemProcessInfo(
                pid=1000 + i * 4,
                name=sample_names[i % len(sample_names)],
                status="running",
                cpu_percent=self._random.uniform(0, 15),
                memory_percent=self._random.uniform(0, 5),
                memory_mb=self._random.uniform(10, 500),
                threads=self._random.randint(1, 20),
                username="User",
                create_time="08:00:00"
            ))

        if sort_by == "cpu":
            processes.sort(key=lambda x: x.cpu_percent, reverse=True)
        elif sort_by == "memory":
            processes.sort(key=lambda x: x.memory_percent, reverse=True)

        return processes

    def get_cpu_per_core(self) -> List[float]:
        return [self._random.uniform(5, 80) for _ in range(8)]

    def kill_process(self, pid: int) -> bool:
        return False


def create_monitor() -> SystemMonitor:
    """创建监控器实例"""
    if PSUTIL_AVAILABLE:
        return SystemMonitor()
    else:
        return MockSystemMonitor()
