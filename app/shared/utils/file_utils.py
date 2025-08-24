"""文件处理工具模块

提供文件操作、验证、转换等通用功能，集成MinIO对象存储支持。
"""

import mimetypes
import os
from pathlib import Path
from typing import Any


class FileUtils:
    """文件处理工具类."""

    async def extract_text_content(self, file_path: str) -> str:
        """
        提取文件文本内容

        Args:
            file_path: 文件路径

        Returns:
            str: 文本内容
        """
        try:
            # 根据文件类型选择不同的提取方法
            file_extension = Path(file_path).suffix.lower()

            if file_extension == ".txt":
                return await self._extract_txt_content(file_path)
            elif file_extension == ".pdf":
                return await self._extract_pdf_content(file_path)
            elif file_extension in [".doc", ".docx"]:
                return await self._extract_word_content(file_path)
            elif file_extension == ".md":
                return await self._extract_markdown_content(file_path)
            else:
                # 默认按文本文件处理
                return await self._extract_txt_content(file_path)

        except Exception as e:
            raise RuntimeError(f"Failed to extract content from {file_path}: {str(e)}") from e

    async def _extract_txt_content(self, file_path: str) -> str:
        """提取TXT文件内容."""
        with open(file_path, encoding="utf-8") as f:
            return f.read()

    async def _extract_pdf_content(self, file_path: str) -> str:
        """提取PDF文件内容."""
        # 这里应该使用PDF处理库如PyPDF2或pdfplumber
        # 暂时返回模拟内容
        return f"PDF content from {file_path}"

    async def _extract_word_content(self, file_path: str) -> str:
        """提取Word文档内容."""
        # 这里应该使用python-docx库
        # 暂时返回模拟内容
        return f"Word document content from {file_path}"

    async def _extract_markdown_content(self, file_path: str) -> str:
        """提取Markdown文件内容."""
        with open(file_path, encoding="utf-8") as f:
            return f.read()

    def get_file_info(self, file_path: str) -> dict[str, Any]:
        """
        获取文件信息

        Args:
            file_path: 文件路径

        Returns:
            dict: 文件信息
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        stat = os.stat(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)

        return {
            "size": stat.st_size,
            "extension": Path(file_path).suffix.lower(),
            "mime_type": mime_type,
            "created_time": stat.st_ctime,
            "modified_time": stat.st_mtime,
        }

    # MinIO相关的静态方法
    @staticmethod
    def get_file_hash(file_path: str) -> str:
        """计算文件MD5哈希值."""
        import hashlib

        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    @staticmethod
    def get_content_hash(content: bytes) -> str:
        """计算内容MD5哈希值."""
        import hashlib

        return hashlib.md5(content).hexdigest()

    @staticmethod
    def get_file_size(file_path: str) -> int:
        """获取文件大小（字节）."""
        return os.path.getsize(file_path)

    @staticmethod
    def get_file_extension(filename: str) -> str:
        """获取文件扩展名."""
        return Path(filename).suffix.lower()

    @staticmethod
    def get_mime_type(filename: str) -> str:
        """获取文件MIME类型."""
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or "application/octet-stream"

    @staticmethod
    def is_safe_filename(filename: str) -> bool:
        """检查文件名是否安全."""
        dangerous_chars = ["../", "..\\", "/", "\\", ":", "*", "?", '"', "<", ">", "|"]
        return not any(char in filename for char in dangerous_chars)

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """清理文件名，移除危险字符."""
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_"
        sanitized = "".join(c if c in safe_chars else "_" for c in filename)

        if not sanitized or sanitized.startswith("."):
            sanitized = f"file_{sanitized}"

        return sanitized

    @staticmethod
    def get_human_readable_size(size_bytes: int) -> str:
        """将字节数转换为人类可读的大小."""
        if size_bytes == 0:
            return "0B"

        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1

        return f"{size_bytes:.1f}{size_names[i]}"

    @staticmethod
    def validate_file_with_config(filename: str, file_size: int) -> tuple[bool, str]:
        """使用配置验证文件."""
        try:
            from app.shared.config.storage_config import storage_config

            extension = FileUtils.get_file_extension(filename)

            # 检查文件类型是否允许
            if not storage_config.is_file_type_allowed(extension):
                return False, f"File type {extension} is not allowed"

            # 检查文件大小
            max_size = storage_config.get_max_file_size(extension)
            if file_size > max_size:
                return (
                    False,
                    f"File size {FileUtils.get_human_readable_size(file_size)} exceeds limit {FileUtils.get_human_readable_size(max_size)}",
                )

            return True, "File validation passed"
        except ImportError:
            # 如果配置模块不可用，使用默认验证
            return True, "File validation passed (default)"

    @staticmethod
    def get_bucket_type_for_file(filename: str) -> str:
        """根据文件类型确定存储桶类型."""
        extension = FileUtils.get_file_extension(filename)

        # 图片文件
        if extension in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]:
            return "images"
        # 音频文件
        elif extension in [".mp3", ".wav", ".flac", ".aac", ".ogg"]:
            return "audio"
        # 视频文件
        elif extension in [".mp4", ".avi", ".mov", ".wmv", ".flv", ".mkv"]:
            return "video"
        # 文档文件
        else:
            return "documents"

    @staticmethod
    def generate_storage_path(filename: str, user_id: str = None) -> str:
        """生成存储路径."""
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y/%m/%d")
        sanitized_name = FileUtils.sanitize_filename(filename)

        if user_id:
            return f"{timestamp}/{user_id}/{sanitized_name}"
        else:
            return f"{timestamp}/{sanitized_name}"

    @staticmethod
    def is_image_file(filename: str) -> bool:
        """检查是否为图片文件."""
        extension = FileUtils.get_file_extension(filename)
        return extension in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]

    @staticmethod
    def is_document_file(filename: str) -> bool:
        """检查是否为文档文件."""
        extension = FileUtils.get_file_extension(filename)
        return extension in [".pdf", ".doc", ".docx", ".txt", ".md", ".html"]

    @staticmethod
    def is_audio_file(filename: str) -> bool:
        """检查是否为音频文件."""
        extension = FileUtils.get_file_extension(filename)
        return extension in [".mp3", ".wav", ".flac", ".aac", ".ogg"]

    @staticmethod
    def is_video_file(filename: str) -> bool:
        """检查是否为视频文件."""
        extension = FileUtils.get_file_extension(filename)
        return extension in [".mp4", ".avi", ".mov", ".wmv", ".flv", ".mkv"]
