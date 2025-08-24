"""RSS和外部资源获取工具."""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime
from typing import Any

import aiohttp
import feedparser
from bs4 import BeautifulSoup

from app.shared.models.enums import ContentType, DifficultyLevel

logger = logging.getLogger(__name__)


class RSSFeedParser:
    """RSS源解析器."""

    def __init__(self) -> None:
        self.session: aiohttp.ClientSession | None = None
        self.timeout = aiohttp.ClientTimeout(total=30)

    async def __aenter__(self) -> RSSFeedParser:
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: type | None,
    ) -> None:
        if self.session:
            await self.session.close()

    async def parse_rss_feed(
        self, feed_url: str, max_items: int = 20, language_filter: str | None = None
    ) -> list[dict[str, Any]]:
        """解析RSS源."""
        try:
            if not self.session:
                raise RuntimeError("RSSFeedParser must be used as async context manager")

            # 获取RSS内容
            async with self.session.get(feed_url) as response:
                if response.status != 200:
                    logger.warning(
                        f"Failed to fetch RSS feed: {feed_url}, status: {response.status}"
                    )
                    return []

                content = await response.text()

            # 解析RSS
            feed = feedparser.parse(content)
            if feed.bozo:
                logger.warning(f"RSS feed parsing warning: {feed.bozo_exception}")

            items = []
            for entry in feed.entries[:max_items]:
                try:
                    item = await self._parse_rss_entry(entry, feed_url, language_filter)
                    if item:
                        items.append(item)
                except Exception as e:
                    logger.error(f"Error parsing RSS entry: {str(e)}")
                    continue

            return items

        except Exception as e:
            logger.error(f"Error parsing RSS feed {feed_url}: {str(e)}")
            return []

    async def _parse_rss_entry(
        self, entry: Any, feed_url: str, language_filter: str | None = None
    ) -> dict[str, Any] | None:
        """解析RSS条目."""
        try:
            # 基本信息
            title = getattr(entry, "title", "")
            link = getattr(entry, "link", "")
            summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
            author = getattr(entry, "author", "") or getattr(entry, "dc_creator", "")

            # 发布时间
            published = getattr(entry, "published_parsed", None) or getattr(
                entry, "updated_parsed", None
            )
            if published:
                publish_date = datetime(*published[:6]).strftime("%Y-%m-%d")
            else:
                publish_date = datetime.now().strftime("%Y-%m-%d")

            if not title or not link:
                return None

            # 获取完整内容
            full_content = await self._extract_full_content(link)

            # 语言检测和过滤
            detected_language = await self._detect_language(title + " " + summary)
            if language_filter and detected_language != language_filter:
                return None

            # 提取关键词和话题
            keywords = await self._extract_keywords(
                title + " " + summary + " " + (full_content or "")
            )
            topics = await self._extract_topics(title + " " + summary)

            # 估计难度级别
            difficulty = await self._estimate_difficulty(full_content or summary)

            # 提取词汇重点
            vocabulary_highlights = await self._extract_vocabulary_highlights(
                full_content or summary
            )

            # 生成理解问题
            comprehension_questions = await self._generate_comprehension_questions(title, summary)

            return {
                "title": title,
                "source_type": "rss",
                "source_url": link,
                "author": author,
                "publish_date": publish_date,
                "content_preview": summary[:500] if summary else "",
                "full_content": full_content,
                "content_type": ContentType.TEXT,
                "language": detected_language,
                "difficulty_level": difficulty,
                "topics": topics,
                "keywords": keywords,
                "vocabulary_highlights": vocabulary_highlights,
                "comprehension_questions": comprehension_questions,
                "discussion_topics": await self._generate_discussion_topics(title, summary),
            }

        except Exception as e:
            logger.error(f"Error parsing RSS entry: {str(e)}")
            return None

    async def _extract_full_content(self, url: str) -> str | None:
        """提取网页完整内容."""
        try:
            if not self.session:
                return None

            async with self.session.get(url) as response:
                if response.status != 200:
                    return None

                html_content = await response.text()
                soup = BeautifulSoup(html_content, "html.parser")

                # 移除脚本和样式
                for script in soup(["script", "style"]):
                    script.decompose()

                # 尝试找到主要内容区域
                main_content = None

                # 常见的内容选择器
                content_selectors = [
                    "article",
                    "main",
                    ".content",
                    ".post",
                    ".article",
                    "#content",
                    "#main",
                    ".entry-content",
                    ".post-content",
                ]

                for selector in content_selectors:
                    main_content = soup.select_one(selector)
                    if main_content:
                        break

                if not main_content:
                    main_content = soup.find("body")

                if main_content:
                    text = main_content.get_text(separator=" ", strip=True)
                    # 清理文本，限制长度
                    text = re.sub(r"\s+", " ", text)
                    return text[:10000] if text else None

                return None

        except Exception as e:
            logger.error(f"Error extracting content from {url}: {str(e)}")
            return None

    async def _detect_language(self, text: str) -> str:
        """检测文本语言."""
        # 简单的语言检测逻辑
        if not text:
            return "en"

        # 统计中文字符
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
        total_chars = len(text)

        if chinese_chars / total_chars > 0.3:
            return "zh-CN"
        else:
            return "en"

    async def _extract_keywords(self, text: str) -> list[str]:
        """提取关键词."""
        if not text:
            return []

        # 简单的关键词提取（实际项目中可以使用更复杂的NLP技术）
        words = re.findall(r"\b\w{4,}\b", text.lower())

        # 过滤常用词
        stop_words = {
            "this",
            "that",
            "with",
            "have",
            "will",
            "from",
            "they",
            "been",
            "their",
            "said",
            "each",
            "which",
            "what",
            "there",
            "about",
            "other",
            "many",
            "some",
            "time",
            "very",
            "when",
            "much",
            "more",
            "most",
            "这个",
            "那个",
            "可以",
            "没有",
            "我们",
            "他们",
            "现在",
            "已经",
            "因为",
        }

        # 按长度和出现频率排序，取前10个
        word_freq: dict[str, int] = {}
        for word in words:
            if word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1

        sorted_keywords = sorted(word_freq.items(), key=lambda x: (-x[1], -len(x[0])))
        return [word for word, _ in sorted_keywords[:10]]

    async def _extract_topics(self, text: str) -> list[str]:
        """提取话题标签."""
        if not text:
            return []

        # 预定义话题关键词映射
        topic_keywords = {
            "technology": [
                "technology",
                "tech",
                "software",
                "computer",
                "digital",
                "AI",
                "internet",
            ],
            "education": [
                "education",
                "learning",
                "student",
                "teacher",
                "school",
                "university",
            ],
            "business": [
                "business",
                "company",
                "market",
                "economy",
                "finance",
                "trade",
            ],
            "health": [
                "health",
                "medical",
                "doctor",
                "hospital",
                "medicine",
                "disease",
            ],
            "science": ["science", "research", "study", "experiment", "discovery"],
            "culture": ["culture", "art", "music", "book", "movie", "literature"],
            "sports": ["sport", "game", "team", "player", "match", "competition"],
            "travel": ["travel", "trip", "vacation", "tourist", "destination"],
        }

        text_lower = text.lower()
        detected_topics = []

        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                detected_topics.append(topic)

        return detected_topics[:5]  # 最多返回5个话题

    async def _estimate_difficulty(self, text: str) -> DifficultyLevel:
        """估计文本难度."""
        if not text:
            return DifficultyLevel.INTERMEDIATE

        # 简单的难度评估（基于句子长度、词汇复杂度等）
        sentences = re.split(r"[.!?]", text)
        avg_sentence_length = (
            sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        )

        # 统计长词汇（6个字符以上）
        words = re.findall(r"\b\w+\b", text)
        long_words = sum(1 for word in words if len(word) > 6)
        long_word_ratio = long_words / len(words) if words else 0

        # 难度评分
        difficulty_score = 0

        if avg_sentence_length > 20:
            difficulty_score += 2
        elif avg_sentence_length > 15:
            difficulty_score += 1

        if long_word_ratio > 0.3:
            difficulty_score += 2
        elif long_word_ratio > 0.2:
            difficulty_score += 1

        # 根据评分返回难度级别
        if difficulty_score >= 3:
            return DifficultyLevel.ADVANCED
        elif difficulty_score >= 1:
            return DifficultyLevel.INTERMEDIATE
        else:
            return DifficultyLevel.BEGINNER

    async def _extract_vocabulary_highlights(self, text: str) -> list[dict[str, Any]]:
        """提取重点词汇."""
        if not text:
            return []

        # 提取可能的重点词汇（长度>5的不常见词）
        words = re.findall(r"\b[A-Za-z]{6,}\b", text)

        # 简单过滤，实际项目中可以使用词频数据库
        common_words = {
            "through",
            "without",
            "between",
            "during",
            "before",
            "after",
            "another",
            "different",
            "important",
            "because",
            "information",
        }

        highlighted_words: list[dict[str, Any]] = []
        seen_words = set()

        for word in words:
            word_lower = word.lower()
            if (
                word_lower not in common_words
                and word_lower not in seen_words
                and len(highlighted_words) < 10
            ):
                highlighted_words.append(
                    {
                        "word": word,
                        "definition": f"Definition of {word}",  # 实际项目中可以调用词典API
                        "context": self._find_word_context(text, word),
                    }
                )
                seen_words.add(word_lower)

        return highlighted_words

    def _find_word_context(self, text: str, word: str) -> str:
        """查找词汇在文本中的上下文."""
        sentences = re.split(r"[.!?]", text)
        for sentence in sentences:
            if word.lower() in sentence.lower():
                return sentence.strip()
        return ""

    async def _generate_comprehension_questions(
        self, title: str, summary: str
    ) -> list[dict[str, Any]]:
        """生成理解问题."""
        if not title and not summary:
            return []

        # 基础的问题模板
        questions = []

        if title:
            questions.append(
                {
                    "question": f'What is the main topic of "{title}"?',
                    "type": "main_idea",
                    "difficulty": "easy",
                }
            )

        if summary:
            questions.append(
                {
                    "question": "Summarize the key points mentioned in the text.",
                    "type": "summary",
                    "difficulty": "medium",
                }
            )

            questions.append(
                {
                    "question": "What conclusions can you draw from this text?",
                    "type": "inference",
                    "difficulty": "hard",
                }
            )

        return questions[:3]  # 最多返回3个问题

    async def _generate_discussion_topics(self, title: str, summary: str) -> list[str]:
        """生成讨论话题."""
        if not title and not summary:
            return []

        topics = []

        if title:
            topics.append(f'Discuss the implications of "{title}"')

        if summary:
            topics.append("Share your opinion on the main points raised")
            topics.append("How does this relate to your personal experience?")

        return topics[:3]


class ExternalResourceCollector:
    """外部资源收集器."""

    def __init__(self) -> None:
        self.rss_feeds = [
            "https://feeds.bbci.co.uk/news/rss.xml",
            "https://rss.cnn.com/rss/edition.rss",
            "https://feeds.reuters.com/reuters/topNews",
            "https://www.npr.org/rss/rss.php?id=1001",
        ]

    async def collect_daily_resources(
        self, max_items_per_feed: int = 5, target_language: str = "en"
    ) -> list[dict[str, Any]]:
        """每日收集外部资源."""
        all_resources: list[dict[str, Any]] = []

        async with RSSFeedParser() as parser:
            tasks = []
            for feed_url in self.rss_feeds:
                task = parser.parse_rss_feed(feed_url, max_items_per_feed, target_language)
                tasks.append(task)

            # 并发获取所有RSS源
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"RSS collection error: {str(result)}")
                    continue

                # result is guaranteed to be list[dict[str, Any]] here
                typed_result: list[dict[str, Any]] = result  # type: ignore[assignment]
                all_resources.extend(typed_result)

        # 去重（基于URL）
        seen_urls = set()
        unique_resources = []
        for resource in all_resources:
            url = resource.get("source_url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_resources.append(resource)

        # 按发布时间排序
        unique_resources.sort(key=lambda x: x.get("publish_date", ""), reverse=True)

        return unique_resources

    async def search_web_resources(
        self, query: str, max_results: int = 10, source_types: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """搜索网络资源（这里是示例实现，实际需要接入搜索API）."""
        # 这里只是示例，实际项目中需要接入Google Custom Search API等
        logger.info(f"Searching web resources for query: {query}")

        # 模拟搜索结果
        mock_results = [
            {
                "title": f"Learning about {query}",
                "source_type": "web",
                "source_url": f"https://example.com/learning-{query.lower().replace(' ', '-')}",
                "author": "Education Expert",
                "publish_date": datetime.now().strftime("%Y-%m-%d"),
                "content_preview": f"This is a comprehensive guide about {query}...",
                "language": "en",
                "difficulty_level": DifficultyLevel.INTERMEDIATE,
                "topics": ["education", "learning"],
                "keywords": [query.lower()],
            }
        ]

        return mock_results[:max_results]
