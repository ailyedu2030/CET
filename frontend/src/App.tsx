import { MantineProvider } from '@mantine/core'
import { Notifications } from '@mantine/notifications'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useEffect } from 'react'
import { BrowserRouter } from 'react-router-dom'

import { AppLayout } from '@/components/Layout/AppLayout'
import { AppRouter } from '@/components/Router/AppRouter'
import { useAuthStore } from '@/stores/authStore'
import { pwaManager, pwaUtils } from '@/utils/pwa'
import { offlineSync } from '@/services/offlineSync'
import { smartPreloader } from '@/services/smartPreloader'

// 创建QueryClient实例 - 统一配置
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5分钟
    },
  },
})

function AppContent(): JSX.Element {
  const { isAuthenticated } = useAuthStore()

  return isAuthenticated ? <AppLayout /> : <AppRouter />
}

function App(): JSX.Element {
  // PWA初始化
  useEffect(() => {
    const initializePWA = async () => {
      // 检查PWA支持
      if (pwaUtils.isSupported()) {
        // 注册Service Worker
        await pwaManager.registerServiceWorker()

        // 请求通知权限（仅在移动设备上）
        if (pwaUtils.isMobile()) {
          await pwaUtils.requestNotificationPermission()
        }

        // 初始化离线同步服务
        await offlineSync.initialize()

        // 启用智能预加载（仅在非省流量模式下）
        const connection = (navigator as any).connection
        if (!connection?.saveData) {
          smartPreloader.setEnabled(true)
        }

        // PWA功能已初始化
      } else {
        // 当前浏览器不支持PWA功能
      }
    }

    initializePWA().catch(() => {
      // PWA初始化失败，静默处理
    })
  }, [])

  return (
    <QueryClientProvider client={queryClient}>
      <MantineProvider>
        <Notifications />
        <BrowserRouter>
          <AppContent />
        </BrowserRouter>
      </MantineProvider>
    </QueryClientProvider>
  )
}

export default App
