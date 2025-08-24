# Pyright/Pylance 禁用配置说明

## 📋 背景

本项目使用 **ruff** 和 **mypy** 作为官方代码质量审查工具，为避免工具冲突和重复报警，已禁用 IDE 中的 pyright/pylance 类型检查。

## ⚙️ 配置文件

### 1. `pyproject.toml` - 项目级配置
```toml
[tool.pyright]
# 禁用pyright类型检查 - 项目使用ruff和mypy作为代码质量工具
typeCheckingMode = "off"
reportMissingImports = false
reportMissingTypeStubs = false
reportGeneralTypeIssues = false
reportOptionalMemberAccess = false
reportOptionalSubscript = false
reportPrivateImportUsage = false
```

### 2. `.vscode/settings.json` - VS Code工作区配置
```json
{
    "python.analysis.typeCheckingMode": "off",
    "python.analysis.disabled": [
        "reportMissingImports",
        "reportMissingTypeStubs",
        "reportGeneralTypeIssues",
        ...
    ],
    "python.linting.ruffEnabled": true,
    "python.linting.mypyEnabled": true
}
```

### 3. `pyrightconfig.json` - 项目根目录配置
```json
{
    "typeCheckingMode": "off",
    "reportMissingImports": false,
    ...
}
```

## 🛠️ 启用的代码质量工具

### Ruff - 代码风格和错误检查
```bash
# 运行ruff检查
ruff check .

# 自动修复
ruff check --fix .
```

### mypy - 静态类型检查
```bash
# 运行mypy检查
mypy .
```

### Black - 代码格式化
```bash
# 检查格式
black --check .

# 自动格式化
black .
```

## 🎯 配置效果

- ✅ **消除工具冲突**：避免pyright与ruff/mypy的重复报警
- ✅ **统一标准**：使用项目统一的代码质量工具链
- ✅ **保持一致**：团队使用相同的代码检查规则
- ✅ **提升效率**：减少IDE中的误报和干扰

## 📝 注意事项

1. **重启IDE**：修改配置后请重启VS Code或其他IDE使配置生效
2. **团队同步**：确保团队成员都应用了相同的配置
3. **CI/CD**：持续集成流程仍使用ruff和mypy进行检查
4. **扩展管理**：可以考虑在VS Code中禁用Pylance扩展

## 🔄 如需重新启用pyright

如需重新启用pyright检查，请：

1. 将 `pyproject.toml` 中的 `typeCheckingMode` 改为 `"basic"` 或 `"strict"`
2. 在 `.vscode/settings.json` 中设置 `"python.analysis.typeCheckingMode": "basic"`
3. 删除或重命名 `pyrightconfig.json` 文件
4. 重启IDE

## ✨ 推荐VS Code扩展

- **Ruff** - 代码检查和格式化
- **mypy** - 类型检查  
- **Black Formatter** - 代码格式化
- **Python** - Python语言支持（保留，但禁用其Pylance功能）

---

*此配置确保项目使用统一的代码质量标准，提升开发体验和代码一致性。*
