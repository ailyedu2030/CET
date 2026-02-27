---
globs: ["**/*"]
alwaysApply: false
description: "Common coding best practices applicable to all languages"
---

# Common Coding Best Practices

## Error Handling

- Always handle errors explicitly - never use empty catch blocks
- Use try-catch for operations that can fail
- Provide meaningful error messages

## Naming Conventions

- Use descriptive, intent-revealing names
- Avoid single-letter names except for loop indices
- Use camelCase for variables/functions, PascalCase for types/classes

## Code Organization

- Keep functions small and focused (single responsibility)
- Group related functionality together
- Put related files in the same directory

## Comments

- Explain WHY, not WHAT
- Keep comments up-to-date with code changes
- Avoid obvious comments that add no value

## Testing

- Write tests for critical functionality
- Test edge cases and error conditions
- Keep tests maintainable and readable
