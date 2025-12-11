"""
进程间通信（IPC）机制实现
实现生产者-消费者模型
"""
import threading
import time
import random
from typing import List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum


class IPCEventType(Enum):
    """IPC事件类型"""
    PRODUCE = "生产"
    CONSUME = "消费"
    WAIT_FULL = "等待(缓冲区满)"
    WAIT_EMPTY = "等待(缓冲区空)"
    WAKE_UP = "唤醒"


@dataclass
class IPCEvent:
    """IPC事件"""
    timestamp: float
    event_type: IPCEventType
    actor_name: str
    item: Any = None
    buffer_size: int = 0


@dataclass
class BufferItem:
    """缓冲区项"""
    id: int
    value: Any
    producer_name: str
    produce_time: float


class SharedBuffer:
    """共享缓冲区"""

    def __init__(self, capacity: int = 10):
        self.capacity = capacity
        self.buffer: List[BufferItem] = []
        self._lock = threading.Lock()
        self._not_full = threading.Condition(self._lock)
        self._not_empty = threading.Condition(self._lock)
        self._item_id = 0
        self._event_callback: Optional[Callable] = None
        self._buffer_change_callback: Optional[Callable] = None

    def set_event_callback(self, callback: Callable):
        """设置事件回调"""
        self._event_callback = callback

    def set_buffer_change_callback(self, callback: Callable):
        """设置缓冲区变化回调"""
        self._buffer_change_callback = callback

    def _notify_event(self, event_type: IPCEventType, actor_name: str, item: Any = None):
        """通知事件"""
        if self._event_callback:
            event = IPCEvent(
                timestamp=time.time(),
                event_type=event_type,
                actor_name=actor_name,
                item=item,
                buffer_size=len(self.buffer)
            )
            self._event_callback(event)

    def _notify_buffer_change(self):
        """通知缓冲区变化"""
        if self._buffer_change_callback:
            self._buffer_change_callback(self.buffer.copy(), self.capacity)

    def produce(self, value: Any, producer_name: str) -> BufferItem:
        """生产数据"""
        with self._not_full:
            # 等待缓冲区不满
            while len(self.buffer) >= self.capacity:
                self._notify_event(IPCEventType.WAIT_FULL, producer_name)
                self._not_full.wait()
                self._notify_event(IPCEventType.WAKE_UP, producer_name)

            # 生产
            self._item_id += 1
            item = BufferItem(
                id=self._item_id,
                value=value,
                producer_name=producer_name,
                produce_time=time.time()
            )
            self.buffer.append(item)

            self._notify_event(IPCEventType.PRODUCE, producer_name, item)
            self._notify_buffer_change()

            # 唤醒消费者
            self._not_empty.notify()

            return item

    def consume(self, consumer_name: str) -> Optional[BufferItem]:
        """消费数据"""
        with self._not_empty:
            # 等待缓冲区不空
            while len(self.buffer) == 0:
                self._notify_event(IPCEventType.WAIT_EMPTY, consumer_name)
                self._not_empty.wait()
                self._notify_event(IPCEventType.WAKE_UP, consumer_name)

            # 消费（FIFO）
            item = self.buffer.pop(0)

            self._notify_event(IPCEventType.CONSUME, consumer_name, item)
            self._notify_buffer_change()

            # 唤醒生产者
            self._not_full.notify()

            return item

    def get_buffer_state(self) -> List[BufferItem]:
        """获取缓冲区状态"""
        with self._lock:
            return self.buffer.copy()

    def get_size(self) -> int:
        """获取当前大小"""
        with self._lock:
            return len(self.buffer)

    def is_full(self) -> bool:
        """是否满"""
        with self._lock:
            return len(self.buffer) >= self.capacity

    def is_empty(self) -> bool:
        """是否空"""
        with self._lock:
            return len(self.buffer) == 0

    def clear(self):
        """清空缓冲区"""
        with self._lock:
            self.buffer.clear()
            self._item_id = 0
            self._notify_buffer_change()


class Producer(threading.Thread):
    """生产者线程"""

    def __init__(self, producer_id: int, buffer: SharedBuffer,
                 produce_rate: float = 1.0, name: str = None):
        super().__init__()
        self.producer_id = producer_id
        self.producer_name = name or f"生产者{producer_id}"
        self.buffer = buffer
        self.produce_rate = produce_rate  # 生产间隔（秒）
        self._running = False
        self._paused = False
        self._pause_condition = threading.Condition()
        self._produce_count = 0
        self.daemon = True

    def run(self):
        """生产者线程主循环"""
        self._running = True
        while self._running:
            # 检查暂停
            with self._pause_condition:
                while self._paused and self._running:
                    self._pause_condition.wait()

            if not self._running:
                break

            # 生产数据
            self._produce_count += 1
            value = f"数据{self._produce_count}"
            self.buffer.produce(value, self.producer_name)

            # 按照生产速率等待
            time.sleep(self.produce_rate)

    def stop(self):
        """停止生产者"""
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

    def set_rate(self, rate: float):
        """设置生产速率"""
        self.produce_rate = rate


class Consumer(threading.Thread):
    """消费者线程"""

    def __init__(self, consumer_id: int, buffer: SharedBuffer,
                 consume_rate: float = 1.5, name: str = None):
        super().__init__()
        self.consumer_id = consumer_id
        self.consumer_name = name or f"消费者{consumer_id}"
        self.buffer = buffer
        self.consume_rate = consume_rate  # 消费间隔（秒）
        self._running = False
        self._paused = False
        self._pause_condition = threading.Condition()
        self._consume_count = 0
        self.daemon = True

    def run(self):
        """消费者线程主循环"""
        self._running = True
        while self._running:
            # 检查暂停
            with self._pause_condition:
                while self._paused and self._running:
                    self._pause_condition.wait()

            if not self._running:
                break

            # 消费数据
            item = self.buffer.consume(self.consumer_name)
            if item:
                self._consume_count += 1

            # 按照消费速率等待
            time.sleep(self.consume_rate)

    def stop(self):
        """停止消费者"""
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

    def set_rate(self, rate: float):
        """设置消费速率"""
        self.consume_rate = rate


class IPCManager:
    """IPC管理器"""

    def __init__(self, buffer_capacity: int = 10):
        self.buffer = SharedBuffer(buffer_capacity)
        self.producers: List[Producer] = []
        self.consumers: List[Consumer] = []
        self._running = False
        self._next_producer_id = 1
        self._next_consumer_id = 1

    def set_event_callback(self, callback: Callable):
        """设置事件回调"""
        self.buffer.set_event_callback(callback)

    def set_buffer_change_callback(self, callback: Callable):
        """设置缓冲区变化回调"""
        self.buffer.set_buffer_change_callback(callback)

    def add_producer(self, produce_rate: float = 1.0) -> Producer:
        """添加生产者"""
        producer = Producer(
            producer_id=self._next_producer_id,
            buffer=self.buffer,
            produce_rate=produce_rate
        )
        self.producers.append(producer)
        self._next_producer_id += 1

        if self._running:
            producer.start()

        return producer

    def add_consumer(self, consume_rate: float = 1.5) -> Consumer:
        """添加消费者"""
        consumer = Consumer(
            consumer_id=self._next_consumer_id,
            buffer=self.buffer,
            consume_rate=consume_rate
        )
        self.consumers.append(consumer)
        self._next_consumer_id += 1

        if self._running:
            consumer.start()

        return consumer

    def remove_producer(self, producer_id: int) -> bool:
        """移除生产者"""
        for i, producer in enumerate(self.producers):
            if producer.producer_id == producer_id:
                producer.stop()
                # 只对已启动的线程调用join
                if producer.is_alive():
                    producer.join(timeout=1.0)
                self.producers.pop(i)
                return True
        return False

    def remove_consumer(self, consumer_id: int) -> bool:
        """移除消费者"""
        for i, consumer in enumerate(self.consumers):
            if consumer.consumer_id == consumer_id:
                consumer.stop()
                # 只对已启动的线程调用join
                if consumer.is_alive():
                    consumer.join(timeout=1.0)
                self.consumers.pop(i)
                return True
        return False

    def start(self):
        """启动所有线程"""
        if self._running:
            return

        self._running = True
        for producer in self.producers:
            if not producer.is_alive():
                producer.start()
        for consumer in self.consumers:
            if not consumer.is_alive():
                consumer.start()

    def stop(self):
        """停止所有线程"""
        self._running = False

        for producer in self.producers:
            producer.stop()
        for consumer in self.consumers:
            consumer.stop()

        # 唤醒可能在等待缓冲区的线程
        with self.buffer._lock:
            self.buffer._not_full.notify_all()
            self.buffer._not_empty.notify_all()

        # 等待线程结束（只对已启动的线程调用join）
        for producer in self.producers:
            if producer.is_alive():
                producer.join(timeout=1.0)
        for consumer in self.consumers:
            if consumer.is_alive():
                consumer.join(timeout=1.0)

    def pause(self):
        """暂停所有线程"""
        for producer in self.producers:
            producer.pause()
        for consumer in self.consumers:
            consumer.pause()

    def resume(self):
        """恢复所有线程"""
        for producer in self.producers:
            producer.resume()
        for consumer in self.consumers:
            consumer.resume()

    def reset(self):
        """重置"""
        self.stop()
        self.buffer.clear()
        self.producers.clear()
        self.consumers.clear()
        self._next_producer_id = 1
        self._next_consumer_id = 1

    def get_status(self) -> dict:
        """获取状态"""
        return {
            "buffer_size": self.buffer.get_size(),
            "buffer_capacity": self.buffer.capacity,
            "producer_count": len(self.producers),
            "consumer_count": len(self.consumers),
            "running": self._running
        }
