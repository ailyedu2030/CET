/**
 * 虚拟滚动列表组件
 *
 * 提供高性能的长列表渲染：
 * - 虚拟滚动优化
 * - 固定高度支持
 * - 平滑滚动体验
 * - 内存使用优化
 */

import { Box, ScrollArea } from '@mantine/core'
import { useCallback, useMemo, useState } from 'react'

// 虚拟列表配置
interface VirtualListProps<T> {
  items: T[]
  itemHeight: number
  renderItem: (item: T, index: number) => React.ReactNode
  height: number
  overscan?: number
  onScroll?: (scrollTop: number) => void
  className?: string
  style?: React.CSSProperties
}

export function VirtualList<T>({
  items,
  itemHeight,
  renderItem,
  height,
  overscan = 5,
  onScroll,
  className,
  style,
}: VirtualListProps<T>): JSX.Element {
  const [scrollTop, setScrollTop] = useState(0)

  // 计算可见范围
  const { startIndex, endIndex } = useMemo(() => {
    const start = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan)
    const end = Math.min(
      items.length - 1,
      Math.ceil((scrollTop + height) / itemHeight) + overscan
    )
    return { startIndex: start, endIndex: end }
  }, [scrollTop, height, itemHeight, overscan, items.length])

  // 计算总高度
  const totalHeight = useMemo(() => {
    return items.length * itemHeight
  }, [items.length, itemHeight])

  // 处理滚动
  const handleScrollChange = useCallback(
    (position: { x: number; y: number }) => {
      setScrollTop(position.y)
      if (onScroll) {
        onScroll(position.y)
      }
    },
    [onScroll]
  )

  // 渲染可见项目
  const visibleItems = useMemo(() => {
    const rendered: React.ReactNode[] = []

    for (let i = startIndex; i <= endIndex; i++) {
      if (i >= 0 && i < items.length) {
        const item = items[i]
        if (item !== undefined && item !== null) {
          rendered.push(
            <div
              key={i}
              style={{
                position: 'absolute',
                top: i * itemHeight,
                left: 0,
                right: 0,
                height: itemHeight,
              }}
            >
              {renderItem(item, i)}
            </div>
          )
        }
      }
    }

    return rendered
  }, [items, renderItem, startIndex, endIndex, itemHeight])

  return (
    <ScrollArea
      style={{ height, ...style }}
      className={className}
      onScrollPositionChange={handleScrollChange}
    >
      <Box
        style={{
          position: 'relative',
          height: totalHeight,
          overflow: 'hidden',
        }}
      >
        {visibleItems}
      </Box>
    </ScrollArea>
  )
}
