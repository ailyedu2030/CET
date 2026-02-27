---
globs: ["**/*.go"]
alwaysApply: false
description: "Go best practices and coding standards"
---

# Go Best Practices

## Code Style

- Run gofmt on save
- Follow Go style guide
- Keep lines under 100 characters
- Use meaningful names

## Error Handling

- Return errors, don't panic
- Wrap errors with context
- Use sentinel errors
- Handle all errors

## Concurrency

- Use channels for communication
- Don't use shared memory
- Use context for cancellation
- Don't leak goroutines

## Testing

- Write table-driven tests
- Use testing.T for assertions
- Write benchmarks when needed
- Use testify/assert

## Best Practices

- Keep functions small
- Use interfaces for abstraction
- Use defer for cleanup
- Avoid premature optimization
