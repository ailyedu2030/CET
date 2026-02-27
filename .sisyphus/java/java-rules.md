---
globs: ["**/*.java"]
alwaysApply: false
description: "Java best practices and coding standards"
---

# Java Best Practices

## Code Style

- Follow Google Java Style
- Use proper indentation
- Keep lines under 100 characters
- Use meaningful names

## Best Practices

- Use streams and lambdas
- Prefer composition over inheritance
- Use Optional for null safety
- Use builder pattern for complex objects

## Error Handling

- Use specific exceptions
- Don't catch Exception/RuntimeException
- Use try-with-resources
- Log appropriately

## Performance

- Use StringBuilder for concatenation
- Avoid unnecessary boxing
- Use appropriate collections
- Lazy initialize when possible

## Testing

- Use JUnit 5
- Write descriptive test names
- Use assertions properly
- Test edge cases
