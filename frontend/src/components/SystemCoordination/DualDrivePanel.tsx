/**
 * 需求16：双驱动机制面板组件
 * 
 * 实现学生端驱动和教师端驱动的可视化管理界面
 */

import { useState } from 'react'
import {
  Card,
  Text,
  Group,
  Badge,
  Button,
  Stack,
  Progress,
  Grid,
  Alert,
  ActionIcon,
  RingProgress,
  Center,
  Divider,
  Select,
} from '@mantine/core'
import {
  IconBrain,
  IconUsers,
  IconRefresh,
  IconPlayerPlay,
  IconChartLine,
  IconAlertTriangle,
} from '@tabler/icons-react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { notifications } from '@mantine/notifications'

import { learningAnalysisApi, systemHealthApi } from '@/api/systemCoordination'

interface DualDrivePanelProps {
  classId?: number
  courseId?: number
  onRefresh?: () => void
}

export function DualDrivePanel({ classId, courseId, onRefresh }: DualDrivePanelProps): JSX.Element {
  const [selectedPeriod, setSelectedPeriod] = useState<string>('7')

  // 查询系统健康状态
  const {
    data: dualDriveData,
    isLoading,
    refetch,
  } = useQuery({
    queryKey: ['system-health-status', classId, selectedPeriod],
    queryFn: () => systemHealthApi.getCoordinationHealth(),
    enabled: !!classId,
  })

  // 触发学生端驱动
  const triggerStudentDriveMutation = useMutation({
    mutationFn: (_studentId: number) => systemHealthApi.getAIStatus(),
    onSuccess: () => {
      notifications.show({
        title: '成功',
        message: '学生端驱动已触发',
        color: 'green',
      })
      refetch()
      onRefresh?.()
    },
    onError: (error: any) => {
      notifications.show({
        title: '错误',
        message: error.response?.data?.detail || '学生端驱动触发失败',
        color: 'red',
      })
    },
  })

  // 触发教师端驱动
  const triggerTeacherDriveMutation = useMutation({
    mutationFn: () => learningAnalysisApi.getComprehensiveAnalysis(classId!, courseId!),
    onSuccess: () => {
      notifications.show({
        title: '成功',
        message: '教师端驱动已触发',
        color: 'green',
      })
      refetch()
      onRefresh?.()
    },
    onError: (error: any) => {
      notifications.show({
        title: '错误',
        message: error.response?.data?.detail || '教师端驱动触发失败',
        color: 'red',
      })
    },
  })

  // 查询数据同步状态
  const { data: _syncStatus } = useQuery({
    queryKey: ['data-sync-status', classId],
    queryFn: () => systemHealthApi.getSystemCapabilities(),
    enabled: !!classId,
    refetchInterval: 30000, // 30秒刷新一次
  })

  const periodOptions = [
    { value: '1', label: '1天' },
    { value: '3', label: '3天' },
    { value: '7', label: '7天' },
    { value: '14', label: '14天' },
    { value: '30', label: '30天' },
  ]

  const handleTriggerStudentDrive = () => {
    if (classId) {
      triggerStudentDriveMutation.mutate(classId)
    }
  }

  const handleTriggerTeacherDrive = () => {
    if (classId && courseId) {
      triggerTeacherDriveMutation.mutate()
    }
  }

  const getSyncStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'green'
      case 'pending':
        return 'orange'
      case 'failed':
        return 'red'
      default:
        return 'gray'
    }
  }

  const getSyncStatusText = (status: string) => {
    switch (status) {
      case 'completed':
        return '已完成'
      case 'pending':
        return '进行中'
      case 'failed':
        return '失败'
      default:
        return '未知'
    }
  }

  if (!classId) {
    return (
      <Alert icon={<IconAlertTriangle size={16} />} color="orange">
        请先选择班级以查看双驱动机制状态
      </Alert>
    )
  }

  return (
    <Stack gap="md">
      {/* 控制面板 */}
      <Card withBorder p="md">
        <Group justify="space-between" mb="md">
          <Text fw={500} size="lg">
            双驱动机制控制面板
          </Text>
          <Group>
            <Select
              placeholder="分析周期"
              data={periodOptions}
              value={selectedPeriod}
              onChange={value => setSelectedPeriod(value || '7')}
              w={120}
            />
            <ActionIcon
              variant="light"
              onClick={() => refetch()}
              loading={isLoading}
            >
              <IconRefresh size={16} />
            </ActionIcon>
          </Group>
        </Group>

        <Grid>
          <Grid.Col span={6}>
            <Card withBorder p="sm" bg="blue.0">
              <Group justify="space-between" mb="xs">
                <Group>
                  <IconUsers size={20} color="blue" />
                  <Text fw={500} c="blue">
                    学生端驱动
                  </Text>
                </Group>
                <Badge color="blue" size="sm">
                  自适应
                </Badge>
              </Group>
              <Text size="sm" c="dimmed" mb="md">
                基于学生学习数据的实时反馈和个性化调整
              </Text>
              <Button
                fullWidth
                variant="light"
                color="blue"
                leftSection={<IconPlayerPlay size={16} />}
                onClick={handleTriggerStudentDrive}
                loading={triggerStudentDriveMutation.isPending}
              >
                触发学生端驱动
              </Button>
            </Card>
          </Grid.Col>

          <Grid.Col span={6}>
            <Card withBorder p="sm" bg="green.0">
              <Group justify="space-between" mb="xs">
                <Group>
                  <IconBrain size={20} color="green" />
                  <Text fw={500} c="green">
                    教师端驱动
                  </Text>
                </Group>
                <Badge color="green" size="sm">
                  智能分析
                </Badge>
              </Group>
              <Text size="sm" c="dimmed" mb="md">
                基于教学数据的策略优化和内容调整建议
              </Text>
              <Button
                fullWidth
                variant="light"
                color="green"
                leftSection={<IconChartLine size={16} />}
                onClick={handleTriggerTeacherDrive}
                loading={triggerTeacherDriveMutation.isPending}
                disabled={!courseId}
              >
                触发教师端驱动
              </Button>
            </Card>
          </Grid.Col>
        </Grid>
      </Card>

      {/* 驱动状态详情 */}
      <Grid>
        <Grid.Col span={6}>
          <Card withBorder p="md" h="100%">
            <Group justify="space-between" mb="md">
              <Text fw={500}>学生端驱动状态</Text>
              <Badge color="blue">
                {dualDriveData?.student_drive ? '活跃' : '待激活'}
              </Badge>
            </Group>

            <Stack gap="sm">
              <Group justify="space-between">
                <Text size="sm">实时反馈</Text>
                <Group gap="xs">
                  <Text size="sm" fw={500}>
                    {dualDriveData?.student_drive?.real_time_feedback?.length || 0}
                  </Text>
                  <Text size="sm" c="dimmed">
                    条
                  </Text>
                </Group>
              </Group>

              <Group justify="space-between">
                <Text size="sm">学习建议</Text>
                <Group gap="xs">
                  <Text size="sm" fw={500}>
                    {dualDriveData?.student_drive?.learning_suggestions?.length || 0}
                  </Text>
                  <Text size="sm" c="dimmed">
                    条
                  </Text>
                </Group>
              </Group>

              <Group justify="space-between">
                <Text size="sm">难度调整</Text>
                <Group gap="xs">
                  <Text size="sm" fw={500}>
                    {dualDriveData?.student_drive?.difficulty_adjustments?.length || 0}
                  </Text>
                  <Text size="sm" c="dimmed">
                    次
                  </Text>
                </Group>
              </Group>

              <Group justify="space-between">
                <Text size="sm">自适应内容</Text>
                <Group gap="xs">
                  <Text size="sm" fw={500}>
                    {dualDriveData?.student_drive?.adaptive_content?.length || 0}
                  </Text>
                  <Text size="sm" c="dimmed">
                    项
                  </Text>
                </Group>
              </Group>
            </Stack>

            <Divider my="md" />

            <Group justify="center">
              <RingProgress
                size={80}
                thickness={8}
                sections={[
                  {
                    value: dualDriveData?.student_drive ? 85 : 0,
                    color: 'blue',
                  },
                ]}
                label={
                  <Center>
                    <Text size="xs" ta="center">
                      活跃度
                      <br />
                      {dualDriveData?.student_drive ? '85%' : '0%'}
                    </Text>
                  </Center>
                }
              />
            </Group>
          </Card>
        </Grid.Col>

        <Grid.Col span={6}>
          <Card withBorder p="md" h="100%">
            <Group justify="space-between" mb="md">
              <Text fw={500}>教师端驱动状态</Text>
              <Badge color="green">
                {dualDriveData?.teacher_drive ? '运行中' : '待启动'}
              </Badge>
            </Group>

            <Stack gap="sm">
              <Group justify="space-between">
                <Text size="sm">数据看板</Text>
                <Badge size="sm" color={dualDriveData?.teacher_drive?.data_dashboard ? 'green' : 'gray'}>
                  {dualDriveData?.teacher_drive?.data_dashboard ? '已更新' : '待更新'}
                </Badge>
              </Group>

              <Group justify="space-between">
                <Text size="sm">教学优化</Text>
                <Group gap="xs">
                  <Text size="sm" fw={500}>
                    {dualDriveData?.teacher_drive?.teaching_optimization?.length || 0}
                  </Text>
                  <Text size="sm" c="dimmed">
                    项
                  </Text>
                </Group>
              </Group>

              <Group justify="space-between">
                <Text size="sm">内容调整</Text>
                <Group gap="xs">
                  <Text size="sm" fw={500}>
                    {dualDriveData?.teacher_drive?.content_adjustments?.length || 0}
                  </Text>
                  <Text size="sm" c="dimmed">
                    项
                  </Text>
                </Group>
              </Group>

              <Group justify="space-between">
                <Text size="sm">策略推荐</Text>
                <Group gap="xs">
                  <Text size="sm" fw={500}>
                    {dualDriveData?.teacher_drive?.strategy_recommendations?.length || 0}
                  </Text>
                  <Text size="sm" c="dimmed">
                    条
                  </Text>
                </Group>
              </Group>
            </Stack>

            <Divider my="md" />

            <Group justify="center">
              <RingProgress
                size={80}
                thickness={8}
                sections={[
                  {
                    value: dualDriveData?.teacher_drive ? 92 : 0,
                    color: 'green',
                  },
                ]}
                label={
                  <Center>
                    <Text size="xs" ta="center">
                      效率
                      <br />
                      {dualDriveData?.teacher_drive ? '92%' : '0%'}
                    </Text>
                  </Center>
                }
              />
            </Group>
          </Card>
        </Grid.Col>
      </Grid>

      {/* 交互周期和闭环反馈 */}
      <Card withBorder p="md">
        <Group justify="space-between" mb="md">
          <Text fw={500}>交互周期与闭环反馈</Text>
          <Group>
            <Badge color={getSyncStatusColor(dualDriveData?.interaction_cycle?.sync_status || 'unknown')}>
              {getSyncStatusText(dualDriveData?.interaction_cycle?.sync_status || 'unknown')}
            </Badge>
            <Text size="sm" c="dimmed">
              数据新鲜度: {dualDriveData?.interaction_cycle?.data_freshness_hours || 0} 小时
            </Text>
          </Group>
        </Group>

        <Progress
          value={
            dualDriveData?.interaction_cycle?.sync_status === 'completed'
              ? 100
              : dualDriveData?.interaction_cycle?.sync_status === 'pending'
              ? 60
              : 0
          }
          color={getSyncStatusColor(dualDriveData?.interaction_cycle?.sync_status || 'unknown')}
          size="lg"
          mb="md"
        />

        <Grid>
          <Grid.Col span={3}>
            <Text size="sm" c="dimmed" mb="xs">
              最后同步时间
            </Text>
            <Text size="sm" fw={500}>
              {dualDriveData?.interaction_cycle?.last_sync_time || '未知'}
            </Text>
          </Grid.Col>

          <Grid.Col span={3}>
            <Text size="sm" c="dimmed" mb="xs">
              训练数据
            </Text>
            <Text size="sm" fw={500}>
              {dualDriveData?.closed_loop_feedback?.training_data?.length || 0} 条
            </Text>
          </Grid.Col>

          <Grid.Col span={3}>
            <Text size="sm" c="dimmed" mb="xs">
              分析结果
            </Text>
            <Text size="sm" fw={500}>
              {dualDriveData?.closed_loop_feedback?.analysis_results?.length || 0} 项
            </Text>
          </Grid.Col>

          <Grid.Col span={3}>
            <Text size="sm" c="dimmed" mb="xs">
              教师调整
            </Text>
            <Text size="sm" fw={500}>
              {dualDriveData?.closed_loop_feedback?.teacher_adjustments?.length || 0} 次
            </Text>
          </Grid.Col>
        </Grid>
      </Card>
    </Stack>
  )
}
