"""MinIO集成测试模块

测试MinIO对象存储的基本功能，包括连接、配置、文件操作等。
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.shared.config.storage_config import StorageConfig, storage_config
from app.shared.utils.file_utils import FileUtils
from app.shared.utils.minio_client import MinIOClient, MinIOClientError


class TestStorageConfig:
    """测试存储配置"""

    def test_storage_config_initialization(self):
        """测试存储配置初始化"""
        config = StorageConfig()

        # 检查连接配置
        assert config.connection is not None
        assert config.connection.endpoint
        assert config.connection.access_key
        assert config.connection.secret_key

        # 检查存储桶配置
        assert "documents" in config.buckets
        assert "images" in config.buckets
        assert "audio" in config.buckets
        assert "video" in config.buckets
        assert "backups" in config.buckets
        assert "temp" in config.buckets

        # 检查文件类型配置
        assert ".pdf" in config.file_types
        assert ".jpg" in config.file_types
        assert ".mp3" in config.file_types
        assert ".mp4" in config.file_types

    def test_bucket_config_validation(self):
        """测试存储桶配置验证"""
        config = StorageConfig()

        # 测试获取存储桶配置
        documents_config = config.get_bucket_config("documents")
        assert documents_config is not None
        assert documents_config.versioning is True
        assert documents_config.encryption is True

        # 测试不存在的存储桶类型
        invalid_config = config.get_bucket_config("invalid")
        assert invalid_config is None

    def test_file_type_validation(self):
        """测试文件类型验证"""
        config = StorageConfig()

        # 测试允许的文件类型
        assert config.is_file_type_allowed(".pdf") is True
        assert config.is_file_type_allowed(".jpg") is True
        assert config.is_file_type_allowed("pdf") is True  # 不带点的扩展名

        # 测试不允许的文件类型
        assert config.is_file_type_allowed(".exe") is False
        assert config.is_file_type_allowed(".bat") is False

    def test_file_size_limits(self):
        """测试文件大小限制"""
        config = StorageConfig()

        # 测试PDF文件大小限制
        pdf_max_size = config.get_max_file_size(".pdf")
        assert pdf_max_size == 50 * 1024 * 1024  # 50MB

        # 测试图片文件大小限制
        jpg_max_size = config.get_max_file_size(".jpg")
        assert jpg_max_size == 10 * 1024 * 1024  # 10MB

        # 测试不存在的文件类型
        unknown_max_size = config.get_max_file_size(".unknown")
        assert unknown_max_size == 0


class TestFileUtils:
    """测试文件工具类"""

    def test_file_extension_extraction(self):
        """测试文件扩展名提取"""
        assert FileUtils.get_file_extension("test.pdf") == ".pdf"
        assert FileUtils.get_file_extension("test.PDF") == ".pdf"
        assert FileUtils.get_file_extension("test") == ""
        assert FileUtils.get_file_extension("test.tar.gz") == ".gz"

    def test_mime_type_detection(self):
        """测试MIME类型检测"""
        assert FileUtils.get_mime_type("test.pdf") == "application/pdf"
        assert FileUtils.get_mime_type("test.jpg") == "image/jpeg"
        assert FileUtils.get_mime_type("test.txt") == "text/plain"
        assert FileUtils.get_mime_type("test.unknown") == "application/octet-stream"

    def test_filename_sanitization(self):
        """测试文件名清理"""
        assert FileUtils.sanitize_filename("test.pdf") == "test.pdf"
        assert FileUtils.sanitize_filename("test file.pdf") == "test_file.pdf"
        assert (
            FileUtils.sanitize_filename("../../../etc/passwd")
            == "file_.._.._.._etc_passwd"
        )
        assert FileUtils.sanitize_filename("") == "file_"
        assert FileUtils.sanitize_filename(".hidden") == "file_.hidden"

    def test_file_safety_check(self):
        """测试文件安全性检查"""
        assert FileUtils.is_safe_filename("test.pdf") is True
        assert FileUtils.is_safe_filename("test file.pdf") is True
        assert FileUtils.is_safe_filename("../test.pdf") is False
        assert FileUtils.is_safe_filename("test\\file.pdf") is False
        assert FileUtils.is_safe_filename("test:file.pdf") is False

    def test_human_readable_size(self):
        """测试人类可读的文件大小"""
        assert FileUtils.get_human_readable_size(0) == "0B"
        assert FileUtils.get_human_readable_size(1024) == "1.0KB"
        assert FileUtils.get_human_readable_size(1024 * 1024) == "1.0MB"
        assert FileUtils.get_human_readable_size(1024 * 1024 * 1024) == "1.0GB"

    def test_bucket_type_determination(self):
        """测试存储桶类型确定"""
        assert FileUtils.get_bucket_type_for_file("test.pdf") == "documents"
        assert FileUtils.get_bucket_type_for_file("test.jpg") == "images"
        assert FileUtils.get_bucket_type_for_file("test.mp3") == "audio"
        assert FileUtils.get_bucket_type_for_file("test.mp4") == "video"
        assert FileUtils.get_bucket_type_for_file("test.txt") == "documents"

    def test_file_type_checks(self):
        """测试文件类型检查"""
        assert FileUtils.is_image_file("test.jpg") is True
        assert FileUtils.is_image_file("test.png") is True
        assert FileUtils.is_image_file("test.pdf") is False

        assert FileUtils.is_document_file("test.pdf") is True
        assert FileUtils.is_document_file("test.doc") is True
        assert FileUtils.is_document_file("test.jpg") is False

        assert FileUtils.is_audio_file("test.mp3") is True
        assert FileUtils.is_audio_file("test.wav") is True
        assert FileUtils.is_audio_file("test.pdf") is False

        assert FileUtils.is_video_file("test.mp4") is True
        assert FileUtils.is_video_file("test.avi") is True
        assert FileUtils.is_video_file("test.pdf") is False

    def test_file_validation_with_config(self):
        """测试使用配置验证文件"""
        # 测试有效文件
        is_valid, message = FileUtils.validate_file_with_config(
            "test.pdf", 1024 * 1024
        )  # 1MB
        assert is_valid is True
        assert "passed" in message

        # 测试文件类型不允许
        is_valid, message = FileUtils.validate_file_with_config("test.exe", 1024)
        assert is_valid is False
        assert "not allowed" in message

        # 测试文件过大
        is_valid, message = FileUtils.validate_file_with_config(
            "test.pdf", 100 * 1024 * 1024
        )  # 100MB
        assert is_valid is False
        assert "exceeds limit" in message

    def test_content_hash_calculation(self):
        """测试内容哈希计算"""
        content = b"test content"
        hash_value = FileUtils.get_content_hash(content)
        assert isinstance(hash_value, str)
        assert len(hash_value) == 32  # MD5哈希长度

    def test_storage_path_generation(self):
        """测试存储路径生成"""
        path = FileUtils.generate_storage_path("test.pdf")
        assert "test.pdf" in path
        assert "/" in path  # 包含日期路径

        path_with_user = FileUtils.generate_storage_path("test.pdf", "user123")
        assert "test.pdf" in path_with_user
        assert "user123" in path_with_user


@pytest.mark.asyncio
class TestMinIOClient:
    """测试MinIO客户端"""

    @patch("app.shared.utils.minio_client.Minio")
    async def test_minio_client_initialization(self, mock_minio):
        """测试MinIO客户端初始化"""
        mock_client_instance = MagicMock()
        mock_minio.return_value = mock_client_instance

        client = MinIOClient()
        assert client.client is None
        assert client.is_connected is False

    @patch("app.shared.utils.minio_client.Minio")
    async def test_minio_client_connection(self, mock_minio):
        """测试MinIO客户端连接"""
        mock_client_instance = MagicMock()
        mock_client_instance.list_buckets.return_value = []
        mock_client_instance.bucket_exists.return_value = True
        mock_minio.return_value = mock_client_instance

        client = MinIOClient()

        # 模拟连接成功
        with patch.object(client, "_test_connection", new_callable=AsyncMock):
            with patch.object(client, "_initialize_buckets", new_callable=AsyncMock):
                result = await client.connect()
                assert result is True
                assert client.is_connected is True

    @patch("app.shared.utils.minio_client.Minio")
    async def test_minio_client_connection_failure(self, mock_minio):
        """测试MinIO客户端连接失败"""
        mock_minio.side_effect = Exception("Connection failed")

        client = MinIOClient()
        result = await client.connect()
        assert result is False
        assert client.is_connected is False

    async def test_file_validation(self):
        """测试文件验证"""
        client = MinIOClient()

        # 创建临时文件进行测试
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(b"test content")
            temp_path = Path(temp_file.name)

        try:
            # 测试有效文件
            await client._validate_file(temp_path)

            # 测试文件过大（通过修改配置）
            with patch.object(storage_config, "get_max_file_size", return_value=1):
                with pytest.raises(MinIOClientError, match="exceeds limit"):
                    await client._validate_file(temp_path)

            # 测试不允许的文件类型
            exe_path = temp_path.with_suffix(".exe")
            temp_path.rename(exe_path)
            with pytest.raises(MinIOClientError, match="not allowed"):
                await client._validate_file(exe_path)

        finally:
            # 清理临时文件
            for path in [temp_path, temp_path.with_suffix(".exe")]:
                if path.exists():
                    os.unlink(path)

    def test_object_name_generation(self):
        """测试对象名称生成"""
        client = MinIOClient()

        test_path = Path("test.pdf")
        object_name = client._generate_object_name(test_path)

        assert "test.pdf" in object_name
        assert len(object_name) > len("test.pdf")  # 包含时间戳和哈希

    async def test_file_hash_calculation(self):
        """测试文件哈希计算"""
        client = MinIOClient()

        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"test content")
            temp_path = Path(temp_file.name)

        try:
            hash_value = await client._calculate_file_hash(temp_path)
            assert isinstance(hash_value, str)
            assert len(hash_value) == 32  # MD5哈希长度
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__])
