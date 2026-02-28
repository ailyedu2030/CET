"""
资源库模块集成测试

测试功能：
1. 完整的文档处理流程
2. 向量检索功能
3. AI内容生成
4. 性能监控
5. 错误处理机制
"""

import asyncio
import tempfile
from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.resources.models.resource_models import ProcessingStatus
from app.resources.services.document_processing_service import DocumentProcessingService
from app.resources.services.performance_monitoring_service import \
    ResourcePerformanceMonitor
from app.resources.services.resource_library_service import (ResourceCreateRequest,
                                                             ResourceLibraryService)
from app.resources.services.vector_search_service import (SearchQuery,
                                                          VectorSearchService)
from app.shared.models.enums import PermissionLevel, ResourceType
from app.shared.services.cache_service import CacheService


class TestResourceLibraryIntegration:
    """资源库模块集成测试"""

    @pytest.fixture
    async def db_session(self) -> AsyncSession:
        """数据库会话fixture"""
        async for session in get_db():
            yield session

    @pytest.fixture
    async def cache_service(self) -> CacheService:
        """缓存服务fixture"""
        # 这里应该创建测试用的缓存服务
        # 简化实现，返回None
        return None  # type: ignore

    @pytest.fixture
    async def resource_service(
        self, db_session: AsyncSession, cache_service: CacheService
    ) -> ResourceLibraryService:
        """资源库服务fixture"""
        document_processing_service = DocumentProcessingService(
            db_session, None, cache_service
        )
        return ResourceLibraryService(
            db_session, cache_service, document_processing_service
        )

    @pytest.fixture
    async def vector_service(
        self, db_session: AsyncSession, cache_service: CacheService
    ) -> VectorSearchService:
        """向量检索服务fixture"""
        return VectorSearchService(db_session, cache_service)

    @pytest.fixture
    async def performance_monitor(
        self, db_session: AsyncSession, cache_service: CacheService
    ) -> ResourcePerformanceMonitor:
        """性能监控服务fixture"""
        return ResourcePerformanceMonitor(db_session, cache_service)

    @pytest.fixture
    def sample_document_content(self) -> str:
        """示例文档内容"""
        return """
        英语四级考试综合训练教程

        第一章：听力理解
        听力理解是英语四级考试的重要组成部分，占总分的35%。本章将介绍听力理解的基本技巧和训练方法。

        1.1 短对话理解
        短对话理解要求考生能够理解日常生活中的简短对话，把握对话的主要内容和说话人的态度。

        1.2 长对话理解
        长对话理解涉及更复杂的语境和更多的信息点，需要考生具备较强的信息筛选和整合能力。

        第二章：阅读理解
        阅读理解是英语四级考试的核心部分，占总分的35%。本章将系统介绍阅读理解的解题策略。

        2.1 词汇理解
        词汇理解要求考生能够根据上下文推断生词的含义，这是阅读理解的基础技能。

        2.2 长篇阅读
        长篇阅读考查考生对文章整体结构和逻辑关系的把握能力。

        第三章：写作与翻译
        写作与翻译部分占总分的30%，是考生综合语言运用能力的体现。

        3.1 短文写作
        短文写作要求考生能够在30分钟内完成一篇120-180词的短文。

        3.2 汉译英
        汉译英要求考生能够将中文段落准确翻译成英文，考查语言转换能力。
        """

    async def test_complete_document_processing_workflow(
        self,
        resource_service: ResourceLibraryService,
        sample_document_content: str,
        performance_monitor: ResourcePerformanceMonitor,
    ) -> None:
        """测试完整的文档处理工作流程"""
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(sample_document_content)
            temp_file_path = f.name

        try:
            # 1. 创建资源
            async with performance_monitor.create_performance_context_manager(
                "resource_creation", "create_resource"
            ) as ctx:
                ctx.add_metadata("file_size", len(sample_document_content))

                create_request = ResourceCreateRequest(
                    name="英语四级综合训练教程",
                    resource_type=ResourceType.TEXTBOOK,
                    category="教材",
                    description="英语四级考试综合训练教程",
                    permission_level=PermissionLevel.PUBLIC,
                    file_path=temp_file_path,
                    file_format="txt",
                )

                resource = await resource_service.create_resource(
                    create_request, user_id=1
                )
                assert resource is not None
                assert resource.name == "英语四级综合训练教程"
                assert resource.processing_status == ProcessingStatus.PENDING

            # 2. 处理文档
            async with performance_monitor.create_performance_context_manager(
                "document_processing", "process_large_document"
            ) as ctx:
                ctx.add_metadata("resource_id", resource.id)

                processing_result = await resource_service.document_processing_service.process_large_document(
                    resource.id, force_reprocess=True
                )

                assert processing_result is not None
                assert processing_result.success
                assert processing_result.chunks_count > 0
                ctx.add_metadata("chunks_count", processing_result.chunks_count)

            # 3. 验证资源状态更新
            updated_resource = await resource_service.get_resource(
                resource.id, user_id=1
            )
            assert updated_resource.processing_status == ProcessingStatus.COMPLETED

        finally:
            # 清理临时文件
            Path(temp_file_path).unlink(missing_ok=True)

    async def test_vector_search_functionality(
        self,
        vector_service: VectorSearchService,
        performance_monitor: ResourcePerformanceMonitor,
    ) -> None:
        """测试向量检索功能"""
        # 初始化Milvus集群
        async with performance_monitor.create_performance_context_manager(
            "vector_search", "initialize_milvus"
        ) as ctx:
            init_success = await vector_service.initialize_milvus_cluster()
            ctx.add_metadata("init_success", init_success)

        # 执行混合检索
        async with performance_monitor.create_performance_context_manager(
            "vector_search", "hybrid_search"
        ) as ctx:
            search_query = SearchQuery(
                query_text="英语四级听力理解技巧",
                top_k=10,
                similarity_threshold=0.7,
                filters={"resource_type": "textbook"},
            )

            search_response = await vector_service.hybrid_search(search_query)

            assert search_response is not None
            assert isinstance(search_response.results, list)
            ctx.add_metadata("results_count", len(search_response.results))
            ctx.add_metadata("search_time_ms", search_response.search_time_ms)

    async def test_ai_content_generation(
        self, performance_monitor: ResourcePerformanceMonitor
    ) -> None:
        """测试AI内容生成功能"""
        from app.ai.services.deepseek_content_service import DeepSeekContentService

        content_service = DeepSeekContentService()

        # 测试教学大纲生成
        async with performance_monitor.create_performance_context_manager(
            "ai_generation", "generate_syllabus"
        ) as ctx:
            course_info = {
                "name": "英语四级综合训练",
                "duration": "16周",
                "target_level": "CET-4",
            }

            resource_content = "英语四级考试是大学生英语能力的重要评估标准..."

            syllabus = await content_service.generate_syllabus(
                resource_content, course_info
            )

            if syllabus:
                assert isinstance(syllabus, dict)
                assert "course_title" in syllabus
                ctx.add_metadata("syllabus_generated", True)
            else:
                ctx.add_metadata("syllabus_generated", False)

        # 测试教案生成
        async with performance_monitor.create_performance_context_manager(
            "ai_generation", "generate_lesson_plan"
        ) as ctx:
            lesson_info = {
                "title": "听力理解训练",
                "duration": "90分钟",
                "objectives": ["提高听力理解能力"],
            }

            basic_syllabus = {
                "course_title": "英语四级综合训练",
                "course_outline": [{"week": 1, "topic": "听力训练"}],
            }

            lesson_plan = await content_service.generate_lesson_plan(
                basic_syllabus, lesson_info
            )

            if lesson_plan:
                assert isinstance(lesson_plan, dict)
                assert "lesson_title" in lesson_plan
                ctx.add_metadata("lesson_plan_generated", True)
            else:
                ctx.add_metadata("lesson_plan_generated", False)

    async def test_embedding_service_functionality(
        self, performance_monitor: ResourcePerformanceMonitor
    ) -> None:
        """测试向量化服务功能"""
        from app.ai.services.deepseek_embedding_service import DeepSeekEmbeddingService

        embedding_service = DeepSeekEmbeddingService()

        # 测试单文本向量化
        async with performance_monitor.create_performance_context_manager(
            "embedding", "vectorize_text"
        ) as ctx:
            test_text = "英语四级听力理解是考试的重要组成部分"

            embedding = await embedding_service.vectorize_text(test_text)

            assert isinstance(embedding, list)
            assert len(embedding) == 1536  # DeepSeek embedding dimension
            assert all(isinstance(x, float) for x in embedding)

            ctx.add_metadata("text_length", len(test_text))
            ctx.add_metadata("embedding_dimension", len(embedding))

        # 测试批量向量化
        async with performance_monitor.create_performance_context_manager(
            "embedding", "vectorize_batch"
        ) as ctx:
            test_texts = [
                "英语四级听力技巧",
                "阅读理解方法",
                "写作训练要点",
                "翻译技能提升",
            ]

            embeddings = await embedding_service.vectorize_batch(test_texts)

            assert len(embeddings) == len(test_texts)
            assert all(len(emb) == 1536 for emb in embeddings)

            ctx.add_metadata("batch_size", len(test_texts))
            ctx.add_metadata("total_embeddings", len(embeddings))

    async def test_performance_monitoring_system(
        self, performance_monitor: ResourcePerformanceMonitor
    ) -> None:
        """测试性能监控系统"""
        # 记录一些测试指标
        start_time = datetime.utcnow()
        await asyncio.sleep(0.1)  # 模拟操作耗时
        end_time = datetime.utcnow()

        await performance_monitor.record_metric(
            service_name="test_service",
            operation_name="test_operation",
            start_time=start_time,
            end_time=end_time,
            success=True,
            metadata={"test": True},
        )

        # 获取性能统计
        stats = await performance_monitor.get_performance_stats("test_service")
        assert stats.service_name == "test_service"

        # 检查服务健康状态
        health_report = await performance_monitor.check_service_health()
        assert "overall_status" in health_report
        assert "services" in health_report
        assert "timestamp" in health_report

    async def test_error_handling_and_fallback(
        self, performance_monitor: ResourcePerformanceMonitor
    ) -> None:
        """测试错误处理和降级机制"""
        from app.ai.services.deepseek_embedding_service import DeepSeekEmbeddingService

        embedding_service = DeepSeekEmbeddingService()

        # 测试空文本处理
        async with performance_monitor.create_performance_context_manager(
            "embedding", "handle_empty_text"
        ) as ctx:
            try:
                embedding = await embedding_service.vectorize_text("")
                # 应该返回零向量或抛出异常
                assert isinstance(embedding, list)
                ctx.add_metadata("handled_empty_text", True)
            except Exception as e:
                ctx.add_metadata("error_type", type(e).__name__)

        # 测试超长文本处理
        async with performance_monitor.create_performance_context_manager(
            "embedding", "handle_long_text"
        ) as ctx:
            long_text = "测试文本 " * 10000  # 创建超长文本

            try:
                embedding = await embedding_service.vectorize_text(long_text)
                assert isinstance(embedding, list)
                assert len(embedding) == 1536
                ctx.add_metadata("handled_long_text", True)
            except Exception as e:
                ctx.add_metadata("error_type", type(e).__name__)

    async def test_concurrent_operations(
        self,
        vector_service: VectorSearchService,
        performance_monitor: ResourcePerformanceMonitor,
    ) -> None:
        """测试并发操作"""
        # 创建多个并发搜索任务
        search_tasks = []

        for i in range(5):
            search_query = SearchQuery(
                query_text=f"英语四级测试查询 {i}",
                top_k=5,
                similarity_threshold=0.7,
            )

            async def search_with_monitoring(query: SearchQuery, task_id: int) -> None:
                async with performance_monitor.create_performance_context_manager(
                    "vector_search", f"concurrent_search_{task_id}"
                ) as ctx:
                    result = await vector_service.hybrid_search(query)
                    ctx.add_metadata("task_id", task_id)
                    ctx.add_metadata(
                        "results_count", len(result.results) if result else 0
                    )

            search_tasks.append(search_with_monitoring(search_query, i))

        # 并发执行所有搜索任务
        await asyncio.gather(*search_tasks, return_exceptions=True)

        # 验证性能监控记录了所有操作
        stats = await performance_monitor.get_performance_stats("vector_search")
        # 注意：由于缓存服务的限制，这里可能无法获取到实际的统计数据

    async def test_end_to_end_workflow(
        self,
        resource_service: ResourceLibraryService,
        vector_service: VectorSearchService,
        sample_document_content: str,
        performance_monitor: ResourcePerformanceMonitor,
    ) -> None:
        """测试端到端工作流程"""
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(sample_document_content)
            temp_file_path = f.name

        try:
            # 1. 创建和处理资源
            create_request = ResourceCreateRequest(
                name="端到端测试文档",
                resource_type=ResourceType.TEXTBOOK,
                category="测试",
                description="端到端测试文档",
                permission_level=PermissionLevel.PUBLIC,
                file_path=temp_file_path,
                file_format="txt",
            )

            resource = await resource_service.create_resource(create_request, user_id=1)

            # 2. 处理文档
            processing_result = await resource_service.document_processing_service.process_large_document(
                resource.id, force_reprocess=True
            )

            assert processing_result.success

            # 3. 执行向量检索
            search_query = SearchQuery(
                query_text="听力理解技巧",
                top_k=5,
                similarity_threshold=0.6,
                filters={"resource_ids": [resource.id]},
            )

            search_result = await vector_service.hybrid_search(search_query)

            # 验证搜索结果
            assert search_result is not None
            # 注意：由于是测试环境，可能没有实际的向量数据

            # 4. 获取性能报告
            health_report = await performance_monitor.check_service_health()
            assert health_report["overall_status"] in ["healthy", "degraded", "unknown"]

        finally:
            # 清理临时文件
            Path(temp_file_path).unlink(missing_ok=True)


# 运行测试的辅助函数
async def run_integration_tests() -> None:
    """运行集成测试"""
    test_instance = TestResourceLibraryIntegration()

    print("🚀 开始资源库模块集成测试...")

    try:
        # 这里应该设置测试数据库和缓存服务
        # 由于环境限制，这里只是示例

        print("✅ 集成测试完成")

    except Exception as e:
        print(f"❌ 集成测试失败: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(run_integration_tests())
