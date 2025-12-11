"""
基于信号量的进程同步机制实现
实现哲学家就餐问题
"""
import threading
import time
import random
from enum import Enum
from typing import List, Callable, Optional
from dataclasses import dataclass


class PhilosopherState(Enum):
    """哲学家状态"""
    THINKING = "思考"
    HUNGRY = "饥饿"
    EATING = "进餐"


@dataclass
class SemaphoreLog:
    """信号量操作日志"""
    timestamp: float
    operation: str  # "P" or "V"
    semaphore_name: str
    process_name: str
    old_value: int
    new_value: int
    result: str  # "success" or "blocked"


class Semaphore:
    """信号量实现"""

    def __init__(self, value: int = 1, name: str = "sem"):
        self._value = value
        self._initial_value = value
        self.name = name
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)
        self.waiting_queue: List[str] = []
        self._log_callback: Optional[Callable] = None
        self._force_wakeup = False  # 强制唤醒标志

    @property
    def value(self) -> int:
        return self._value

    def set_log_callback(self, callback: Callable):
        """设置日志回调"""
        self._log_callback = callback

    def _log(self, operation: str, process_name: str, old_value: int, new_value: int, result: str):
        """记录操作日志"""
        if self._log_callback:
            log = SemaphoreLog(
                timestamp=time.time(),
                operation=operation,
                semaphore_name=self.name,
                process_name=process_name,
                old_value=old_value,
                new_value=new_value,
                result=result
            )
            self._log_callback(log)

    def P(self, process_name: str = "unknown") -> bool:
        """P操作（wait/申请资源）"""
        with self._condition:
            old_value = self._value
            self._value -= 1

            if self._value < 0:
                # 需要阻塞
                self.waiting_queue.append(process_name)
                self._log("P", process_name, old_value, self._value, "blocked")
                # 等待被唤醒
                self._condition.wait()
                # 检查是否因为强制唤醒（停止）而退出
                if process_name in self.waiting_queue:
                    self.waiting_queue.remove(process_name)
                    # 如果是强制唤醒，恢复信号量值并返回失败
                    if self._force_wakeup:
                        self._value += 1
                        return False

            self._log("P", process_name, old_value, self._value, "success")
            return True

    def V(self, process_name: str = "unknown"):
        """V操作（signal/释放资源）"""
        with self._condition:
            old_value = self._value
            self._value += 1
            self._log("V", process_name, old_value, self._value, "success")

            if self._value <= 0:
                # 唤醒一个等待进程
                self._condition.notify()

    def force_wakeup_all(self):
        """强制唤醒所有等待的线程"""
        with self._condition:
            self._force_wakeup = True
            self._condition.notify_all()

    def reset(self):
        """重置信号量"""
        with self._lock:
            self._value = self._initial_value
            self.waiting_queue.clear()
            self._force_wakeup = False


class Philosopher(threading.Thread):
    """哲学家线程"""

    def __init__(self, philosopher_id: int, left_fork: Semaphore, right_fork: Semaphore,
                 state_callback: Optional[Callable] = None):
        super().__init__()
        self.philosopher_id = philosopher_id
        self.name = f"哲学家{philosopher_id}"
        self.left_fork = left_fork
        self.right_fork = right_fork
        self.state = PhilosopherState.THINKING
        self._state_callback = state_callback
        self._running = False
        self._paused = False
        self._pause_condition = threading.Condition()
        self.think_time = 2.0
        self.eat_time = 2.0
        self.pickup_delay = 0.0  # 拿起左叉子后的延迟（用于增加死锁概率）
        self.initial_delay = 0.0  # 初始延迟，用于错开哲学家启动时间
        self.time_randomness = 0.0  # 时间随机性系数 (0.0-1.0)
        self.daemon = True

    def set_state(self, state: PhilosopherState):
        """设置状态并通知"""
        self.state = state
        if self._state_callback:
            self._state_callback(self.philosopher_id, state)

    def _check_pause(self):
        """检查是否暂停"""
        with self._pause_condition:
            while self._paused and self._running:
                self._pause_condition.wait()

    def _get_randomized_time(self, base_time: float) -> float:
        """获取带随机波动的时间"""
        if self.time_randomness <= 0:
            return base_time
        # 在 base_time * (1 - randomness) 到 base_time * (1 + randomness) 之间随机
        min_time = base_time * (1 - self.time_randomness)
        max_time = base_time * (1 + self.time_randomness)
        return random.uniform(min_time, max_time)

    def run(self):
        """哲学家行为循环"""
        self._running = True

        # 初始延迟，错开哲学家启动时间
        if self.initial_delay > 0:
            self._interruptible_sleep(self.initial_delay)
            if not self._running:
                return

        while self._running:
            self._check_pause()
            if not self._running:
                break

            # 思考
            self.set_state(PhilosopherState.THINKING)
            self._interruptible_sleep(self._get_randomized_time(self.think_time))

            self._check_pause()
            if not self._running:
                break

            # 饥饿，尝试拿叉子
            self.set_state(PhilosopherState.HUNGRY)

            # 拿左叉子
            if not self.left_fork.P(self.name):
                # P操作被强制中断
                break
            self._check_pause()
            if not self._running:
                self.left_fork.V(self.name)
                break

            # 拿起左叉子后的延迟（增加死锁概率）
            if self.pickup_delay > 0:
                self._interruptible_sleep(self.pickup_delay)
                if not self._running:
                    self.left_fork.V(self.name)
                    break

            # 拿右叉子
            if not self.right_fork.P(self.name):
                # P操作被强制中断，释放左叉子
                self.left_fork.V(self.name)
                break
            self._check_pause()
            if not self._running:
                self.right_fork.V(self.name)
                self.left_fork.V(self.name)
                break

            # 进餐
            self.set_state(PhilosopherState.EATING)
            self._interruptible_sleep(self._get_randomized_time(self.eat_time))

            if not self._running:
                # 即使被中断，也要放下叉子
                self.right_fork.V(self.name)
                self.left_fork.V(self.name)
                break

            # 放下叉子
            self.right_fork.V(self.name)
            self.left_fork.V(self.name)

    def _interruptible_sleep(self, duration: float):
        """可中断的睡眠"""
        interval = 0.1  # 每0.1秒检查一次
        elapsed = 0
        while elapsed < duration and self._running and not self._paused:
            time.sleep(min(interval, duration - elapsed))
            elapsed += interval

    def stop(self):
        """停止哲学家"""
        self._running = False
        with self._pause_condition:
            self._paused = False
            self._pause_condition.notify_all()

    def pause(self):
        """暂停"""
        with self._pause_condition:
            self._paused = True

    def resume(self):
        """恢复"""
        with self._pause_condition:
            self._paused = False
            self._pause_condition.notify_all()


class DiningPhilosophers:
    """哲学家就餐问题管理器"""

    def __init__(self, num_philosophers: int = 5):
        self.num_philosophers = num_philosophers
        self.forks: List[Semaphore] = []
        self.philosophers: List[Philosopher] = []
        self._state_callback: Optional[Callable] = None
        self._log_callback: Optional[Callable] = None
        self._fork_state_callback: Optional[Callable] = None
        self._running = False
        self._paused = False  # 暂停标志
        self._use_deadlock_prevention = True

        self._init_resources()

    def _init_resources(self):
        """初始化资源"""
        # 创建叉子（信号量）
        self.forks = [Semaphore(1, f"叉子{i}") for i in range(self.num_philosophers)]

        # 设置日志回调
        for fork in self.forks:
            fork.set_log_callback(self._on_log)

    def set_state_callback(self, callback: Callable):
        """设置哲学家状态变化回调"""
        self._state_callback = callback

    def set_log_callback(self, callback: Callable):
        """设置日志回调"""
        self._log_callback = callback

    def set_fork_state_callback(self, callback: Callable):
        """设置叉子状态回调"""
        self._fork_state_callback = callback

    def _on_state_change(self, philosopher_id: int, state: PhilosopherState):
        """哲学家状态变化处理"""
        if self._state_callback:
            self._state_callback(philosopher_id, state)

    def _on_log(self, log: SemaphoreLog):
        """日志处理"""
        # 如果已停止，不输出日志
        if not self._running:
            return
        # 如果已暂停，也不输出日志
        if self._paused:
            return
        if self._log_callback:
            self._log_callback(log)
        # 更新叉子状态
        if self._fork_state_callback:
            fork_states = self.get_fork_states()
            self._fork_state_callback(fork_states)

    def set_deadlock_prevention(self, enabled: bool):
        """设置是否启用死锁预防"""
        self._use_deadlock_prevention = enabled

    def start(self):
        """启动模拟"""
        if self._running:
            return

        self._running = True
        self._paused = False
        self.philosophers = []

        for i in range(self.num_philosophers):
            if self._use_deadlock_prevention and i == self.num_philosophers - 1:
                # 最后一个哲学家先拿右叉子（打破循环等待）
                left_fork = self.forks[(i + 1) % self.num_philosophers]
                right_fork = self.forks[i]
            else:
                left_fork = self.forks[i]
                right_fork = self.forks[(i + 1) % self.num_philosophers]

            philosopher = Philosopher(
                philosopher_id=i,
                left_fork=left_fork,
                right_fork=right_fork,
                state_callback=self._on_state_change
            )

            # 如果关闭死锁预防，添加少量随机性
            # 平衡点：不会立即死锁，但在10-30秒内大概率死锁
            if not self._use_deadlock_prevention:
                philosopher.pickup_delay = 0.08
                philosopher.initial_delay = random.uniform(0, 0.07)  # 稍微错开启动
                philosopher.time_randomness = 0.03  # 5%的时间随机波动

            self.philosophers.append(philosopher)
            philosopher.start()

    def stop(self):
        """停止模拟"""
        self._running = False

        # 先停止所有哲学家
        for philosopher in self.philosophers:
            philosopher.stop()

        # 强制唤醒所有在信号量上等待的线程
        for fork in self.forks:
            fork.force_wakeup_all()

        # 等待线程结束
        for philosopher in self.philosophers:
            if philosopher.is_alive():
                philosopher.join(timeout=1.0)

        # 重置叉子
        for fork in self.forks:
            fork.reset()

        self.philosophers = []
        self._paused = False

    def pause(self):
        """暂停所有哲学家"""
        self._paused = True
        for philosopher in self.philosophers:
            philosopher.pause()

    def resume(self):
        """恢复所有哲学家"""
        self._paused = False
        for philosopher in self.philosophers:
            philosopher.resume()

    def set_speed(self, think_time: float, eat_time: float):
        """设置思考和进餐时间"""
        for philosopher in self.philosophers:
            philosopher.think_time = think_time
            philosopher.eat_time = eat_time

    def get_states(self) -> List[PhilosopherState]:
        """获取所有哲学家的状态"""
        return [p.state for p in self.philosophers]

    def get_fork_states(self) -> List[dict]:
        """获取所有叉子的状态"""
        states = []
        for i, fork in enumerate(self.forks):
            states.append({
                "id": i,
                "value": fork.value,  # 实际信号量值
                "available": fork.value > 0,
                "waiting": fork.waiting_queue.copy()
            })
        return states

    def check_deadlock(self) -> bool:
        """检测是否发生死锁"""
        if not self._running or len(self.philosophers) == 0:
            return False
        # 死锁条件：所有哲学家都处于饥饿状态（等待叉子）
        all_hungry = all(p.state == PhilosopherState.HUNGRY for p in self.philosophers)
        # 且所有叉子都被占用
        all_forks_taken = all(fork.value <= 0 for fork in self.forks)
        return all_hungry and all_forks_taken

    def get_semaphore_values(self) -> List[int]:
        """获取所有信号量的值"""
        return [fork.value for fork in self.forks]
