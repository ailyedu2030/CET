/**
 * 离线状态面板
 * 
 * 显示离线功能状态：
 * - 同步状态
 * - 存储统计
 * - 冲突管理
 * - 手动操作
 */

import {
  Card,
  Text,
  Button,
  Group,
  Stack,
  Badge,
  Progress,
  Alert,
  ActionIcon,
  Tooltip,
  Grid,
  Divider,

} from '@mantine/core'
import {
  IconCloudUpload,
  IconDatabase,
  IconAlertTriangle,
  IconRefresh,
  IconTrash,
  IconSettings,
  IconWifiOff,
  IconWifi,
} from '@tabler/icons-react'
import { useState } from 'react'

import { ConflictResolver } from './ConflictResolver'
import { 
  useSyncStatus, 
  useOfflineStatus, 
  useStorageStats, 
  useConflictResolver 
} from '@/hooks/useOfflineData'
import { offlineStorage, STORES } from '@/services/offlineStorage'

export function OfflineStatusPanel(): JSX.Element {
  const [conflictModalOpened, setConflictModalOpened] = useState(false)
  const [isClearing, setIsClearing] = useState(false)

  const { isOffline } = useOfflineStatus()
  const { 
    isSync, 
    lastSyncTime, 
    pendingItems, 
    errors, 
    manualSync 
  } = useSyncStatus()
  const { stats, refreshStats } = useStorageStats()
  const { hasConflicts, conflicts } = useConflictResolver()

  // 手动同步
  const handleManualSync = async () => {
    try {
      await manualSync()
    } catch (error) {
      // 错误已在Hook中处理
    }
  }

  // 清理离线数据
  const handleClearOfflineData = async () => {
    setIsClearing(true)
    try {
      for (const store of Object.values(STORES)) {
        const items = await offlineStorage.getAll(store)
        for (const item of items) {
          await offlineStorage.delete(store, item.id)
        }
      }
      await refreshStats()
    } catch (error) {
      // 错误处理
    } finally {
      setIsClearing(false)
    }
  }

  // 格式化时间
  const formatTime = (timestamp: number | null) => {
    if (!timestamp) return '从未同步'
    return new Date(timestamp).toLocaleString()
  }

  // 计算总存储项目
  const totalItems = Object.values(stats).reduce((sum, count) => sum + count, 0)

  return (
    <>
      <Card withBorder>
        <Stack gap="md">
          {/* 标题 */}
          <Group justify="space-between">
            <Text size="lg" fw={600}>离线状态</Text>
            <Group gap="xs">
              <Badge 
                color={isOffline ? 'orange' : 'green'}
                leftSection={isOffline ? <IconWifiOff size={12} /> : <IconWifi size={12} />}
              >
                {isOffline ? '离线模式' : '在线模式'}
              </Badge>
              
              {isSync && (
                <Badge color="blue" leftSection={<IconCloudUpload size={12} />}>
                  同步中
                </Badge>
              )}
            </Group>
          </Group>

          {/* 同步状态 */}
          <Card withBorder>
            <Stack gap="md">
              <Text fw={600} size="sm">同步状态</Text>
              
              <Grid>
                <Grid.Col span={6}>
                  <Stack gap="xs">
                    <Text size="xs" c="dimmed">最后同步时间</Text>
                    <Text size="sm">{formatTime(lastSyncTime)}</Text>
                  </Stack>
                </Grid.Col>
                
                <Grid.Col span={6}>
                  <Stack gap="xs">
                    <Text size="xs" c="dimmed">待同步项目</Text>
                    <Group gap="xs">
                      <Text size="sm">{pendingItems}</Text>
                      {pendingItems > 0 && (
                        <Badge size="xs" color="orange">{pendingItems}</Badge>
                      )}
                    </Group>
                  </Stack>
                </Grid.Col>
              </Grid>

              {pendingItems > 0 && (
                <Progress 
                  value={isSync ? 50 : 0} 
                  color="blue" 
                  size="sm"
                  animated={isSync}
                />
              )}

              <Group justify="space-between">
                <Button
                  size="xs"
                  variant="outline"
                  leftSection={<IconRefresh size={14} />}
                  onClick={handleManualSync}
                  disabled={isOffline || isSync}
                  loading={isSync}
                >
                  手动同步
                </Button>
                
                {hasConflicts && (
                  <Button
                    size="xs"
                    color="orange"
                    leftSection={<IconAlertTriangle size={14} />}
                    onClick={() => setConflictModalOpened(true)}
                  >
                    解决冲突 ({conflicts.length})
                  </Button>
                )}
              </Group>
            </Stack>
          </Card>

          {/* 存储统计 */}
          <Card withBorder>
            <Stack gap="md">
              <Group justify="space-between">
                <Text fw={600} size="sm">存储统计</Text>
                <ActionIcon
                  size="sm"
                  variant="outline"
                  onClick={refreshStats}
                >
                  <IconRefresh size={14} />
                </ActionIcon>
              </Group>
              
              <Grid>
                <Grid.Col span={6}>
                  <Stack gap="xs">
                    <Text size="xs" c="dimmed">总项目数</Text>
                    <Group gap="xs">
                      <IconDatabase size={16} />
                      <Text size="sm" fw={600}>{totalItems}</Text>
                    </Group>
                  </Stack>
                </Grid.Col>
                
                <Grid.Col span={6}>
                  <Stack gap="xs">
                    <Text size="xs" c="dimmed">存储详情</Text>
                    <Stack gap={2}>
                      {Object.entries(stats).map(([store, count]) => (
                        <Group key={store} justify="space-between" gap="xs">
                          <Text size="xs">{store}:</Text>
                          <Badge size="xs" variant="outline">{count}</Badge>
                        </Group>
                      ))}
                    </Stack>
                  </Stack>
                </Grid.Col>
              </Grid>
            </Stack>
          </Card>

          {/* 错误信息 */}
          {errors.length > 0 && (
            <Alert color="red" icon={<IconAlertTriangle size={16} />}>
              <Text size="sm" fw={600}>同步错误：</Text>
              <Stack gap="xs" mt="xs">
                {errors.map((error, index) => (
                  <Text key={index} size="xs">{error}</Text>
                ))}
              </Stack>
            </Alert>
          )}

          {/* 冲突提示 */}
          {hasConflicts && (
            <Alert color="orange" icon={<IconAlertTriangle size={16} />}>
              <Group justify="space-between">
                <Text size="sm">
                  发现 {conflicts.length} 个数据冲突，需要手动解决
                </Text>
                <Button
                  size="xs"
                  variant="outline"
                  onClick={() => setConflictModalOpened(true)}
                >
                  解决
                </Button>
              </Group>
            </Alert>
          )}

          <Divider />

          {/* 管理操作 */}
          <Group justify="space-between">
            <Text size="sm" c="dimmed">数据管理</Text>
            
            <Group gap="xs">
              <Tooltip label="清理离线数据">
                <ActionIcon
                  variant="outline"
                  color="red"
                  size="sm"
                  loading={isClearing}
                  onClick={handleClearOfflineData}
                >
                  <IconTrash size={14} />
                </ActionIcon>
              </Tooltip>
              
              <Tooltip label="离线设置">
                <ActionIcon
                  variant="outline"
                  size="sm"
                >
                  <IconSettings size={14} />
                </ActionIcon>
              </Tooltip>
            </Group>
          </Group>
        </Stack>
      </Card>

      {/* 冲突解决模态框 */}
      <ConflictResolver
        opened={conflictModalOpened}
        onClose={() => setConflictModalOpened(false)}
      />
    </>
  )
}
