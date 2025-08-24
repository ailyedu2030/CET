"""Excel批量导入学生信息工具类."""

import logging
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import ValidationError

from app.users.schemas.registration_schemas import StudentRegistrationRequest

logger = logging.getLogger(__name__)


class ExcelImportResult:
    """Excel导入结果."""

    def __init__(self) -> None:
        """初始化导入结果."""
        self.total_records: int = 0
        self.successful_imports: int = 0
        self.failed_imports: int = 0
        self.validation_errors: list[str] = []
        self.created_students: list[dict[str, Any]] = []
        self.failed_records: list[dict[str, Any]] = []


class StudentExcelImportUtils:
    """学生Excel批量导入工具类."""

    # 必需的Excel列名映射
    REQUIRED_COLUMNS = {
        "username": "用户名",
        "password": "密码",
        "email": "邮箱",
        "real_name": "真实姓名",
        "age": "年龄",
        "gender": "性别",
        "id_number": "身份证号",
        "phone": "手机号",
        "emergency_contact_name": "紧急联系人姓名",
        "emergency_contact_phone": "紧急联系人电话",
        "school": "学校",
        "department": "院系",
        "major": "专业",
        "grade": "年级",
        "class_name": "班级",
    }

    @staticmethod
    async def parse_excel_file(file_path: str) -> ExcelImportResult:
        """解析Excel文件并验证数据."""
        result = ExcelImportResult()
        try:
            # 检查文件是否存在
            if not Path(file_path).exists():
                result.validation_errors.append(f"文件不存在: {file_path}")
                return result

            # 读取Excel文件
            df = pd.read_excel(file_path)
            result.total_records = len(df)

            # 检查必需列
            missing_columns = []
            for _eng_name, cn_name in StudentExcelImportUtils.REQUIRED_COLUMNS.items():
                if cn_name not in df.columns:
                    missing_columns.append(cn_name)

            if missing_columns:
                result.validation_errors.append(f"缺少必需列: {', '.join(missing_columns)}")
                return result

            # 逐行验证数据
            for index, row in df.iterrows():
                try:
                    # 构建学生注册数据
                    student_data = {}
                    for (
                        eng_name,
                        cn_name,
                    ) in StudentExcelImportUtils.REQUIRED_COLUMNS.items():
                        value = row[cn_name]
                        # 处理空值
                        if pd.isna(value):
                            if eng_name in [
                                "username",
                                "password",
                                "email",
                                "real_name",
                            ]:
                                raise ValueError(f"必填字段不能为空: {cn_name}")
                            value = None
                        else:
                            # 类型转换
                            if eng_name == "age" and value is not None:
                                value = int(value)
                            elif isinstance(value, str):
                                value = value.strip()

                        student_data[eng_name] = value

                    # 使用Pydantic验证数据
                    validated_data = StudentRegistrationRequest(**student_data)
                    # 添加到成功列表
                    result.created_students.append(
                        {
                            "row_number": index + 2,  # Excel行号（从2开始，因为第1行是标题）
                            "data": validated_data.model_dump(),
                        }
                    )
                    result.successful_imports += 1

                except (ValueError, ValidationError) as e:
                    # 记录验证失败的记录
                    error_msg = f"第{index + 2}行数据验证失败: {str(e)}"
                    result.validation_errors.append(error_msg)
                    result.failed_records.append(
                        {
                            "row_number": index + 2,
                            "data": row.to_dict(),
                            "error": str(e),
                        }
                    )
                    result.failed_imports += 1

        except Exception as e:
            logger.error(f"Excel文件解析失败: {str(e)}")
            result.validation_errors.append(f"文件解析失败: {str(e)}")

        return result

    @staticmethod
    def generate_excel_template() -> dict[str, Any]:
        """生成Excel导入模板."""
        template_data = {
            "columns": list(StudentExcelImportUtils.REQUIRED_COLUMNS.values()),
            "sample_data": [
                {
                    "用户名": "student001",
                    "密码": "password123",
                    "邮箱": "student001@example.com",
                    "真实姓名": "张三",
                    "年龄": 20,
                    "性别": "男",
                    "身份证号": "110101200001011234",
                    "手机号": "13800138000",
                    "紧急联系人姓名": "张父",
                    "紧急联系人电话": "13900139000",
                    "学校": "某某大学",
                    "院系": "计算机学院",
                    "专业": "计算机科学与技术",
                    "年级": "2024",
                    "班级": "计科2401班",
                },
                {
                    "用户名": "student002",
                    "密码": "password456",
                    "邮箱": "student002@example.com",
                    "真实姓名": "李四",
                    "年龄": 19,
                    "性别": "女",
                    "身份证号": "110101200101015678",
                    "手机号": "13800138001",
                    "紧急联系人姓名": "李母",
                    "紧急联系人电话": "13900139001",
                    "学校": "某某大学",
                    "院系": "外国语学院",
                    "专业": "英语",
                    "年级": "2024",
                    "班级": "英语2401班",
                },
            ],
            "instructions": [
                "1. 请按照模板格式填写学生信息",
                "2. 用户名必须唯一，建议使用学号",
                "3. 邮箱地址必须有效且唯一",
                "4. 身份证号必须为18位",
                "5. 手机号必须为11位数字",
                "6. 年龄范围：16-100岁",
                "7. 性别填写：男/女/其他",
                "8. 所有必填字段不能为空",
            ],
        }
        return template_data

    @staticmethod
    def validate_excel_format(file_path: str) -> dict[str, Any]:
        """验证Excel文件格式."""
        validation_result: dict[str, Any] = {
            "valid": False,
            "errors": [],
            "warnings": [],
            "file_info": {},
        }

        try:
            # 检查文件扩展名
            file_ext = Path(file_path).suffix.lower()
            if file_ext not in [".xlsx", ".xls"]:
                validation_result["errors"].append("文件格式不正确，请上传Excel文件(.xlsx或.xls)")
                return validation_result

            # 读取文件信息
            df = pd.read_excel(file_path)
            validation_result["file_info"] = {
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "columns": df.columns.tolist(),
            }

            # 检查是否为空文件
            if len(df) == 0:
                validation_result["errors"].append("Excel文件为空，请添加学生数据")
                return validation_result

            # 检查行数限制（建议单次导入不超过1000条）
            if len(df) > 1000:
                validation_result["warnings"].append(
                    f"数据量较大({len(df)}行)，建议分批导入以提高成功率"
                )

            # 检查必需列
            missing_columns = []
            for _eng_name, cn_name in StudentExcelImportUtils.REQUIRED_COLUMNS.items():
                if cn_name not in df.columns:
                    missing_columns.append(cn_name)

            if missing_columns:
                validation_result["errors"].append(f"缺少必需列: {', '.join(missing_columns)}")
                return validation_result

            # 检查数据完整性
            empty_required_fields = []
            for _eng_name, cn_name in StudentExcelImportUtils.REQUIRED_COLUMNS.items():
                if _eng_name in ["username", "password", "email", "real_name"]:
                    empty_count = df[cn_name].isna().sum()
                    if empty_count > 0:
                        empty_required_fields.append(f"{cn_name}({empty_count}行为空)")

            if empty_required_fields:
                validation_result["warnings"].extend(
                    [
                        f"发现必填字段为空: {', '.join(empty_required_fields)}",
                        "这些记录将在导入时被跳过",
                    ]
                )

            validation_result["valid"] = True

        except Exception as e:
            validation_result["errors"].append(f"文件读取失败: {str(e)}")

        return validation_result
