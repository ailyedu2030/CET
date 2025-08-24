/**
 * 共享的错误处理Hook
 */
import { notifications } from '@mantine/notifications'
import { useCallback } from 'react'

export interface UseErrorHandlerOptions {
  defaultMessage?: string
  showNotification?: boolean
}

export function useErrorHandler(options: UseErrorHandlerOptions = {}) {
  const { defaultMessage = '操作失败，请重试', showNotification = true } = options

  const handleError = useCallback(
    (error: unknown, customMessage?: string) => {
      const message = customMessage || (error instanceof Error ? error.message : defaultMessage)

      if (showNotification) {
        notifications.show({
          title: '错误',
          message,
          color: 'red',
        })
      }

      // 可以在这里添加错误日志记录到外部服务
      // console.error('Error handled:', error)

      return message
    },
    [defaultMessage, showNotification]
  )

  const handleSuccess = useCallback(
    (message: string, title: string = '成功') => {
      if (showNotification) {
        notifications.show({
          title,
          message,
          color: 'green',
        })
      }
    },
    [showNotification]
  )

  return {
    handleError,
    handleSuccess,
  }
}
