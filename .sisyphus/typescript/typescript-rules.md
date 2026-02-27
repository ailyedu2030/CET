---
globs: ["**/*.ts", "**/*.tsx"]
alwaysApply: false
description: "TypeScript best practices and coding standards"
---

# TypeScript Best Practices

## Type Safety

- Always enable strict mode
- Never use `any` type
- Use proper type annotations
- Leverage generics appropriately

## Code Organization

- Use clear file structure
- Group related types together
- Export types that are reused
- Use barrel files (index.ts) for imports

## Interfaces vs Types

- Use interfaces for object shapes
- Use types for unions, intersections
- Prefer interfaces for extensibility

## Error Handling

- Use proper error types
- Never silently catch errors
- Type async/await properly

## Testing

- Write unit tests with Vitest/Jest
- Test edge cases
- Mock external dependencies
