/**
 * 需求25：错题强化与自适应学习页面 - 学生端
 *
 * 实现学生端的自适应学习功能，包括智能诊断、记忆优化、动态难度调节等
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
  Progress,
  Stack,
  Alert,
  LoadingOverlay,
  RingProgress,
  Center,
  Timeline,
  Divider,

} from '@mantine/core'
import {
  IconBrain,
  IconTarget,
  IconTrendingUp,
  IconClock,
  IconStar,
  IconChartLine,
  IconRefresh,
  IconPlayerPlay,
  IconCheck,
  IconBulb,

} from '@tabler/icons-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notifications } from '@mantine/notifications'

import { adaptiveLearningApi } from '@/api/adaptiveLearning'
import { useAuthStore } from '@/stores/authStore'

export function AdaptiveLearningPage(): JSX.Element {
  // 状态管理
  const [refreshKey, setRefreshKey] = useState(0)

  const { user } = useAuthStore()
  const queryClient = useQueryClient()

  // 查询错题分析
  const {
    data: errorAnalysis,
    isLoading: errorAnalysisLoading,
  } = useQuery({
    queryKey: ['error-analysis', user?.id, refreshKey],
    queryFn: () => adaptiveLearningApi.getErrorAnalysis({
      student_id: parseInt(user!.id),
      analysis_days: 30,
      include_categories: true,
      include_trends: true,
    }),
    enabled: !!user?.id,
  })

  // 查询知识缺口
  const {
    data: knowledgeGaps,
    isLoading: knowledgeGapsLoading,
  } = useQuery({
    queryKey: ['knowledge-gaps', user?.id],
    queryFn: () => adaptiveLearningApi.getKnowledgeGaps(parseInt(user!.id)),
    enabled: !!user?.id,
  })

  // 查询学习策略
  const {
    data: learningStrategy,
    isLoading: strategyLoading,
  } = useQuery({
    queryKey: ['learning-strategy', user?.id],
    queryFn: () => adaptiveLearningApi.getLearningStrategy(parseInt(user!.id)),
    enabled: !!user?.id,
  })

  // 查询强化计划
  const {
    data: _reinforcementPlan,
    isLoading: planLoading,
  } = useQuery({
    queryKey: ['reinforcement-plan', user?.id],
    queryFn: () => adaptiveLearningApi.getReinforcementPlan(parseInt(user!.id)),
    enabled: !!user?.id,
  })

  // 查询复习计划
  const {
    data: _reviewSchedule,
    isLoading: reviewLoading,
  } = useQuery({
    queryKey: ['review-schedule', user?.id],
    queryFn: () => adaptiveLearningApi.getReviewSchedule({
      student_id: parseInt(user!.id),
      schedule_days: 7,
      daily_time_limit: 60,
      priority_focus: 'weak_areas',
    }),
    enabled: !!user?.id,
  })

  // 触发自适应调整
  const triggerAdaptationMutation = useMutation({
    mutationFn: () => adaptiveLearningApi.triggerAdaptation(parseInt(user!.id)),
    onSuccess: () => {
      notifications.show({
        title: '成功',
        message: '自适应调整已触发，系统正在重新分析您的学习情况',
        color: 'green',
      })
      setRefreshKey(prev => prev + 1)
      queryClient.invalidateQueries({ queryKey: ['error-analysis'] })
      queryClient.invalidateQueries({ queryKey: ['knowledge-gaps'] })
    },
    onError: (error: any) => {
      notifications.show({
        title: '调整失败',
        message: error.response?.data?.detail || error.message || '自适应调整失败，请稍后重试',
        color: 'red',
      })
    },
  })

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1)
    queryClient.invalidateQueries({ queryKey: ['error-analysis'] })
    queryClient.invalidateQueries({ queryKey: ['knowledge-gaps'] })
    queryClient.invalidateQueries({ queryKey: ['learning-strategy'] })
    queryClient.invalidateQueries({ queryKey: ['reinforcement-plan'] })
    queryClient.invalidateQueries({ queryKey: ['review-schedule'] })
  }

  const handleStartAdaptiveLearning = () => {
    triggerAdaptationMutation.mutate()
  }

  // 模拟数据
  const mockLearningPath = [
    {
      id: '1',
      title: '基础词汇强化',
      status: 'completed',
      progress: 100,
      estimatedTime: '30分钟',
    },
    {
      id: '2',
      title: '阅读理解技巧',
      status: 'in-progress',
      progress: 65,
      estimatedTime: '45分钟',
    },
    {
      id: '3',
      title: '写作结构训练',
      status: 'pending',
      progress: 0,
      estimatedTime: '60分钟',
    },
    {
      id: '4',
      title: '听力理解提升',
      status: 'pending',
      progress: 0,
      estimatedTime: '40分钟',
    },
  ]

  const mockWeakAreas = [
    { area: '词汇运用', score: 65, improvement: '+5%' },
    { area: '语法结构', score: 72, improvement: '+8%' },
    { area: '阅读速度', score: 58, improvement: '+12%' },
    { area: '写作逻辑', score: 69, improvement: '+3%' },
  ]

  const isLoading = errorAnalysisLoading || knowledgeGapsLoading || strategyLoading || planLoading || reviewLoading

  return (
    <Container size="xl" py="lg">
      <LoadingOverlay visible={isLoading} />

      {/* 页面头部 */}
      <Group justify="space-between" mb="xl">
        <div>
          <Title order={1}>智能自适应学习</Title>
          <Text c="dimmed" size="sm">
            基于AI的个性化学习路径和智能推荐系统
          </Text>
        </div>
        <Group>
          <Button
            leftSection={<IconRefresh size={16} />}
            variant="light"
            onClick={handleRefresh}
          >
            刷新
          </Button>
          <Button
            leftSection={<IconPlayerPlay size={16} />}
            onClick={handleStartAdaptiveLearning}
            loading={triggerAdaptationMutation.isPending}
          >
            开始自适应学习
          </Button>
        </Group>
      </Group>

      {/* 学习状态概览 */}
      <Grid mb="xl">
        <Grid.Col span={3}>
          <Card withBorder p="md">
            <Group justify="space-between">
              <div>
                <Text size="sm" c="dimmed">
                  当前难度等级
                </Text>
                <Text size="xl" fw={700}>
                  {learningStrategy?.current_strategy?.parameters?.['difficulty_level'] || 3}/5
                </Text>
              </div>
              <RingProgress
                size={60}
                thickness={6}
                sections={[{ value: ((learningStrategy?.current_strategy?.parameters?.['difficulty_level'] || 3) / 5) * 100, color: 'blue' }]}
                label={
                  <Center>
                    <IconTarget size={16} color="blue" />
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
                  学习强度
                </Text>
                <Text size="xl" fw={700}>
                  {Math.round((learningStrategy?.effectiveness_score || 0.75) * 100)}%
                </Text>
              </div>
              <RingProgress
                size={60}
                thickness={6}
                sections={[{ value: (learningStrategy?.effectiveness_score || 0.75) * 100, color: 'orange' }]}
                label={
                  <Center>
                    <IconTrendingUp size={16} color="orange" />
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
                  算法准确度
                </Text>
                <Text size="xl" fw={700}>
                  {Math.round((errorAnalysis?.total_errors ? (1 - errorAnalysis.total_errors / 100) : 0.88) * 100)}%
                </Text>
              </div>
              <RingProgress
                size={60}
                thickness={6}
                sections={[{ value: (errorAnalysis?.total_errors ? (1 - errorAnalysis.total_errors / 100) : 0.88) * 100, color: 'green' }]}
                label={
                  <Center>
                    <IconBrain size={16} color="green" />
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
                  掌握进度
                </Text>
                <Text size="xl" fw={700}>
                  {knowledgeGaps ? Math.round((1 - knowledgeGaps.length / 20) * 100) : 92}%
                </Text>
              </div>
              <RingProgress
                size={60}
                thickness={6}
                sections={[{ value: knowledgeGaps ? (1 - knowledgeGaps.length / 20) * 100 : 92, color: 'purple' }]}
                label={
                  <Center>
                    <IconStar size={16} color="purple" />
                  </Center>
                }
              />
            </Group>
          </Card>
        </Grid.Col>
      </Grid>

      <Grid>
        {/* 个性化学习路径 */}
        <Grid.Col span={8}>
          <Card withBorder p="md" h="100%">
            <Group justify="space-between" mb="md">
              <Text fw={500} size="lg">
                个性化学习路径
              </Text>
              <Badge color="blue">AI推荐</Badge>
            </Group>

            <Timeline active={1} bulletSize={24} lineWidth={2}>
              {mockLearningPath.map((item, _index) => (
                <Timeline.Item
                  key={item.id}
                  bullet={
                    item.status === 'completed' ? (
                      <IconCheck size={12} />
                    ) : item.status === 'in-progress' ? (
                      <IconPlayerPlay size={12} />
                    ) : (
                      <IconClock size={12} />
                    )
                  }
                  title={item.title}
                  color={
                    item.status === 'completed'
                      ? 'green'
                      : item.status === 'in-progress'
                      ? 'blue'
                      : 'gray'
                  }
                >
                  <Group justify="space-between" mb="xs">
                    <Text size="sm" c="dimmed">
                      预计时间: {item.estimatedTime}
                    </Text>
                    <Badge
                      size="sm"
                      color={
                        item.status === 'completed'
                          ? 'green'
                          : item.status === 'in-progress'
                          ? 'blue'
                          : 'gray'
                      }
                    >
                      {item.status === 'completed'
                        ? '已完成'
                        : item.status === 'in-progress'
                        ? '进行中'
                        : '待开始'}
                    </Badge>
                  </Group>
                  {item.progress > 0 && (
                    <Progress value={item.progress} size="sm" color="blue" />
                  )}
                  {item.status === 'in-progress' && (
                    <Button size="xs" variant="light" mt="xs">
                      继续学习
                    </Button>
                  )}
                </Timeline.Item>
              ))}
            </Timeline>
          </Card>
        </Grid.Col>

        {/* 薄弱环节分析 */}
        <Grid.Col span={4}>
          <Card withBorder p="md" h="100%">
            <Group justify="space-between" mb="md">
              <Text fw={500} size="lg">
                薄弱环节分析
              </Text>
              <IconChartLine size={20} color="orange" />
            </Group>

            <Stack gap="md">
              {mockWeakAreas.map((area, index) => (
                <div key={index}>
                  <Group justify="space-between" mb="xs">
                    <Text size="sm" fw={500}>
                      {area.area}
                    </Text>
                    <Group gap="xs">
                      <Text size="sm" c="dimmed">
                        {area.score}分
                      </Text>
                      <Badge size="sm" color="green">
                        {area.improvement}
                      </Badge>
                    </Group>
                  </Group>
                  <Progress
                    value={area.score}
                    size="sm"
                    color={area.score >= 70 ? 'green' : area.score >= 60 ? 'orange' : 'red'}
                  />
                </div>
              ))}
            </Stack>

            <Divider my="md" />

            <Alert icon={<IconBulb size={16} />} color="blue" variant="light">
              <Text size="sm">
                建议重点关注阅读速度和词汇运用，这两个方面的提升将显著改善整体表现。
              </Text>
            </Alert>
          </Card>
        </Grid.Col>

        {/* 智能推荐 */}
        <Grid.Col span={12}>
          <Card withBorder p="md">
            <Group justify="space-between" mb="md">
              <Text fw={500} size="lg">
                智能推荐内容
              </Text>
              <Badge color="purple">个性化</Badge>
            </Group>

            <Grid>
              {errorAnalysis?.improvement_suggestions?.slice(0, 4).map((suggestion: string, index: number) => (
                <Grid.Col key={index} span={3}>
                  <Card withBorder p="sm" h="100%">
                    <Stack gap="xs">
                      <Group justify="space-between">
                        <Text size="sm" fw={500} lineClamp={2}>
                          改进建议 {index + 1}
                        </Text>
                        <Badge size="xs" color="blue">
                          建议
                        </Badge>
                      </Group>
                      <Text size="xs" c="dimmed" lineClamp={3}>
                        {suggestion}
                      </Text>
                      <Group justify="space-between">
                        <Text size="xs" c="dimmed">
                          优先级: 高
                        </Text>
                        <Text size="xs" c="dimmed">
                          建议时长: 15分钟
                        </Text>
                      </Group>
                      <Button size="xs" variant="light" fullWidth>
                        开始学习
                      </Button>
                    </Stack>
                  </Card>
                </Grid.Col>
              )) || (
                // 模拟推荐内容
                Array.from({ length: 4 }, (_, index) => (
                  <Grid.Col key={index} span={3}>
                    <Card withBorder p="sm" h="100%">
                      <Stack gap="xs">
                        <Group justify="space-between">
                          <Text size="sm" fw={500}>
                            推荐练习 {index + 1}
                          </Text>
                          <Badge size="xs" color="blue">
                            练习
                          </Badge>
                        </Group>
                        <Text size="xs" c="dimmed">
                          基于您的学习情况，推荐此内容以提升相关技能。
                        </Text>
                        <Group justify="space-between">
                          <Text size="xs" c="dimmed">
                            难度: 中等
                          </Text>
                          <Text size="xs" c="dimmed">
                            20分钟
                          </Text>
                        </Group>
                        <Button size="xs" variant="light" fullWidth>
                          开始学习
                        </Button>
                      </Stack>
                    </Card>
                  </Grid.Col>
                ))
              )}
            </Grid>
          </Card>
        </Grid.Col>
      </Grid>
    </Container>
  )
}
