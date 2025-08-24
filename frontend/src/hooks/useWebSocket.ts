/**
 * WebSocket Hook - 需求16实时通知功能
 */

import { useEffect, useRef, useState, useCallback } from 'react'

import { useAuth } from '@/stores/authStore'

interface UseWebSocketOptions {
  /** WebSocket连接URL */
  url: string | null
  /** 连接建立时的回调 */
  onOpen?: (event: Event) => void
  /** 收到消息时的回调 */
  onMessage?: (message: any) => void
  /** 连接关闭时的回调 */
  onClose?: (event: CloseEvent) => void
  /** 连接错误时的回调 */
  onError?: (event: Event) => void
  /** 是否自动重连 */
  autoReconnect?: boolean
  /** 重连间隔（毫秒） */
  reconnectInterval?: number
  /** 最大重连次数 */
  maxReconnectAttempts?: number
  /** 心跳间隔（毫秒） */
  heartbeatInterval?: number
}

interface UseWebSocketReturn {
  /** WebSocket实例 */
  socket: WebSocket | null
  /** 连接状态 */
  isConnected: boolean
  /** 是否正在连接 */
  isConnecting: boolean
  /** 连接错误 */
  error: string | null
  /** 发送消息 */
  sendMessage: (message: any) => void
  /** 手动连接 */
  connect: () => void
  /** 手动断开连接 */
  disconnect: () => void
  /** 重连次数 */
  reconnectCount: number
}

export function useWebSocket(options: UseWebSocketOptions): UseWebSocketReturn {
  const {
    url,
    onOpen,
    onMessage,
    onClose,
    onError,
    autoReconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    heartbeatInterval = 30000,
  } = options

  const [socket, setSocket] = useState<WebSocket | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [reconnectCount, setReconnectCount] = useState(0)

  const reconnectTimeoutRef = useRef<number>()
  const heartbeatTimeoutRef = useRef<number>()
  const shouldReconnectRef = useRef(true)

  const connect = useCallback(() => {
    if (!url || isConnecting || isConnected) {
      return
    }

    setIsConnecting(true)
    setError(null)

    try {
      // 构建WebSocket URL
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const host = window.location.host
      const wsUrl = `${protocol}//${host}${url}`

      const newSocket = new WebSocket(wsUrl)

      newSocket.onopen = (event) => {
        // WebSocket连接已建立
        setIsConnected(true)
        setIsConnecting(false)
        setError(null)
        setReconnectCount(0)
        
        // 启动心跳
        startHeartbeat(newSocket)
        
        onOpen?.(event)
      }

      newSocket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          
          // 处理心跳响应
          if (message.type === 'heartbeat') {
            // 收到心跳响应
            return
          }
          
          onMessage?.(message)
        } catch (err) {
          // 解析WebSocket消息失败
        }
      }

      newSocket.onclose = (event) => {
        // WebSocket连接已关闭
        setIsConnected(false)
        setIsConnecting(false)
        setSocket(null)
        
        // 清理心跳
        stopHeartbeat()
        
        onClose?.(event)

        // 自动重连
        if (
          shouldReconnectRef.current &&
          autoReconnect &&
          reconnectCount < maxReconnectAttempts &&
          event.code !== 1000 // 正常关闭不重连
        ) {
          // WebSocket将重连
          reconnectTimeoutRef.current = window.setTimeout(() => {
            setReconnectCount(prev => prev + 1)
            connect()
          }, reconnectInterval)
        }
      }

      newSocket.onerror = (event) => {
        // WebSocket连接错误
        setError('WebSocket连接失败')
        setIsConnecting(false)
        onError?.(event)
      }

      setSocket(newSocket)
    } catch (err) {
      // 创建WebSocket连接失败
      setError('创建WebSocket连接失败')
      setIsConnecting(false)
    }
  }, [
    url,
    isConnecting,
    isConnected,
    onOpen,
    onMessage,
    onClose,
    onError,
    autoReconnect,
    reconnectInterval,
    maxReconnectAttempts,
    reconnectCount,
  ])

  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false
    
    // 清理重连定时器
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    
    // 清理心跳
    stopHeartbeat()
    
    // 关闭连接
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.close(1000, '手动断开连接')
    }
    
    setSocket(null)
    setIsConnected(false)
    setIsConnecting(false)
    setReconnectCount(0)
  }, [socket])

  const sendMessage = useCallback((message: any) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      try {
        const messageStr = typeof message === 'string' ? message : JSON.stringify(message)
        socket.send(messageStr)
      } catch (err) {
        // 发送WebSocket消息失败
        setError('发送消息失败')
      }
    } else {
      // WebSocket未连接，无法发送消息
      setError('WebSocket未连接')
    }
  }, [socket])

  const startHeartbeat = useCallback((ws: WebSocket) => {
    const sendHeartbeat = () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
          type: 'heartbeat',
          timestamp: new Date().toISOString(),
        }))
        
        heartbeatTimeoutRef.current = window.setTimeout(sendHeartbeat, heartbeatInterval)
      }
    }
    
    heartbeatTimeoutRef.current = window.setTimeout(sendHeartbeat, heartbeatInterval)
  }, [heartbeatInterval])

  const stopHeartbeat = useCallback(() => {
    if (heartbeatTimeoutRef.current) {
      clearTimeout(heartbeatTimeoutRef.current)
    }
  }, [])

  // 初始连接
  useEffect(() => {
    if (url) {
      shouldReconnectRef.current = true
      connect()
    }

    return () => {
      shouldReconnectRef.current = false
      disconnect()
    }
  }, [url])

  // 页面可见性变化时的处理
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        // 页面隐藏时暂停心跳
        stopHeartbeat()
      } else {
        // 页面显示时恢复心跳
        if (socket && socket.readyState === WebSocket.OPEN) {
          startHeartbeat(socket)
        }
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [socket, startHeartbeat, stopHeartbeat])

  // 网络状态变化时的处理
  useEffect(() => {
    const handleOnline = () => {
      // 网络已连接，尝试重新建立WebSocket连接
      if (!isConnected && url) {
        connect()
      }
    }

    const handleOffline = () => {
      // 网络已断开
      setError('网络连接已断开')
    }

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [isConnected, url, connect])

  // 组件卸载时清理
  useEffect(() => {
    return () => {
      shouldReconnectRef.current = false
      
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      
      stopHeartbeat()
      
      if (socket) {
        socket.close(1000, '组件卸载')
      }
    }
  }, [socket, stopHeartbeat])

  return {
    socket,
    isConnected,
    isConnecting,
    error,
    sendMessage,
    connect,
    disconnect,
    reconnectCount,
  }
}

// 便捷的通知WebSocket Hook
export function useNotificationWebSocket() {
  const { user } = useAuth()
  
  return useWebSocket({
    url: user ? `/api/v1/notifications/ws/${user.id}` : null,
    autoReconnect: true,
    reconnectInterval: 3000,
    maxReconnectAttempts: 5,
    heartbeatInterval: 30000,
  })
}


