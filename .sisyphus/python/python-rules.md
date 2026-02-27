---
globs: ["**/*.py"]
alwaysApply: false
description: "Python best practices and coding standards"
---

# Python Best Practices

## Code Style

- Follow PEP 8
- Use Black for formatting
- Use isort for imports
- Keep lines under 88 characters

## Type Hints

- Use type hints for all functions
- Use mypy for type checking
- Avoid Any type
- Use typing module properly

## Best Practices

- Use virtual environments
- Use requirements.txt or pyproject.toml
- Follow Django/Flask conventions
- Use f-strings for formatting

## Error Handling

- Use specific exception types
- Don't use bare except
- Log errors properly
- Handle edge cases

## Testing

- Use pytest
- Write descriptive test names
- Use fixtures
- Aim for high coverage
