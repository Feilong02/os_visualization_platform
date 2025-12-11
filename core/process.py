"""
进程与线程数据结构及管理器
"""
from enum import Enum
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
import time


class ProcessState(Enum):
    """进程状态枚举"""
    CREATED = "创建"
    READY = "就绪"
    RUNNING = "运行"
    BLOCKED = "阻塞"
    TERMINATED = "终止"


class ThreadState(Enum):
    """线程状态枚举"""
    CREATED = "创建"
    READY = "就绪"
    RUNNING = "运行"
    BLOCKED = "阻塞"
    TERMINATED = "终止"


@dataclass
class Thread:
    """线程数据结构"""
    tid: int                                      # 线程ID
    pid: int                                      # 所属进程ID
    name: str                                     # 线程名
    state: ThreadState = ThreadState.CREATED     # 线程状态


@dataclass
class Process:
    """进程数据结构"""
    pid: int
    name: str
    state: ProcessState = ProcessState.CREATED
    # 调度相关字段（供调度模块使用）
    arrival_time: float = 0.0
    burst_time: float = 0.0
    remaining_time: float = 0.0
    waiting_time: float = 0.0
    turnaround_time: float = 0.0
    start_time: float = -1.0
    finish_time: float = -1.0
    # 线程列表
    threads: List[int] = field(default_factory=list)  # 线程ID列表

    def __post_init__(self):
        if self.remaining_time == 0:
            self.remaining_time = self.burst_time


class ProcessManager:
    """进程管理器"""

    # 有效的状态转换定义
    VALID_TRANSITIONS = {
        ProcessState.CREATED: [ProcessState.READY, ProcessState.TERMINATED],
        ProcessState.READY: [ProcessState.RUNNING, ProcessState.TERMINATED],
        ProcessState.RUNNING: [ProcessState.READY, ProcessState.BLOCKED, ProcessState.TERMINATED],
        ProcessState.BLOCKED: [ProcessState.READY, ProcessState.TERMINATED],
        ProcessState.TERMINATED: []
    }

    # 线程有效的状态转换定义
    THREAD_VALID_TRANSITIONS = {
        ThreadState.CREATED: [ThreadState.READY, ThreadState.TERMINATED],
        ThreadState.READY: [ThreadState.RUNNING, ThreadState.TERMINATED],
        ThreadState.RUNNING: [ThreadState.READY, ThreadState.BLOCKED, ThreadState.TERMINATED],
        ThreadState.BLOCKED: [ThreadState.READY, ThreadState.TERMINATED],
        ThreadState.TERMINATED: []
    }

    def __init__(self):
        self.processes: Dict[int, Process] = {}
        self.ready_queue: List[int] = []
        self.blocked_queue: List[int] = []
        self.running_process: Optional[int] = None
        self._next_pid = 1
        self._state_change_callbacks: List[Callable] = []
        # 线程管理
        self.threads: Dict[int, Thread] = {}  # 所有线程
        self._next_tid = 1
        self._thread_state_change_callbacks: List[Callable] = []

    def add_state_change_callback(self, callback: Callable):
        """添加状态变化回调"""
        self._state_change_callbacks.append(callback)

    def _notify_state_change(self, process: Process, old_state: ProcessState, new_state: ProcessState):
        """通知状态变化"""
        for callback in self._state_change_callbacks:
            callback(process, old_state, new_state)

    def create_process(self, name: str,
                       arrival_time: float = 0.0, burst_time: float = 5.0) -> Process:
        """创建新进程"""
        process = Process(
            pid=self._next_pid,
            name=name,
            state=ProcessState.CREATED,
            arrival_time=arrival_time,
            burst_time=burst_time,
            remaining_time=burst_time
        )
        self.processes[self._next_pid] = process
        self._next_pid += 1
        self._notify_state_change(process, None, ProcessState.CREATED)
        return process

    def _can_transition(self, pid: int, new_state: ProcessState) -> bool:
        """检查状态转换是否有效"""
        if pid not in self.processes:
            return False
        current_state = self.processes[pid].state
        return new_state in self.VALID_TRANSITIONS.get(current_state, [])

    def ready(self, pid: int) -> bool:
        """将进程设为就绪状态"""
        if not self._can_transition(pid, ProcessState.READY):
            return False

        process = self.processes[pid]
        old_state = process.state

        # 从阻塞队列移除（如果在的话）
        if pid in self.blocked_queue:
            self.blocked_queue.remove(pid)

        # 如果当前是运行状态，清除运行进程
        if self.running_process == pid:
            self.running_process = None

        process.state = ProcessState.READY
        if pid not in self.ready_queue:
            self.ready_queue.append(pid)

        self._notify_state_change(process, old_state, ProcessState.READY)
        return True

    def run(self, pid: int) -> bool:
        """将进程设为运行状态"""
        if not self._can_transition(pid, ProcessState.RUNNING):
            return False

        # 检查是否已有运行进程
        if self.running_process is not None and self.running_process != pid:
            # 将当前运行进程放回就绪队列
            self.ready(self.running_process)

        process = self.processes[pid]
        old_state = process.state

        # 从就绪队列移除
        if pid in self.ready_queue:
            self.ready_queue.remove(pid)

        process.state = ProcessState.RUNNING
        self.running_process = pid

        self._notify_state_change(process, old_state, ProcessState.RUNNING)
        return True

    def block(self, pid: int) -> bool:
        """将进程设为阻塞状态"""
        if not self._can_transition(pid, ProcessState.BLOCKED):
            return False

        process = self.processes[pid]
        old_state = process.state

        # 如果当前是运行进程，清除
        if self.running_process == pid:
            self.running_process = None

        process.state = ProcessState.BLOCKED
        if pid not in self.blocked_queue:
            self.blocked_queue.append(pid)

        self._notify_state_change(process, old_state, ProcessState.BLOCKED)
        return True

    def terminate(self, pid: int) -> bool:
        """终止进程"""
        if pid not in self.processes:
            return False

        process = self.processes[pid]
        if process.state == ProcessState.TERMINATED:
            return False

        old_state = process.state

        # 从各队列移除
        if pid in self.ready_queue:
            self.ready_queue.remove(pid)
        if pid in self.blocked_queue:
            self.blocked_queue.remove(pid)
        if self.running_process == pid:
            self.running_process = None

        process.state = ProcessState.TERMINATED
        self._notify_state_change(process, old_state, ProcessState.TERMINATED)
        return True

    def delete_process(self, pid: int) -> bool:
        """从系统中删除进程"""
        if pid not in self.processes:
            return False

        self.terminate(pid)
        del self.processes[pid]
        return True

    def get_process(self, pid: int) -> Optional[Process]:
        """获取进程"""
        return self.processes.get(pid)

    def get_all_processes(self) -> List[Process]:
        """获取所有进程"""
        return list(self.processes.values())

    def get_ready_queue(self) -> List[Process]:
        """获取就绪队列中的进程"""
        return [self.processes[pid] for pid in self.ready_queue if pid in self.processes]

    def get_blocked_queue(self) -> List[Process]:
        """获取阻塞队列中的进程"""
        return [self.processes[pid] for pid in self.blocked_queue if pid in self.processes]

    def get_running_process(self) -> Optional[Process]:
        """获取当前运行的进程"""
        if self.running_process is not None:
            return self.processes.get(self.running_process)
        return None

    def reset(self):
        """重置管理器"""
        self.processes.clear()
        self.ready_queue.clear()
        self.blocked_queue.clear()
        self.running_process = None
        self._next_pid = 1
        # 重置线程
        self.threads.clear()
        self._next_tid = 1

    # ========== 线程管理方法 ==========

    def add_thread_state_change_callback(self, callback: Callable):
        """添加线程状态变化回调"""
        self._thread_state_change_callbacks.append(callback)

    def _notify_thread_state_change(self, thread: Thread, old_state: ThreadState, new_state: ThreadState):
        """通知线程状态变化"""
        for callback in self._thread_state_change_callbacks:
            callback(thread, old_state, new_state)

    def create_thread(self, pid: int, name: str) -> Optional[Thread]:
        """在指定进程下创建新线程"""
        if pid not in self.processes:
            return None
        process = self.processes[pid]
        # 进程必须处于非终止状态
        if process.state == ProcessState.TERMINATED:
            return None

        thread = Thread(
            tid=self._next_tid,
            pid=pid,
            name=name,
            state=ThreadState.CREATED
        )
        self.threads[self._next_tid] = thread
        process.threads.append(self._next_tid)
        self._next_tid += 1
        self._notify_thread_state_change(thread, None, ThreadState.CREATED)
        return thread

    def _can_thread_transition(self, tid: int, new_state: ThreadState) -> bool:
        """检查线程状态转换是否有效"""
        if tid not in self.threads:
            return False
        current_state = self.threads[tid].state
        return new_state in self.THREAD_VALID_TRANSITIONS.get(current_state, [])

    def thread_ready(self, tid: int) -> bool:
        """将线程设为就绪状态"""
        if not self._can_thread_transition(tid, ThreadState.READY):
            return False
        thread = self.threads[tid]
        old_state = thread.state
        thread.state = ThreadState.READY
        self._notify_thread_state_change(thread, old_state, ThreadState.READY)
        return True

    def thread_run(self, tid: int) -> bool:
        """将线程设为运行状态"""
        if not self._can_thread_transition(tid, ThreadState.RUNNING):
            return False
        thread = self.threads[tid]
        old_state = thread.state
        thread.state = ThreadState.RUNNING
        self._notify_thread_state_change(thread, old_state, ThreadState.RUNNING)
        return True

    def thread_block(self, tid: int) -> bool:
        """将线程设为阻塞状态"""
        if not self._can_thread_transition(tid, ThreadState.BLOCKED):
            return False
        thread = self.threads[tid]
        old_state = thread.state
        thread.state = ThreadState.BLOCKED
        self._notify_thread_state_change(thread, old_state, ThreadState.BLOCKED)
        return True

    def thread_terminate(self, tid: int) -> bool:
        """终止线程"""
        if tid not in self.threads:
            return False
        thread = self.threads[tid]
        if thread.state == ThreadState.TERMINATED:
            return False
        old_state = thread.state
        thread.state = ThreadState.TERMINATED
        self._notify_thread_state_change(thread, old_state, ThreadState.TERMINATED)
        return True

    def delete_thread(self, tid: int) -> bool:
        """从系统中删除线程"""
        if tid not in self.threads:
            return False
        thread = self.threads[tid]
        # 从所属进程的线程列表中移除
        if thread.pid in self.processes:
            process = self.processes[thread.pid]
            if tid in process.threads:
                process.threads.remove(tid)
        self.thread_terminate(tid)
        del self.threads[tid]
        return True

    def get_thread(self, tid: int) -> Optional[Thread]:
        """获取线程"""
        return self.threads.get(tid)

    def get_all_threads(self) -> List[Thread]:
        """获取所有线程"""
        return list(self.threads.values())

    def get_process_threads(self, pid: int) -> List[Thread]:
        """获取指定进程的所有线程"""
        if pid not in self.processes:
            return []
        return [self.threads[tid] for tid in self.processes[pid].threads if tid in self.threads]
