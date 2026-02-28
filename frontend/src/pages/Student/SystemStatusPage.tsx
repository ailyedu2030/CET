/**
 * 学生系统状态页面
 *
 * 集成SystemStatusPanel组件，提供系统状态监控功能
 */

import React from 'react'
import { Container, Title, Text, Stack } from '@mantine/core'
import SystemStatusPanel from '@/components/System/SystemStatusPanel'

const SystemStatusPage: React.FC = () => {
  return (
    <Container size="xl" py="md">
      <Stack gap="lg">
        <div>
          <Title order={2} mb="xs">
            系统状态监控
          </Title>
          <Text c="dimmed" size="sm">
            实时监控系统性能、网络状态、安全会话和批量处理状态
          </Text>
        </div>

        <SystemStatusPanel />
      </Stack>
    </Container>
  )
}

export default SystemStatusPage
