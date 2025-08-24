/**
 * 学生学习进度页面
 */
import {
  Container,
  Title,
  Text,
  Card,
  Grid,
  Group,
  Progress,
  Badge,
  Stack,
  RingProgress,
  Center,
  ActionIcon,
  Tooltip,
} from '@mantine/core'
import {
  IconTrendingUp,
  IconTarget,
  IconClock,
  IconBrain,
  IconRefresh,
  IconChartLine,
} from '@tabler/icons-react'
import { useQuery } from '@tanstack/react-query'
import { trainingApi } from '@/api/training'

export function StudentProgressPage(): JSX.Element {
  // 获取训练统计数据
  const { data: stats, refetch } = useQuery({
    queryKey: ['training-stats'],
    queryFn: () => trainingApi.getTrainingStats(),
  })

  const progressData = [
    {
      label: '词汇掌握',
      value: 75,
      color: 'blue',
      icon: IconBrain,
    },
    {
      label: '听力水平',
      value: 68,
      color: 'green',
      icon: IconTarget,
    },
    {
      label: '阅读理解',
      value: 82,
      color: 'orange',
      icon: IconChartLine,
    },
    {
      label: '写作能力',
      value: 60,
      color: 'violet',
      icon: IconTrendingUp,
    },
  ]

  return (
    <Container size="xl" py="md">
      <Group justify="space-between" mb="lg">
        <Title order={2}>学习进度</Title>
        <Tooltip label="刷新数据">
          <ActionIcon variant="light" size="lg" onClick={() => refetch()}>
            <IconRefresh size={20} />
          </ActionIcon>
        </Tooltip>
      </Group>

      <Grid>
        {/* 总体进度 */}
        <Grid.Col span={{ base: 12, md: 6 }}>
          <Card shadow="sm" padding="lg" radius="md" withBorder h="100%">
            <Group justify="space-between" mb="md">
              <Text size="lg" fw={600}>
                总体进度
              </Text>
              <Badge color="blue" variant="light">
                Level {stats?.level || 1}
              </Badge>
            </Group>

            <Center mb="md">
              <RingProgress
                size={120}
                thickness={8}
                sections={[
                  { value: stats?.exp ? (stats.exp / stats.nextLevelExp) * 100 : 0, color: 'blue' },
                ]}
                label={
                  <Center>
                    <Text size="sm" fw={700}>
                      {stats?.exp || 0} / {stats?.nextLevelExp || 100}
                    </Text>
                  </Center>
                }
              />
            </Center>

            <Stack gap="xs">
              <Group justify="space-between">
                <Text size="sm" c="dimmed">
                  完成训练
                </Text>
                <Text size="sm" fw={500}>
                  {stats?.completedSessions || 0} 次
                </Text>
              </Group>
              <Group justify="space-between">
                <Text size="sm" c="dimmed">
                  平均分数
                </Text>
                <Text size="sm" fw={500}>
                  {stats?.averageScore?.toFixed(1) || '0.0'} 分
                </Text>
              </Group>
              <Group justify="space-between">
                <Text size="sm" c="dimmed">
                  学习天数
                </Text>
                <Text size="sm" fw={500}>
                  {stats?.streak || 0} 天
                </Text>
              </Group>
            </Stack>
          </Card>
        </Grid.Col>

        {/* 能力分析 */}
        <Grid.Col span={{ base: 12, md: 6 }}>
          <Card shadow="sm" padding="lg" radius="md" withBorder h="100%">
            <Text size="lg" fw={600} mb="md">
              能力分析
            </Text>

            <Stack gap="md">
              {progressData.map((item, index) => {
                const IconComponent = item.icon
                return (
                  <div key={index}>
                    <Group justify="space-between" mb="xs">
                      <Group gap="xs">
                        <IconComponent size={16} color={item.color} />
                        <Text size="sm">{item.label}</Text>
                      </Group>
                      <Text size="sm" fw={500}>
                        {item.value}%
                      </Text>
                    </Group>
                    <Progress value={item.value} color={item.color} size="sm" />
                  </div>
                )
              })}
            </Stack>
          </Card>
        </Grid.Col>

        {/* 学习统计 */}
        <Grid.Col span={12}>
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Text size="lg" fw={600} mb="md">
              学习统计
            </Text>

            <Grid>
              <Grid.Col span={{ base: 6, md: 3 }}>
                <Stack gap="xs" align="center">
                  <IconClock size={32} color="blue" />
                  <Text size="xl" fw={700} c="blue">
                    {Math.floor((stats?.totalTime || 0) / 60)}h
                  </Text>
                  <Text size="sm" c="dimmed">
                    总学习时长
                  </Text>
                </Stack>
              </Grid.Col>

              <Grid.Col span={{ base: 6, md: 3 }}>
                <Stack gap="xs" align="center">
                  <IconTarget size={32} color="green" />
                  <Text size="xl" fw={700} c="green">
                    {stats?.totalSessions || 0}
                  </Text>
                  <Text size="sm" c="dimmed">
                    训练次数
                  </Text>
                </Stack>
              </Grid.Col>

              <Grid.Col span={{ base: 6, md: 3 }}>
                <Stack gap="xs" align="center">
                  <IconTrendingUp size={32} color="orange" />
                  <Text size="xl" fw={700} c="orange">
                    {stats?.streak || 0}
                  </Text>
                  <Text size="sm" c="dimmed">
                    连续学习
                  </Text>
                </Stack>
              </Grid.Col>

              <Grid.Col span={{ base: 6, md: 3 }}>
                <Stack gap="xs" align="center">
                  <IconBrain size={32} color="violet" />
                  <Text size="xl" fw={700} c="violet">
                    {stats?.averageScore?.toFixed(0) || '0'}
                  </Text>
                  <Text size="sm" c="dimmed">
                    平均分数
                  </Text>
                </Stack>
              </Grid.Col>
            </Grid>
          </Card>
        </Grid.Col>
      </Grid>
    </Container>
  )
}
