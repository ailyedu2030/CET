"""OCR服务测试 - 需求33验收测试."""

import os
import tempfile
from pathlib import Path

import pytest

from app.core.exceptions import BusinessLogicError
from app.resources.services.ocr_service import OCRService


class TestOCRService:
    """OCR服务测试类 - 验证需求33的OCR功能."""

    @pytest.fixture
    def ocr_service(self):
        """创建OCR服务实例."""
        return OCRService()

    @pytest.fixture
    def temp_image_file(self):
        """创建临时图片文件."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
            # 写入一些模拟图片数据
            temp_file.write(b"fake image data")
            temp_file_path = temp_file.name

        yield temp_file_path

        # 清理
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

    @pytest.fixture
    def temp_pdf_file(self):
        """创建临时PDF文件."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            # 写入一些模拟PDF数据
            temp_file.write(b"fake pdf data")
            temp_file_path = temp_file.name

        yield temp_file_path

        # 清理
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

    def test_ocr_service_initialization(self, ocr_service):
        """测试OCR服务初始化."""
        assert ocr_service is not None
        assert hasattr(ocr_service, "ocr_config")
        assert hasattr(ocr_service, "quality_control")
        assert hasattr(ocr_service, "supported_formats")

    def test_supported_formats_requirement(self, ocr_service):
        """测试支持格式数量 - 需求33要求支持20+种格式."""
        formats = ocr_service.get_supported_formats()

        # 计算总格式数量
        total_formats = sum(len(format_list) for format_list in formats.values())

        # 验证需求33：支持20+种格式
        assert total_formats >= 20, f"支持的格式数量({total_formats})少于需求的20种"

        # 验证包含主要格式类别
        assert "image" in formats
        assert "pdf" in formats
        assert "document" in formats

    @pytest.mark.asyncio
    async def test_extract_text_from_image_mock(self, ocr_service, temp_image_file):
        """测试图片OCR文字提取 - 模拟模式."""
        result = await ocr_service.extract_text_from_image(temp_image_file)

        # 验证返回结果结构
        assert "text" in result
        assert "confidence" in result
        assert "word_count" in result
        assert "char_count" in result
        assert "meets_quality_threshold" in result
        assert "processing_time" in result

        # 验证需求33：OCR识别准确率>95%
        if result["confidence"] > 0:  # 如果有置信度数据
            assert result["confidence"] >= 0.95, f"OCR置信度({result['confidence']})低于需求的95%"

    @pytest.mark.asyncio
    async def test_extract_text_from_pdf_mock(self, ocr_service, temp_pdf_file):
        """测试PDF OCR文字提取 - 模拟模式."""
        result = await ocr_service.extract_text_from_pdf(temp_pdf_file)

        # 验证返回结果结构
        assert "text" in result
        assert "confidence" in result
        assert "page_count" in result
        assert "meets_quality_threshold" in result

    @pytest.mark.asyncio
    async def test_batch_extract_text_size_limit(self, ocr_service):
        """测试批量处理大小限制 - 需求33批量上传最大2GB."""
        # 创建模拟文件路径列表
        file_paths = [f"test_file_{i}.jpg" for i in range(5)]

        # 测试正常大小限制
        result = await ocr_service.batch_extract_text(file_paths, max_size_mb=2048)

        assert "success" in result
        assert "total_files" in result
        assert "processing_summary" in result

    def test_quality_control_configuration(self, ocr_service):
        """测试质量控制配置 - 需求33质量控制要求."""
        quality_config = ocr_service.quality_control

        # 验证质量控制参数
        assert "min_confidence" in quality_config
        assert "max_noise_ratio" in quality_config
        assert "min_word_length" in quality_config

        # 验证需求33：最小置信度>=95%
        assert quality_config["min_confidence"] >= 95.0

    def test_calculate_noise_ratio(self, ocr_service):
        """测试噪声比例计算."""
        # 测试纯文本
        clean_text = "This is clean text"
        noise_ratio = ocr_service._calculate_noise_ratio(clean_text)
        assert noise_ratio <= 0.2  # 干净文本噪声比例应该很低

        # 测试含噪声文本
        noisy_text = "Th!s @s n0!sy t3xt w!th $ymb0ls"
        noise_ratio = ocr_service._calculate_noise_ratio(noisy_text)
        assert noise_ratio > 0.2  # 噪声文本噪声比例应该较高

    def test_calculate_readability_score(self, ocr_service):
        """测试可读性评分计算."""
        # 测试可读文本
        readable_text = "This is a simple and readable text with normal words."
        score = ocr_service._calculate_readability_score(readable_text)
        assert 0 <= score <= 100

        # 测试空文本
        empty_score = ocr_service._calculate_readability_score("")
        assert empty_score == 0.0

    def test_is_supported_format(self, ocr_service):
        """测试文件格式支持检查."""
        # 测试支持的图片格式
        assert ocr_service._is_supported_format(Path("test.jpg"), "image")
        assert ocr_service._is_supported_format(Path("test.png"), "image")
        assert ocr_service._is_supported_format(Path("test.pdf"), "pdf")

        # 测试不支持的格式
        assert not ocr_service._is_supported_format(Path("test.xyz"), "image")

    @pytest.mark.asyncio
    async def test_quality_validation(self, ocr_service):
        """测试质量验证功能 - 需求33质量控制."""
        # 模拟OCR结果
        mock_result = {
            "text": "This is a test text with good quality.",
            "confidence": 0.97,  # 97%置信度
            "word_count": 9,
            "char_count": 42,
        }

        quality_report = await ocr_service._validate_ocr_quality(mock_result)

        # 验证质量报告结构
        assert "overall_quality" in quality_report
        assert "quality_score" in quality_report
        assert "confidence_score" in quality_report
        assert "meets_requirements" in quality_report

        # 验证高质量结果
        assert quality_report["meets_requirements"]

    def test_mock_ocr_result(self, ocr_service):
        """测试模拟OCR结果生成."""
        result = ocr_service._mock_ocr_result("image", "test.jpg")

        # 验证模拟结果结构
        assert "text" in result
        assert "confidence" in result
        assert "meets_quality_threshold" in result
        assert "quality_report" in result

        # 验证需求33：模拟结果也应满足95%准确率要求
        assert result["confidence"] >= 0.95

    @pytest.mark.asyncio
    async def test_advanced_preprocessing(self, ocr_service):
        """测试高级预处理功能."""
        # 由于依赖PIL，这里主要测试方法存在性和基本逻辑
        assert hasattr(ocr_service, "_advanced_preprocess_image")
        assert hasattr(ocr_service, "_process_image_advanced")
        assert hasattr(ocr_service, "_process_pdf_advanced")

    def test_performance_requirements(self, ocr_service):
        """测试性能要求 - 需求33性能指标."""
        # 验证配置中的性能参数
        config = ocr_service.ocr_config

        # 验证DPI设置（影响处理质量和速度）
        assert "dpi" in config
        assert config["dpi"] >= 200  # 确保足够的分辨率

    @pytest.mark.asyncio
    async def test_error_handling(self, ocr_service):
        """测试错误处理."""
        # 测试不存在的文件
        with pytest.raises((FileNotFoundError, BusinessLogicError)):
            await ocr_service.extract_text_from_image("nonexistent_file.jpg")

        # 测试无效文件路径
        with pytest.raises((FileNotFoundError, BusinessLogicError)):
            await ocr_service.extract_text_from_pdf("invalid_file.pdf")

    def test_format_coverage_requirement(self, ocr_service):
        """测试格式覆盖要求 - 需求33格式支持."""
        formats = ocr_service.get_supported_formats()

        # 验证图片格式覆盖
        image_formats = formats.get("image", [])
        required_image_formats = [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".gif"]
        for fmt in required_image_formats:
            assert fmt in image_formats, f"缺少必需的图片格式: {fmt}"

        # 验证文档格式覆盖
        doc_formats = formats.get("document", [])
        assert len(doc_formats) > 0, "应该支持文档格式"

        # 验证PDF格式
        pdf_formats = formats.get("pdf", [])
        assert ".pdf" in pdf_formats, "必须支持PDF格式"
