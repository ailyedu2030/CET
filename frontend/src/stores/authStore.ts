import { create } from 'zustand'
import { persist } from 'zustand/middleware'

import { User } from '../types/auth'
import { authUtils } from '@/utils/auth'

// 认证状态接口
interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
}

// 认证操作接口
interface AuthActions {
  login: (userData: User, userToken: string) => void
  logout: () => void
  updateUser: (userData: Partial<User>) => void
  setLoading: (isLoading: boolean) => void
  checkAuth: () => void
}

// 认证store类型
type AuthStore = AuthState & AuthActions

// 创建认证store
export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      // 初始状态
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,

      // 登录操作
      login: (userData, userToken) => {
        authUtils.setToken(userToken)
        authUtils.setCurrentUser(userData)

        set({
          user: userData,
          token: userToken,
          isAuthenticated: true,
          isLoading: false,
        })
      },

      // 登出操作
      logout: () => {
        authUtils.logout()

        set({
          user: null,
          token: null,
          isAuthenticated: false,
          isLoading: false,
        })
      },

      // 更新用户信息
      updateUser: userData => {
        const currentUser = get().user
        if (!currentUser) return

        const updatedUser = { ...currentUser, ...userData }
        authUtils.setCurrentUser(updatedUser)

        set({ user: updatedUser })
      },

      // 设置加载状态
      setLoading: isLoading => {
        set({ isLoading })
      },

      // 检查认证状态
      checkAuth: () => {
        const token = authUtils.getToken()
        const user = authUtils.getCurrentUser()

        if (token && user) {
          set({
            user,
            token,
            isAuthenticated: true,
            isLoading: false,
          })
        } else {
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
          })
        }
      },
    }),
    {
      name: 'auth-store',
      partialize: state => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)

// 便捷的useAuth hook
export const useAuth = () => {
  const { user, isAuthenticated, isLoading, login, logout, updateUser, checkAuth } = useAuthStore()
  return { user, isAuthenticated, isLoading, login, logout, updateUser, checkAuth }
}
