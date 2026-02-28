import React, { useState, useCallback } from 'react'
import {
  Card,
  Text,
  Stack,
  Group,
  Progress,
  Badge,
  Button,
  Alert,
  Accordion,
  ActionIcon,
  NumberInput,
  LoadingOverlay,
  Timeline,
  ThemeIcon,
} from '@mantine/core'
import { useQuery, useMutation } from '@tanstack/react-query'
import { notifications } from '@mantine/notifications'
import {
  IconAlertTriangle,
  IconTrendingUp,
  IconTarget,
  IconRefresh,
  IconDownload,
  IconBrain,
  IconCheck,
} from '@tabler/icons-react'
import { knowledgeAnalysisApi } from '../../api/knowledgeAnalysis'

interface WeaknessAnalysisComponentProps {
  studentId: number
  onWeakPointClick?: (weakPoint: any) => void
  showActions?: boolean
  autoRefresh?: boolean
}

export const WeaknessAnalysisComponent: React.FC<WeaknessAnalysisComponentProps> = ({
  studentId,
  onWeakPointClick,
  showActions = true,
  autoRefresh = false,
}) => {
  const [filters, setFilters] = useState({
    min_weakness_score: 60,
    limit: 10,
    include_categories: [] as string[],
  })

  // 获取薄弱环节分析
  const {
    data: weaknessData,
    isLoading: weaknessLoading,
    refetch: refetchWeakness,
  } = useQuery({
    queryKey: ['weakness-analysis', studentId, filters],
    queryFn: () => knowledgeAnalysisApi.getWeaknessAnalysis(studentId, filters),
    refetchInterval: autoRefresh ? 60000 : false, // 1分钟自动刷新
  })

  // 获取知识点统计
  const { data: statsData, isLoading: statsLoading } = useQuery({
    queryKey: ['knowledge-stats', studentId],
    queryFn: () => knowledgeAnalysisApi.getKnowledgeStats(studentId),
  })

  // 生成学习路径
  const generatePathMutation = useMutation({
    mutationFn: (data: any) => knowledgeAnalysisApi.generateLearningPath(studentId, data),
    onSuccess: result => {
      notifications.show({
        title: '学习路径生成成功',
        message: `已生成包含 ${result.learning_sequence.length} 个知识点的学习路径`,
        color: 'green',
      })
    },
    onError: error => {
      notifications.show({
        title: '生成失败',
        message: error.message,
        color: 'red',
      })
    },
  })

  // 导出分析报告
  const handleExportReport = useCallback(async () => {
    try {
      const blob = await knowledgeAnalysisApi.exportAnalysisReport(studentId, {
        format: 'pdf',
        include_recommendations: true,
        time_range: 'month',
      })

      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `weakness-analysis-${studentId}-${Date.now()}.pdf`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)

      notifications.show({
        title: '导出成功',
        message: '薄弱环节分析报告已导出',
        color: 'green',
      })
    } catch (error) {
      notifications.show({
        title: '导出失败',
        message: '导出过程中发生错误',
        color: 'red',
      })
    }
  }, [studentId])

  // 生成针对性学习路径
  const handleGenerateLearningPath = useCallback(() => {
    if (!weaknessData?.weak_points.length) {
      notifications.show({
        title: '无薄弱点',
        message: '当前没有发现明显的薄弱知识点',
        color: 'yellow',
      })
      return
    }

    const weakPointIds = weaknessData.weak_points
      .filter(wp => wp.priority_level === 'high')
      .map(wp => wp.knowledge_point.id)

    generatePathMutation.mutate({
      target_knowledge_points: weakPointIds,
      time_constraint: 30, // 30天
      difficulty_preference: 'gradual',
      focus_weak_points: true,
    })
  }, [weaknessData, generatePathMutation])

  // 获取优先级颜色
  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'red'
      case 'medium':
        return 'yellow'
      case 'low':
        return 'green'
      default:
        return 'gray'
    }
  }

  // 获取薄弱程度描述（暂时未使用，保留备用）
  // const getWeaknessDescription = (score: number) => {
  //   if (score >= 80) return '严重薄弱'
  //   if (score >= 60) return '中度薄弱'
  //   if (score >= 40) return '轻度薄弱'
  //   return '需要关注'
  // }

  const isLoading = weaknessLoading || statsLoading

  return (
    <Stack gap="lg">
      {/* 统计概览 */}
      {statsData && (
        <Card withBorder padding="lg">
          <Stack gap="md">
            <Group justify="space-between" align="center">
              <Text fw={500} size="lg">
                知识点掌握概览
              </Text>
              <Group gap="xs">
                <ActionIcon variant="outline" onClick={() => refetchWeakness()}>
                  <IconRefresh size={16} />
                </ActionIcon>
                {showActions && (
                  <ActionIcon variant="outline" onClick={handleExportReport}>
                    <IconDownload size={16} />
                  </ActionIcon>
                )}
              </Group>
            </Group>

            <Group grow>
              <Card withBorder padding="sm">
                <Stack gap="xs" align="center">
                  <ThemeIcon size="lg" color="blue" variant="light">
                    <IconBrain size={20} />
                  </ThemeIcon>
                  <Text size="xl" fw={700}>
                    {statsData.mastered_points}
                  </Text>
                  <Text size="sm" c="dimmed">
                    已掌握知识点
                  </Text>
                </Stack>
              </Card>

              <Card withBorder padding="sm">
                <Stack gap="xs" align="center">
                  <ThemeIcon size="lg" color="red" variant="light">
                    <IconAlertTriangle size={20} />
                  </ThemeIcon>
                  <Text size="xl" fw={700}>
                    {statsData.weak_points}
                  </Text>
                  <Text size="sm" c="dimmed">
                    薄弱知识点
                  </Text>
                </Stack>
              </Card>

              <Card withBorder padding="sm">
                <Stack gap="xs" align="center">
                  <ThemeIcon size="lg" color="green" variant="light">
                    <IconTrendingUp size={20} />
                  </ThemeIcon>
                  <Text size="xl" fw={700}>
                    {statsData.improving_points}
                  </Text>
                  <Text size="sm" c="dimmed">
                    进步中知识点
                  </Text>
                </Stack>
              </Card>
            </Group>

            <Stack gap="xs">
              <Text size="sm" fw={500}>
                总体掌握率:{' '}
                {((statsData.mastered_points / statsData.total_points) * 100).toFixed(1)}%
              </Text>
              <Progress
                value={(statsData.mastered_points / statsData.total_points) * 100}
                size="lg"
                color="blue"
              />
            </Stack>
          </Stack>
        </Card>
      )}

      {/* 薄弱环节分析 */}
      <Card withBorder padding="lg">
        <Stack gap="md">
          <LoadingOverlay visible={isLoading} />

          <Group justify="space-between" align="center">
            <Text fw={500} size="lg">
              薄弱环节分析
            </Text>
            {showActions && weaknessData && (
              <Button
                leftSection={<IconTarget size={16} />}
                onClick={handleGenerateLearningPath}
                loading={generatePathMutation.isPending}
              >
                生成学习路径
              </Button>
            )}
          </Group>

          {/* 筛选器 */}
          <Group>
            <NumberInput
              label="最低薄弱分数"
              value={filters.min_weakness_score}
              onChange={value =>
                setFilters(prev => ({
                  ...prev,
                  min_weakness_score: typeof value === 'number' ? value : 60,
                }))
              }
              min={0}
              max={100}
              style={{ width: 150 }}
            />
            <NumberInput
              label="显示数量"
              value={filters.limit}
              onChange={value =>
                setFilters(prev => ({
                  ...prev,
                  limit: typeof value === 'number' ? value : 10,
                }))
              }
              min={1}
              max={50}
              style={{ width: 120 }}
            />
          </Group>

          {weaknessData && (
            <>
              {/* 整体分析 */}
              <Alert color="blue" title="整体分析" icon={<IconBrain size={16} />}>
                <Stack gap="xs">
                  <Text size="sm">
                    整体掌握度: <strong>{weaknessData.overall_mastery.toFixed(1)}%</strong>
                  </Text>
                  <Text size="sm">
                    发现 <strong>{weaknessData.weak_points.length}</strong> 个薄弱知识点
                  </Text>
                  <Text size="sm">
                    建议下次复习时间:{' '}
                    <strong>{new Date(weaknessData.next_review_date).toLocaleDateString()}</strong>
                  </Text>
                </Stack>
              </Alert>

              {/* 重点关注领域 */}
              {weaknessData.focus_areas.length > 0 && (
                <Group gap="xs">
                  <Text size="sm" fw={500}>
                    重点关注领域:
                  </Text>
                  {weaknessData.focus_areas.map(area => (
                    <Badge key={area} color="orange" variant="light">
                      {area}
                    </Badge>
                  ))}
                </Group>
              )}

              {/* 薄弱知识点列表 */}
              {weaknessData.weak_points.length > 0 ? (
                <Accordion variant="separated">
                  {weaknessData.weak_points.map((weakPoint, index) => (
                    <Accordion.Item key={weakPoint.knowledge_point.id} value={`weak-${index}`}>
                      <Accordion.Control>
                        <Group justify="space-between" style={{ width: '100%' }}>
                          <Group gap="sm">
                            <Text fw={500}>{weakPoint.knowledge_point.name}</Text>
                            <Badge color={getPriorityColor(weakPoint.priority_level)} size="sm">
                              {weakPoint.priority_level === 'high'
                                ? '高优先级'
                                : weakPoint.priority_level === 'medium'
                                  ? '中优先级'
                                  : '低优先级'}
                            </Badge>
                          </Group>
                          <Group gap="xs">
                            <Text size="sm" c="dimmed">
                              薄弱度: {weakPoint.weakness_score}%
                            </Text>
                            <Progress
                              value={weakPoint.weakness_score}
                              size="sm"
                              color="red"
                              style={{ width: 60 }}
                            />
                          </Group>
                        </Group>
                      </Accordion.Control>
                      <Accordion.Panel>
                        <Stack gap="sm">
                          <Text size="sm">
                            <strong>类别:</strong> {weakPoint.knowledge_point.category}
                          </Text>
                          <Text size="sm">
                            <strong>难度:</strong> {weakPoint.knowledge_point.difficulty_level}
                          </Text>
                          <Text size="sm">
                            <strong>当前掌握度:</strong> {weakPoint.knowledge_point.mastery_score}%
                          </Text>
                          <Text size="sm">
                            <strong>练习次数:</strong> {weakPoint.knowledge_point.practice_count}
                          </Text>
                          <Text size="sm">
                            <strong>预计改进时间:</strong> {weakPoint.estimated_improvement_time}
                          </Text>

                          {weakPoint.error_patterns.length > 0 && (
                            <div>
                              <Text size="sm" fw={500} mb="xs">
                                错误模式:
                              </Text>
                              <Group gap="xs">
                                {weakPoint.error_patterns.map(pattern => (
                                  <Badge key={pattern} color="red" variant="outline" size="sm">
                                    {pattern}
                                  </Badge>
                                ))}
                              </Group>
                            </div>
                          )}

                          {weakPoint.recommended_actions.length > 0 && (
                            <div>
                              <Text size="sm" fw={500} mb="xs">
                                建议行动:
                              </Text>
                              <Timeline active={-1} bulletSize={16}>
                                {weakPoint.recommended_actions.map((action, actionIndex) => (
                                  <Timeline.Item
                                    key={actionIndex}
                                    bullet={<IconCheck size={12} />}
                                    title={action}
                                  />
                                ))}
                              </Timeline>
                            </div>
                          )}

                          {showActions && (
                            <Button
                              size="xs"
                              variant="outline"
                              onClick={() => onWeakPointClick?.(weakPoint)}
                            >
                              开始针对性练习
                            </Button>
                          )}
                        </Stack>
                      </Accordion.Panel>
                    </Accordion.Item>
                  ))}
                </Accordion>
              ) : (
                <Alert color="green" title="恭喜！" icon={<IconCheck size={16} />}>
                  当前没有发现明显的薄弱知识点，继续保持！
                </Alert>
              )}

              {/* 改进建议 */}
              {weaknessData.improvement_suggestions.length > 0 && (
                <Alert color="blue" title="改进建议">
                  <Stack gap="xs">
                    {weaknessData.improvement_suggestions.map((suggestion, index) => (
                      <Text key={index} size="sm">
                        • {suggestion}
                      </Text>
                    ))}
                  </Stack>
                </Alert>
              )}
            </>
          )}
        </Stack>
      </Card>
    </Stack>
  )
}
