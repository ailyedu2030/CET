/**
 * PWA功能测试页面
 *
 * 用于测试和演示PWA功能：
 * - PWA状态显示
 * - 安装功能测试
 * - 离线功能测试
 * - 缓存状态查看
 */

import {
  Card,
  Container,
  Title,
  Text,
  Button,
  Group,
  Stack,
  Badge,
  Alert,
  Code,
  Divider,
} from '@mantine/core'
import {
  IconInfoCircle,
  IconDownload,
  IconRefresh,
  IconWifi,
  IconWifiOff,
} from '@tabler/icons-react'
import { useState, useEffect } from 'react'

import { pwaManager, pwaUtils, type PWAStatus as PWAStatusType } from '@/utils/pwa'

export function PWATest(): JSX.Element {
  const [status, setStatus] = useState<PWAStatusType>(pwaManager.getStatus())
  const [isInstalling, setIsInstalling] = useState(false)
  const [isUpdating, setIsUpdating] = useState(false)

  // 定期更新状态
  useEffect(() => {
    const updateStatus = () => {
      setStatus(pwaManager.getStatus())
    }

    const interval = setInterval(updateStatus, 1000)
    return () => clearInterval(interval)
  }, [])

  // 处理安装
  const handleInstall = async () => {
    setIsInstalling(true)
    try {
      await pwaManager.install()
      setStatus(pwaManager.getStatus())
    } finally {
      setIsInstalling(false)
    }
  }

  // 处理更新
  const handleUpdate = async () => {
    setIsUpdating(true)
    try {
      await pwaManager.applyUpdate()
    } finally {
      setIsUpdating(false)
    }
  }

  return (
    <Container size="md" py="xl">
      <Stack gap="lg">
        <Title order={2}>PWA功能测试</Title>

        <Alert icon={<IconInfoCircle size={16} />} color="blue">
          此页面用于测试和演示PWA（渐进式Web应用）功能
        </Alert>

        {/* PWA状态卡片 */}
        <Card withBorder>
          <Stack gap="md">
            <Title order={3}>PWA状态</Title>

            <Group>
              <Badge color={status.isOffline ? 'orange' : 'green'}>
                {status.isOffline ? '离线模式' : '在线模式'}
              </Badge>

              {pwaUtils.isRunningAsPWA() && <Badge color="blue">PWA模式运行</Badge>}

              {status.isInstalled && <Badge color="green">已安装</Badge>}

              {status.isInstallable && <Badge color="orange">可安装</Badge>}

              {status.hasUpdate && <Badge color="red">有更新</Badge>}
            </Group>

            <Divider />

            <Stack gap="xs">
              <Text size="sm">
                <strong>PWA支持:</strong> {pwaUtils.isSupported() ? '✅ 支持' : '❌ 不支持'}
              </Text>
              <Text size="sm">
                <strong>移动设备:</strong> {pwaUtils.isMobile() ? '✅ 是' : '❌ 否'}
              </Text>
              <Text size="sm">
                <strong>通知支持:</strong>{' '}
                {pwaUtils.supportsNotifications() ? '✅ 支持' : '❌ 不支持'}
              </Text>
              <Text size="sm">
                <strong>网络状态:</strong>{' '}
                {pwaUtils.getNetworkStatus() === 'online' ? '🌐 在线' : '📱 离线'}
              </Text>
            </Stack>
          </Stack>
        </Card>

        {/* 操作按钮 */}
        <Card withBorder>
          <Stack gap="md">
            <Title order={3}>PWA操作</Title>

            <Group>
              {status.isInstallable && !status.isInstalled && (
                <Button
                  leftSection={<IconDownload size={16} />}
                  loading={isInstalling}
                  onClick={handleInstall}
                >
                  安装到桌面
                </Button>
              )}

              {status.hasUpdate && (
                <Button
                  leftSection={<IconRefresh size={16} />}
                  loading={isUpdating}
                  onClick={handleUpdate}
                  color="orange"
                >
                  应用更新
                </Button>
              )}

              <Button
                leftSection={status.isOffline ? <IconWifiOff size={16} /> : <IconWifi size={16} />}
                variant="outline"
                onClick={() => setStatus(pwaManager.getStatus())}
              >
                刷新状态
              </Button>
            </Group>
          </Stack>
        </Card>

        {/* 技术信息 */}
        <Card withBorder>
          <Stack gap="md">
            <Title order={3}>技术信息</Title>

            <Stack gap="xs">
              <Text size="sm">
                <strong>User Agent:</strong>
              </Text>
              <Code block>{navigator.userAgent}</Code>

              <Text size="sm">
                <strong>Service Worker状态:</strong>{' '}
                {'serviceWorker' in navigator ? '✅ 支持' : '❌ 不支持'}
              </Text>

              <Text size="sm">
                <strong>当前URL:</strong> {window.location.href}
              </Text>

              <Text size="sm">
                <strong>显示模式:</strong>{' '}
                {window.matchMedia('(display-mode: standalone)').matches ? 'Standalone' : 'Browser'}
              </Text>
            </Stack>
          </Stack>
        </Card>
      </Stack>
    </Container>
  )
}
