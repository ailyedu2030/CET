"""语义检索服务 - 基于AI的智能语义搜索和理解."""

import logging
from datetime import datetime
from typing import Any

from app.ai.services.deepseek_service import DeepSeekService
from app.resources.services.vector_service import VectorService
from app.shared.services.cache_service import CacheService

logger = logging.getLogger(__name__)


class SemanticSearchService:
    """语义检索服务 - 提供智能语义搜索和内容理解功能."""

    def __init__(self, cache_service: CacheService | None = None) -> None:
        """初始化语义搜索服务."""
        self.cache_service = cache_service
        self.vector_service = VectorService(cache_service)
        self.deepseek_service = DeepSeekService()

        # 语义搜索配置
        self.search_config = {
            "max_query_expansion": 5,  # 最大查询扩展数量
            "semantic_threshold": 0.75,  # 语义相关性阈值
            "context_window": 3,  # 上下文窗口大小
            "rerank_top_k": 50,  # 重排序候选数量
            "final_top_k": 10,  # 最终返回数量
        }

        # 查询类型配置
        self.query_types = {
            "factual": {
                "name": "事实查询",
                "description": "查找具体事实和信息",
                "weight": 1.0,
            },
            "conceptual": {
                "name": "概念查询",
                "description": "查找概念解释和定义",
                "weight": 0.9,
            },
            "procedural": {
                "name": "过程查询",
                "description": "查找操作步骤和方法",
                "weight": 0.8,
            },
            "comparative": {
                "name": "比较查询",
                "description": "查找比较和对比信息",
                "weight": 0.85,
            },
        }

    async def semantic_search(
        self, query: str, filters: dict[str, Any] | None = None, top_k: int = 10
    ) -> dict[str, Any]:
        """执行语义搜索."""
        try:
            start_time = datetime.now()

            # 1. 查询理解和分析
            query_analysis = await self._analyze_query(query)

            # 2. 查询扩展
            expanded_queries = await self._expand_query(query, query_analysis)

            # 3. 多策略检索
            search_results = await self._multi_strategy_search(
                query, expanded_queries, filters, top_k
            )

            # 4. 语义重排序
            reranked_results = await self._semantic_rerank(query, search_results, query_analysis)

            # 5. 结果后处理
            final_results = await self._post_process_results(reranked_results, query_analysis)

            # 6. 生成搜索摘要
            search_summary = await self._generate_search_summary(
                query, final_results, query_analysis
            )

            end_time = datetime.now()
            search_time = (end_time - start_time).total_seconds()

            return {
                "query": query,
                "query_analysis": query_analysis,
                "results": final_results[:top_k],
                "total_results": len(search_results),
                "search_summary": search_summary,
                "search_time": search_time,
                "timestamp": end_time,
            }

        except Exception as e:
            logger.error(f"Semantic search failed: {str(e)}")
            return {
                "query": query,
                "results": [],
                "error": str(e),
                "timestamp": datetime.now(),
            }

    async def _analyze_query(self, query: str) -> dict[str, Any]:
        """分析查询意图和类型."""
        try:
            # 构建分析提示
            analysis_prompt = f"""
            分析以下查询的语义特征：
            查询：{query}

            请分析：
            1. 查询类型（factual/conceptual/procedural/comparative）
            2. 关键概念和实体
            3. 查询意图
            4. 重要关键词
            5. 语义复杂度（1-5分）

            返回JSON格式：
            {{
                "query_type": "类型",
                "key_concepts": ["概念1", "概念2"],
                "intent": "查询意图描述",
                "keywords": ["关键词1", "关键词2"],
                "complexity": 数字,
                "confidence": 置信度
            }}
            """

            success, response, error = await self.deepseek_service.generate_completion(
                prompt=analysis_prompt,
                temperature=0.1,
                max_tokens=500,
                user_id=None,
                task_type="query_analysis",
            )

            if success and response:
                try:
                    import json

                    content = (
                        response.get("choices", [{}])[0].get("message", {}).get("content", "{}")
                    )
                    analysis = json.loads(content)

                    # 验证和补充分析结果
                    analysis.setdefault("query_type", "factual")
                    analysis.setdefault("key_concepts", [])
                    analysis.setdefault("intent", "信息查询")
                    analysis.setdefault("keywords", query.split())
                    analysis.setdefault("complexity", 3)
                    analysis.setdefault("confidence", 0.8)

                    return dict(analysis)
                except json.JSONDecodeError:
                    pass

            # 回退到简单分析
            return self._simple_query_analysis(query)

        except Exception as e:
            logger.error(f"Query analysis failed: {str(e)}")
            return self._simple_query_analysis(query)

    def _simple_query_analysis(self, query: str) -> dict[str, Any]:
        """简单查询分析（回退方案）."""
        words = query.split()

        # 简单的查询类型判断
        query_type = "factual"
        if any(word in query.lower() for word in ["什么是", "定义", "概念"]):
            query_type = "conceptual"
        elif any(word in query.lower() for word in ["如何", "怎么", "步骤"]):
            query_type = "procedural"
        elif any(word in query.lower() for word in ["比较", "区别", "对比"]):
            query_type = "comparative"

        return {
            "query_type": query_type,
            "key_concepts": [word for word in words if len(word) > 2],
            "intent": "信息查询",
            "keywords": words,
            "complexity": min(len(words), 5),
            "confidence": 0.6,
        }

    async def _expand_query(self, original_query: str, query_analysis: dict[str, Any]) -> list[str]:
        """扩展查询以提高召回率."""
        try:
            expanded_queries = [original_query]

            # 基于关键概念扩展
            key_concepts = query_analysis.get("key_concepts", [])
            for concept in key_concepts[:3]:  # 限制扩展数量
                expanded_queries.append(f"{concept} 相关内容")

            # 基于查询类型扩展
            query_type = query_analysis.get("query_type", "factual")
            if query_type == "conceptual":
                expanded_queries.append(f"{original_query} 定义 解释")
            elif query_type == "procedural":
                expanded_queries.append(f"{original_query} 方法 步骤")
            elif query_type == "comparative":
                expanded_queries.append(f"{original_query} 比较 区别")

            # 使用AI生成同义查询
            if len(expanded_queries) < self.search_config["max_query_expansion"]:
                ai_expansions = await self._ai_query_expansion(original_query)
                expanded_queries.extend(ai_expansions)

            return expanded_queries[: self.search_config["max_query_expansion"]]

        except Exception as e:
            logger.error(f"Query expansion failed: {str(e)}")
            return [original_query]

    async def _ai_query_expansion(self, query: str) -> list[str]:
        """使用AI生成查询扩展."""
        try:
            expansion_prompt = f"""
            为以下查询生成2-3个语义相似的查询变体：
            原查询：{query}

            要求：
            1. 保持原意不变
            2. 使用不同的表达方式
            3. 每行一个查询

            示例：
            原查询：机器学习算法
            变体1：人工智能算法
            变体2：ML算法原理
            变体3：机器学习方法
            """

            success, response, error = await self.deepseek_service.generate_completion(
                prompt=expansion_prompt,
                temperature=0.3,
                max_tokens=200,
                user_id=None,
                task_type="query_expansion",
            )

            if success and response:
                content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
                lines = [line.strip() for line in content.split("\n") if line.strip()]

                # 提取变体查询
                expansions = []
                for line in lines:
                    if "变体" in line and "：" in line:
                        expansion = line.split("：", 1)[1].strip()
                        if expansion and expansion != query:
                            expansions.append(expansion)

                return expansions[:3]

            return []

        except Exception as e:
            logger.error(f"AI query expansion failed: {str(e)}")
            return []

    async def _multi_strategy_search(
        self,
        original_query: str,
        expanded_queries: list[str],
        filters: dict[str, Any] | None,
        top_k: int,
    ) -> list[dict[str, Any]]:
        """多策略检索."""
        try:
            all_results = []

            # 1. 向量检索（主要策略）
            vector_results = await self.vector_service.search_similar_vectors(
                original_query, top_k=top_k * 2, filters=filters
            )
            for result in vector_results:
                result["search_strategy"] = "vector"
                result["strategy_weight"] = 1.0
            all_results.extend(vector_results)

            # 2. 扩展查询检索
            for i, expanded_query in enumerate(expanded_queries[1:], 1):
                expanded_results = await self.vector_service.search_similar_vectors(
                    expanded_query, top_k=top_k, filters=filters
                )
                for result in expanded_results:
                    result["search_strategy"] = f"expanded_{i}"
                    result["strategy_weight"] = 0.8 / i  # 权重递减
                all_results.extend(expanded_results)

            # 3. 去重
            unique_results = self._deduplicate_results(all_results)

            logger.info(
                f"Multi-strategy search completed: "
                f"total_results={len(all_results)}, unique_results={len(unique_results)}"
            )

            return unique_results

        except Exception as e:
            logger.error(f"Multi-strategy search failed: {str(e)}")
            return []

    def _deduplicate_results(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """去重搜索结果."""
        seen_ids = set()
        unique_results = []

        for result in results:
            result_id = (result.get("document_id"), result.get("chunk_id"))
            if result_id not in seen_ids:
                seen_ids.add(result_id)
                unique_results.append(result)

        return unique_results

    async def _semantic_rerank(
        self, query: str, results: list[dict[str, Any]], query_analysis: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """语义重排序."""
        try:
            if not results:
                return results

            # 限制重排序的结果数量
            rerank_candidates = results[: self.search_config["rerank_top_k"]]

            # 为每个结果计算语义相关性分数
            for result in rerank_candidates:
                content = result.get("content", "")

                # 计算语义相关性
                semantic_score = await self._calculate_semantic_relevance(
                    query, content, query_analysis
                )

                # 综合分数计算
                vector_score = result.get("similarity_score", 0.0)
                strategy_weight = result.get("strategy_weight", 1.0)

                final_score = vector_score * 0.4 + semantic_score * 0.5 + strategy_weight * 0.1

                result["semantic_score"] = semantic_score
                result["final_score"] = final_score

            # 按最终分数排序
            rerank_candidates.sort(key=lambda x: x.get("final_score", 0), reverse=True)

            logger.info(f"Semantic reranking completed: {len(rerank_candidates)} results")
            return rerank_candidates

        except Exception as e:
            logger.error(f"Semantic reranking failed: {str(e)}")
            return results

    async def _calculate_semantic_relevance(
        self, query: str, content: str, query_analysis: dict[str, Any]
    ) -> float:
        """计算语义相关性分数."""
        try:
            # 简化的语义相关性计算
            query_keywords = query_analysis.get("keywords", [])
            content_lower = content.lower()
            query_lower = query.lower()

            # 关键词匹配分数
            keyword_matches = sum(
                1 for keyword in query_keywords if keyword.lower() in content_lower
            )
            keyword_score = keyword_matches / max(len(query_keywords), 1)

            # 查询文本匹配分数
            query_match_score = 1.0 if query_lower in content_lower else 0.0

            # 长度惩罚（避免过短或过长的内容）
            content_length = len(content)
            length_penalty = 1.0
            if content_length < 50:
                length_penalty = 0.8
            elif content_length > 2000:
                length_penalty = 0.9

            # 综合分数
            semantic_score = (keyword_score * 0.4 + query_match_score * 0.6) * length_penalty

            return min(semantic_score, 1.0)

        except Exception as e:
            logger.error(f"Semantic relevance calculation failed: {str(e)}")
            return 0.5

    async def _post_process_results(
        self, results: list[dict[str, Any]], query_analysis: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """结果后处理."""
        try:
            processed_results = []

            for result in results:
                # 生成结果摘要
                content = result.get("content", "")
                summary = await self._generate_result_summary(content, query_analysis)

                # 添加处理后的字段
                processed_result = result.copy()
                processed_result.update(
                    {
                        "summary": summary,
                        "relevance_explanation": self._explain_relevance(result, query_analysis),
                        "processed_at": datetime.now(),
                    }
                )

                processed_results.append(processed_result)

            return processed_results

        except Exception as e:
            logger.error(f"Result post-processing failed: {str(e)}")
            return results

    async def _generate_result_summary(self, content: str, query_analysis: dict[str, Any]) -> str:
        """生成结果摘要."""
        try:
            # 简化的摘要生成
            if len(content) <= 200:
                return content

            # 提取包含关键词的句子
            keywords = query_analysis.get("keywords", [])
            sentences = content.split("。")

            relevant_sentences = []
            for sentence in sentences:
                if any(keyword.lower() in sentence.lower() for keyword in keywords):
                    relevant_sentences.append(sentence.strip())
                    if len(relevant_sentences) >= 2:
                        break

            if relevant_sentences:
                summary = "。".join(relevant_sentences) + "。"
                return summary[:200] + "..." if len(summary) > 200 else summary

            # 回退到前200个字符
            return content[:200] + "..."

        except Exception as e:
            logger.error(f"Summary generation failed: {str(e)}")
            return content[:200] + "..."

    def _explain_relevance(self, result: dict[str, Any], query_analysis: dict[str, Any]) -> str:
        """解释相关性."""
        try:
            semantic_score = result.get("semantic_score", 0.0)
            search_strategy = result.get("search_strategy", "unknown")

            if semantic_score > 0.8:
                return f"高度相关（{search_strategy}检索）"
            elif semantic_score > 0.6:
                return f"相关（{search_strategy}检索）"
            else:
                return f"可能相关（{search_strategy}检索）"

        except Exception as e:
            logger.error(f"Relevance explanation failed: {str(e)}")
            return "相关性未知"

    async def _generate_search_summary(
        self, query: str, results: list[dict[str, Any]], query_analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """生成搜索摘要."""
        try:
            return {
                "total_results": len(results),
                "query_type": query_analysis.get("query_type", "unknown"),
                "avg_relevance": sum(r.get("semantic_score", 0) for r in results)
                / max(len(results), 1),
                "search_strategies": list({r.get("search_strategy", "unknown") for r in results}),
                "has_high_quality_results": any(r.get("semantic_score", 0) > 0.8 for r in results),
            }

        except Exception as e:
            logger.error(f"Search summary generation failed: {str(e)}")
            return {"total_results": len(results), "error": str(e)}
