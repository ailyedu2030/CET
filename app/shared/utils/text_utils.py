"""文本处理工具类."""

import re


class TextUtils:
    """文本处理工具类."""

    async def parse_structured_content(self, content: str) -> list[str]:
        """
        解析结构化内容

        Args:
            content: 文档内容

        Returns:
            list[str]: 章节列表
        """
        # 简单的章节分割逻辑
        sections = []

        # 按标题分割
        title_pattern = r"^#+\s+(.+)$|^第[一二三四五六七八九十\d]+[章节]\s+(.+)$"
        lines = content.split("\n")
        current_section: list[str] = []

        for line in lines:
            if re.match(title_pattern, line, re.MULTILINE):
                if current_section:
                    sections.append("\n".join(current_section))
                    current_section = []
            current_section.append(line)

        if current_section:
            sections.append("\n".join(current_section))

        return sections if sections else [content]

    async def split_by_paragraphs(self, content: str) -> list[str]:
        """
        按段落分割文本

        Args:
            content: 文本内容

        Returns:
            list[str]: 段落列表
        """
        # 按双换行符分割段落
        paragraphs = re.split(r"\n\s*\n", content.strip())
        return [p.strip() for p in paragraphs if p.strip()]

    async def split_sentences(self, text: str) -> list[str]:
        """
        分割句子

        Args:
            text: 文本内容

        Returns:
            list[str]: 句子列表
        """
        # 简单的句子分割
        sentence_pattern = r"[.!?。！？]+\s*"
        sentences = re.split(sentence_pattern, text)
        return [s.strip() for s in sentences if s.strip()]

    async def extract_keywords(self, text: str) -> list[str]:
        """
        提取关键词

        Args:
            text: 文本内容

        Returns:
            list[str]: 关键词列表
        """
        # 简单的关键词提取
        # 移除标点符号，转小写，分词
        words = re.findall(r"\b[a-zA-Z\u4e00-\u9fff]+\b", text.lower())

        # 过滤停用词（简化版）
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "的",
            "了",
            "在",
            "是",
            "我",
            "你",
            "他",
            "她",
            "它",
            "们",
            "这",
            "那",
            "有",
            "和",
            "与",
            "或",
            "但",
            "如果",
            "因为",
            "所以",
            "然后",
            "现在",
        }

        keywords = [word for word in words if word not in stop_words and len(word) > 2]

        # 去重并返回前10个
        return list(dict.fromkeys(keywords))[:10]

    def clean_text(self, text: str) -> str:
        """
        清理文本

        Args:
            text: 原始文本

        Returns:
            str: 清理后的文本
        """
        # 移除多余的空白字符
        text = re.sub(r"\s+", " ", text)

        # 移除特殊字符（保留基本标点）
        text = re.sub(r'[^\w\s\u4e00-\u9fff.,!?;:()"\'-]', "", text)

        return text.strip()

    def truncate_text(self, text: str, max_length: int = 1000) -> str:
        """
        截断文本

        Args:
            text: 原始文本
            max_length: 最大长度

        Returns:
            str: 截断后的文本
        """
        if len(text) <= max_length:
            return text

        # 在单词边界截断
        truncated = text[:max_length]
        last_space = truncated.rfind(" ")

        if last_space > max_length * 0.8:  # 如果最后一个空格位置合理
            return truncated[:last_space] + "..."
        else:
            return truncated + "..."
