module.exports = {
  root: true,
  env: {
    browser: true,
    es2020: true,
    node: true,
  },
  extends: ['eslint:recommended'],
  ignorePatterns: ['dist', '.eslintrc.cjs', 'node_modules'],
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
    ecmaFeatures: {
      jsx: true,
    },
  },
  plugins: ['@typescript-eslint', 'react-refresh'],
  rules: {
    // 通用规则
    'no-console': 'warn',
    'no-debugger': 'error',
    'prefer-const': 'error',
    'no-var': 'error',
    'no-unused-vars': 'off', // 关闭基础规则，使用TypeScript版本

    // TypeScript规则
    '@typescript-eslint/no-unused-vars': [
      'error',
      {
        argsIgnorePattern: '^_',
        varsIgnorePattern: '^_|^ImportMetaEnv$',
        ignoreRestSiblings: true,
      },
    ],

    // React Refresh
    'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
  },
  globals: {
    JSX: 'readonly',
    React: 'readonly',
  },
}
