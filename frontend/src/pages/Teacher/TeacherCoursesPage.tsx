/**
 * 教师课程管理页面
 */
import { Container, Title, Text, Card } from '@mantine/core'

export function TeacherCoursesPage(): JSX.Element {
  return (
    <Container size="xl">
      <Title order={1} mb="lg">
        我的课程
      </Title>

      <Card shadow="sm" padding="lg" radius="md" withBorder>
        <Text size="lg" fw={500} mb="md">
          课程管理功能
        </Text>
        <Text c="dimmed">
          此功能将在第三阶段开发中实现，包括教学计划、资源管理、智能调整等功能。
        </Text>
      </Card>
    </Container>
  )
}
