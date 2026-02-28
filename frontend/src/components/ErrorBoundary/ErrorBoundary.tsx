/* eslint-disable no-console */
import { Button, Container, Paper, Stack, Text, Title } from '@mantine/core'
import { Component, ReactNode } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  override componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
  }

  handleReload = (): void => {
    window.location.reload()
  }

  override render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <Container size="sm" py="xl">
          <Paper shadow="md" p="xl" radius="md">
            <Stack gap="md">
              <Title order={3}>出现了一些问题</Title>
              <Text c="dimmed">应用程序遇到了一个意外错误。请尝试重新加载页面。</Text>
              {this.state.error && (
                <Text size="sm" c="red" style={{ fontFamily: 'monospace' }}>
                  {this.state.error.message}
                </Text>
              )}
              <Button onClick={this.handleReload} mt="md">
                重新加载
              </Button>
            </Stack>
          </Paper>
        </Container>
      )
    }

    return this.props.children
  }
}
