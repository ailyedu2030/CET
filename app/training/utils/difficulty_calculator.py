"""难度计算器 - 智能题目难度评估和调整算法."""

from typing import Any

from app.shared.models.enums import DifficultyLevel, QuestionType, TrainingType


class DifficultyCalculator:
    """智能难度计算器 - 基于多维度数据计算和调整题目难度."""

    def __init__(self) -> None:
        # 难度权重配置
        self.difficulty_weights = {
            "accuracy_rate": 0.4,  # 准确率权重
            "time_spent": 0.2,  # 用时权重
            "attempt_count": 0.15,  # 尝试次数权重
            "complexity": 0.15,  # 题目复杂度权重
            "student_level": 0.1,  # 学生水平权重
        }

        # 难度等级映射
        self.difficulty_scores = {
            DifficultyLevel.BEGINNER: 0.5,
            DifficultyLevel.ELEMENTARY: 1.0,
            DifficultyLevel.INTERMEDIATE: 2.0,
            DifficultyLevel.UPPER_INTERMEDIATE: 3.0,
            DifficultyLevel.ADVANCED: 4.0,
        }

        # 题目类型复杂度系数
        self.question_complexity = {
            QuestionType.MULTIPLE_CHOICE: 1.0,
            QuestionType.TRUE_FALSE: 0.8,
            QuestionType.FILL_BLANK: 1.2,
            QuestionType.SHORT_ANSWER: 1.5,
            QuestionType.ESSAY: 2.0,
            QuestionType.LISTENING_COMPREHENSION: 1.3,
            QuestionType.READING_COMPREHENSION: 1.4,
            QuestionType.TRANSLATION_EN_TO_CN: 1.8,
            QuestionType.TRANSLATION_CN_TO_EN: 1.9,
        }

    def calculate_question_difficulty(
        self,
        question_type: QuestionType,
        content_complexity: float,
        historical_data: dict[str, Any] | None = None,
    ) -> float:
        """
        计算题目的绝对难度分数.

        Args:
            question_type: 题目类型
            content_complexity: 内容复杂度 (0.0-1.0)
            historical_data: 历史统计数据

        Returns:
            难度分数 (0.0-5.0)
        """
        # 基础难度（基于题目类型）
        base_difficulty = self.question_complexity.get(question_type, 1.0)

        # 内容复杂度调整
        content_factor = 1.0 + (content_complexity * 0.5)

        # 历史数据调整
        historical_factor = 1.0
        if historical_data:
            avg_accuracy = historical_data.get("average_accuracy", 0.7)
            avg_time = historical_data.get("average_time_seconds", 60)
            attempt_count = historical_data.get("total_attempts", 0)

            # 准确率越低，难度越高
            accuracy_factor = 2.0 - avg_accuracy

            # 用时越长，难度越高（标准化到60秒）
            time_factor = min(avg_time / 60.0, 2.0)

            # 尝试次数越多，说明题目越难
            attempt_factor = min(1.0 + (attempt_count / 100.0), 1.5)

            historical_factor = (accuracy_factor + time_factor + attempt_factor) / 3.0

        # 计算最终难度
        final_difficulty = base_difficulty * content_factor * historical_factor

        # 限制在合理范围内
        return max(0.5, min(5.0, final_difficulty))

    def suggest_difficulty_level(self, difficulty_score: float) -> DifficultyLevel:
        """
        根据难度分数建议难度等级.

        Args:
            difficulty_score: 难度分数 (0.0-5.0)

        Returns:
            建议的难度等级
        """
        if difficulty_score <= 1.5:
            return DifficultyLevel.ELEMENTARY
        elif difficulty_score <= 2.5:
            return DifficultyLevel.INTERMEDIATE
        elif difficulty_score <= 3.5:
            return DifficultyLevel.ADVANCED
        else:
            return DifficultyLevel.ADVANCED

    def calculate_adaptive_difficulty(
        self,
        student_performance: dict[str, Any],
        current_difficulty: DifficultyLevel,
        training_type: TrainingType,
    ) -> DifficultyLevel:
        """
        基于学生表现计算自适应难度调整.

        Args:
            student_performance: 学生表现数据
            current_difficulty: 当前难度等级
            training_type: 训练类型

        Returns:
            调整后的难度等级
        """
        # 获取表现指标
        accuracy_rate = student_performance.get("accuracy_rate", 0.0)
        avg_time_ratio = student_performance.get("avg_time_ratio", 1.0)  # 相对于标准时间的比例
        consecutive_correct = student_performance.get("consecutive_correct", 0)
        consecutive_wrong = student_performance.get("consecutive_wrong", 0)

        # 计算调整分数
        adjustment_score = 0.0

        # 准确率调整
        if accuracy_rate >= 0.9:
            adjustment_score += 0.5  # 准确率很高，增加难度
        elif accuracy_rate >= 0.8:
            adjustment_score += 0.2  # 准确率较高，略微增加难度
        elif accuracy_rate <= 0.5:
            adjustment_score -= 0.5  # 准确率较低，降低难度
        elif accuracy_rate <= 0.6:
            adjustment_score -= 0.3  # 准确率偏低，适当降低难度

        # 用时调整
        if avg_time_ratio <= 0.6:
            adjustment_score += 0.3  # 用时很短，增加难度
        elif avg_time_ratio >= 1.5:
            adjustment_score -= 0.3  # 用时很长，降低难度

        # 连续正确/错误调整
        if consecutive_correct >= 5:
            adjustment_score += 0.4  # 连续正确多题，增加难度
        elif consecutive_wrong >= 3:
            adjustment_score -= 0.4  # 连续错误多题，降低难度

        # 训练类型特殊调整
        type_factor = self._get_training_type_factor(training_type)
        adjustment_score *= type_factor

        # 应用调整
        current_score = self.difficulty_scores[current_difficulty]
        new_score = current_score + adjustment_score

        # 转换回难度等级
        return self._score_to_difficulty_level(new_score)

    def calculate_content_complexity(
        self,
        content: dict[str, Any],
        question_type: QuestionType,
    ) -> float:
        """
        计算题目内容的复杂度.

        Args:
            content: 题目内容
            question_type: 题目类型

        Returns:
            内容复杂度 (0.0-1.0)
        """
        complexity_score = 0.0

        # 基于题目类型的复杂度分析
        if question_type in [QuestionType.MULTIPLE_CHOICE, QuestionType.TRUE_FALSE]:
            complexity_score = self._analyze_choice_complexity(content)
        elif question_type == QuestionType.FILL_BLANK:
            complexity_score = self._analyze_fill_blank_complexity(content)
        elif question_type in [QuestionType.SHORT_ANSWER, QuestionType.ESSAY]:
            complexity_score = self._analyze_text_complexity(content)
        elif question_type == QuestionType.LISTENING_COMPREHENSION:
            complexity_score = self._analyze_listening_complexity(content)
        elif question_type == QuestionType.READING_COMPREHENSION:
            complexity_score = self._analyze_reading_complexity(content)
        elif question_type in [
            QuestionType.TRANSLATION_EN_TO_CN,
            QuestionType.TRANSLATION_CN_TO_EN,
        ]:
            complexity_score = self._analyze_translation_complexity(content)

        return max(0.0, min(1.0, complexity_score))

    def estimate_completion_time(
        self,
        question_type: QuestionType,
        difficulty_level: DifficultyLevel,
        content_length: int,
        student_level: float = 0.5,
    ) -> int:
        """
        估算题目完成时间（秒）.

        Args:
            question_type: 题目类型
            difficulty_level: 难度等级
            content_length: 内容长度
            student_level: 学生水平 (0.0-1.0)

        Returns:
            预估完成时间（秒）
        """
        # 基础时间（秒）
        base_times = {
            QuestionType.MULTIPLE_CHOICE: 30,
            QuestionType.TRUE_FALSE: 20,
            QuestionType.FILL_BLANK: 45,
            QuestionType.SHORT_ANSWER: 120,
            QuestionType.ESSAY: 600,
            QuestionType.LISTENING_COMPREHENSION: 180,
            QuestionType.READING_COMPREHENSION: 300,
            QuestionType.TRANSLATION_EN_TO_CN: 240,
            QuestionType.TRANSLATION_CN_TO_EN: 300,
        }

        base_time = base_times.get(question_type, 60)

        # 难度调整
        difficulty_multiplier = self.difficulty_scores[difficulty_level] / 2.0

        # 内容长度调整
        length_factor = 1.0 + (content_length / 1000.0)  # 每1000字符增加100%时间

        # 学生水平调整（水平越高，用时越短）
        student_factor = 2.0 - student_level

        # 计算最终时间
        estimated_time = base_time * difficulty_multiplier * length_factor * student_factor

        return int(max(10, min(1800, estimated_time)))  # 限制在10秒到30分钟之间

    def batch_calculate_difficulties(
        self,
        questions: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        批量计算题目难度.

        Args:
            questions: 题目列表

        Returns:
            包含难度信息的题目列表
        """
        results = []

        for question in questions:
            question_type_raw = question.get("question_type")
            if not question_type_raw:
                continue

            # 确保question_type是QuestionType枚举
            if isinstance(question_type_raw, str):
                try:
                    question_type = QuestionType(question_type_raw)
                except ValueError:
                    continue
            elif isinstance(question_type_raw, QuestionType):
                question_type = question_type_raw
            else:
                continue

            content = question.get("content", {})
            historical_data = question.get("historical_data")

            # 计算内容复杂度
            content_complexity = self.calculate_content_complexity(content, question_type)

            # 计算难度分数
            difficulty_score = self.calculate_question_difficulty(
                question_type, content_complexity, historical_data
            )

            # 建议难度等级
            suggested_level = self.suggest_difficulty_level(difficulty_score)

            # 估算完成时间
            content_length = len(str(content))
            estimated_time = self.estimate_completion_time(
                question_type, suggested_level, content_length
            )

            # 构建结果
            result = {
                **question,
                "difficulty_analysis": {
                    "content_complexity": content_complexity,
                    "difficulty_score": difficulty_score,
                    "suggested_level": suggested_level,
                    "estimated_time_seconds": estimated_time,
                },
            }

            results.append(result)

        return results

    # ==================== 私有辅助方法 ====================

    def _get_training_type_factor(self, training_type: TrainingType) -> float:
        """获取训练类型调整系数."""
        factors = {
            TrainingType.VOCABULARY: 1.0,
            TrainingType.LISTENING: 1.1,
            TrainingType.READING: 1.0,
            TrainingType.WRITING: 0.9,  # 写作调整更保守
            TrainingType.TRANSLATION: 0.8,  # 翻译调整更保守
            TrainingType.COMPREHENSIVE: 1.0,
        }
        return factors.get(training_type, 1.0)

    def _score_to_difficulty_level(self, score: float) -> DifficultyLevel:
        """将分数转换为难度等级."""
        if score <= 1.5:
            return DifficultyLevel.ELEMENTARY
        elif score <= 2.5:
            return DifficultyLevel.INTERMEDIATE
        elif score <= 3.5:
            return DifficultyLevel.ADVANCED
        else:
            return DifficultyLevel.ADVANCED

    def _analyze_choice_complexity(self, content: dict[str, Any]) -> float:
        """分析选择题复杂度."""
        complexity = 0.3  # 基础复杂度

        # 选项数量
        options = content.get("options", [])
        if len(options) > 4:
            complexity += 0.1

        # 题目文本长度
        question_text = content.get("question", "")
        if len(question_text) > 100:
            complexity += 0.2

        # 选项文本长度
        avg_option_length = sum(len(str(opt)) for opt in options) / max(len(options), 1)
        if avg_option_length > 50:
            complexity += 0.2

        return complexity

    def _analyze_fill_blank_complexity(self, content: dict[str, Any]) -> float:
        """分析填空题复杂度."""
        complexity = 0.4  # 基础复杂度

        # 空格数量
        blanks = content.get("blanks", [])
        complexity += len(blanks) * 0.1

        # 文本长度
        text = content.get("text", "")
        if len(text) > 200:
            complexity += 0.2

        return complexity

    def _analyze_text_complexity(self, content: dict[str, Any]) -> float:
        """分析文本题复杂度."""
        complexity = 0.5  # 基础复杂度

        # 字数要求
        word_limit = content.get("word_limit", 0)
        if word_limit > 150:
            complexity += 0.3
        elif word_limit > 100:
            complexity += 0.2

        # 题目要求复杂度
        instruction = content.get("instruction", "")
        if "分析" in instruction or "评价" in instruction:
            complexity += 0.2

        return complexity

    def _analyze_listening_complexity(self, content: dict[str, Any]) -> float:
        """分析听力题复杂度."""
        complexity = 0.6  # 基础复杂度

        # 音频时长
        duration = content.get("audio_duration_seconds", 0)
        if duration > 180:
            complexity += 0.2
        elif duration > 120:
            complexity += 0.1

        # 语速
        speech_rate = content.get("speech_rate", "normal")
        if speech_rate == "fast":
            complexity += 0.2

        return complexity

    def _analyze_reading_complexity(self, content: dict[str, Any]) -> float:
        """分析阅读理解复杂度."""
        complexity = 0.5  # 基础复杂度

        # 文章长度
        passage = content.get("passage", "")
        word_count = len(passage.split())
        if word_count > 300:
            complexity += 0.3
        elif word_count > 200:
            complexity += 0.2

        # 题目数量
        questions = content.get("questions", [])
        complexity += len(questions) * 0.05

        return complexity

    def _analyze_translation_complexity(self, content: dict[str, Any]) -> float:
        """分析翻译题复杂度."""
        complexity = 0.7  # 基础复杂度

        # 源文本长度
        source_text = content.get("source_text", "")
        word_count = len(source_text.split())
        if word_count > 100:
            complexity += 0.2
        elif word_count > 50:
            complexity += 0.1

        # 专业术语检测（简化）
        technical_keywords = ["技术", "科学", "医学", "法律", "经济"]
        if any(keyword in source_text for keyword in technical_keywords):
            complexity += 0.1

        return complexity
