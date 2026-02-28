#!/usr/bin/env python3
"""
API审计数据库
存储和管理API审计过程中的所有数据
"""

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class APIEndpointRecord:
    """API端点记录"""

    id: str
    path: str
    method: str
    status_code: int
    response_time: float
    error_message: str | None
    requires_auth: bool
    last_checked: str
    check_count: int


@dataclass
class RequirementRecord:
    """需求记录"""

    id: str
    requirement_id: str
    title: str
    description: str
    status: str
    priority: str
    completion_percentage: float
    created_at: str
    updated_at: str


@dataclass
class IssueRecord:
    """问题记录"""

    id: str
    issue_type: str
    description: str
    severity: str
    impact_scope: str
    business_priority: str
    affected_apis: str  # JSON string
    affected_requirements: str  # JSON string
    estimated_fix_time: int
    status: str  # open, in_progress, resolved, closed
    created_at: str
    resolved_at: str | None


@dataclass
class FixTaskRecord:
    """修复任务记录"""

    id: str
    task_id: str
    title: str
    description: str
    priority_score: float
    estimated_time: int
    actual_time: int | None
    status: str  # pending, in_progress, completed, failed
    assigned_to: str | None
    created_at: str
    started_at: str | None
    completed_at: str | None


class AuditDatabase:
    """API审计数据库"""

    def __init__(self, db_path: str = "tools/database/api_audit.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self) -> None:
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # API端点表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_endpoints (
                    id TEXT PRIMARY KEY,
                    path TEXT NOT NULL,
                    method TEXT NOT NULL,
                    status_code INTEGER,
                    response_time REAL,
                    error_message TEXT,
                    requires_auth BOOLEAN,
                    last_checked TEXT,
                    check_count INTEGER DEFAULT 1,
                    UNIQUE(path, method)
                )
            """)

            # 需求表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS requirements (
                    id TEXT PRIMARY KEY,
                    requirement_id TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT,
                    priority TEXT,
                    completion_percentage REAL,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)

            # 问题表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS issues (
                    id TEXT PRIMARY KEY,
                    issue_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    severity TEXT,
                    impact_scope TEXT,
                    business_priority TEXT,
                    affected_apis TEXT,
                    affected_requirements TEXT,
                    estimated_fix_time INTEGER,
                    status TEXT DEFAULT 'open',
                    created_at TEXT,
                    resolved_at TEXT
                )
            """)

            # 修复任务表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fix_tasks (
                    id TEXT PRIMARY KEY,
                    task_id TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    priority_score REAL,
                    estimated_time INTEGER,
                    actual_time INTEGER,
                    status TEXT DEFAULT 'pending',
                    assigned_to TEXT,
                    created_at TEXT,
                    started_at TEXT,
                    completed_at TEXT
                )
            """)

            # 任务-问题关联表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_issues (
                    task_id TEXT,
                    issue_id TEXT,
                    PRIMARY KEY (task_id, issue_id),
                    FOREIGN KEY (task_id) REFERENCES fix_tasks (id),
                    FOREIGN KEY (issue_id) REFERENCES issues (id)
                )
            """)

            # 需求-API关联表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS requirement_apis (
                    requirement_id TEXT,
                    api_id TEXT,
                    PRIMARY KEY (requirement_id, api_id),
                    FOREIGN KEY (requirement_id) REFERENCES requirements (id),
                    FOREIGN KEY (api_id) REFERENCES api_endpoints (id)
                )
            """)

            # 审计日志表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id TEXT PRIMARY KEY,
                    action TEXT NOT NULL,
                    entity_type TEXT,
                    entity_id TEXT,
                    details TEXT,
                    timestamp TEXT,
                    user_id TEXT
                )
            """)

            conn.commit()

    def insert_api_endpoint(self, endpoint: APIEndpointRecord) -> None:
        """插入或更新API端点记录"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 检查是否已存在
            cursor.execute(
                "SELECT id, check_count FROM api_endpoints WHERE path = ? AND method = ?",
                (endpoint.path, endpoint.method),
            )
            existing = cursor.fetchone()

            if existing:
                # 更新现有记录
                cursor.execute(
                    """
                    UPDATE api_endpoints SET
                        status_code = ?,
                        response_time = ?,
                        error_message = ?,
                        requires_auth = ?,
                        last_checked = ?,
                        check_count = ?
                    WHERE id = ?
                """,
                    (
                        endpoint.status_code,
                        endpoint.response_time,
                        endpoint.error_message,
                        endpoint.requires_auth,
                        endpoint.last_checked,
                        existing[1] + 1,
                        existing[0],
                    ),
                )
            else:
                # 插入新记录
                cursor.execute(
                    """
                    INSERT INTO api_endpoints
                    (id, path, method, status_code, response_time, error_message,
                     requires_auth, last_checked, check_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        endpoint.id,
                        endpoint.path,
                        endpoint.method,
                        endpoint.status_code,
                        endpoint.response_time,
                        endpoint.error_message,
                        endpoint.requires_auth,
                        endpoint.last_checked,
                        endpoint.check_count,
                    ),
                )

            conn.commit()

    def insert_requirement(self, requirement: RequirementRecord) -> None:
        """插入或更新需求记录"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO requirements
                (id, requirement_id, title, description, status, priority,
                 completion_percentage, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    requirement.id,
                    requirement.requirement_id,
                    requirement.title,
                    requirement.description,
                    requirement.status,
                    requirement.priority,
                    requirement.completion_percentage,
                    requirement.created_at,
                    requirement.updated_at,
                ),
            )

            conn.commit()

    def insert_issue(self, issue: IssueRecord) -> None:
        """插入问题记录"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO issues
                (id, issue_type, description, severity, impact_scope, business_priority,
                 affected_apis, affected_requirements, estimated_fix_time, status,
                 created_at, resolved_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    issue.id,
                    issue.issue_type,
                    issue.description,
                    issue.severity,
                    issue.impact_scope,
                    issue.business_priority,
                    issue.affected_apis,
                    issue.affected_requirements,
                    issue.estimated_fix_time,
                    issue.status,
                    issue.created_at,
                    issue.resolved_at,
                ),
            )

            conn.commit()

    def insert_fix_task(self, task: FixTaskRecord, issue_ids: list[str]) -> None:
        """插入修复任务记录"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 插入任务
            cursor.execute(
                """
                INSERT INTO fix_tasks
                (id, task_id, title, description, priority_score, estimated_time,
                 actual_time, status, assigned_to, created_at, started_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    task.id,
                    task.task_id,
                    task.title,
                    task.description,
                    task.priority_score,
                    task.estimated_time,
                    task.actual_time,
                    task.status,
                    task.assigned_to,
                    task.created_at,
                    task.started_at,
                    task.completed_at,
                ),
            )

            # 插入任务-问题关联
            for issue_id in issue_ids:
                cursor.execute(
                    """
                    INSERT INTO task_issues (task_id, issue_id)
                    VALUES (?, ?)
                """,
                    (task.id, issue_id),
                )

            conn.commit()

    def update_task_status(self, task_id: str, status: str, **kwargs: Any) -> None:
        """更新任务状态"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            update_fields = ["status = ?"]
            update_values = [status]

            if status == "in_progress" and "started_at" not in kwargs:
                update_fields.append("started_at = ?")
                update_values.append(datetime.now().isoformat())

            if status == "completed" and "completed_at" not in kwargs:
                update_fields.append("completed_at = ?")
                update_values.append(datetime.now().isoformat())

            for field, value in kwargs.items():
                update_fields.append(f"{field} = ?")
                update_values.append(value)

            update_values.append(task_id)

            cursor.execute(
                f"""
                UPDATE fix_tasks SET {", ".join(update_fields)}
                WHERE task_id = ?
            """,
                update_values,
            )

            conn.commit()

    def update_issue_status(self, issue_id: str, status: str) -> None:
        """更新问题状态"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            resolved_at = datetime.now().isoformat() if status == "resolved" else None

            cursor.execute(
                """
                UPDATE issues SET status = ?, resolved_at = ?
                WHERE id = ?
            """,
                (status, resolved_at, issue_id),
            )

            conn.commit()

    def get_api_endpoints(
        self, status_filter: int | None = None
    ) -> list[APIEndpointRecord]:
        """获取API端点记录"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            if status_filter is not None:
                cursor.execute(
                    """
                    SELECT * FROM api_endpoints WHERE status_code = ?
                    ORDER BY last_checked DESC
                """,
                    (status_filter,),
                )
            else:
                cursor.execute("""
                    SELECT * FROM api_endpoints ORDER BY last_checked DESC
                """)

            rows = cursor.fetchall()

            return [
                APIEndpointRecord(
                    id=row[0],
                    path=row[1],
                    method=row[2],
                    status_code=row[3],
                    response_time=row[4],
                    error_message=row[5],
                    requires_auth=bool(row[6]),
                    last_checked=row[7],
                    check_count=row[8],
                )
                for row in rows
            ]

    def get_requirements(
        self, status_filter: str | None = None
    ) -> list[RequirementRecord]:
        """获取需求记录"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            if status_filter:
                cursor.execute(
                    """
                    SELECT * FROM requirements WHERE status = ?
                    ORDER BY priority DESC, updated_at DESC
                """,
                    (status_filter,),
                )
            else:
                cursor.execute("""
                    SELECT * FROM requirements ORDER BY priority DESC, updated_at DESC
                """)

            rows = cursor.fetchall()

            return [
                RequirementRecord(
                    id=row[0],
                    requirement_id=row[1],
                    title=row[2],
                    description=row[3],
                    status=row[4],
                    priority=row[5],
                    completion_percentage=row[6],
                    created_at=row[7],
                    updated_at=row[8],
                )
                for row in rows
            ]

    def get_issues(self, status_filter: str | None = None) -> list[IssueRecord]:
        """获取问题记录"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            if status_filter:
                cursor.execute(
                    """
                    SELECT * FROM issues WHERE status = ?
                    ORDER BY severity DESC, created_at DESC
                """,
                    (status_filter,),
                )
            else:
                cursor.execute("""
                    SELECT * FROM issues ORDER BY severity DESC, created_at DESC
                """)

            rows = cursor.fetchall()

            return [
                IssueRecord(
                    id=row[0],
                    issue_type=row[1],
                    description=row[2],
                    severity=row[3],
                    impact_scope=row[4],
                    business_priority=row[5],
                    affected_apis=row[6],
                    affected_requirements=row[7],
                    estimated_fix_time=row[8],
                    status=row[9],
                    created_at=row[10],
                    resolved_at=row[11],
                )
                for row in rows
            ]

    def get_fix_tasks(self, status_filter: str | None = None) -> list[FixTaskRecord]:
        """获取修复任务记录"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            if status_filter:
                cursor.execute(
                    """
                    SELECT * FROM fix_tasks WHERE status = ?
                    ORDER BY priority_score DESC, created_at ASC
                """,
                    (status_filter,),
                )
            else:
                cursor.execute("""
                    SELECT * FROM fix_tasks ORDER BY priority_score DESC, created_at ASC
                """)

            rows = cursor.fetchall()

            return [
                FixTaskRecord(
                    id=row[0],
                    task_id=row[1],
                    title=row[2],
                    description=row[3],
                    priority_score=row[4],
                    estimated_time=row[5],
                    actual_time=row[6],
                    status=row[7],
                    assigned_to=row[8],
                    created_at=row[9],
                    started_at=row[10],
                    completed_at=row[11],
                )
                for row in rows
            ]

    def get_dashboard_stats(self) -> dict[str, Any]:
        """获取仪表板统计数据"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            stats = {}

            # API端点统计
            cursor.execute("SELECT COUNT(*) FROM api_endpoints")
            stats["total_apis"] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM api_endpoints WHERE status_code = 200")
            stats["working_apis"] = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM api_endpoints WHERE status_code >= 500"
            )
            stats["error_apis"] = cursor.fetchone()[0]

            # 需求统计
            cursor.execute("SELECT COUNT(*) FROM requirements")
            stats["total_requirements"] = cursor.fetchone()[0]

            cursor.execute(
                'SELECT COUNT(*) FROM requirements WHERE status = "fully_implemented"'
            )
            stats["completed_requirements"] = cursor.fetchone()[0]

            # 问题统计
            cursor.execute('SELECT COUNT(*) FROM issues WHERE status = "open"')
            stats["open_issues"] = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM issues WHERE severity = "critical"')
            stats["critical_issues"] = cursor.fetchone()[0]

            # 任务统计
            cursor.execute('SELECT COUNT(*) FROM fix_tasks WHERE status = "pending"')
            stats["pending_tasks"] = cursor.fetchone()[0]

            cursor.execute(
                'SELECT COUNT(*) FROM fix_tasks WHERE status = "in_progress"'
            )
            stats["active_tasks"] = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM fix_tasks WHERE status = "completed"')
            stats["completed_tasks"] = cursor.fetchone()[0]

            # 时间统计
            cursor.execute(
                'SELECT SUM(estimated_time) FROM fix_tasks WHERE status != "completed"'
            )
            result = cursor.fetchone()[0]
            stats["remaining_work_hours"] = result if result else 0

            cursor.execute(
                'SELECT SUM(actual_time) FROM fix_tasks WHERE status = "completed"'
            )
            result = cursor.fetchone()[0]
            stats["completed_work_hours"] = result if result else 0

            return stats

    def log_action(
        self,
        action: str,
        entity_type: str,
        entity_id: str,
        details: dict[str, Any],
        user_id: str = "system",
    ) -> None:
        """记录审计日志"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO audit_logs
                (id, action, entity_type, entity_id, details, timestamp, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    str(uuid.uuid4()),
                    action,
                    entity_type,
                    entity_id,
                    json.dumps(details, ensure_ascii=False),
                    datetime.now().isoformat(),
                    user_id,
                ),
            )

            conn.commit()

    def import_health_report(self, health_report: dict[str, Any]) -> None:
        """导入API健康检查报告"""
        print("📥 导入API健康检查报告...")

        endpoints = health_report.get("endpoints", [])
        imported_count = 0

        for endpoint_data in endpoints:
            endpoint = APIEndpointRecord(
                id=str(uuid.uuid4()),
                path=endpoint_data.get("path", ""),
                method=endpoint_data.get("method", "GET"),
                status_code=endpoint_data.get("status_code", 0),
                response_time=endpoint_data.get("response_time", 0.0),
                error_message=endpoint_data.get("error"),
                requires_auth=endpoint_data.get("status_code") == 403,
                last_checked=datetime.now().isoformat(),
                check_count=1,
            )

            self.insert_api_endpoint(endpoint)
            imported_count += 1

        print(f"✅ 已导入 {imported_count} 个API端点记录")

        # 记录导入日志
        self.log_action(
            "import_health_report",
            "api_endpoints",
            "batch",
            {"imported_count": imported_count, "source": "health_check"},
        )

    def import_mapping_report(self, mapping_report: dict[str, Any]) -> None:
        """导入需求映射报告"""
        print("📥 导入需求映射报告...")

        requirements = mapping_report.get("requirements", {})
        imported_count = 0

        for req_id, req_data in requirements.items():
            requirement = RequirementRecord(
                id=str(uuid.uuid4()),
                requirement_id=req_id,
                title=req_data.get("title", ""),
                description=req_data.get("description", ""),
                status=req_data.get("status", "not_implemented"),
                priority=req_data.get("priority", "medium"),
                completion_percentage=req_data.get("completion_percentage", 0.0),
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
            )

            self.insert_requirement(requirement)
            imported_count += 1

        print(f"✅ 已导入 {imported_count} 个需求记录")

        # 记录导入日志
        self.log_action(
            "import_mapping_report",
            "requirements",
            "batch",
            {"imported_count": imported_count, "source": "requirement_mapping"},
        )

    def export_database_summary(self, output_file: str) -> None:
        """导出数据库摘要"""
        stats = self.get_dashboard_stats()

        summary = {
            "export_time": datetime.now().isoformat(),
            "database_path": str(self.db_path),
            "statistics": stats,
            "recent_activities": self._get_recent_activities(),
        }

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        print(f"✅ 数据库摘要已导出: {output_file}")

    def _get_recent_activities(self, limit: int = 20) -> list[dict[str, Any]]:
        """获取最近活动"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT action, entity_type, entity_id, details, timestamp, user_id
                FROM audit_logs
                ORDER BY timestamp DESC
                LIMIT ?
            """,
                (limit,),
            )

            rows = cursor.fetchall()

            return [
                {
                    "action": row[0],
                    "entity_type": row[1],
                    "entity_id": row[2],
                    "details": json.loads(row[3]) if row[3] else {},
                    "timestamp": row[4],
                    "user_id": row[5],
                }
                for row in rows
            ]


def main() -> int:
    """主函数"""
    print("🗄️  初始化API审计数据库...")

    db = AuditDatabase()

    try:
        # 导入现有报告
        health_report_file = "tools/api_health_report.json"
        if Path(health_report_file).exists():
            with open(health_report_file, encoding="utf-8") as f:
                health_report = json.load(f)
            db.import_health_report(health_report)

        mapping_report_file = "tools/reports/requirement_mapping_report.json"
        if Path(mapping_report_file).exists():
            with open(mapping_report_file, encoding="utf-8") as f:
                mapping_report = json.load(f)
            db.import_mapping_report(mapping_report)

        # 导出数据库摘要
        db.export_database_summary("tools/reports/database_summary.json")

        # 显示统计信息
        stats = db.get_dashboard_stats()
        print("\\n📊 数据库统计")
        print("=" * 40)
        print(f"API端点总数: {stats['total_apis']}")
        print(f"正常工作: {stats['working_apis']}")
        print(f"错误端点: {stats['error_apis']}")
        print(f"需求总数: {stats['total_requirements']}")
        print(f"已完成需求: {stats['completed_requirements']}")
        print(f"待解决问题: {stats['open_issues']}")
        print(f"关键问题: {stats['critical_issues']}")
        print(f"待处理任务: {stats['pending_tasks']}")
        print(f"进行中任务: {stats['active_tasks']}")
        print(f"已完成任务: {stats['completed_tasks']}")
        print(f"剩余工作量: {stats['remaining_work_hours']}小时")

    except Exception as e:
        print(f"❌ 数据库操作出错: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
