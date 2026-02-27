/**
 * 需求26：英语四级写作标准库 - 主页面
 * 
 * 实现写作训练的主要功能界面
 */

import { useState } from 'react'
import {
  Container,
  Title,
  Text,
  Grid,
  Card,
  Button,
  Group,
  Badge,
  Stack,
  Tabs,
  ActionIcon,
  Tooltip,
  Alert,
  LoadingOverlay,
  RingProgress,
  Center,
  Timeline,
} from '@mantine/core'
import {
  IconPencil,
  IconTemplate,
  IconBook,
  IconChartLine,
  IconBulb,
  IconClock,
  IconStar,
  IconTarget,
  IconTrendingUp,
  IconCheck,
  IconAlertCircle,
  IconSparkles,
  IconFileText,
  IconSettings,
} from '@tabler/icons-react'
import { useQuery } from '@tanstack/react-query'

import { writingApi } from '@/api/writing'
import { useAuthStore } from '@/stores/authStore'

export function WritingPage(): JSX.Element {
  // 状态管理
  const [activeTab, setActiveTab] = useState<string>('overview')
  const { user } = useAuthStore()

  // 查询写作统计
  const {
    data: statistics,
    isLoading: statisticsLoading,
  } = useQuery({
    queryKey: ['writing-statistics', user?.id],
    queryFn: () => writingApi.getStatistics(),
    enabled: !!user?.id,
  })

  // 查询写作推荐
  const {
    data: recommendations,
    isLoading: recommendationsLoading,
  } = useQuery({
    queryKey: ['writing-recommendations', user?.id],
    queryFn: () => writingApi.getRecommendations(),
    enabled: !!user?.id,
  })

  // 查询最近的写作提交
  const {
    data: recentSubmissions,
    isLoading: submissionsLoading,
  } = useQuery({
    queryKey: ['writing-submissions', user?.id],
    queryFn: () => writingApi.getMySubmissions({ limit: 5 }),
    enabled: !!user?.id,
  })

  const isLoading = statisticsLoading || recommendationsLoading || submissionsLoading

  return (
    <Container size="xl" py="lg">
      <LoadingOverlay visible={isLoading} />

      {/* 页面标题 */}
      <Group justify="space-between" mb="lg">
        <div>
          <Title order={2}>英语四级写作标准库</Title>
          <Text size="lg" c="dimmed">
            专业的写作训练系统，提升你的英语写作能力
          </Text>
        </div>
        <Group>
          <Tooltip label="写作技巧">
            <ActionIcon variant="light" size="lg">
              <IconBulb size={20} />
            </ActionIcon>
          </Tooltip>
          <Tooltip label="写作设置">
            <ActionIcon variant="light" size="lg">
              <IconSettings size={20} />
            </ActionIcon>
          </Tooltip>
        </Group>
      </Group>

      <Tabs value={activeTab} onChange={(value) => setActiveTab(value || 'overview')}>
        <Tabs.List>
          <Tabs.Tab value="overview" leftSection={<IconChartLine size={16} />}>
            概览
          </Tabs.Tab>
          <Tabs.Tab value="practice" leftSection={<IconPencil size={16} />}>
            写作练习
          </Tabs.Tab>
          <Tabs.Tab value="templates" leftSection={<IconTemplate size={16} />}>
            模板库
          </Tabs.Tab>
          <Tabs.Tab value="vocabulary" leftSection={<IconBook size={16} />}>
            写作词汇
          </Tabs.Tab>
          <Tabs.Tab value="analysis" leftSection={<IconTrendingUp size={16} />}>
            写作分析
          </Tabs.Tab>
        </Tabs.List>

        {/* 概览页面 */}
        <Tabs.Panel value="overview">
          <Stack gap="lg" mt="lg">
            {/* 写作统计卡片 */}
            <Grid>
              <Grid.Col span={3}>
                <Card withBorder p="md">
                  <Group justify="space-between">
                    <div>
                      <Text size="sm" c="dimmed">
                        总提交数
                      </Text>
                      <Text size="xl" fw={700}>
                        {statistics?.total_submissions || 0}
                      </Text>
                    </div>
                    <RingProgress
                      size={60}
                      thickness={6}
                      sections={[{ value: Math.min((statistics?.total_submissions || 0) * 2, 100), color: 'blue' }]}
                      label={
                        <Center>
                          <IconFileText size={16} color="blue" />
                        </Center>
                      }
                    />
                  </Group>
                </Card>
              </Grid.Col>

              <Grid.Col span={3}>
                <Card withBorder p="md">
                  <Group justify="space-between">
                    <div>
                      <Text size="sm" c="dimmed">
                        平均分数
                      </Text>
                      <Text size="xl" fw={700}>
                        {Math.round((statistics?.average_score || 0) * 10) / 10}
                      </Text>
                    </div>
                    <RingProgress
                      size={60}
                      thickness={6}
                      sections={[{ value: (statistics?.average_score || 0) * 100 / 15, color: 'green' }]}
                      label={
                        <Center>
                          <IconStar size={16} color="green" />
                        </Center>
                      }
                    />
                  </Group>
                </Card>
              </Grid.Col>

              <Grid.Col span={3}>
                <Card withBorder p="md">
                  <Group justify="space-between">
                    <div>
                      <Text size="sm" c="dimmed">
                        优势领域
                      </Text>
                      <Text size="xl" fw={700}>
                        {statistics?.strengths?.length || 0}
                      </Text>
                    </div>
                    <RingProgress
                      size={60}
                      thickness={6}
                      sections={[{ value: (statistics?.strengths?.length || 0) * 20, color: 'orange' }]}
                      label={
                        <Center>
                          <IconTarget size={16} color="orange" />
                        </Center>
                      }
                    />
                  </Group>
                </Card>
              </Grid.Col>

              <Grid.Col span={3}>
                <Card withBorder p="md">
                  <Group justify="space-between">
                    <div>
                      <Text size="sm" c="dimmed">
                        改进空间
                      </Text>
                      <Text size="xl" fw={700}>
                        {statistics?.weaknesses?.length || 0}
                      </Text>
                    </div>
                    <RingProgress
                      size={60}
                      thickness={6}
                      sections={[{ value: Math.max(100 - (statistics?.weaknesses?.length || 0) * 20, 20), color: 'red' }]}
                      label={
                        <Center>
                          <IconAlertCircle size={16} color="red" />
                        </Center>
                      }
                    />
                  </Group>
                </Card>
              </Grid.Col>
            </Grid>

            {/* 智能推荐 */}
            <Card shadow="sm" padding="lg" radius="md" withBorder>
              <Group justify="space-between" mb="md">
                <Group>
                  <IconSparkles size={24} color="purple" />
                  <Text size="lg" fw={600}>
                    智能推荐
                  </Text>
                </Group>
                <Badge color="purple">AI推荐</Badge>
              </Group>
              
              <Grid>
                {recommendations?.recommended_templates?.slice(0, 4).map((template) => (
                  <Grid.Col key={template.id} span={3}>
                    <Card withBorder p="sm" h="100%">
                      <Stack gap="xs">
                        <Group justify="space-between">
                          <Text size="sm" fw={500} lineClamp={2}>
                            {template.template_name}
                          </Text>
                          <Badge size="xs" color="blue">
                            {template.writing_type}
                          </Badge>
                        </Group>
                        <Text size="xs" c="dimmed" lineClamp={3}>
                          {template.usage_instructions || '专业的写作模板，帮助您快速构建文章结构'}
                        </Text>
                        <Group justify="space-between">
                          <Text size="xs" c="dimmed">
                            难度: {template.difficulty}
                          </Text>
                          <Text size="xs" c="dimmed">
                            评分: {Math.round(template.average_score * 10) / 10}
                          </Text>
                        </Group>
                        <Button size="xs" variant="light" fullWidth>
                          使用模板
                        </Button>
                      </Stack>
                    </Card>
                  </Grid.Col>
                )) || (
                  <Grid.Col span={12}>
                    <Center h={200}>
                      <Text c="dimmed">暂无推荐模板</Text>
                    </Center>
                  </Grid.Col>
                )}
              </Grid>
            </Card>

            {/* 最近写作记录 */}
            <Card shadow="sm" padding="lg" radius="md" withBorder>
              <Group justify="space-between" mb="md">
                <Group>
                  <IconClock size={24} color="blue" />
                  <Text size="lg" fw={600}>
                    最近写作记录
                  </Text>
                </Group>
                <Button variant="light" size="sm">
                  查看全部
                </Button>
              </Group>
              
              <Timeline active={1} bulletSize={24} lineWidth={2}>
                {recentSubmissions?.data?.map((submission) => (
                  <Timeline.Item
                    key={submission.id}
                    bullet={<IconCheck size={12} />}
                    title={`写作练习 #${submission.id}`}
                  >
                    <Text size="sm" c="dimmed">
                      分数: {submission.total_score}/15 | 
                      字数: {submission.word_count} | 
                      用时: {submission.writing_time_minutes}分钟
                    </Text>
                    <Text size="xs" c="dimmed">
                      {new Date(submission.submitted_at).toLocaleDateString()}
                    </Text>
                  </Timeline.Item>
                )) || (
                  <Timeline.Item bullet={<IconAlertCircle size={12} />} title="暂无写作记录">
                    <Text size="sm" c="dimmed">
                      开始您的第一次写作练习吧！
                    </Text>
                  </Timeline.Item>
                )}
              </Timeline>
            </Card>
          </Stack>
        </Tabs.Panel>

        {/* 其他标签页内容将在后续实现 */}
        <Tabs.Panel value="practice">
          <Alert icon={<IconBulb size={16} />} color="blue" mt="lg">
            写作练习功能正在开发中，敬请期待！
          </Alert>
        </Tabs.Panel>

        <Tabs.Panel value="templates">
          <Alert icon={<IconTemplate size={16} />} color="blue" mt="lg">
            模板库功能正在开发中，敬请期待！
          </Alert>
        </Tabs.Panel>

        <Tabs.Panel value="vocabulary">
          <Alert icon={<IconBook size={16} />} color="blue" mt="lg">
            写作词汇功能正在开发中，敬请期待！
          </Alert>
        </Tabs.Panel>

        <Tabs.Panel value="analysis">
          <Alert icon={<IconTrendingUp size={16} />} color="blue" mt="lg">
            写作分析功能正在开发中，敬请期待！
          </Alert>
        </Tabs.Panel>
      </Tabs>
    </Container>
  )
}
