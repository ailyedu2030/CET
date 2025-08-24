"""文档解析器 - 支持多种文档格式的解析和处理."""

import logging
import mimetypes
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class DocumentParser:
    """文档解析器 - 支持多种格式的文档解析."""

    def __init__(self) -> None:
        """初始化文档解析器."""
        # 支持的文档格式
        self.supported_formats = {
            "text/plain": self._parse_text,
            "text/markdown": self._parse_markdown,
            "application/pdf": self._parse_pdf,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": self._parse_docx,
            "application/msword": self._parse_doc,
            "text/html": self._parse_html,
            "application/json": self._parse_json,
            "text/csv": self._parse_csv,
        }

        # 解析配置
        self.parse_config = {
            "max_file_size": 50 * 1024 * 1024,  # 50MB
            "chunk_size": 1000,  # 默认分块大小
            "chunk_overlap": 100,  # 分块重叠
            "preserve_structure": True,  # 保留文档结构
        }

    async def parse_document(
        self, file_path: str, file_content: bytes | None = None
    ) -> dict[str, Any]:
        """解析文档."""
        try:
            # 检查文件大小
            if file_content and len(file_content) > self.parse_config["max_file_size"]:
                raise ValueError(f"文件大小超过限制: {len(file_content)} bytes")

            # 检测文件类型
            mime_type = self._detect_mime_type(file_path, file_content)

            if mime_type not in self.supported_formats:
                raise ValueError(f"不支持的文件格式: {mime_type}")

            # 解析文档
            parser_func = self.supported_formats[mime_type]
            parse_result = await parser_func(file_path, file_content)

            # 添加元数据
            parse_result.update(
                {
                    "file_path": file_path,
                    "mime_type": mime_type,
                    "file_size": len(file_content) if file_content else 0,
                    "parser_version": "1.0",
                }
            )

            logger.info(
                f"Document parsed successfully: {file_path}, "
                f"pages: {parse_result.get('page_count', 0)}, "
                f"chunks: {len(parse_result.get('chunks', []))}"
            )

            return parse_result

        except Exception as e:
            logger.error(f"Document parsing failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path,
            }

    def _detect_mime_type(self, file_path: str, file_content: bytes | None = None) -> str:
        """检测文件MIME类型."""
        # 首先尝试根据文件扩展名检测
        mime_type, _ = mimetypes.guess_type(file_path)

        if mime_type:
            return mime_type

        # 根据文件扩展名手动映射
        file_ext = Path(file_path).suffix.lower()
        ext_mapping = {
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".doc": "application/msword",
            ".html": "text/html",
            ".htm": "text/html",
            ".json": "application/json",
            ".csv": "text/csv",
        }

        if file_ext in ext_mapping:
            return ext_mapping[file_ext]

        # 如果有文件内容，尝试根据内容检测
        if file_content:
            return self._detect_mime_from_content(file_content)

        return "application/octet-stream"

    def _detect_mime_from_content(self, content: bytes) -> str:
        """根据文件内容检测MIME类型."""
        # PDF文件标识
        if content.startswith(b"%PDF"):
            return "application/pdf"

        # ZIP文件标识（DOCX等）
        if content.startswith(b"PK\x03\x04"):
            return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

        # HTML文件标识
        if b"<html" in content[:1000].lower() or b"<!doctype html" in content[:1000].lower():
            return "text/html"

        # JSON文件标识
        try:
            content_str = content.decode("utf-8")
            if content_str.strip().startswith(("{", "[")):
                return "application/json"
        except UnicodeDecodeError:
            pass

        # 默认为纯文本
        return "text/plain"

    async def _parse_text(
        self, file_path: str, file_content: bytes | None = None
    ) -> dict[str, Any]:
        """解析纯文本文件."""
        try:
            if file_content:
                content = file_content.decode("utf-8")
            else:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

            # 分块处理
            chunks = self._split_text_into_chunks(content)

            return {
                "success": True,
                "content": content,
                "chunks": chunks,
                "page_count": 1,
                "word_count": len(content.split()),
                "char_count": len(content),
            }

        except Exception as e:
            logger.error(f"Text parsing failed: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _parse_markdown(
        self, file_path: str, file_content: bytes | None = None
    ) -> dict[str, Any]:
        """解析Markdown文件."""
        try:
            if file_content:
                content = file_content.decode("utf-8")
            else:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

            # 提取标题结构
            headers = self._extract_markdown_headers(content)

            # 分块处理（保留结构）
            chunks = self._split_markdown_into_chunks(content, headers)

            return {
                "success": True,
                "content": content,
                "chunks": chunks,
                "headers": headers,
                "page_count": 1,
                "word_count": len(content.split()),
                "char_count": len(content),
            }

        except Exception as e:
            logger.error(f"Markdown parsing failed: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _parse_pdf(self, file_path: str, file_content: bytes | None = None) -> dict[str, Any]:
        """解析PDF文件."""
        try:
            # 注意：实际项目中需要安装PyPDF2或pdfplumber
            # 这里提供模拟实现

            logger.warning(
                "PDF parsing is simulated - install PyPDF2 or pdfplumber for real implementation"
            )

            # 模拟PDF解析结果
            content = f"模拟PDF内容 - {file_path}\n这是一个模拟的PDF文档内容。"
            chunks = self._split_text_into_chunks(content)

            return {
                "success": True,
                "content": content,
                "chunks": chunks,
                "page_count": 1,
                "word_count": len(content.split()),
                "char_count": len(content),
                "extraction_method": "simulated",
            }

        except Exception as e:
            logger.error(f"PDF parsing failed: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _parse_docx(
        self, file_path: str, file_content: bytes | None = None
    ) -> dict[str, Any]:
        """解析DOCX文件."""
        try:
            # 注意：实际项目中需要安装python-docx
            # 这里提供模拟实现

            logger.warning(
                "DOCX parsing is simulated - install python-docx for real implementation"
            )

            # 模拟DOCX解析结果
            content = f"模拟DOCX内容 - {file_path}\n这是一个模拟的Word文档内容。"
            chunks = self._split_text_into_chunks(content)

            return {
                "success": True,
                "content": content,
                "chunks": chunks,
                "page_count": 1,
                "word_count": len(content.split()),
                "char_count": len(content),
                "extraction_method": "simulated",
            }

        except Exception as e:
            logger.error(f"DOCX parsing failed: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _parse_doc(self, file_path: str, file_content: bytes | None = None) -> dict[str, Any]:
        """解析DOC文件."""
        try:
            # 注意：实际项目中需要安装python-docx或其他库
            # 这里提供模拟实现

            logger.warning(
                "DOC parsing is simulated - install appropriate library for real implementation"
            )

            # 模拟DOC解析结果
            content = f"模拟DOC内容 - {file_path}\n这是一个模拟的Word文档内容。"
            chunks = self._split_text_into_chunks(content)

            return {
                "success": True,
                "content": content,
                "chunks": chunks,
                "page_count": 1,
                "word_count": len(content.split()),
                "char_count": len(content),
                "extraction_method": "simulated",
            }

        except Exception as e:
            logger.error(f"DOC parsing failed: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _parse_html(
        self, file_path: str, file_content: bytes | None = None
    ) -> dict[str, Any]:
        """解析HTML文件."""
        try:
            if file_content:
                content = file_content.decode("utf-8")
            else:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

            # 提取纯文本内容（简单实现）
            text_content = self._extract_text_from_html(content)

            # 分块处理
            chunks = self._split_text_into_chunks(text_content)

            return {
                "success": True,
                "content": text_content,
                "raw_html": content,
                "chunks": chunks,
                "page_count": 1,
                "word_count": len(text_content.split()),
                "char_count": len(text_content),
            }

        except Exception as e:
            logger.error(f"HTML parsing failed: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _parse_json(
        self, file_path: str, file_content: bytes | None = None
    ) -> dict[str, Any]:
        """解析JSON文件."""
        try:
            if file_content:
                content = file_content.decode("utf-8")
            else:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

            import json

            json_data = json.loads(content)

            # 将JSON转换为文本
            text_content = self._json_to_text(json_data)

            # 分块处理
            chunks = self._split_text_into_chunks(text_content)

            return {
                "success": True,
                "content": text_content,
                "json_data": json_data,
                "chunks": chunks,
                "page_count": 1,
                "word_count": len(text_content.split()),
                "char_count": len(text_content),
            }

        except Exception as e:
            logger.error(f"JSON parsing failed: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _parse_csv(self, file_path: str, file_content: bytes | None = None) -> dict[str, Any]:
        """解析CSV文件."""
        try:
            if file_content:
                content = file_content.decode("utf-8")
            else:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

            # 简单CSV解析
            lines = content.strip().split("\n")
            headers = lines[0].split(",") if lines else []
            rows = [line.split(",") for line in lines[1:]] if len(lines) > 1 else []

            # 将CSV转换为文本
            text_content = self._csv_to_text(headers, rows)

            # 分块处理
            chunks = self._split_text_into_chunks(text_content)

            return {
                "success": True,
                "content": text_content,
                "headers": headers,
                "row_count": len(rows),
                "chunks": chunks,
                "page_count": 1,
                "word_count": len(text_content.split()),
                "char_count": len(text_content),
            }

        except Exception as e:
            logger.error(f"CSV parsing failed: {str(e)}")
            return {"success": False, "error": str(e)}

    def _split_text_into_chunks(self, text: str) -> list[dict[str, Any]]:
        """将文本分割成块."""
        chunk_size = self.parse_config["chunk_size"]
        chunk_overlap = self.parse_config["chunk_overlap"]

        chunks = []
        start = 0
        chunk_index = 0

        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]

            # 尝试在句子边界分割
            if end < len(text):
                last_sentence_end = max(
                    chunk_text.rfind("。"),
                    chunk_text.rfind("！"),
                    chunk_text.rfind("？"),
                    chunk_text.rfind("."),
                    chunk_text.rfind("!"),
                    chunk_text.rfind("?"),
                )
                if last_sentence_end > chunk_size // 2:
                    chunk_text = chunk_text[: last_sentence_end + 1]
                    end = start + last_sentence_end + 1

            chunks.append(
                {
                    "chunk_index": chunk_index,
                    "content": chunk_text.strip(),
                    "start_position": start,
                    "end_position": end,
                    "chunk_size": len(chunk_text),
                    "metadata": {
                        "chunk_type": "text",
                        "overlap": chunk_overlap if start > 0 else 0,
                    },
                }
            )

            start = end - chunk_overlap
            chunk_index += 1

        return chunks

    def _extract_markdown_headers(self, content: str) -> list[dict[str, Any]]:
        """提取Markdown标题."""
        headers = []
        lines = content.split("\n")

        for i, line in enumerate(lines):
            if line.strip().startswith("#"):
                level = len(line) - len(line.lstrip("#"))
                title = line.strip("#").strip()
                headers.append(
                    {
                        "level": level,
                        "title": title,
                        "line_number": i + 1,
                    }
                )

        return headers

    def _split_markdown_into_chunks(
        self, content: str, headers: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """按Markdown结构分块."""
        if not headers:
            return self._split_text_into_chunks(content)

        chunks = []
        lines = content.split("\n")
        current_section: list[str] = []
        current_header = None
        chunk_index = 0

        for i, line in enumerate(lines):
            if line.strip().startswith("#"):
                # 保存前一个section
                if current_section:
                    section_content = "\n".join(current_section)
                    chunks.append(
                        {
                            "chunk_index": chunk_index,
                            "content": section_content.strip(),
                            "start_position": 0,  # 简化实现
                            "end_position": len(section_content),
                            "chunk_size": len(section_content),
                            "metadata": {
                                "chunk_type": "markdown_section",
                                "header": current_header,
                                "section_title": (
                                    current_header["title"] if current_header else None
                                ),
                            },
                        }
                    )
                    chunk_index += 1

                # 开始新section
                current_header = next((h for h in headers if h["line_number"] == i + 1), None)
                current_section = [line]
            else:
                current_section.append(line)

        # 保存最后一个section
        if current_section:
            section_content = "\n".join(current_section)
            chunks.append(
                {
                    "chunk_index": chunk_index,
                    "content": section_content.strip(),
                    "start_position": 0,
                    "end_position": len(section_content),
                    "chunk_size": len(section_content),
                    "metadata": {
                        "chunk_type": "markdown_section",
                        "header": current_header,
                        "section_title": (current_header["title"] if current_header else None),
                    },
                }
            )

        return chunks

    def _extract_text_from_html(self, html_content: str) -> str:
        """从HTML中提取纯文本."""
        # 简单的HTML标签移除
        text = re.sub(r"<[^>]+>", " ", html_content)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _json_to_text(self, json_data: Any) -> str:
        """将JSON数据转换为文本."""
        if isinstance(json_data, dict):
            text_parts = []
            for key, value in json_data.items():
                text_parts.append(f"{key}: {self._json_to_text(value)}")
            return "\n".join(text_parts)
        elif isinstance(json_data, list):
            return "\n".join(self._json_to_text(item) for item in json_data)
        else:
            return str(json_data)

    def _csv_to_text(self, headers: list[str], rows: list[list[str]]) -> str:
        """将CSV数据转换为文本."""
        text_parts = []

        if headers:
            text_parts.append("表头: " + ", ".join(headers))

        for i, row in enumerate(rows):
            if len(row) == len(headers):
                row_text = ", ".join(f"{headers[j]}: {row[j]}" for j in range(len(headers)))
                text_parts.append(f"第{i + 1}行: {row_text}")
            else:
                text_parts.append(f"第{i + 1}行: {', '.join(row)}")

        return "\n".join(text_parts)
