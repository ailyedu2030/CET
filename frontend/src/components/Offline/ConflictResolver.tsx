/**
 * 冲突解决组件
 * 
 * 处理离线同步冲突：
 * - 显示冲突详情
 * - 提供解决选项
 * - 支持手动合并
 * - 冲突历史记录
 */

import {
  Modal,
  Card,
  Text,
  Button,
  Group,
  Stack,
  Badge,
  Tabs,
  Code,
  Alert,
  Divider,
  ActionIcon,
  Tooltip,
  ScrollArea,
} from '@mantine/core'
import {
  IconAlertTriangle,
  IconCheck,
  IconX,
  IconGitMerge,
  IconClock,
  IconUser,
  IconServer,
} from '@tabler/icons-react'
import { useState } from 'react'

import { useConflictResolver } from '@/hooks/useOfflineData'
import type { ConflictItem } from '@/services/offlineStorage'

interface ConflictResolverProps {
  opened: boolean
  onClose: () => void
}

export function ConflictResolver({ opened, onClose }: ConflictResolverProps): JSX.Element {
  const { conflicts, resolveConflict, hasConflicts } = useConflictResolver()
  const [selectedConflict, setSelectedConflict] = useState<ConflictItem | null>(null)
  const [_mergeData, _setMergeData] = useState<any>(null)
  const [isResolving, setIsResolving] = useState(false)

  // 处理冲突解决
  const handleResolve = async (
    conflict: ConflictItem,
    resolution: 'local' | 'server' | 'merge',
    data?: any
  ) => {
    setIsResolving(true)
    
    try {
      switch (resolution) {
        case 'local':
          await resolveConflict.withLocal(conflict)
          break
        case 'server':
          await resolveConflict.withServer(conflict)
          break
        case 'merge':
          if (data) {
            await resolveConflict.withMerge(conflict, data)
          }
          break
      }
      
      setSelectedConflict(null)
      _setMergeData(null)
    } catch (error) {
      // 错误处理
    } finally {
      setIsResolving(false)
    }
  }

  // 生成合并数据
  const generateMergeData = (conflict: ConflictItem) => {
    const merged = { ...conflict.serverData }
    
    // 简单的合并策略：优先使用最新的字段
    Object.keys(conflict.localData).forEach(key => {
      if (conflict.conflictFields.includes(key)) {
        // 冲突字段，需要用户选择
        merged[key] = conflict.localTimestamp > conflict.serverTimestamp 
          ? conflict.localData[key] 
          : conflict.serverData[key]
      } else {
        // 非冲突字段，使用本地数据
        merged[key] = conflict.localData[key]
      }
    })
    
    return merged
  }

  // 格式化时间
  const formatTime = (timestamp: number) => {
    return new Date(timestamp).toLocaleString()
  }

  // 获取冲突类型标签
  const getConflictTypeBadge = (type: string) => {
    const colors = {
      lessonPlans: 'blue',
      resources: 'green',
      students: 'orange',
    }
    
    return (
      <Badge color={colors[type as keyof typeof colors] || 'gray'}>
        {type}
      </Badge>
    )
  }

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title="数据冲突解决"
      size="xl"
      scrollAreaComponent={ScrollArea.Autosize}
    >
      <Stack gap="md">
        {!hasConflicts ? (
          <Alert color="green" icon={<IconCheck size={16} />}>
            当前没有需要解决的数据冲突
          </Alert>
        ) : (
          <>
            {/* 冲突列表 */}
            <Card withBorder>
              <Stack gap="md">
                <Group justify="space-between">
                  <Text fw={600}>冲突列表</Text>
                  <Badge color="red">{conflicts.length} 个冲突</Badge>
                </Group>
                
                <Stack gap="xs">
                  {conflicts.map((conflict) => (
                    <Card
                      key={conflict.id}
                      withBorder
                      style={{
                        cursor: 'pointer',
                        backgroundColor: selectedConflict?.id === conflict.id ? 'var(--mantine-color-blue-0)' : undefined,
                      }}
                      onClick={() => setSelectedConflict(conflict)}
                    >
                      <Group justify="space-between">
                        <Group gap="xs">
                          {getConflictTypeBadge(conflict.type)}
                          <Text size="sm" fw={500}>
                            {conflict.id}
                          </Text>
                        </Group>
                        
                        <Group gap="xs">
                          <Tooltip label="冲突字段数量">
                            <Badge variant="outline" size="sm">
                              {conflict.conflictFields.length} 字段
                            </Badge>
                          </Tooltip>
                          
                          <ActionIcon
                            size="sm"
                            variant="light"
                            color="blue"
                            onClick={(e) => {
                              e.stopPropagation()
                              setSelectedConflict(conflict)
                            }}
                          >
                            <IconAlertTriangle size={12} />
                          </ActionIcon>
                        </Group>
                      </Group>
                    </Card>
                  ))}
                </Stack>
              </Stack>
            </Card>

            {/* 冲突详情 */}
            {selectedConflict && (
              <Card withBorder>
                <Stack gap="md">
                  <Group justify="space-between">
                    <Text fw={600}>冲突详情</Text>
                    <ActionIcon
                      variant="subtle"
                      onClick={() => setSelectedConflict(null)}
                    >
                      <IconX size={16} />
                    </ActionIcon>
                  </Group>

                  <Tabs defaultValue="comparison">
                    <Tabs.List>
                      <Tabs.Tab value="comparison" leftSection={<IconGitMerge size={16} />}>
                        数据对比
                      </Tabs.Tab>
                      <Tabs.Tab value="details" leftSection={<IconClock size={16} />}>
                        冲突详情
                      </Tabs.Tab>
                    </Tabs.List>

                    <Tabs.Panel value="comparison" pt="md">
                      <Stack gap="md">
                        <Group grow>
                          {/* 本地数据 */}
                          <Card withBorder>
                            <Stack gap="xs">
                              <Group gap="xs">
                                <IconUser size={16} />
                                <Text fw={600} size="sm">本地数据</Text>
                                <Badge size="xs" color="blue">
                                  {formatTime(selectedConflict.localTimestamp)}
                                </Badge>
                              </Group>
                              <Code block>
                                {JSON.stringify(selectedConflict.localData, null, 2)}
                              </Code>
                            </Stack>
                          </Card>

                          {/* 服务器数据 */}
                          <Card withBorder>
                            <Stack gap="xs">
                              <Group gap="xs">
                                <IconServer size={16} />
                                <Text fw={600} size="sm">服务器数据</Text>
                                <Badge size="xs" color="green">
                                  {formatTime(selectedConflict.serverTimestamp)}
                                </Badge>
                              </Group>
                              <Code block>
                                {JSON.stringify(selectedConflict.serverData, null, 2)}
                              </Code>
                            </Stack>
                          </Card>
                        </Group>

                        {/* 冲突字段 */}
                        <Alert color="orange" icon={<IconAlertTriangle size={16} />}>
                          <Text size="sm" fw={600}>冲突字段：</Text>
                          <Group gap="xs" mt="xs">
                            {selectedConflict.conflictFields.map(field => (
                              <Badge key={field} color="orange" variant="outline">
                                {field}
                              </Badge>
                            ))}
                          </Group>
                        </Alert>
                      </Stack>
                    </Tabs.Panel>

                    <Tabs.Panel value="details" pt="md">
                      <Stack gap="md">
                        <Group>
                          <Text size="sm" fw={600}>数据类型：</Text>
                          {getConflictTypeBadge(selectedConflict.type)}
                        </Group>
                        
                        <Group>
                          <Text size="sm" fw={600}>数据ID：</Text>
                          <Code>{selectedConflict.id}</Code>
                        </Group>
                        
                        <Divider />
                        
                        <Group>
                          <Text size="sm" fw={600}>本地修改时间：</Text>
                          <Text size="sm">{formatTime(selectedConflict.localTimestamp)}</Text>
                        </Group>
                        
                        <Group>
                          <Text size="sm" fw={600}>服务器修改时间：</Text>
                          <Text size="sm">{formatTime(selectedConflict.serverTimestamp)}</Text>
                        </Group>
                      </Stack>
                    </Tabs.Panel>
                  </Tabs>

                  {/* 解决选项 */}
                  <Divider />
                  
                  <Group justify="center" gap="md">
                    <Button
                      variant="outline"
                      color="blue"
                      leftSection={<IconUser size={16} />}
                      loading={isResolving}
                      onClick={() => handleResolve(selectedConflict, 'local')}
                    >
                      使用本地数据
                    </Button>
                    
                    <Button
                      variant="outline"
                      color="green"
                      leftSection={<IconServer size={16} />}
                      loading={isResolving}
                      onClick={() => handleResolve(selectedConflict, 'server')}
                    >
                      使用服务器数据
                    </Button>
                    
                    <Button
                      variant="outline"
                      color="orange"
                      leftSection={<IconGitMerge size={16} />}
                      loading={isResolving}
                      onClick={() => {
                        const merged = generateMergeData(selectedConflict)
                        handleResolve(selectedConflict, 'merge', merged)
                      }}
                    >
                      智能合并
                    </Button>
                  </Group>
                </Stack>
              </Card>
            )}
          </>
        )}
      </Stack>
    </Modal>
  )
}
