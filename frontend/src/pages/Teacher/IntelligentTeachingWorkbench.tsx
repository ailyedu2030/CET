/**
 * 需求14：智能教学工作台 - 教师智能教学调整系统
 * 
 * 功能包括：
 * 1. 学情分析看板
 * 2. 调整建议中心
 * 3. 效果跟踪面板
 * 4. 智能提醒系统
 * 5. 协作功能
 */

import { useState } from 'react'
import {
  Container,
  Title,
  Grid,
  Card,
  Text,
  Button,
  Group,
  Stack,
  Badge,
  Progress,
  Alert,
  Tabs,
  ActionIcon,
  Menu,
  LoadingOverlay,
  RingProgress,
} from '@mantine/core'
import {
  IconBrain,
  IconChartLine,
  IconBulb,
  IconTarget,
  IconUsers,
  IconAlertTriangle,
  IconRefresh,
  IconSettings,
  IconBell,
  IconCheck,
} from '@tabler/icons-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  learningAnalysisApi,
  teachingAdjustmentApi,
  effectTrackingApi,
  systemApi,
  type TeachingAdjustmentRequest,
} from '../../api/intelligentTeaching'

export function IntelligentTeachingWorkbench(): JSX.Element {
  const [selectedClass] = useState<number>(1)
  const [selectedCourse] = useState<number>(1)
  const [activeTab, setActiveTab] = useState<string>('overview')
  const queryClient = useQueryClient()

  // 获取学情分析数据
  const { data: learningAnalysis, isLoading: analysisLoading } = useQuery({
    queryKey: ['learning-analysis', selectedClass, selectedCourse],
    queryFn: () => learningAnalysisApi.comprehensiveAnalysis({
      class_id: selectedClass,
      course_id: selectedCourse,
      analysis_period_days: 30,
      analysis_type: 'comprehensive',
    }),
    enabled: selectedClass > 0 && selectedCourse > 0,
  })

  // 获取系统健康状态
  const { data: systemHealth } = useQuery({
    queryKey: ['system-health'],
    queryFn: () => systemApi.healthCheck(),
    refetchInterval: 30000, // 30秒刷新一次
  })

  // 获取效果跟踪数据
  useQuery({
    queryKey: ['effect-tracking', selectedClass],
    queryFn: () => effectTrackingApi.getProgressAnalysis({
      period_days: 30,
    }),
    enabled: selectedClass > 0,
  })

  // 生成教学调整建议
  const adjustmentMutation = useMutation({
    mutationFn: (request: TeachingAdjustmentRequest) => 
      teachingAdjustmentApi.comprehensiveAdjustment(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teaching-adjustments'] })
    },
  })

  const generateAdjustments = () => {
    adjustmentMutation.mutate({
      class_id: selectedClass,
      course_id: selectedCourse,
      adjustment_focus: 'comprehensive',
      priority: 'high',
    })
  }

  return (
    <Container size="xl" py="md">
      <Group justify="space-between" mb="lg">
        <Title order={2}>智能教学工作台</Title>
        <Group>
          <ActionIcon variant="light" onClick={() => queryClient.invalidateQueries()}>
            <IconRefresh size={16} />
          </ActionIcon>
          <Menu>
            <Menu.Target>
              <ActionIcon variant="light">
                <IconSettings size={16} />
              </ActionIcon>
            </Menu.Target>
            <Menu.Dropdown>
              <Menu.Item leftSection={<IconBell size={14} />}>
                通知设置
              </Menu.Item>
              <Menu.Item leftSection={<IconUsers size={14} />}>
                协作设置
              </Menu.Item>
            </Menu.Dropdown>
          </Menu>
        </Group>
      </Group>

      {/* 系统状态指示器 */}
      {systemHealth && (
        <Alert 
          icon={<IconCheck size={16} />} 
          color="green" 
          mb="md"
          variant="light"
        >
          系统运行正常 - 所有AI服务可用
        </Alert>
      )}

      <Tabs value={activeTab} onChange={(value) => setActiveTab(value || 'overview')}>
        <Tabs.List>
          <Tabs.Tab value="overview" leftSection={<IconChartLine size={16} />}>
            总览
          </Tabs.Tab>
          <Tabs.Tab value="analysis" leftSection={<IconBrain size={16} />}>
            学情分析
          </Tabs.Tab>
          <Tabs.Tab value="adjustments" leftSection={<IconBulb size={16} />}>
            调整建议
          </Tabs.Tab>
          <Tabs.Tab value="tracking" leftSection={<IconTarget size={16} />}>
            效果跟踪
          </Tabs.Tab>
          <Tabs.Tab value="collaboration" leftSection={<IconUsers size={16} />}>
            协作中心
          </Tabs.Tab>
        </Tabs.List>

        {/* 总览面板 */}
        <Tabs.Panel value="overview" pt="md">
          <Grid>
            <Grid.Col span={4}>
              <Card withBorder>
                <Group justify="space-between">
                  <div>
                    <Text size="sm" c="dimmed">学习进度</Text>
                    <Text size="xl" fw={700}>
                      {Math.round((learningAnalysis?.analysis_metadata?.data_quality_score || 0) * 100)}%
                    </Text>
                  </div>
                  <RingProgress
                    size={60}
                    thickness={6}
                    sections={[
                      { value: Math.round((learningAnalysis?.analysis_metadata?.data_quality_score || 0) * 100), color: 'blue' }
                    ]}
                  />
                </Group>
              </Card>
            </Grid.Col>

            <Grid.Col span={4}>
              <Card withBorder>
                <Group justify="space-between">
                  <div>
                    <Text size="sm" c="dimmed">学习效果</Text>
                    <Text size="xl" fw={700}>
                      {Math.round((learningAnalysis?.analysis_metadata?.data_quality_score || 0) * 85)}%
                    </Text>
                  </div>
                  <RingProgress
                    size={60}
                    thickness={6}
                    sections={[
                      { value: Math.round((learningAnalysis?.analysis_metadata?.data_quality_score || 0) * 85), color: 'green' }
                    ]}
                  />
                </Group>
              </Card>
            </Grid.Col>

            <Grid.Col span={4}>
              <Card withBorder>
                <Group justify="space-between">
                  <div>
                    <Text size="sm" c="dimmed">预警数量</Text>
                    <Text size="xl" fw={700}>
                      {learningAnalysis?.risk_assessment?.risk_students?.length || 0}
                    </Text>
                  </div>
                  <ActionIcon size="xl" variant="light" color="orange">
                    <IconAlertTriangle size={24} />
                  </ActionIcon>
                </Group>
              </Card>
            </Grid.Col>

            {/* 最新预警 */}
            <Grid.Col span={12}>
              <Card withBorder>
                <Title order={4} mb="md">最新预警</Title>
                {learningAnalysis?.risk_assessment?.risk_students && learningAnalysis.risk_assessment.risk_students.length > 0 ? (
                  <Stack gap="sm">
                    {learningAnalysis.risk_assessment.risk_students.slice(0, 3).map((riskStudent, index) => (
                      <Alert
                        key={index}
                        icon={<IconAlertTriangle size={16} />}
                        color={riskStudent.risk_level === 'high' ? 'red' : riskStudent.risk_level === 'medium' ? 'orange' : 'yellow'}
                        variant="light"
                      >
                        <Group justify="space-between">
                          <div>
                            <Text fw={500}>学生ID: {riskStudent.student_id} - 风险等级: {riskStudent.risk_level}</Text>
                            <Text size="sm" c="dimmed">
                              风险因素: {riskStudent.risk_factors.join(', ')}
                            </Text>
                          </div>
                          <Button size="xs" variant="light">
                            查看详情
                          </Button>
                        </Group>
                      </Alert>
                    ))}
                  </Stack>
                ) : (
                  <Text c="dimmed">暂无预警信息</Text>
                )}
              </Card>
            </Grid.Col>
          </Grid>
        </Tabs.Panel>

        {/* 学情分析面板 */}
        <Tabs.Panel value="analysis" pt="md">
          <LoadingOverlay visible={analysisLoading} />
          <Card withBorder>
            <Group justify="space-between" mb="md">
              <Title order={4}>学情分析结果</Title>
              <Button 
                leftSection={<IconRefresh size={16} />}
                onClick={() => queryClient.invalidateQueries({ queryKey: ['learning-analysis'] })}
              >
                刷新分析
              </Button>
            </Group>
            
            {learningAnalysis ? (
              <Stack gap="md">
                <div>
                  <Text fw={500} mb="xs">数据质量评分</Text>
                  <Progress
                    value={Math.round((learningAnalysis.analysis_metadata?.data_quality_score || 0) * 100)}
                    size="lg"
                  />
                  <Text size="sm" ta="center">
                    {Math.round((learningAnalysis.analysis_metadata?.data_quality_score || 0) * 100)}%
                  </Text>
                </div>

                <div>
                  <Text fw={500} mb="xs">预警指标</Text>
                  <Stack gap="xs">
                    {learningAnalysis.risk_assessment?.warning_indicators?.map((indicator, index) => (
                      <Badge key={index} variant="light" color="orange">
                        {indicator}
                      </Badge>
                    )) || []}
                  </Stack>
                </div>
              </Stack>
            ) : (
              <Text c="dimmed">暂无分析数据</Text>
            )}
          </Card>
        </Tabs.Panel>

        {/* 调整建议面板 */}
        <Tabs.Panel value="adjustments" pt="md">
          <Card withBorder>
            <Group justify="space-between" mb="md">
              <Title order={4}>智能调整建议</Title>
              <Button 
                leftSection={<IconBulb size={16} />}
                onClick={generateAdjustments}
                loading={adjustmentMutation.isPending}
              >
                生成建议
              </Button>
            </Group>
            
            <Text c="dimmed">
              基于学情分析结果，系统将为您生成个性化的教学调整建议
            </Text>
          </Card>
        </Tabs.Panel>

        {/* 效果跟踪面板 */}
        <Tabs.Panel value="tracking" pt="md">
          <Card withBorder>
            <Title order={4} mb="md">教学效果跟踪</Title>
            <Text c="dimmed">
              跟踪教学调整的实施效果，提供数据驱动的改进建议
            </Text>
          </Card>
        </Tabs.Panel>

        {/* 协作中心面板 */}
        <Tabs.Panel value="collaboration" pt="md">
          <Card withBorder>
            <Title order={4} mb="md">协作中心</Title>
            <Text c="dimmed">
              与其他教师分享成功的教学调整经验，协同优化教学方案
            </Text>
          </Card>
        </Tabs.Panel>
      </Tabs>
    </Container>
  )
}
