/**
 * 系统状态面板
 * 
 * 集成展示🔥需求31的所有功能：
 * - 网络状态和优化
 * - 安全会话管理
 * - 批量处理状态
 * - 性能监控
 */

import React, { useState, useEffect } from 'react'
import {
  Card,
  Grid,
  Text,
  Badge,
  Progress,
  Group,
  Stack,
  Button,
  Alert,
  Divider,
  ActionIcon,
  Tooltip,
} from '@mantine/core'
import {
  IconWifi,
  IconWifiOff,
  IconShield,
  IconClock,
  IconActivity,
  IconRefresh,
  IconSettings,
  IconAlertTriangle,
} from '@tabler/icons-react'

import { networkOptimizer } from '../../services/networkOptimizer'
import { securityService } from '../../services/securityService'
import { batchProcessor } from '../../services/batchProcessor'

interface SystemStatusPanelProps {
  className?: string
}

const SystemStatusPanel: React.FC<SystemStatusPanelProps> = ({ className }) => {
  const [networkStatus, setNetworkStatus] = useState(networkOptimizer.getNetworkStatus())
  const [sessionInfo, setSessionInfo] = useState(securityService.getSessionInfo())
  const [batchStats, setBatchStats] = useState(batchProcessor.getStats())
  const [queueStatus, setQueueStatus] = useState(batchProcessor.getQueueStatus())

  useEffect(() => {
    let isMounted = true

    // 网络状态监听
    const networkListener = (status: any) => {
      if (isMounted) {
        setNetworkStatus(status)
      }
    }
    networkOptimizer.addStatusListener(networkListener)

    // 定期更新状态
    const interval = setInterval(() => {
      if (isMounted) {
        setSessionInfo(securityService.getSessionInfo())
        setBatchStats(batchProcessor.getStats())
        setQueueStatus(batchProcessor.getQueueStatus())
      }
    }, 5000)

    return () => {
      isMounted = false
      networkOptimizer.removeStatusListener(networkListener)
      clearInterval(interval)
    }
  }, [])

  const getNetworkQualityColor = (quality: string) => {
    switch (quality) {
      case 'excellent': return 'green'
      case 'good': return 'blue'
      case 'fair': return 'yellow'
      case 'poor': return 'red'
      default: return 'gray'
    }
  }

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`
  }

  const formatTime = (timestamp: number) => {
    return new Date(timestamp).toLocaleTimeString()
  }

  return (
    <Card className={className} padding="lg" radius="md" withBorder>
      <Group justify="space-between" mb="md">
        <Text size="lg" fw={600}>系统状态监控</Text>
        <Group gap="xs">
          <Tooltip label="刷新状态">
            <ActionIcon 
              variant="light" 
              onClick={() => window.location.reload()}
            >
              <IconRefresh size={16} />
            </ActionIcon>
          </Tooltip>
          <Tooltip label="系统设置">
            <ActionIcon variant="light">
              <IconSettings size={16} />
            </ActionIcon>
          </Tooltip>
        </Group>
      </Group>

      <Grid>
        {/* 网络状态 */}
        <Grid.Col span={{ base: 12, md: 6 }}>
          <Card padding="md" radius="sm" withBorder>
            <Group justify="space-between" mb="xs">
              <Group gap="xs">
                {networkStatus.isOnline ? (
                  <IconWifi size={20} color="green" />
                ) : (
                  <IconWifiOff size={20} color="red" />
                )}
                <Text fw={500}>网络状态</Text>
              </Group>
              <Badge 
                color={getNetworkQualityColor(networkStatus.quality)}
                variant="light"
              >
                {networkStatus.quality}
              </Badge>
            </Group>
            
            <Stack gap="xs">
              <Group justify="space-between">
                <Text size="sm" c="dimmed">连接状态</Text>
                <Text size="sm">
                  {networkStatus.isOnline ? '已连接' : '已断开'}
                </Text>
              </Group>
              
              <Group justify="space-between">
                <Text size="sm" c="dimmed">网络质量</Text>
                <Text size="sm">{networkStatus.quality}</Text>
              </Group>
              
              <Group justify="space-between">
                <Text size="sm" c="dimmed">最后检测</Text>
                <Text size="sm">{formatTime(networkStatus.lastCheck)}</Text>
              </Group>
            </Stack>
          </Card>
        </Grid.Col>

        {/* 安全会话 */}
        <Grid.Col span={{ base: 12, md: 6 }}>
          <Card padding="md" radius="sm" withBorder>
            <Group justify="space-between" mb="xs">
              <Group gap="xs">
                <IconShield size={20} color="blue" />
                <Text fw={500}>安全会话</Text>
              </Group>
              <Badge 
                color={sessionInfo.isActive ? 'green' : 'gray'}
                variant="light"
              >
                {sessionInfo.isActive ? '活跃' : '非活跃'}
              </Badge>
            </Group>
            
            <Stack gap="xs">
              <Group justify="space-between">
                <Text size="sm" c="dimmed">会话开始</Text>
                <Text size="sm">{formatTime(sessionInfo.startTime)}</Text>
              </Group>
              
              <Group justify="space-between">
                <Text size="sm" c="dimmed">最后活动</Text>
                <Text size="sm">{formatTime(sessionInfo.lastActivity)}</Text>
              </Group>
              
              <Group justify="space-between">
                <Text size="sm" c="dimmed">今日使用</Text>
                <Text size="sm">{formatDuration(sessionInfo.dailyUsage)}</Text>
              </Group>

              {sessionInfo.dailyUsage > 60 && (
                <Alert
                  icon={<IconClock size={16} />}
                  color="yellow"
                >
                  学习时间较长，建议适当休息
                </Alert>
              )}
            </Stack>
          </Card>
        </Grid.Col>

        {/* 批量处理状态 */}
        <Grid.Col span={{ base: 12, md: 6 }}>
          <Card padding="md" radius="sm" withBorder>
            <Group justify="space-between" mb="xs">
              <Group gap="xs">
                <IconActivity size={20} color="purple" />
                <Text fw={500}>批量处理</Text>
              </Group>
              <Badge 
                color={queueStatus.queueLength > 0 ? 'orange' : 'green'}
                variant="light"
              >
                {queueStatus.queueLength > 0 ? '处理中' : '空闲'}
              </Badge>
            </Group>
            
            <Stack gap="xs">
              <Group justify="space-between">
                <Text size="sm" c="dimmed">队列长度</Text>
                <Text size="sm">{queueStatus.queueLength}</Text>
              </Group>
              
              <Group justify="space-between">
                <Text size="sm" c="dimmed">高优先级</Text>
                <Text size="sm">{queueStatus.highPriorityCount}</Text>
              </Group>
              
              <Group justify="space-between">
                <Text size="sm" c="dimmed">总请求数</Text>
                <Text size="sm">{batchStats.totalRequests}</Text>
              </Group>
              
              <Group justify="space-between">
                <Text size="sm" c="dimmed">成功率</Text>
                <Text size="sm">{(batchStats.successRate * 100).toFixed(1)}%</Text>
              </Group>

              {queueStatus.queueLength > 5 && (
                <Alert
                  icon={<IconAlertTriangle size={16} />}
                  color="orange"
                >
                  请求队列较长，可能影响响应速度
                </Alert>
              )}
            </Stack>
          </Card>
        </Grid.Col>

        {/* 性能指标 */}
        <Grid.Col span={{ base: 12, md: 6 }}>
          <Card padding="md" radius="sm" withBorder>
            <Group justify="space-between" mb="xs">
              <Group gap="xs">
                <IconActivity size={20} color="teal" />
                <Text fw={500}>性能指标</Text>
              </Group>
            </Group>
            
            <Stack gap="xs">
              <div>
                <Group justify="space-between" mb={4}>
                  <Text size="sm" c="dimmed">批处理效率</Text>
                  <Text size="sm">
                    {batchStats.batchedRequests > 0 
                      ? `${((batchStats.batchedRequests / batchStats.totalRequests) * 100).toFixed(1)}%`
                      : '0%'
                    }
                  </Text>
                </Group>
                <Progress 
                  value={batchStats.batchedRequests > 0 
                    ? (batchStats.batchedRequests / batchStats.totalRequests) * 100
                    : 0
                  } 
                  size="sm" 
                  color="teal" 
                />
              </div>
              
              <div>
                <Group justify="space-between" mb={4}>
                  <Text size="sm" c="dimmed">系统稳定性</Text>
                  <Text size="sm">{(batchStats.successRate * 100).toFixed(1)}%</Text>
                </Group>
                <Progress 
                  value={batchStats.successRate * 100} 
                  size="sm" 
                  color={batchStats.successRate > 0.9 ? 'green' : 'yellow'} 
                />
              </div>
              
              <Group justify="space-between">
                <Text size="sm" c="dimmed">平均批次大小</Text>
                <Text size="sm">{batchStats.averageBatchSize.toFixed(1)}</Text>
              </Group>
            </Stack>
          </Card>
        </Grid.Col>
      </Grid>

      <Divider my="md" />

      {/* 快速操作 */}
      <Group justify="center">
        <Button 
          variant="light" 
          size="sm"
          onClick={() => batchProcessor.flush()}
          disabled={queueStatus.queueLength === 0}
        >
          立即处理队列
        </Button>
        
        <Button 
          variant="light" 
          size="sm"
          onClick={() => networkOptimizer.detectNetworkQuality()}
        >
          检测网络质量
        </Button>
        
        <Button 
          variant="light" 
          size="sm"
          onClick={() => securityService.updateActivity()}
        >
          更新活动状态
        </Button>
      </Group>
    </Card>
  )
}

export default SystemStatusPanel
