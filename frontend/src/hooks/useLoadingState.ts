/**
 * 共享的加载状态管理Hook
 */
import { useState, useCallback } from 'react'

export interface LoadingState {
  loading: boolean
  error: string | null
}

export function useLoadingState(initialState: LoadingState = { loading: false, error: null }) {
  const [state, setState] = useState<LoadingState>(initialState)

  const setLoading = useCallback((loading: boolean) => {
    setState(prev => ({ ...prev, loading, error: loading ? null : prev.error }))
  }, [])

  const setError = useCallback((error: string | null) => {
    setState(prev => ({ ...prev, error, loading: false }))
  }, [])

  const reset = useCallback(() => {
    setState({ loading: false, error: null })
  }, [])

  const executeAsync = useCallback(
    async <T>(
      asyncFn: () => Promise<T>,
      options: {
        onSuccess?: (result: T) => void
        onError?: (error: unknown) => void
        throwOnError?: boolean
      } = {}
    ): Promise<T | null> => {
      const { onSuccess, onError, throwOnError = false } = options

      try {
        setLoading(true)
        const result = await asyncFn()
        setLoading(false)
        onSuccess?.(result)
        return result
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : '未知错误'
        setError(errorMessage)
        onError?.(error)

        if (throwOnError) {
          throw error
        }

        return null
      }
    },
    [setLoading, setError]
  )

  return {
    ...state,
    setLoading,
    setError,
    reset,
    executeAsync,
  }
}
