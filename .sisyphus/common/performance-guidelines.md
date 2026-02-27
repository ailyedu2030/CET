---
globs: ["**/*"]
alwaysApply: false
description: "Performance optimization guidelines"
---

# Performance Guidelines

## General Principles

- Profile before optimizing - don't guess
- Focus on the biggest bottlenecks first
- Measure the impact of optimizations

## Code Efficiency

- Avoid unnecessary computations
- Use appropriate data structures
- Minimize I/O operations
- Batch operations when possible

## Memory Management

- Avoid memory leaks
- Clean up resources properly
- Use appropriate data types
- Be mindful of large data structures

## Async Operations

- Use async/await for I/O operations
- Don't block the event loop
- Use streaming for large files
- Parallelize independent operations

## Caching

- Cache expensive computations
- Use appropriate cache invalidation
- Consider memory vs disk cache
- Set appropriate TTLs
