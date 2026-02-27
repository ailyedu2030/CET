---
globs: ["**/*"]
alwaysApply: true
description: "Security best practices for all code"
---

# Security Best Practices

## Input Validation

- Always validate and sanitize user input
- Never trust client-side validation alone
- Use parameterized queries for database operations

## Authentication & Authorization

- Store passwords using secure hashing (bcrypt, argon2)
- Implement proper session management
- Follow principle of least privilege

## Data Protection

- Encrypt sensitive data at rest and in transit
- Never commit secrets to version control
- Use environment variables for configuration secrets

## Common Vulnerabilities

- Prevent SQL injection using parameterized queries
- Prevent XSS by escaping output
- Prevent CSRF with proper tokens
- Prevent path traversal attacks

## Dependencies

- Keep dependencies up-to-date
- Audit dependencies for vulnerabilities
- Prefer well-maintained packages
