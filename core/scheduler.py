"""
CPU调度算法实现
"""
from enum import Enum
from typing import List, Tuple, Optional, Callable
from dataclasses import dataclass
from copy import deepcopy


class SchedulerAlgorithm(Enum):
    """调度算法枚举"""
    FCFS = "先来先服务 (FCFS)"
    RR = "时间片轮转 (RR)"
    SJF = "最短作业优先 (SJF)"
    PRIORITY = "优先级调度"


@dataclass
class ScheduleProcess:
    """用于调度的进程信息"""
    pid: int
    name: str
    arrival_time: float
    burst_time: float
    priority: int = 1
    remaining_time: float = 0.0
    start_time: float = -1.0
    finish_time: float = -1.0
    waiting_time: float = 0.0
    turnaround_time: float = 0.0

    def __post_init__(self):
        if self.remaining_time == 0:
            self.remaining_time = self.burst_time


@dataclass
class GanttBlock:
    """甘特图块"""
    pid: int
    name: str
    start_time: float
    end_time: float
    color_index: int = 0


class Scheduler:
    """CPU调度器"""

    def __init__(self):
        self.processes: List[ScheduleProcess] = []
        self.gantt_chart: List[GanttBlock] = []
        self.current_time: float = 0
        self.time_slice: float = 2.0
        self._step_callback: Optional[Callable] = None

    def set_step_callback(self, callback: Callable):
        """设置单步执行回调"""
        self._step_callback = callback

    def add_process(self, pid: int, name: str, arrival_time: float,
                    burst_time: float, priority: int = 1):
        """添加进程"""
        process = ScheduleProcess(
            pid=pid,
            name=name,
            arrival_time=arrival_time,
            burst_time=burst_time,
            priority=priority
        )
        self.processes.append(process)

    def clear_processes(self):
        """清空进程列表"""
        self.processes.clear()
        self.gantt_chart.clear()
        self.current_time = 0

    def reset(self):
        """重置调度状态（保留进程）"""
        for p in self.processes:
            p.remaining_time = p.burst_time
            p.start_time = -1
            p.finish_time = -1
            p.waiting_time = 0
            p.turnaround_time = 0
        self.gantt_chart.clear()
        self.current_time = 0

    def fcfs(self) -> Tuple[List[GanttBlock], List[ScheduleProcess]]:
        """先来先服务调度算法"""
        self.reset()
        if not self.processes:
            return [], []

        # 按到达时间排序
        sorted_processes = sorted(self.processes, key=lambda p: (p.arrival_time, p.pid))
        self.current_time = 0

        for i, process in enumerate(sorted_processes):
            # 如果CPU空闲，跳到进程到达时间
            if self.current_time < process.arrival_time:
                self.current_time = process.arrival_time

            process.start_time = self.current_time
            process.finish_time = self.current_time + process.burst_time

            # 创建甘特图块
            block = GanttBlock(
                pid=process.pid,
                name=process.name,
                start_time=self.current_time,
                end_time=process.finish_time,
                color_index=i % 10
            )
            self.gantt_chart.append(block)

            process.remaining_time = 0
            self.current_time = process.finish_time
            process.turnaround_time = process.finish_time - process.arrival_time
            process.waiting_time = process.turnaround_time - process.burst_time

        return self.gantt_chart, sorted_processes

    def round_robin(self, time_slice: float = 2.0) -> Tuple[List[GanttBlock], List[ScheduleProcess]]:
        """时间片轮转调度算法"""
        self.reset()
        self.time_slice = time_slice
        if not self.processes:
            return [], []

        # 复制进程列表
        processes = deepcopy(self.processes)
        ready_queue: List[ScheduleProcess] = []
        color_map = {p.pid: i % 10 for i, p in enumerate(processes)}

        # 按到达时间排序
        processes.sort(key=lambda p: (p.arrival_time, p.pid))
        self.current_time = 0
        process_index = 0
        n = len(processes)

        while process_index < n or ready_queue:
            # 将已到达的进程加入就绪队列
            while process_index < n and processes[process_index].arrival_time <= self.current_time:
                ready_queue.append(processes[process_index])
                process_index += 1

            if not ready_queue:
                # 没有就绪进程，跳到下一个进程到达时间
                if process_index < n:
                    self.current_time = processes[process_index].arrival_time
                continue

            # 取出队首进程
            current_process = ready_queue.pop(0)

            # 记录首次开始时间
            if current_process.start_time < 0:
                current_process.start_time = self.current_time

            # 计算执行时间
            execute_time = min(time_slice, current_process.remaining_time)
            start = self.current_time
            self.current_time += execute_time
            current_process.remaining_time -= execute_time

            # 创建甘特图块
            block = GanttBlock(
                pid=current_process.pid,
                name=current_process.name,
                start_time=start,
                end_time=self.current_time,
                color_index=color_map[current_process.pid]
            )
            self.gantt_chart.append(block)

            # 将在此期间到达的进程加入就绪队列
            while process_index < n and processes[process_index].arrival_time <= self.current_time:
                ready_queue.append(processes[process_index])
                process_index += 1

            # 如果进程未完成，放回队尾
            if current_process.remaining_time > 0:
                ready_queue.append(current_process)
            else:
                current_process.finish_time = self.current_time
                current_process.turnaround_time = current_process.finish_time - current_process.arrival_time
                current_process.waiting_time = current_process.turnaround_time - current_process.burst_time
                # 更新原始进程数据
                for p in self.processes:
                    if p.pid == current_process.pid:
                        p.start_time = current_process.start_time
                        p.finish_time = current_process.finish_time
                        p.turnaround_time = current_process.turnaround_time
                        p.waiting_time = current_process.waiting_time
                        p.remaining_time = 0
                        break

        return self.gantt_chart, self.processes

    def sjf(self, preemptive: bool = False) -> Tuple[List[GanttBlock], List[ScheduleProcess]]:
        """最短作业优先调度算法"""
        self.reset()
        if not self.processes:
            return [], []

        if preemptive:
            return self._sjf_preemptive()
        else:
            return self._sjf_non_preemptive()

    def _sjf_non_preemptive(self) -> Tuple[List[GanttBlock], List[ScheduleProcess]]:
        """非抢占式SJF"""
        processes = deepcopy(self.processes)
        color_map = {p.pid: i % 10 for i, p in enumerate(processes)}
        completed = []
        self.current_time = 0

        while len(completed) < len(processes):
            # 找出已到达且未完成的进程
            available = [p for p in processes
                         if p.arrival_time <= self.current_time and p not in completed]

            if not available:
                # 跳到下一个进程到达时间
                not_arrived = [p for p in processes if p not in completed]
                if not_arrived:
                    self.current_time = min(p.arrival_time for p in not_arrived)
                continue

            # 选择最短作业
            shortest = min(available, key=lambda p: (p.burst_time, p.arrival_time))

            shortest.start_time = self.current_time
            shortest.finish_time = self.current_time + shortest.burst_time

            block = GanttBlock(
                pid=shortest.pid,
                name=shortest.name,
                start_time=self.current_time,
                end_time=shortest.finish_time,
                color_index=color_map[shortest.pid]
            )
            self.gantt_chart.append(block)

            self.current_time = shortest.finish_time
            shortest.turnaround_time = shortest.finish_time - shortest.arrival_time
            shortest.waiting_time = shortest.turnaround_time - shortest.burst_time
            shortest.remaining_time = 0
            completed.append(shortest)

            # 更新原始进程
            for p in self.processes:
                if p.pid == shortest.pid:
                    p.start_time = shortest.start_time
                    p.finish_time = shortest.finish_time
                    p.turnaround_time = shortest.turnaround_time
                    p.waiting_time = shortest.waiting_time
                    p.remaining_time = 0
                    break

        return self.gantt_chart, self.processes

    def _sjf_preemptive(self) -> Tuple[List[GanttBlock], List[ScheduleProcess]]:
        """抢占式SJF (SRTF)"""
        processes = deepcopy(self.processes)
        color_map = {p.pid: i % 10 for i, p in enumerate(processes)}
        self.current_time = 0
        completed_count = 0
        n = len(processes)
        last_process = None
        last_start = 0

        while completed_count < n:
            # 找出已到达且未完成的进程
            available = [p for p in processes
                         if p.arrival_time <= self.current_time and p.remaining_time > 0]

            if not available:
                not_completed = [p for p in processes if p.remaining_time > 0]
                if not_completed:
                    self.current_time = min(p.arrival_time for p in not_completed)
                continue

            # 选择剩余时间最短的
            shortest = min(available, key=lambda p: (p.remaining_time, p.arrival_time))

            # 如果切换进程，保存上一个甘特图块
            if last_process is not None and last_process.pid != shortest.pid:
                block = GanttBlock(
                    pid=last_process.pid,
                    name=last_process.name,
                    start_time=last_start,
                    end_time=self.current_time,
                    color_index=color_map[last_process.pid]
                )
                self.gantt_chart.append(block)
                last_start = self.current_time

            if last_process is None or last_process.pid != shortest.pid:
                last_start = self.current_time
                if shortest.start_time < 0:
                    shortest.start_time = self.current_time

            last_process = shortest

            # 执行1个时间单位
            self.current_time += 1
            shortest.remaining_time -= 1

            if shortest.remaining_time == 0:
                # 进程完成
                block = GanttBlock(
                    pid=shortest.pid,
                    name=shortest.name,
                    start_time=last_start,
                    end_time=self.current_time,
                    color_index=color_map[shortest.pid]
                )
                self.gantt_chart.append(block)

                shortest.finish_time = self.current_time
                shortest.turnaround_time = shortest.finish_time - shortest.arrival_time
                shortest.waiting_time = shortest.turnaround_time - shortest.burst_time
                completed_count += 1
                last_process = None

                # 更新原始进程
                for p in self.processes:
                    if p.pid == shortest.pid:
                        p.start_time = shortest.start_time
                        p.finish_time = shortest.finish_time
                        p.turnaround_time = shortest.turnaround_time
                        p.waiting_time = shortest.waiting_time
                        p.remaining_time = 0
                        break

        return self.gantt_chart, self.processes

    def priority_scheduling(self, preemptive: bool = False) -> Tuple[List[GanttBlock], List[ScheduleProcess]]:
        """优先级调度算法（数字越小优先级越高）"""
        self.reset()
        if not self.processes:
            return [], []

        processes = deepcopy(self.processes)
        color_map = {p.pid: i % 10 for i, p in enumerate(processes)}
        completed = []
        self.current_time = 0

        while len(completed) < len(processes):
            available = [p for p in processes
                         if p.arrival_time <= self.current_time and p not in completed]

            if not available:
                not_arrived = [p for p in processes if p not in completed]
                if not_arrived:
                    self.current_time = min(p.arrival_time for p in not_arrived)
                continue

            # 选择最高优先级（数字最小）
            highest = min(available, key=lambda p: (p.priority, p.arrival_time))

            highest.start_time = self.current_time
            highest.finish_time = self.current_time + highest.burst_time

            block = GanttBlock(
                pid=highest.pid,
                name=highest.name,
                start_time=self.current_time,
                end_time=highest.finish_time,
                color_index=color_map[highest.pid]
            )
            self.gantt_chart.append(block)

            self.current_time = highest.finish_time
            highest.turnaround_time = highest.finish_time - highest.arrival_time
            highest.waiting_time = highest.turnaround_time - highest.burst_time
            highest.remaining_time = 0
            completed.append(highest)

            for p in self.processes:
                if p.pid == highest.pid:
                    p.start_time = highest.start_time
                    p.finish_time = highest.finish_time
                    p.turnaround_time = highest.turnaround_time
                    p.waiting_time = highest.waiting_time
                    p.remaining_time = 0
                    break

        return self.gantt_chart, self.processes

    def get_metrics(self) -> dict:
        """计算性能指标"""
        if not self.processes:
            return {}

        completed = [p for p in self.processes if p.finish_time >= 0]
        if not completed:
            return {}

        avg_waiting = sum(p.waiting_time for p in completed) / len(completed)
        avg_turnaround = sum(p.turnaround_time for p in completed) / len(completed)

        return {
            "avg_waiting_time": round(avg_waiting, 2),
            "avg_turnaround_time": round(avg_turnaround, 2),
            "total_time": self.current_time,
            "process_count": len(completed)
        }
