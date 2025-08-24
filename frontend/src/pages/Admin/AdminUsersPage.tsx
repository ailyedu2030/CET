/**
 * 管理员用户管理页面
 */
import { Container, Title, Text, Card } from '@mantine/core'

export function AdminUsersPage(): JSX.Element {
  return (
    <Container size="xl">
      <Title order={1} mb="lg">
        用户管理
      </Title>

      <Card shadow="sm" padding="lg" radius="md" withBorder>
        <Text size="lg" fw={500} mb="md">
          用户管理功能
        </Text>
        <Text c="dimmed">此功能将在第二阶段开发中实现，包括用户注册审核、权限管理等功能。</Text>
      </Card>
    </Container>
  )
}
