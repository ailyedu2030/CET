---
globs: ["**/*.cpp", "**/*.hpp", "**/*.h", "**/*.cc"]
alwaysApply: false
description: "C++ best practices and coding standards"
---

# C++ Best Practices

## Code Style

- Follow C++ Core Guidelines
- Use consistent formatting
- Keep functions small
- Use meaningful names

## Modern C++

- Use C++11/14/17/20 features
- Use auto for type inference
- Use range-based for loops
- Use smart pointers
- Use std::optional

## Memory Management

- Use smart pointers (unique_ptr, shared_ptr)
- Avoid raw new/delete
- Use RAII pattern
- Check for memory leaks

## Performance

- Use constexpr where possible
- Avoid unnecessary copies
- Use move semantics
- Prefer algorithms over loops

## Error Handling

- Use exceptions for errors
- Don't use exceptions for flow control
- Use noexcept appropriately
- Validate input

## Testing

- Use Google Test or Catch2
- Write unit tests
- Test edge cases
- Use assertions properly
