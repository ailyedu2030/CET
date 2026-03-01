"""
英语四级学习系统 - Mock服务

提供端到端测试所需的各种Mock服务，包括AI服务、第三方API、外部依赖等。
确保测试的独立性和可重复性。
"""

import random
from datetime import datetime
from typing import Any
from unittest.mock import patch


class MockAIService:
    """Mock AI服务"""

    def __init__(self):
        self.call_count = 0
        self.responses = []

    async def generate_response(self, prompt: str, **kwargs) -> dict[str, Any]:
        """模拟AI响应生成"""
        self.call_count += 1

        # 根据提示词类型生成不同的响应
        if "vocabulary" in prompt.lower():
            response = self._generate_vocabulary_response()
        elif "grammar" in prompt.lower():
            response = self._generate_grammar_response()
        elif "writing" in prompt.lower():
            response = self._generate_writing_response()
        elif "translation" in prompt.lower():
            response = self._generate_translation_response()
        else:
            response = self._generate_general_response()

        self.responses.append(response)
        return response

    def _generate_vocabulary_response(self) -> dict[str, Any]:
        """生成词汇相关响应"""
        return {
            "content": "这个单词的意思是...",
            "explanation": "词汇解释和用法示例",
            "examples": ["Example sentence 1", "Example sentence 2"],
            "difficulty": random.choice(["beginner", "intermediate", "advanced"]),
            "confidence": random.uniform(0.8, 0.95),
        }

    def _generate_grammar_response(self) -> dict[str, Any]:
        """生成语法相关响应"""
        return {
            "content": "这个语法点的解释是...",
            "rule": "语法规则说明",
            "examples": ["Grammar example 1", "Grammar example 2"],
            "common_mistakes": ["常见错误1", "常见错误2"],
            "confidence": random.uniform(0.85, 0.98),
        }

    def _generate_writing_response(self) -> dict[str, Any]:
        """生成写作相关响应"""
        return {
            "content": "写作建议和改进意见",
            "score": random.randint(70, 95),
            "feedback": {
                "strengths": ["语法正确", "词汇丰富"],
                "weaknesses": ["逻辑连贯性", "句式变化"],
                "suggestions": ["建议使用更多连接词", "增加句式多样性"],
            },
            "corrected_text": "修正后的文本内容",
            "confidence": random.uniform(0.75, 0.90),
        }

    def _generate_translation_response(self) -> dict[str, Any]:
        """生成翻译相关响应"""
        return {
            "content": "翻译结果",
            "original_text": "原文",
            "translated_text": "译文",
            "alternative_translations": ["备选翻译1", "备选翻译2"],
            "confidence": random.uniform(0.80, 0.95),
        }

    def _generate_general_response(self) -> dict[str, Any]:
        """生成通用响应"""
        return {
            "content": "AI助手的回复内容",
            "type": "general",
            "confidence": random.uniform(0.70, 0.90),
        }

    def reset(self):
        """重置Mock状态"""
        self.call_count = 0
        self.responses = []


class MockVectorService:
    """Mock向量服务"""

    def __init__(self):
        self.vectors = {}
        self.search_results = []

    async def store_vector(
        self, text: str, vector: list[float], metadata: dict[str, Any]
    ) -> str:
        """模拟向量存储"""
        vector_id = f"vec_{len(self.vectors)}"
        self.vectors[vector_id] = {
            "text": text,
            "vector": vector,
            "metadata": metadata,
            "created_at": datetime.now(),
        }
        return vector_id

    async def search_similar(
        self, query_vector: list[float], limit: int = 10
    ) -> list[dict[str, Any]]:
        """模拟相似度搜索"""
        # 返回模拟的搜索结果
        results = []
        for i in range(min(limit, 5)):
            result = {
                "id": f"result_{i}",
                "text": f"相似内容 {i}",
                "score": random.uniform(0.7, 0.95),
                "metadata": {
                    "type": "vocabulary",
                    "difficulty": random.choice(
                        ["beginner", "intermediate", "advanced"]
                    ),
                },
            }
            results.append(result)

        self.search_results = results
        return results

    async def delete_vector(self, vector_id: str) -> bool:
        """模拟向量删除"""
        if vector_id in self.vectors:
            del self.vectors[vector_id]
            return True
        return False

    def reset(self):
        """重置Mock状态"""
        self.vectors = {}
        self.search_results = []


class MockEmailService:
    """Mock邮件服务"""

    def __init__(self):
        self.sent_emails = []

    async def send_email(
        self, to: str, subject: str, content: str, html_content: str | None = None
    ) -> bool:
        """模拟邮件发送"""
        email = {
            "to": to,
            "subject": subject,
            "content": content,
            "html_content": html_content,
            "sent_at": datetime.now(),
            "status": "sent",
        }
        self.sent_emails.append(email)
        return True

    async def send_verification_email(self, email: str, token: str) -> bool:
        """模拟验证邮件发送"""
        return await self.send_email(
            to=email, subject="邮箱验证", content=f"验证码: {token}"
        )

    async def send_password_reset_email(self, email: str, token: str) -> bool:
        """模拟密码重置邮件发送"""
        return await self.send_email(
            to=email,
            subject="密码重置",
            content=f"重置链接: https://example.com/reset?token={token}",
        )

    def get_sent_emails(self, to: str | None = None) -> list[dict[str, Any]]:
        """获取已发送邮件"""
        if to:
            return [email for email in self.sent_emails if email["to"] == to]
        return self.sent_emails

    def reset(self):
        """重置Mock状态"""
        self.sent_emails = []


class MockFileStorageService:
    """Mock文件存储服务"""

    def __init__(self):
        self.stored_files = {}

    async def upload_file(
        self, file_content: bytes, filename: str, content_type: str
    ) -> str:
        """模拟文件上传"""
        file_id = f"file_{len(self.stored_files)}"
        file_url = f"https://mock-storage.com/{file_id}/{filename}"

        self.stored_files[file_id] = {
            "filename": filename,
            "content_type": content_type,
            "size": len(file_content),
            "url": file_url,
            "uploaded_at": datetime.now(),
        }

        return file_url

    async def delete_file(self, file_url: str) -> bool:
        """模拟文件删除"""
        # 从URL中提取文件ID
        file_id = file_url.split("/")[-2] if "/" in file_url else None
        if file_id and file_id in self.stored_files:
            del self.stored_files[file_id]
            return True
        return False

    async def get_file_info(self, file_url: str) -> dict[str, Any] | None:
        """模拟获取文件信息"""
        file_id = file_url.split("/")[-2] if "/" in file_url else None
        return self.stored_files.get(file_id)

    def reset(self):
        """重置Mock状态"""
        self.stored_files = {}


class MockPaymentService:
    """Mock支付服务"""

    def __init__(self):
        self.transactions = []

    async def create_payment(
        self, amount: float, currency: str = "CNY", description: str = ""
    ) -> dict[str, Any]:
        """模拟创建支付"""
        transaction_id = f"txn_{len(self.transactions)}"

        transaction = {
            "transaction_id": transaction_id,
            "amount": amount,
            "currency": currency,
            "description": description,
            "status": "pending",
            "created_at": datetime.now(),
            "payment_url": f"https://mock-payment.com/pay/{transaction_id}",
        }

        self.transactions.append(transaction)
        return transaction

    async def confirm_payment(self, transaction_id: str) -> bool:
        """模拟确认支付"""
        for transaction in self.transactions:
            if transaction["transaction_id"] == transaction_id:
                transaction["status"] = "completed"
                transaction["completed_at"] = datetime.now()
                return True
        return False

    async def refund_payment(self, transaction_id: str) -> bool:
        """模拟退款"""
        for transaction in self.transactions:
            if transaction["transaction_id"] == transaction_id:
                transaction["status"] = "refunded"
                transaction["refunded_at"] = datetime.now()
                return True
        return False

    def get_transaction(self, transaction_id: str) -> dict[str, Any] | None:
        """获取交易信息"""
        for transaction in self.transactions:
            if transaction["transaction_id"] == transaction_id:
                return transaction
        return None

    def reset(self):
        """重置Mock状态"""
        self.transactions = []


class MockExternalAPIService:
    """Mock外部API服务"""

    def __init__(self):
        self.api_calls = []

    async def translate_text(
        self, text: str, target_lang: str = "zh"
    ) -> dict[str, Any]:
        """模拟翻译API"""
        self.api_calls.append(
            {
                "service": "translate",
                "text": text,
                "target_lang": target_lang,
                "timestamp": datetime.now(),
            }
        )

        return {
            "original_text": text,
            "translated_text": f"翻译结果: {text}",
            "source_lang": "en",
            "target_lang": target_lang,
            "confidence": random.uniform(0.85, 0.98),
        }

    async def get_pronunciation(self, word: str) -> dict[str, Any]:
        """模拟发音API"""
        self.api_calls.append(
            {"service": "pronunciation", "word": word, "timestamp": datetime.now()}
        )

        return {
            "word": word,
            "phonetic": f"/ˈ{word}/",
            "audio_url": f"https://mock-audio.com/{word}.mp3",
            "accent": "american",
        }

    async def check_grammar(self, text: str) -> dict[str, Any]:
        """模拟语法检查API"""
        self.api_calls.append(
            {"service": "grammar_check", "text": text, "timestamp": datetime.now()}
        )

        return {
            "original_text": text,
            "corrected_text": text,  # 假设没有错误
            "errors": [],
            "suggestions": [],
            "score": random.randint(85, 100),
        }

    def get_api_calls(self, service: str | None = None) -> list[dict[str, Any]]:
        """获取API调用记录"""
        if service:
            return [call for call in self.api_calls if call["service"] == service]
        return self.api_calls

    def reset(self):
        """重置Mock状态"""
        self.api_calls = []


# 全局Mock服务实例
mock_ai_service = MockAIService()
mock_vector_service = MockVectorService()
mock_email_service = MockEmailService()
mock_file_storage_service = MockFileStorageService()
mock_payment_service = MockPaymentService()
mock_external_api_service = MockExternalAPIService()


def reset_all_mocks():
    """重置所有Mock服务"""
    mock_ai_service.reset()
    mock_vector_service.reset()
    mock_email_service.reset()
    mock_file_storage_service.reset()
    mock_payment_service.reset()
    mock_external_api_service.reset()


def get_mock_patches() -> list[patch]:
    """获取所有Mock补丁"""
    return [
        patch("app.ai.services.ai_service.ai_service", mock_ai_service),
        patch(
            "app.resources.services.vector_service.vector_service", mock_vector_service
        ),
        patch("app.core.email.email_service", mock_email_service),
        patch("app.core.storage.file_storage_service", mock_file_storage_service),
        patch("app.core.payment.payment_service", mock_payment_service),
        patch("app.core.external_api.external_api_service", mock_external_api_service),
    ]
