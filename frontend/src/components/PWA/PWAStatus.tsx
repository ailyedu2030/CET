/**
 * PWA状态组件
 * 
 * 显示PWA相关状态和操作：
 * - 安装提示
 * - 更新通知
 * - 离线状态
 * - 网络状态
 */

import { ActionIcon, Badge, Group, Tooltip } from '@mantine/core'
import { 
  IconDownload, 
  IconRefresh, 
  IconWifi, 
  IconWifiOff,
  IconDeviceMobile
} from '@tabler/icons-react'
import { useEffect, useState } from 'react'

import { pwaManager, pwaUtils, type PWAStatus as PWAStatusType } from '@/utils/pwa'

export function PWAStatus(): JSX.Element {
  const [status, setStatus] = useState<PWAStatusType>(pwaManager.getStatus())
  const [isInstalling, setIsInstalling] = useState(false)
  const [isUpdating, setIsUpdating] = useState(false)

  // 定期更新状态
  useEffect(() => {
    const updateStatus = () => {
      setStatus(pwaManager.getStatus())
    }

    // 初始更新
    updateStatus()

    // 监听网络状态变化
    const handleOnline = () => updateStatus()
    const handleOffline = () => updateStatus()

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    // 定期检查状态
    const interval = setInterval(updateStatus, 30000) // 30秒

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
      clearInterval(interval)
    }
  }, [])

  // 处理安装
  const handleInstall = async () => {
    setIsInstalling(true)
    try {
      const success = await pwaManager.install()
      if (success) {
        setStatus(pwaManager.getStatus())
      }
    } catch (error) {
      // 安装失败，静默处理
    } finally {
      setIsInstalling(false)
    }
  }

  // 处理更新
  const handleUpdate = async () => {
    setIsUpdating(true)
    try {
      await pwaManager.applyUpdate()
    } catch (error) {
      // 更新失败，静默处理
    } finally {
      setIsUpdating(false)
    }
  }

  return (
    <Group gap="xs">
      {/* 网络状态 */}
      <Tooltip label={status.isOffline ? '离线模式' : '在线模式'}>
        <Badge
          color={status.isOffline ? 'orange' : 'green'}
          variant="light"
          leftSection={status.isOffline ? <IconWifiOff size={12} /> : <IconWifi size={12} />}
        >
          {status.isOffline ? '离线' : '在线'}
        </Badge>
      </Tooltip>

      {/* PWA运行状态 */}
      {pwaUtils.isRunningAsPWA() && (
        <Tooltip label="PWA模式运行">
          <Badge color="blue" variant="light" leftSection={<IconDeviceMobile size={12} />}>
            PWA
          </Badge>
        </Tooltip>
      )}

      {/* 安装按钮 */}
      {status.isInstallable && !status.isInstalled && (
        <Tooltip label="安装到桌面">
          <ActionIcon
            variant="light"
            color="blue"
            loading={isInstalling}
            onClick={handleInstall}
          >
            <IconDownload size={16} />
          </ActionIcon>
        </Tooltip>
      )}

      {/* 更新按钮 */}
      {status.hasUpdate && (
        <Tooltip label="应用更新">
          <ActionIcon
            variant="light"
            color="orange"
            loading={isUpdating}
            onClick={handleUpdate}
          >
            <IconRefresh size={16} />
          </ActionIcon>
        </Tooltip>
      )}
    </Group>
  )
}
