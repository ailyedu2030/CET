"""布隆过滤器实现 - 用于题目去重，误判率<0.1%."""

import hashlib
import math
from typing import Any


class BloomFilter:
    """
    布隆过滤器实现 - 需求23验收标准.

    用于智能去重避免重复题目生成，误判率<0.1%
    """

    def __init__(self, capacity: int = 100000, error_rate: float = 0.001) -> None:
        """
        初始化布隆过滤器.

        Args:
            capacity: 预期元素数量
            error_rate: 误判率（默认0.1%）
        """
        self.capacity = capacity
        self.error_rate = error_rate

        # 计算最优参数
        self.bit_array_size = self._calculate_bit_array_size(capacity, error_rate)
        self.hash_count = self._calculate_hash_count(self.bit_array_size, capacity)

        # 初始化位数组
        self.bit_array = [False] * self.bit_array_size
        self.element_count = 0

    def _calculate_bit_array_size(self, capacity: int, error_rate: float) -> int:
        """计算位数组大小."""
        # m = -(n * ln(p)) / (ln(2)^2)
        # 其中 n=capacity, p=error_rate
        size = -(capacity * math.log(error_rate)) / (math.log(2) ** 2)
        return int(math.ceil(size))

    def _calculate_hash_count(self, bit_array_size: int, capacity: int) -> int:
        """计算哈希函数数量."""
        # k = (m/n) * ln(2)
        # 其中 m=bit_array_size, n=capacity
        count = (bit_array_size / capacity) * math.log(2)
        return int(math.ceil(count))

    def _hash_functions(self, item: str) -> list[int]:
        """生成多个哈希值."""
        hashes = []

        # 使用MD5和SHA1生成不同的哈希值
        md5_hash = hashlib.md5(item.encode("utf-8")).hexdigest()
        sha1_hash = hashlib.sha1(item.encode("utf-8")).hexdigest()

        # 生成所需数量的哈希值
        for i in range(self.hash_count):
            if i % 2 == 0:
                # 使用MD5的不同部分
                hash_value = int(md5_hash[i * 4 : (i + 1) * 4], 16)
            else:
                # 使用SHA1的不同部分
                hash_value = int(sha1_hash[i * 4 : (i + 1) * 4], 16)

            # 确保哈希值在位数组范围内
            hashes.append(hash_value % self.bit_array_size)

        return hashes

    def add(self, item: str) -> None:
        """添加元素到布隆过滤器."""
        hashes = self._hash_functions(item)

        for hash_value in hashes:
            self.bit_array[hash_value] = True

        self.element_count += 1

    def might_contain(self, item: str) -> bool:
        """
        检查元素是否可能存在.

        Returns:
            True: 元素可能存在（可能误判）
            False: 元素肯定不存在
        """
        hashes = self._hash_functions(item)

        for hash_value in hashes:
            if not self.bit_array[hash_value]:
                return False

        return True

    def get_false_positive_probability(self) -> float:
        """计算当前的误判率."""
        if self.element_count == 0:
            return 0.0

        # 计算实际误判率
        # p = (1 - e^(-k*n/m))^k
        # 其中 k=hash_count, n=element_count, m=bit_array_size
        exponent = -self.hash_count * self.element_count / self.bit_array_size
        probability = (1 - math.exp(exponent)) ** self.hash_count

        return float(probability)

    def get_statistics(self) -> dict[str, Any]:
        """获取布隆过滤器统计信息."""
        return {
            "capacity": self.capacity,
            "element_count": self.element_count,
            "bit_array_size": self.bit_array_size,
            "hash_count": self.hash_count,
            "target_error_rate": self.error_rate,
            "current_error_rate": self.get_false_positive_probability(),
            "memory_usage_bits": self.bit_array_size,
            "memory_usage_kb": self.bit_array_size / 8 / 1024,
            "fill_ratio": sum(self.bit_array) / self.bit_array_size,
        }

    def clear(self) -> None:
        """清空布隆过滤器."""
        self.bit_array = [False] * self.bit_array_size
        self.element_count = 0

    def is_full(self) -> bool:
        """检查布隆过滤器是否已满."""
        # 当元素数量接近容量时，误判率会显著增加
        return self.element_count >= self.capacity * 0.8

    def export_state(self) -> dict[str, Any]:
        """导出布隆过滤器状态（用于持久化）."""
        return {
            "capacity": self.capacity,
            "error_rate": self.error_rate,
            "bit_array_size": self.bit_array_size,
            "hash_count": self.hash_count,
            "element_count": self.element_count,
            "bit_array": self.bit_array,
        }

    @classmethod
    def from_state(cls, state: dict[str, Any]) -> "BloomFilter":
        """从状态恢复布隆过滤器."""
        bloom_filter = cls(state["capacity"], state["error_rate"])
        bloom_filter.bit_array_size = state["bit_array_size"]
        bloom_filter.hash_count = state["hash_count"]
        bloom_filter.element_count = state["element_count"]
        bloom_filter.bit_array = state["bit_array"]
        return bloom_filter


class QuestionBloomFilter:
    """题目专用布隆过滤器 - 针对题目去重优化."""

    def __init__(self, capacity: int = 100000) -> None:
        """初始化题目布隆过滤器."""
        # 设置更严格的误判率要求
        self.bloom_filter = BloomFilter(capacity=capacity, error_rate=0.0005)  # 0.05%

    def generate_question_fingerprint(self, question_data: dict[str, Any]) -> str:
        """生成题目指纹."""
        # 提取关键信息生成唯一指纹
        key_content = {
            "title": question_data.get("title", "").strip().lower(),
            "content": self._normalize_content(question_data.get("content", {})),
            "knowledge_points": sorted(question_data.get("knowledge_points", [])),
            "question_type": question_data.get("question_type", ""),
        }

        # 生成标准化的字符串表示
        fingerprint_str = str(key_content)
        return hashlib.sha256(fingerprint_str.encode("utf-8")).hexdigest()

    def _normalize_content(self, content: dict[str, Any] | Any) -> str:
        """标准化题目内容."""
        if not isinstance(content, dict):
            return str(content).strip().lower()

        # 提取主要文本内容
        text_parts = []

        if "text" in content:
            text_parts.append(content["text"].strip().lower())

        if "options" in content and isinstance(content["options"], list):
            # 选择题选项也参与指纹生成
            options_text = " ".join(opt.strip().lower() for opt in content["options"])
            text_parts.append(options_text)

        return " ".join(text_parts)

    def add_question(self, question_data: dict[str, Any]) -> str:
        """添加题目到过滤器."""
        fingerprint = self.generate_question_fingerprint(question_data)
        self.bloom_filter.add(fingerprint)
        return str(fingerprint)

    def is_duplicate(self, question_data: dict[str, Any]) -> bool:
        """检查题目是否重复."""
        fingerprint = self.generate_question_fingerprint(question_data)
        return bool(self.bloom_filter.might_contain(fingerprint))

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息."""
        stats = self.bloom_filter.get_statistics()
        stats["question_count"] = self.bloom_filter.element_count
        return stats

    def clear(self) -> None:
        """清空过滤器."""
        self.bloom_filter.clear()
