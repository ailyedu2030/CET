/**
 * 通知中心组件 - 需求16通知中枢前端实现
 */

import { useState, useCallback } from 'react'
import {
  ActionIcon,
  Badge,
  Button,
  Card,
  Divider,
  Group,
  Indicator,
  Menu,
  Popover,
  ScrollArea,
  Stack,
  Text,
  Title,
  Tooltip,
  UnstyledButton,
} from '@mantine/core'
import {
  IconBell,
  IconBellRinging,
  IconCheck,
  IconDots,
  IconEye,
  IconSettings,
  IconTrash,
} from '@tabler/icons-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notifications } from '@mantine/notifications'

// import { notificationApi } from '@/api/notifications'
// import { useWebSocket } from '@/hooks/useWebSocket'
import { useAuth } from '@/stores/authStore'

// 临时类型定义
interface NotificationResponse {
  id: number
  title: string
  content: string
  notification_type: string
  priority: string
  is_read: boolean
  created_at: string
  metadata?: any
}

interface NotificationListResponse {
  notifications: NotificationResponse[]
  total: number
  unread_count: number
}

interface NotificationStats {
  total: number
  unread: number
  unread_count: number
  by_type: Record<string, number>
  by_priority: Record<string, number>
}

// 临时API对象
const notificationApi = {
  getNotifications: async (_params?: any) => ({
    notifications: [] as NotificationResponse[],
    total: 0,
    unread_count: 0,
  } as NotificationListResponse),
  getNotificationList: async (_params?: any) => ({
    notifications: [] as NotificationResponse[],
    total: 0,
    unread_count: 0,
  } as NotificationListResponse),
  getNotificationStats: async () => ({
    total: 0,
    unread: 0,
    by_type: {},
    by_priority: {},
  } as NotificationStats),
  markAsRead: async (_id: number) => ({}),
  markAllAsRead: async () => ({}),
  updateNotification: async (_id: number, _data: any) => ({}),
  deleteNotification: async (_id: number) => ({}),
  batchDeleteNotifications: async (_ids: number[]) => ({}),
}

// 临时WebSocket Hook
const useWebSocket = (_options: { url: string | null; onMessage: (message: any) => void }) => ({
  isConnected: false,
  lastMessage: null,
  sendMessage: (_message: any) => {},
})

interface NotificationCenterProps {
  /** 是否显示为弹出层 */
  asPopover?: boolean
  /** 最大显示数量 */
  maxItems?: number
}

export function NotificationCenter({
  asPopover = true,
  maxItems = 10,
}: NotificationCenterProps): JSX.Element {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [opened, setOpened] = useState(false)
  const [selectedNotifications, setSelectedNotifications] = useState<number[]>([])

  // 获取通知列表
  const {
    data: notificationData,
    isLoading,
  } = useQuery<NotificationListResponse>({
    queryKey: ['notifications', 'list'],
    queryFn: () =>
      notificationApi.getNotificationList({
        page: 1,
        page_size: maxItems,
        is_read: false, // 只显示未读通知
      }),
    enabled: !!user,
    refetchInterval: 30000, // 30秒刷新一次
  })

  // 获取通知统计
  const { data: stats } = useQuery<NotificationStats>({
    queryKey: ['notifications', 'stats'],
    queryFn: () => notificationApi.getNotificationStats(),
    enabled: !!user,
    refetchInterval: 60000, // 1分钟刷新一次
  })

  // 标记已读
  const markReadMutation = useMutation({
    mutationFn: (notificationId: number) =>
      notificationApi.updateNotification(notificationId, {
        is_read: true,
        read_at: new Date().toISOString(),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
    },
  })

  // 批量删除
  const batchDeleteMutation = useMutation({
    mutationFn: (notificationIds: number[]) =>
      notificationApi.batchDeleteNotifications(notificationIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
      setSelectedNotifications([])
      notifications.show({
        title: '删除成功',
        message: '选中的通知已删除',
        color: 'green',
      })
    },
  })

  // WebSocket实时通知
  const { isConnected } = useWebSocket({
    url: user ? `/api/v1/notifications/ws/${user.id}` : null,
    onMessage: useCallback((message: any) => {
      if (message.type === 'notification') {
        // 收到新通知，刷新列表
        queryClient.invalidateQueries({ queryKey: ['notifications'] })
        
        // 显示通知提示
        notifications.show({
          title: message.notification.title,
          message: message.notification.content,
          color: getPriorityColor(message.notification.priority),
          icon: <IconBellRinging size={16} />,
        })
      }
    }, [queryClient]),
  })

  const notifications_list = notificationData?.notifications || []
  const unreadCount = stats?.unread_count || 0

  const handleMarkRead = (notificationId: number) => {
    markReadMutation.mutate(notificationId)
  }

  const handleMarkAllRead = () => {
    const unreadIds = notifications_list
      .filter((n) => !n.is_read)
      .map((n) => n.id)
    
    unreadIds.forEach((id) => {
      markReadMutation.mutate(id)
    })
  }

  const handleBatchDelete = () => {
    if (selectedNotifications.length > 0) {
      batchDeleteMutation.mutate(selectedNotifications)
    }
  }

  const handleNotificationClick = (notification: NotificationResponse) => {
    if (!notification.is_read) {
      handleMarkRead(notification.id)
    }
    
    // 根据通知类型执行相应操作
    handleNotificationAction(notification)
  }

  const handleNotificationAction = (notification: NotificationResponse) => {
    const { notification_type, metadata } = notification

    switch (notification_type) {
      case 'teaching_plan_change':
        // 跳转到教学计划页面
        window.location.href = `/teacher/teaching-plans/${metadata.plan_id}`
        break
      case 'training_anomaly':
        // 跳转到学生监控页面
        window.location.href = `/teacher/students/${metadata.student_id}`
        break
      case 'resource_audit':
        // 跳转到资源管理页面
        window.location.href = `/teacher/resources/${metadata.resource_id}`
        break
      default:
        // 默认行为
        break
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return 'red'
      case 'high':
        return 'orange'
      case 'normal':
        return 'blue'
      case 'low':
        return 'gray'
      default:
        return 'blue'
    }
  }

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'urgent':
      case 'high':
        return <IconBellRinging size={16} />
      default:
        return <IconBell size={16} />
    }
  }

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60))

    if (diffInMinutes < 1) return '刚刚'
    if (diffInMinutes < 60) return `${diffInMinutes}分钟前`
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}小时前`
    return `${Math.floor(diffInMinutes / 1440)}天前`
  }

  const NotificationItem = ({ notification }: { notification: NotificationResponse }) => (
    <Card
      key={notification.id}
      p="sm"
      withBorder
      style={{
        cursor: 'pointer',
        backgroundColor: notification.is_read ? undefined : 'var(--mantine-color-blue-0)',
      }}
      onClick={() => handleNotificationClick(notification)}
    >
      <Group justify="space-between" align="flex-start">
        <Group align="flex-start" gap="sm" style={{ flex: 1 }}>
          <div style={{ color: getPriorityColor(notification.priority) }}>
            {getPriorityIcon(notification.priority)}
          </div>
          
          <Stack gap="xs" style={{ flex: 1 }}>
            <Group justify="space-between">
              <Text size="sm" fw={notification.is_read ? 400 : 600}>
                {notification.title}
              </Text>
              <Badge
                size="xs"
                color={getPriorityColor(notification.priority)}
                variant="light"
              >
                {notification.priority}
              </Badge>
            </Group>
            
            <Text size="xs" c="dimmed" lineClamp={2}>
              {notification.content}
            </Text>
            
            <Group justify="space-between">
              <Text size="xs" c="dimmed">
                {formatTimeAgo(notification.created_at)}
              </Text>
              
              {!notification.is_read && (
                <Badge size="xs" color="blue" variant="filled">
                  未读
                </Badge>
              )}
            </Group>
          </Stack>
        </Group>

        <Menu position="bottom-end">
          <Menu.Target>
            <ActionIcon
              variant="subtle"
              size="sm"
              onClick={(e) => e.stopPropagation()}
            >
              <IconDots size={14} />
            </ActionIcon>
          </Menu.Target>
          
          <Menu.Dropdown>
            {!notification.is_read && (
              <Menu.Item
                leftSection={<IconEye size={14} />}
                onClick={(e) => {
                  e.stopPropagation()
                  handleMarkRead(notification.id)
                }}
              >
                标记已读
              </Menu.Item>
            )}
            
            <Menu.Item
              leftSection={<IconTrash size={14} />}
              color="red"
              onClick={(e) => {
                e.stopPropagation()
                batchDeleteMutation.mutate([notification.id])
              }}
            >
              删除
            </Menu.Item>
          </Menu.Dropdown>
        </Menu>
      </Group>
    </Card>
  )

  const NotificationContent = () => (
    <Stack gap="md">
      {/* 头部 */}
      <Group justify="space-between">
        <Title order={4}>通知中心</Title>
        <Group gap="xs">
          {isConnected && (
            <Tooltip label="实时连接已建立">
              <Badge size="xs" color="green" variant="dot">
                在线
              </Badge>
            </Tooltip>
          )}
          
          <Menu position="bottom-end">
            <Menu.Target>
              <ActionIcon variant="subtle">
                <IconSettings size={16} />
              </ActionIcon>
            </Menu.Target>
            
            <Menu.Dropdown>
              <Menu.Item
                leftSection={<IconCheck size={14} />}
                onClick={handleMarkAllRead}
                disabled={unreadCount === 0}
              >
                全部标记已读
              </Menu.Item>
              
              <Menu.Item
                leftSection={<IconTrash size={14} />}
                color="red"
                onClick={handleBatchDelete}
                disabled={selectedNotifications.length === 0}
              >
                删除选中
              </Menu.Item>
            </Menu.Dropdown>
          </Menu>
        </Group>
      </Group>

      <Divider />

      {/* 通知列表 */}
      <ScrollArea h={400}>
        {isLoading ? (
          <Text ta="center" c="dimmed">
            加载中...
          </Text>
        ) : notifications_list.length === 0 ? (
          <Text ta="center" c="dimmed">
            暂无通知
          </Text>
        ) : (
          <Stack gap="xs">
            {notifications_list.map((notification) => (
              <NotificationItem
                key={notification.id}
                notification={notification}
              />
            ))}
          </Stack>
        )}
      </ScrollArea>

      {/* 底部操作 */}
      {notifications_list.length > 0 && (
        <>
          <Divider />
          <Group justify="center">
            <Button
              variant="subtle"
              size="sm"
              onClick={() => {
                window.location.href = '/notifications'
              }}
            >
              查看全部通知
            </Button>
          </Group>
        </>
      )}
    </Stack>
  )

  if (asPopover) {
    return (
      <Popover
        width={400}
        position="bottom-end"
        opened={opened}
        onChange={setOpened}
      >
        <Popover.Target>
          <UnstyledButton onClick={() => setOpened(!opened)}>
            <Indicator
              inline
              label={unreadCount > 99 ? '99+' : unreadCount}
              size={16}
              disabled={unreadCount === 0}
            >
              <ActionIcon variant="subtle" size="lg">
                <IconBell size={20} />
              </ActionIcon>
            </Indicator>
          </UnstyledButton>
        </Popover.Target>
        
        <Popover.Dropdown p="md">
          <NotificationContent />
        </Popover.Dropdown>
      </Popover>
    )
  }

  return <NotificationContent />
}
