#!/usr/bin/env python3
"""
智能体命令模板系统
为多智能体协作提供标准化的命令模板和工作流程
"""

from dataclasses import dataclass
from enum import Enum


class AgentRole(Enum):
    BACKEND = "backend"
    FRONTEND = "frontend"
    DEVOPS = "devops"
    QA = "qa"
    COORDINATOR = "coordinator"
    AI_SPECIALIST = "ai_specialist"  # 专门负责AI集成和算法实现
    TRAINING_SPECIALIST = "training_specialist"  # 专门负责训练系统实现
    API_SPECIALIST = "api_specialist"  # 专门负责API设计和实现


class TaskPhase(Enum):
    PHASE_1 = "强制检查清单执行"
    PHASE_2 = "需求深度分析"
    PHASE_3 = "现状全面评估"
    PHASE_4 = "实现方案制定"
    PHASE_5 = "代码实现与验证"


@dataclass
class CommandTemplate:
    """命令模板基类"""

    name: str
    description: str
    phase: TaskPhase
    agent_role: AgentRole
    commands: list[str]
    checklist: list[str]
    success_criteria: list[str]
    estimated_hours: int


class AgentTemplateManager:
    """智能体模板管理器"""

    def __init__(self: "AgentTemplateManager") -> None:
        self.templates = self._initialize_templates()

    def _initialize_templates(self: "AgentTemplateManager") -> dict[str, CommandTemplate]:
        """初始化所有命令模板"""
        templates = {}

        # 阶段1：强制检查清单模板
        templates["phase1_check"] = CommandTemplate(
            name="阶段1：强制检查清单执行",
            description="确保任务开始前的所有必要检查都已完成，严格按照需求文档和技术文档执行",
            phase=TaskPhase.PHASE_1,
            agent_role=AgentRole.COORDINATOR,
            commands=[
                "view .kiro/specs/cet4-learning-system/requirements.md --search 需求{requirement_id}",
                "extract_requirement_details_from_requirements_md {requirement_id}",
                "view .kiro/specs/cet4-learning-system/design.md --search 需求{requirement_id}",
                "extract_technical_architecture_from_design_md {requirement_id}",
                "codebase_retrieval_existing_implementation {requirement_id}",
                "verify_requirements_vs_design_consistency {requirement_id}",
                "confirm_frontend_backend_scope_with_user {requirement_id}",
                "report_implementation_gaps_and_uncertainties {requirement_id}",
            ],
            checklist=[
                "需求文档解析：从requirements.md精确提取需求{requirement_id}的验收标准",
                "技术文档解析：从design.md提取对应的技术架构和实现要求",
                "现有代码检查：使用codebase-retrieval全面搜索相关现有实现",
                "前后端范围确认：明确前端React组件和后端FastAPI接口的具体实现范围",
                "文档一致性验证：确保requirements.md和design.md对该需求的描述一致",
                "实现差距识别：识别现有实现与需求文档要求之间的具体差距",
                "用户确认：获得前后端具体实现方案的明确确认",
                "不确定性报告：向用户报告任何技术实现上的模糊之处并获得澄清",
            ],
            success_criteria=[
                "需求验收标准100%明确提取",
                "技术架构要求100%明确提取",
                "现有实现状态100%清楚",
                "前后端实现范围100%确认",
                "文档一致性100%验证",
                "实现差距100%识别",
                "用户确认100%获得",
                "所有不确定性100%澄清",
            ],
            estimated_hours=3,
        )

        # 阶段2：需求深度分析模板
        templates["phase2_analysis"] = CommandTemplate(
            name="阶段2：需求深度分析",
            description="基于需求文档和技术文档深入分析所有实现细节",
            phase=TaskPhase.PHASE_2,
            agent_role=AgentRole.COORDINATOR,
            commands=[
                "parse_requirement_acceptance_criteria {requirement_id}",
                "extract_frontend_requirements_from_docs {requirement_id}",
                "extract_backend_requirements_from_docs {requirement_id}",
                "identify_api_endpoints_from_design {requirement_id}",
                "identify_database_models_from_design {requirement_id}",
                "identify_react_components_from_design {requirement_id}",
                "map_requirement_to_technical_stack {requirement_id}",
                "define_implementation_priorities {requirement_id}",
            ],
            checklist=[
                "验收标准解析：逐条解析requirements.md中的WHEN-THEN验收标准",
                "前端需求提取：从文档中提取React组件、页面、路由的具体要求",
                "后端需求提取：从文档中提取FastAPI接口、服务类、数据模型的具体要求",
                "API接口设计：基于design.md确定需要实现的REST API端点",
                "数据模型设计：基于design.md确定需要的数据库表和字段",
                "组件架构设计：基于design.md确定需要的React组件结构",
                "技术栈映射：确保使用design.md指定的技术栈（FastAPI+React+PostgreSQL+Redis）",
                "实现优先级：根据验收标准的重要性确定实现优先级",
            ],
            success_criteria=[
                "验收标准100%解析完成",
                "前端实现要求100%明确",
                "后端实现要求100%明确",
                "API接口设计100%完成",
                "数据模型设计100%完成",
                "组件架构设计100%完成",
                "技术栈100%符合设计文档",
                "实现优先级100%确定",
            ],
            estimated_hours=4,
        )

        # 阶段3：现状评估模板
        templates["phase3_assessment"] = CommandTemplate(
            name="阶段3：现状全面评估",
            description="全面评估当前实现状态，对照需求文档验证实现完整性",
            phase=TaskPhase.PHASE_3,
            agent_role=AgentRole.COORDINATOR,
            commands=[
                "codebase_retrieval_comprehensive_search {requirement_id}",
                "assess_frontend_components_vs_requirements {requirement_id}",
                "assess_backend_services_vs_requirements {requirement_id}",
                "assess_api_endpoints_vs_requirements {requirement_id}",
                "assess_database_models_vs_requirements {requirement_id}",
                "verify_integration_completeness {requirement_id}",
                "identify_implementation_gaps {requirement_id}",
                "validate_against_acceptance_criteria {requirement_id}",
            ],
            checklist=[
                "全面代码搜索：使用codebase-retrieval搜索所有相关现有实现",
                "前端实现评估：检查React组件、页面、路由是否满足需求文档要求",
                "后端实现评估：检查FastAPI端点、服务类、业务逻辑是否满足需求文档要求",
                "API接口评估：验证现有API端点是否覆盖需求文档中的所有功能点",
                "数据模型评估：验证数据库表结构是否支持需求文档中的所有数据需求",
                "集成状态评估：检查前后端集成是否完整，数据流是否符合设计文档",
                "实现差距识别：对照验收标准识别缺失或不完整的功能点",
                "验收标准验证：逐条验证现有实现是否满足requirements.md中的验收标准",
                "测试覆盖评估：检查现有功能的测试覆盖情况",
            ],
            success_criteria=[
                "现有实现100%识别和评估",
                "前端实现完整性100%评估",
                "后端实现完整性100%评估",
                "API接口覆盖率100%评估",
                "数据模型完整性100%评估",
                "集成状态100%评估",
                "实现差距100%识别",
                "验收标准100%验证",
                "测试覆盖100%评估",
            ],
            estimated_hours=5,
        )

        # 阶段4：方案制定模板
        templates["phase4_planning"] = CommandTemplate(
            name="阶段4：实现方案制定",
            description="基于需求文档和技术文档制定精确的实现方案",
            phase=TaskPhase.PHASE_4,
            agent_role=AgentRole.COORDINATOR,
            commands=[
                "design_frontend_implementation_plan {requirement_id}",
                "design_backend_implementation_plan {requirement_id}",
                "design_api_endpoints_specification {requirement_id}",
                "design_database_schema_changes {requirement_id}",
                "plan_existing_code_modifications {requirement_id}",
                "plan_new_code_creation {requirement_id}",
                "ensure_design_document_compliance {requirement_id}",
                "create_implementation_roadmap {requirement_id}",
            ],
            checklist=[
                "前端实现方案：基于需求文档设计React组件、页面、路由的具体实现方案",
                "后端实现方案：基于需求文档设计FastAPI端点、服务类、业务逻辑的具体实现方案",
                "API接口规范：根据需求文档设计REST API的详细规范（路径、方法、参数、响应）",
                "数据库设计：根据需求文档设计数据库表结构、字段、索引、约束",
                "现有代码修改：制定对现有代码的最小化修改方案",
                "新代码创建：仅在必要时创建新文件，严格避免重复功能",
                "设计文档合规：确保所有方案符合design.md的技术架构要求",
                "实现路线图：制定详细的实现步骤和优先级",
                "质量标准：确保方案满足TypeScript类型安全、ESLint规则等质量要求",
            ],
            success_criteria=[
                "前端实现方案100%完整",
                "后端实现方案100%完整",
                "API接口规范100%详细",
                "数据库设计100%完整",
                "现有代码修改方案100%明确",
                "新代码创建100%必要且无重复",
                "设计文档100%合规",
                "实现路线图100%可执行",
                "质量标准100%满足",
            ],
            estimated_hours=4,
        )

        # 阶段5：实现验证模板
        templates["phase5_implementation"] = CommandTemplate(
            name="阶段5：代码实现与验证",
            description="严格按照需求文档和技术文档实现前后端功能并验证",
            phase=TaskPhase.PHASE_5,
            agent_role=AgentRole.COORDINATOR,
            commands=[
                "implement_frontend_components {requirement_id}",
                "implement_backend_services {requirement_id}",
                "implement_api_endpoints {requirement_id}",
                "implement_database_models {requirement_id}",
                "integrate_frontend_backend {requirement_id}",
                "run_quality_checks {requirement_id}",
                "validate_against_acceptance_criteria {requirement_id}",
                "run_integration_tests {requirement_id}",
            ],
            checklist=[
                "前端组件实现：根据需求文档实现所有必需的React组件和页面",
                "后端服务实现：根据需求文档实现所有必需的FastAPI服务和业务逻辑",
                "API接口实现：实现所有需求文档要求的REST API端点",
                "数据模型实现：实现所有需求文档要求的数据库表和字段",
                "前后端集成：确保前端和后端完全集成，数据流正确",
                "代码质量检查：运行TypeScript编译、ESLint检查、Python类型检查",
                "功能验证：逐条验证是否满足requirements.md中的所有验收标准",
                "集成测试：运行端到端测试确保功能完整性",
                "性能验证：验证是否满足设计文档中的性能要求",
                "用户体验验证：确保前端界面符合设计文档的用户体验要求",
            ],
            success_criteria=[
                "前端组件100%实现并符合需求",
                "后端服务100%实现并符合需求",
                "API接口100%实现并符合需求",
                "数据模型100%实现并符合需求",
                "前后端100%集成成功",
                "代码质量100%达标（零错误）",
                "验收标准100%满足",
                "集成测试100%通过",
                "性能要求100%满足",
                "用户体验100%符合设计",
            ],
            estimated_hours=8,
        )

        # 现有代码检查模板 - 在任何实现前强制执行
        templates["existing_code_check"] = CommandTemplate(
            name="现有代码检查",
            description="强制检查现有实现，严格按照需求文档验证实现完整性",
            phase=TaskPhase.PHASE_3,
            agent_role=AgentRole.COORDINATOR,
            commands=[
                "codebase_retrieval_requirement_specific {requirement_id}",
                "search_frontend_components_for_requirement {requirement_id}",
                "search_backend_services_for_requirement {requirement_id}",
                "search_api_endpoints_for_requirement {requirement_id}",
                "search_database_models_for_requirement {requirement_id}",
                "validate_existing_vs_requirements {requirement_id}",
                "identify_implementation_completeness {requirement_id}",
            ],
            checklist=[
                "需求特定搜索：使用codebase-retrieval搜索与需求{requirement_id}相关的所有现有实现",
                "前端组件搜索：搜索现有React组件是否已实现需求文档要求的功能",
                "后端服务搜索：搜索现有FastAPI服务是否已实现需求文档要求的功能",
                "API接口搜索：搜索现有API端点是否已覆盖需求文档要求的接口",
                "数据模型搜索：搜索现有数据库模型是否已支持需求文档要求的数据",
                "需求对照验证：将现有实现与requirements.md中的验收标准逐条对照",
                "完整性评估：评估现有实现是否已100%满足需求文档要求",
                "差距识别：识别现有实现与需求文档要求之间的具体差距",
            ],
            success_criteria=[
                "需求相关代码100%识别",
                "前端实现完整性100%评估",
                "后端实现完整性100%评估",
                "API接口覆盖率100%评估",
                "数据模型完整性100%评估",
                "需求满足度100%验证",
                "实现差距100%识别",
                "重复开发100%避免",
            ],
            estimated_hours=3,
        )

        # 前端实现专用模板
        templates["frontend_implementation"] = CommandTemplate(
            name="前端实现",
            description="严格按照需求文档实现React前端组件和页面",
            phase=TaskPhase.PHASE_5,
            agent_role=AgentRole.FRONTEND,
            commands=[
                "analyze_frontend_requirements_from_docs {requirement_id}",
                "design_react_component_structure {requirement_id}",
                "implement_react_components {requirement_id}",
                "implement_react_pages {requirement_id}",
                "implement_api_integration {requirement_id}",
                "implement_state_management {requirement_id}",
                "implement_routing {requirement_id}",
                "run_frontend_quality_checks {requirement_id}",
            ],
            checklist=[
                "需求分析：从requirements.md提取前端相关的具体实现要求",
                "组件设计：设计符合需求的React组件结构和层次",
                "组件实现：实现所有需求文档要求的React组件",
                "页面实现：实现所有需求文档要求的页面和界面",
                "API集成：实现前端与后端API的完整集成",
                "状态管理：实现符合需求的状态管理（Redux/Context）",
                "路由实现：实现符合需求的页面路由和导航",
                "质量检查：运行TypeScript编译和ESLint检查确保零错误",
            ],
            success_criteria=[
                "前端需求100%分析完成",
                "React组件100%符合需求",
                "页面界面100%符合需求",
                "API集成100%完成",
                "状态管理100%正确",
                "路由导航100%正确",
                "代码质量100%达标",
                "用户体验100%符合设计",
            ],
            estimated_hours=6,
        )

        # 后端实现专用模板
        templates["backend_implementation"] = CommandTemplate(
            name="后端实现",
            description="严格按照需求文档实现FastAPI后端服务和接口",
            phase=TaskPhase.PHASE_5,
            agent_role=AgentRole.BACKEND,
            commands=[
                "analyze_backend_requirements_from_docs {requirement_id}",
                "design_api_endpoints_specification {requirement_id}",
                "implement_fastapi_endpoints {requirement_id}",
                "implement_service_classes {requirement_id}",
                "implement_database_models {requirement_id}",
                "implement_business_logic {requirement_id}",
                "implement_data_validation {requirement_id}",
                "run_backend_quality_checks {requirement_id}",
            ],
            checklist=[
                "需求分析：从requirements.md提取后端相关的具体实现要求",
                "API设计：设计符合需求的REST API端点规范",
                "端点实现：实现所有需求文档要求的FastAPI端点",
                "服务实现：实现所有需求文档要求的业务服务类",
                "模型实现：实现所有需求文档要求的数据库模型",
                "业务逻辑：实现符合需求的核心业务逻辑",
                "数据验证：实现完整的输入验证和错误处理",
                "质量检查：运行Python类型检查和代码质量检查确保零错误",
            ],
            success_criteria=[
                "后端需求100%分析完成",
                "API端点100%符合需求",
                "服务类100%符合需求",
                "数据模型100%符合需求",
                "业务逻辑100%正确",
                "数据验证100%完整",
                "代码质量100%达标",
                "性能要求100%满足",
            ],
            estimated_hours=6,
        )

        # === 基于TODO优先级的专门模板 ===

        # 第一优先级：学生综合训练中心模板
        templates["priority1_training_center"] = CommandTemplate(
            name="第一优先级：学生综合训练中心实现",
            description="实现学生综合训练中心核心功能，包括训练模式、进度跟踪、历史记录等",
            phase=TaskPhase.PHASE_5,
            agent_role=AgentRole.TRAINING_SPECIALIST,
            commands=[
                "codebase-retrieval 'training center API endpoints'",
                "view app/training --type directory",
                "create_training_center_models",
                "create_training_center_services",
                "create_training_center_api_endpoints",
                "create_training_center_frontend_components",
                "implement_training_mode_selection",
                "implement_progress_tracking",
                "implement_training_history",
                "implement_personalized_recommendations",
                "test_training_center_integration",
            ],
            checklist=[
                "✅ 创建训练中心数据模型 (TrainingSession, TrainingMode, TrainingProgress)",
                "✅ 实现训练中心服务层 (TrainingCenterService)",
                "✅ 创建API端点 /api/v1/training/center/*",
                "✅ 实现训练模式选择 (练习/模拟/冲刺)",
                "✅ 实现学习进度跟踪和可视化",
                "✅ 实现训练历史记录管理",
                "✅ 实现个性化训练推荐",
                "✅ 创建前端训练中心组件",
                "✅ 集成测试所有训练中心功能",
                "✅ 验证API响应格式和错误处理",
            ],
            success_criteria=[
                "训练中心API完全可用 (/api/v1/training/center/*)",
                "训练模式选择功能正常工作",
                "进度跟踪数据准确显示",
                "训练历史完整记录",
                "个性化推荐算法有效",
                "前端界面响应流畅",
                "所有API测试通过",
                "错误处理机制完善",
            ],
            estimated_hours=40,
        )

        # 第一优先级：AI智能批改系统模板
        templates["priority1_ai_grading"] = CommandTemplate(
            name="第一优先级：AI智能批改与反馈系统",
            description="集成DeepSeek AI服务，实现智能批改算法和实时反馈机制",
            phase=TaskPhase.PHASE_5,
            agent_role=AgentRole.AI_SPECIALIST,
            commands=[
                "codebase-retrieval 'AI grading DeepSeek integration'",
                "view app/ai --type directory",
                "create_deepseek_service_integration",
                "create_ai_grading_models",
                "create_ai_grading_services",
                "create_ai_grading_api_endpoints",
                "implement_bloom_filter_deduplication",
                "implement_real_time_feedback",
                "implement_d3js_heatmap_visualization",
                "create_ai_grading_frontend_components",
                "test_ai_grading_accuracy",
                "test_ai_grading_performance",
            ],
            checklist=[
                "✅ 集成DeepSeek AI服务 (API密钥管理)",
                "✅ 创建AI批改数据模型 (GradingResult, FeedbackData)",
                "✅ 实现智能批改算法 (准确率>95%)",
                "✅ 实现实时反馈机制 (响应时间<1s)",
                "✅ 实现布隆过滤器去重 (误判率<0.1%)",
                "✅ 创建API端点 /api/v1/ai/grading/*",
                "✅ 实现D3.js可视化热力图",
                "✅ 创建前端AI批改组件",
                "✅ 测试批改准确性和性能",
                "✅ 验证AI服务稳定性",
            ],
            success_criteria=[
                "DeepSeek AI服务成功集成",
                "批改准确率达到95%以上",
                "响应时间稳定在1秒以内",
                "布隆过滤器误判率低于0.1%",
                "AI批改API完全可用",
                "可视化热力图正常显示",
                "前端AI功能流畅运行",
                "性能测试全部通过",
            ],
            estimated_hours=35,
        )

        # 第一优先级：听力训练系统模板
        templates["priority1_listening_training"] = CommandTemplate(
            name="第一优先级：听力训练系统",
            description="实现完整的听力训练功能，包括多种题型、音频控制、成绩统计等",
            phase=TaskPhase.PHASE_5,
            agent_role=AgentRole.TRAINING_SPECIALIST,
            commands=[
                "codebase-retrieval 'listening training audio system'",
                "view app/training/listening --type directory",
                "create_listening_training_models",
                "create_listening_training_services",
                "create_listening_training_api_endpoints",
                "implement_audio_playback_control",
                "implement_listening_question_types",
                "implement_listening_answer_interface",
                "implement_listening_statistics",
                "implement_listening_training_plan",
                "create_listening_frontend_components",
                "test_listening_training_system",
            ],
            checklist=[
                "✅ 创建听力训练数据模型 (ListeningExercise, AudioFile, ListeningResult)",
                "✅ 实现听力训练服务层 (ListeningTrainingService)",
                "✅ 创建API端点 /api/v1/training/listening/*",
                "✅ 支持听力题型 (短对话/长对话/短文理解/复合式听写)",
                "✅ 实现音频播放控制和进度管理",
                "✅ 实现听力答题界面和交互",
                "✅ 实现听力成绩统计和分析",
                "✅ 实现听力训练计划制定",
                "✅ 创建前端听力训练组件",
                "✅ 集成测试听力训练系统",
            ],
            success_criteria=[
                "听力训练API完全可用",
                "所有听力题型正常支持",
                "音频播放控制流畅",
                "答题界面交互良好",
                "成绩统计数据准确",
                "训练计划功能有效",
                "前端组件响应迅速",
                "系统集成测试通过",
            ],
            estimated_hours=30,
        )

        # 第二优先级：AI智能分析与学情报告模板
        templates["priority2_ai_analysis"] = CommandTemplate(
            name="第二优先级：AI智能分析与学情报告",
            description="实现学习数据分析引擎和个性化学情报告生成系统",
            phase=TaskPhase.PHASE_5,
            agent_role=AgentRole.AI_SPECIALIST,
            commands=[
                "codebase-retrieval 'learning analytics AI analysis'",
                "view app/ai/analysis --type directory",
                "create_learning_analytics_models",
                "create_ai_analysis_services",
                "create_ai_analysis_api_endpoints",
                "implement_learning_data_analysis_engine",
                "implement_personalized_report_generation",
                "implement_predictive_learning_suggestions",
                "implement_multi_dimensional_data_fusion",
                "implement_real_time_notification_system",
                "create_analysis_frontend_components",
                "test_ai_analysis_accuracy",
            ],
            checklist=[
                "✅ 创建学习分析数据模型 (LearningAnalytics, StudentReport, PredictionModel)",
                "✅ 实现AI分析服务层 (AIAnalyticsService)",
                "✅ 创建API端点 /api/v1/ai/analysis/*",
                "✅ 实现学习数据分析引擎 (准确率>90%)",
                "✅ 实现个性化学情报告生成",
                "✅ 实现预测性学习建议 (准确率>85%)",
                "✅ 实现多维度数据融合",
                "✅ 实现实时推送和通知机制",
                "✅ 创建前端分析报告组件",
                "✅ 测试AI分析准确性和性能",
            ],
            success_criteria=[
                "AI分析API完全可用",
                "分析准确率达到90%以上",
                "预测准确率达到85%以上",
                "学情报告生成正常",
                "数据融合算法有效",
                "实时通知系统稳定",
                "前端报告界面完善",
                "性能测试全部通过",
            ],
            estimated_hours=45,
        )

        # 第二优先级：错题强化与自适应学习模板
        templates["priority2_adaptive_learning"] = CommandTemplate(
            name="第二优先级：错题强化与自适应学习",
            description="实现艾宾浩斯遗忘曲线算法和智能复习推荐系统",
            phase=TaskPhase.PHASE_5,
            agent_role=AgentRole.AI_SPECIALIST,
            commands=[
                "codebase-retrieval 'adaptive learning forgetting curve'",
                "view app/adaptive --type directory",
                "create_adaptive_learning_models",
                "create_adaptive_learning_services",
                "create_adaptive_learning_api_endpoints",
                "implement_ebbinghaus_forgetting_curve",
                "implement_dynamic_difficulty_adjustment",
                "implement_intelligent_review_recommendation",
                "implement_error_classification_diagnosis",
                "implement_learning_path_optimization",
                "create_adaptive_frontend_components",
                "test_adaptive_learning_effectiveness",
            ],
            checklist=[
                "✅ 创建自适应学习数据模型 (AdaptiveLearning, ForgettingCurve, ReviewSchedule)",
                "✅ 实现自适应学习服务层 (AdaptiveLearningService)",
                "✅ 创建API端点 /api/v1/adaptive/*",
                "✅ 实现艾宾浩斯遗忘曲线算法",
                "✅ 实现动态难度调节机制",
                "✅ 实现智能复习推荐引擎",
                "✅ 实现错题分类和诊断",
                "✅ 实现学习路径优化",
                "✅ 创建前端自适应学习组件",
                "✅ 测试自适应学习有效性",
            ],
            success_criteria=[
                "自适应学习API完全可用",
                "遗忘曲线算法准确实现",
                "难度调节机制有效",
                "复习推荐算法智能",
                "错题诊断准确",
                "学习路径优化合理",
                "前端自适应界面流畅",
                "学习效果测试通过",
            ],
            estimated_hours=35,
        )

        # 第二优先级：词汇训练模块模板
        templates["priority2_vocabulary_training"] = CommandTemplate(
            name="第二优先级：词汇训练模块",
            description="实现完整的词汇训练系统，包括多种题型、词汇量测试、学习计划等",
            phase=TaskPhase.PHASE_5,
            agent_role=AgentRole.TRAINING_SPECIALIST,
            commands=[
                "codebase-retrieval 'vocabulary training word learning'",
                "view app/training/vocabulary --type directory",
                "create_vocabulary_training_models",
                "create_vocabulary_training_services",
                "create_vocabulary_training_api_endpoints",
                "implement_vocabulary_question_types",
                "implement_vocabulary_assessment",
                "implement_vocabulary_learning_plan",
                "implement_vocabulary_review_reminders",
                "implement_vocabulary_mastery_statistics",
                "create_vocabulary_frontend_components",
                "test_vocabulary_training_system",
            ],
            checklist=[
                "✅ 创建词汇训练数据模型 (VocabularyExercise, WordMastery, VocabularyPlan)",
                "✅ 实现词汇训练服务层 (VocabularyTrainingService)",
                "✅ 创建API端点 /api/v1/training/vocabulary/*",
                "✅ 实现词汇训练题型 (选择/填空/拼写)",
                "✅ 实现词汇量测试和评估",
                "✅ 实现词汇学习计划 (15-30题/日)",
                "✅ 实现词汇复习提醒",
                "✅ 实现词汇掌握度统计",
                "✅ 创建前端词汇训练组件",
                "✅ 集成测试词汇训练系统",
            ],
            success_criteria=[
                "词汇训练API完全可用",
                "所有词汇题型正常支持",
                "词汇量测试准确",
                "学习计划功能有效",
                "复习提醒系统稳定",
                "掌握度统计准确",
                "前端词汇界面完善",
                "系统集成测试通过",
            ],
            estimated_hours=25,
        )

        return templates

    def get_template(self: "AgentTemplateManager", template_name: str) -> CommandTemplate | None:
        """获取指定的命令模板"""
        return self.templates.get(template_name)

    def get_phase_template(
        self: "AgentTemplateManager", phase: TaskPhase
    ) -> CommandTemplate | None:
        """根据阶段获取模板"""
        for template in self.templates.values():
            if template.phase == phase:
                return template
        return None

    def generate_agent_commands(
        self: "AgentTemplateManager", requirement_id: str, phase: TaskPhase
    ) -> list[str]:
        """为特定需求和阶段生成智能体命令"""
        template = self.get_phase_template(phase)
        if not template:
            return []

        # 替换命令中的占位符
        commands = []
        for cmd in template.commands:
            formatted_cmd = cmd.format(requirement_id=requirement_id)
            commands.append(formatted_cmd)

        return commands

    def generate_checklist(self: "AgentTemplateManager", phase: TaskPhase) -> list[str]:
        """生成阶段检查清单"""
        template = self.get_phase_template(phase)
        return template.checklist if template else []

    def generate_success_criteria(self: "AgentTemplateManager", phase: TaskPhase) -> list[str]:
        """生成成功标准"""
        template = self.get_phase_template(phase)
        return template.success_criteria if template else []

    def estimate_hours(self: "AgentTemplateManager", phase: TaskPhase) -> int:
        """获取阶段预估工时"""
        template = self.get_phase_template(phase)
        return template.estimated_hours if template else 0

    def get_priority_templates(
        self: "AgentTemplateManager", priority_level: int
    ) -> list[CommandTemplate]:
        """根据优先级获取模板列表"""
        priority_mapping = {
            1: [
                "priority1_training_center",
                "priority1_ai_grading",
                "priority1_listening_training",
            ],
            2: [
                "priority2_ai_analysis",
                "priority2_adaptive_learning",
                "priority2_vocabulary_training",
            ],
            3: [
                "priority3_reading_training",
                "priority3_writing_library",
                "priority3_learning_plan",
            ],
            4: ["priority4_learning_assistant", "priority4_social_interaction"],
            5: ["priority5_resource_architecture", "priority5_performance_optimization"],
        }

        template_names = priority_mapping.get(priority_level, [])
        return [self.templates[name] for name in template_names if name in self.templates]

    def get_all_priority_templates(
        self: "AgentTemplateManager"
    ) -> dict[int, list[CommandTemplate]]:
        """获取所有优先级的模板映射"""
        return {
            1: self.get_priority_templates(1),
            2: self.get_priority_templates(2),
            3: self.get_priority_templates(3),
            4: self.get_priority_templates(4),
            5: self.get_priority_templates(5),
        }

    def get_frontend_template(self: "AgentTemplateManager") -> CommandTemplate | None:
        """获取前端实现模板"""
        return self.templates.get("frontend_implementation")

    def get_backend_template(self: "AgentTemplateManager") -> CommandTemplate | None:
        """获取后端实现模板"""
        return self.templates.get("backend_implementation")

    def generate_requirement_specific_template(
        self: "AgentTemplateManager", requirement_id: str, requirement_title: str
    ) -> str:
        """生成针对特定需求的详细任务模板"""
        template = f"""
### 🎯 需求{requirement_id}：{requirement_title}

#### 📋 实施原则
- 严格按照 .kiro/specs/cet4-learning-system/requirements.md 中需求{requirement_id}的验收标准执行
- 严格按照 .kiro/specs/cet4-learning-system/design.md 中的技术架构要求执行
- 前后端必须完整实现，不允许部分实现或占位符代码
- 所有实现必须通过验收标准的逐条验证

#### 📝 执行阶段

"""

        for phase in TaskPhase:
            phase_template = self.get_phase_template(phase)
            if phase_template:
                template += f"""##### {phase_template.name}
**描述**: {phase_template.description}
**预估时间**: {phase_template.estimated_hours}小时

**检查清单**:
"""
                for item in phase_template.checklist:
                    template += f"- [ ] {item}\n"

                template += """
**成功标准**:
"""
                for criterion in phase_template.success_criteria:
                    template += f"- [ ] {criterion}\n"

                template += "\n"

        # 添加前后端专用模板
        frontend_template = self.get_frontend_template()
        backend_template = self.get_backend_template()

        if frontend_template:
            template += f"""##### {frontend_template.name}（并行执行）
**描述**: {frontend_template.description}
**预估时间**: {frontend_template.estimated_hours}小时

**检查清单**:
"""
            for item in frontend_template.checklist:
                template += f"- [ ] {item}\n"

        if backend_template:
            template += f"""
##### {backend_template.name}（并行执行）
**描述**: {backend_template.description}
**预估时间**: {backend_template.estimated_hours}小时

**检查清单**:
"""
            for item in backend_template.checklist:
                template += f"- [ ] {item}\n"

        total_hours = sum(self.estimate_hours(phase) for phase in TaskPhase)
        if frontend_template:
            total_hours += frontend_template.estimated_hours
        if backend_template:
            total_hours += backend_template.estimated_hours

        template += f"""
#### 📊 总体预估
- **总预估时间**: {total_hours}小时
- **前后端并行**: 可节省约30%时间
- **质量要求**: TypeScript零错误、ESLint零警告、Python类型检查通过

#### ✅ 最终验收
- [ ] 所有验收标准100%满足
- [ ] 前端界面100%完整实现
- [ ] 后端接口100%完整实现
- [ ] 前后端集成100%成功
- [ ] 代码质量100%达标
"""

        return template


def main() -> None:
    """演示模板系统使用"""
    manager = AgentTemplateManager()

    # 生成需求26的详细任务模板
    task_template = manager.generate_requirement_specific_template("26", "英语四级写作标准库")
    print("生成的详细任务模板：")
    print(task_template)

    # 生成阶段1的命令
    commands = manager.generate_agent_commands("26", TaskPhase.PHASE_1)
    print("\n阶段1命令：")
    for cmd in commands:
        print(f"  - {cmd}")

    # 展示前端模板
    frontend_template = manager.get_frontend_template()
    if frontend_template:
        print("\n前端实现模板：")
        print(f"  名称: {frontend_template.name}")
        print(f"  描述: {frontend_template.description}")
        print(f"  预估时间: {frontend_template.estimated_hours}小时")

    # 展示后端模板
    backend_template = manager.get_backend_template()
    if backend_template:
        print("\n后端实现模板：")
        print(f"  名称: {backend_template.name}")
        print(f"  描述: {backend_template.description}")
        print(f"  预估时间: {backend_template.estimated_hours}小时")


if __name__ == "__main__":
    main()
