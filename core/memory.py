"""
内存管理模块
实现动态内存分配算法和页面置换算法
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from collections import OrderedDict
import copy


class AllocationAlgorithm(Enum):
    """内存分配算法"""
    FIRST_FIT = "首次适应"
    BEST_FIT = "最佳适应"
    WORST_FIT = "最坏适应"
    NEXT_FIT = "循环首次适应"


class PageReplacementAlgorithm(Enum):
    """页面置换算法"""
    FIFO = "先进先出"
    LRU = "最近最少使用"
    OPT = "最佳置换"
    CLOCK = "时钟算法"


@dataclass
class MemoryBlock:
    """内存块"""
    start: int          # 起始地址
    size: int           # 大小
    is_free: bool       # 是否空闲
    process_name: str = ""  # 占用进程名

    @property
    def end(self) -> int:
        """结束地址"""
        return self.start + self.size


@dataclass
class MemoryRequest:
    """内存请求"""
    process_name: str   # 进程名
    size: int          # 请求大小


@dataclass
class Page:
    """页面"""
    page_id: int       # 页号
    frame_id: int = -1  # 物理帧号，-1表示不在内存
    in_memory: bool = False
    reference_bit: int = 0  # 引用位（用于时钟算法）


@dataclass
class PageFrame:
    """物理页框"""
    frame_id: int      # 帧号
    page_id: int = -1  # 存放的页号，-1表示空
    is_free: bool = True


class MemoryAllocator:
    """动态内存分配器"""

    def __init__(self, total_size: int = 1024):
        self.total_size = total_size
        self.blocks: List[MemoryBlock] = []
        self.allocation_history: List[Tuple[str, str, bool]] = []  # (操作, 进程, 成功)
        self.next_fit_pointer = 0  # 循环首次适应的指针
        self._init_memory()

    def _init_memory(self):
        """初始化内存为一个大空闲块"""
        self.blocks = [MemoryBlock(0, self.total_size, True)]
        self.allocation_history = []
        self.next_fit_pointer = 0

    def reset(self):
        """重置内存"""
        self._init_memory()

    def allocate(self, request: MemoryRequest, algorithm: AllocationAlgorithm) -> bool:
        """分配内存"""
        if algorithm == AllocationAlgorithm.FIRST_FIT:
            return self._first_fit(request)
        elif algorithm == AllocationAlgorithm.BEST_FIT:
            return self._best_fit(request)
        elif algorithm == AllocationAlgorithm.WORST_FIT:
            return self._worst_fit(request)
        elif algorithm == AllocationAlgorithm.NEXT_FIT:
            return self._next_fit(request)
        return False

    def _first_fit(self, request: MemoryRequest) -> bool:
        """首次适应算法"""
        for i, block in enumerate(self.blocks):
            if block.is_free and block.size >= request.size:
                self._split_block(i, request)
                self.allocation_history.append(("分配", request.process_name, True))
                return True
        self.allocation_history.append(("分配", request.process_name, False))
        return False

    def _best_fit(self, request: MemoryRequest) -> bool:
        """最佳适应算法：找最小的足够大的空闲块"""
        best_idx = -1
        best_size = float('inf')

        for i, block in enumerate(self.blocks):
            if block.is_free and block.size >= request.size:
                if block.size < best_size:
                    best_size = block.size
                    best_idx = i

        if best_idx >= 0:
            self._split_block(best_idx, request)
            self.allocation_history.append(("分配", request.process_name, True))
            return True
        self.allocation_history.append(("分配", request.process_name, False))
        return False

    def _worst_fit(self, request: MemoryRequest) -> bool:
        """最坏适应算法：找最大的空闲块"""
        worst_idx = -1
        worst_size = -1

        for i, block in enumerate(self.blocks):
            if block.is_free and block.size >= request.size:
                if block.size > worst_size:
                    worst_size = block.size
                    worst_idx = i

        if worst_idx >= 0:
            self._split_block(worst_idx, request)
            self.allocation_history.append(("分配", request.process_name, True))
            return True
        self.allocation_history.append(("分配", request.process_name, False))
        return False

    def _next_fit(self, request: MemoryRequest) -> bool:
        """循环首次适应算法"""
        n = len(self.blocks)
        for offset in range(n):
            i = (self.next_fit_pointer + offset) % n
            block = self.blocks[i]
            if block.is_free and block.size >= request.size:
                self._split_block(i, request)
                self.next_fit_pointer = i
                self.allocation_history.append(("分配", request.process_name, True))
                return True
        self.allocation_history.append(("分配", request.process_name, False))
        return False

    def _split_block(self, index: int, request: MemoryRequest):
        """分割内存块"""
        block = self.blocks[index]
        remaining = block.size - request.size

        # 修改当前块为已分配
        block.is_free = False
        block.size = request.size
        block.process_name = request.process_name

        # 如果有剩余空间，创建新的空闲块
        if remaining > 0:
            new_block = MemoryBlock(
                block.start + request.size,
                remaining,
                True
            )
            self.blocks.insert(index + 1, new_block)

    def deallocate(self, process_name: str) -> bool:
        """释放进程占用的内存"""
        found = False
        for block in self.blocks:
            if block.process_name == process_name:
                block.is_free = True
                block.process_name = ""
                found = True

        if found:
            self._merge_free_blocks()
            self.allocation_history.append(("释放", process_name, True))
        return found

    def _merge_free_blocks(self):
        """合并相邻的空闲块"""
        i = 0
        while i < len(self.blocks) - 1:
            if self.blocks[i].is_free and self.blocks[i + 1].is_free:
                # 合并两个块
                self.blocks[i].size += self.blocks[i + 1].size
                del self.blocks[i + 1]
            else:
                i += 1

    def get_fragmentation(self) -> Tuple[int, int]:
        """获取碎片信息"""
        external_frag = 0  # 外部碎片
        free_blocks = 0

        for block in self.blocks:
            if block.is_free:
                external_frag += block.size
                free_blocks += 1

        return external_frag, free_blocks

    def get_usage(self) -> float:
        """获取内存使用率"""
        used = sum(b.size for b in self.blocks if not b.is_free)
        return used / self.total_size * 100


class PageReplacer:
    """页面置换器"""

    def __init__(self, frame_count: int = 4):
        self.frame_count = frame_count
        self.frames: List[PageFrame] = []
        self.page_faults = 0
        self.page_hits = 0
        self.access_history: List[Tuple[int, bool, int]] = []  # (页号, 是否命中, 替换页)
        self.fifo_queue: List[int] = []  # FIFO队列
        self.lru_order: List[int] = []   # LRU访问顺序
        self.clock_pointer = 0           # 时钟指针
        self.reference_bits: dict = {}   # 引用位
        self._init_frames()

    def _init_frames(self):
        """初始化页框"""
        self.frames = [PageFrame(i) for i in range(self.frame_count)]
        self.page_faults = 0
        self.page_hits = 0
        self.access_history = []
        self.fifo_queue = []
        self.lru_order = []
        self.clock_pointer = 0
        self.reference_bits = {}

    def reset(self):
        """重置"""
        self._init_frames()

    def access_page(self, page_id: int, algorithm: PageReplacementAlgorithm,
                    future_access: List[int] = None) -> Tuple[bool, int]:
        """
        访问页面
        返回: (是否命中, 被替换的页号，-1表示无替换)
        """
        # 检查是否在内存中
        for frame in self.frames:
            if frame.page_id == page_id:
                self.page_hits += 1
                self._update_access(page_id, algorithm)
                self.access_history.append((page_id, True, -1))
                return True, -1

        # 页面缺失
        self.page_faults += 1
        replaced_page = -1

        # 查找空闲帧
        for frame in self.frames:
            if frame.is_free:
                frame.page_id = page_id
                frame.is_free = False
                self._add_page(page_id, algorithm)
                self.access_history.append((page_id, False, -1))
                return False, -1

        # 需要置换
        if algorithm == PageReplacementAlgorithm.FIFO:
            replaced_page = self._fifo_replace(page_id)
        elif algorithm == PageReplacementAlgorithm.LRU:
            replaced_page = self._lru_replace(page_id)
        elif algorithm == PageReplacementAlgorithm.OPT:
            replaced_page = self._opt_replace(page_id, future_access or [])
        elif algorithm == PageReplacementAlgorithm.CLOCK:
            replaced_page = self._clock_replace(page_id)

        self.access_history.append((page_id, False, replaced_page))
        return False, replaced_page

    def _add_page(self, page_id: int, algorithm: PageReplacementAlgorithm):
        """添加新页面到队列"""
        if algorithm == PageReplacementAlgorithm.FIFO:
            self.fifo_queue.append(page_id)
        elif algorithm == PageReplacementAlgorithm.LRU:
            self.lru_order.append(page_id)
        elif algorithm == PageReplacementAlgorithm.CLOCK:
            self.reference_bits[page_id] = 1

    def _update_access(self, page_id: int, algorithm: PageReplacementAlgorithm):
        """更新页面访问信息"""
        if algorithm == PageReplacementAlgorithm.LRU:
            if page_id in self.lru_order:
                self.lru_order.remove(page_id)
            self.lru_order.append(page_id)
        elif algorithm == PageReplacementAlgorithm.CLOCK:
            self.reference_bits[page_id] = 1

    def _fifo_replace(self, new_page: int) -> int:
        """FIFO置换"""
        old_page = self.fifo_queue.pop(0)

        # 更新帧
        for frame in self.frames:
            if frame.page_id == old_page:
                frame.page_id = new_page
                break

        self.fifo_queue.append(new_page)
        return old_page

    def _lru_replace(self, new_page: int) -> int:
        """LRU置换"""
        old_page = self.lru_order.pop(0)

        # 更新帧
        for frame in self.frames:
            if frame.page_id == old_page:
                frame.page_id = new_page
                break

        self.lru_order.append(new_page)
        return old_page

    def _opt_replace(self, new_page: int, future_access: List[int]) -> int:
        """OPT最佳置换"""
        # 找出内存中最长时间不会被访问的页面
        in_memory = [f.page_id for f in self.frames if not f.is_free]

        max_distance = -1
        victim = in_memory[0]

        for page in in_memory:
            if page in future_access:
                distance = future_access.index(page)
            else:
                distance = float('inf')

            if distance > max_distance:
                max_distance = distance
                victim = page

        # 更新帧
        for frame in self.frames:
            if frame.page_id == victim:
                frame.page_id = new_page
                break

        return victim

    def _clock_replace(self, new_page: int) -> int:
        """时钟算法置换"""
        while True:
            frame = self.frames[self.clock_pointer]
            page = frame.page_id

            if self.reference_bits.get(page, 0) == 0:
                # 找到victim
                old_page = page
                frame.page_id = new_page
                self.reference_bits[new_page] = 1
                if old_page in self.reference_bits:
                    del self.reference_bits[old_page]
                self.clock_pointer = (self.clock_pointer + 1) % self.frame_count
                return old_page
            else:
                # 给第二次机会
                self.reference_bits[page] = 0
                self.clock_pointer = (self.clock_pointer + 1) % self.frame_count

    def get_hit_rate(self) -> float:
        """获取命中率"""
        total = self.page_faults + self.page_hits
        if total == 0:
            return 0.0
        return self.page_hits / total * 100

    def get_frame_state(self) -> List[int]:
        """获取当前帧状态"""
        return [f.page_id for f in self.frames]

    def run_sequence(self, page_sequence: List[int],
                     algorithm: PageReplacementAlgorithm) -> List[dict]:
        """
        运行一个页面访问序列
        返回每一步的状态
        """
        self.reset()
        steps = []

        for i, page in enumerate(page_sequence):
            future = page_sequence[i+1:] if algorithm == PageReplacementAlgorithm.OPT else None
            hit, replaced = self.access_page(page, algorithm, future)

            steps.append({
                'page': page,
                'hit': hit,
                'replaced': replaced,
                'frame_state': self.get_frame_state().copy(),
                'page_faults': self.page_faults,
                'page_hits': self.page_hits
            })

        return steps
