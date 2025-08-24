/**
 * 优化图片组件
 * 
 * 提供图片性能优化功能：
 * - 懒加载
 * - 自动格式选择
 * - 响应式尺寸
 * - 加载状态显示
 */

import { Box, Skeleton, Alert } from '@mantine/core'
import { IconPhoto, IconAlertCircle } from '@tabler/icons-react'
import { useEffect, useRef, useState } from 'react'

import { imageOptimizer, imageUtils } from '@/utils/imageOptimization'

// 图片组件属性
interface OptimizedImageProps {
  src: string
  alt: string
  width?: number | string
  height?: number | string
  quality?: number
  format?: 'webp' | 'jpeg' | 'png' | 'auto'
  lazy?: boolean
  placeholder?: boolean
  className?: string
  style?: React.CSSProperties
  onLoad?: () => void
  onError?: (error: Error) => void
  sizes?: string
  srcSet?: string
}

// 加载状态
type LoadingState = 'idle' | 'loading' | 'loaded' | 'error'

export function OptimizedImage({
  src,
  alt,
  width,
  height,
  quality = 0.8,
  format = 'auto',
  lazy = true,
  placeholder = true,
  className,
  style,
  onLoad,
  onError,
  sizes,
  srcSet,
}: OptimizedImageProps): JSX.Element {
  const [loadingState, setLoadingState] = useState<LoadingState>('idle')
  const [optimizedSrc, setOptimizedSrc] = useState<string>('')
  const [actualFormat, setActualFormat] = useState<string>('')
  const imgRef = useRef<HTMLImageElement>(null)
  const observerRef = useRef<IntersectionObserver | null>(null)

  // 初始化优化配置
  useEffect(() => {
    const initializeImage = async () => {
      try {
        // 确定最佳格式
        let targetFormat = format
        if (format === 'auto') {
          targetFormat = await imageUtils.getBestFormat()
        }
        setActualFormat(targetFormat)

        // 生成优化后的URL
        const optimized = imageOptimizer.getOptimizedUrl(src, {
          quality,
          format: targetFormat === 'auto' ? undefined : targetFormat,
          maxWidth: typeof width === 'number' ? width : undefined,
          maxHeight: typeof height === 'number' ? height : undefined,
        })
        setOptimizedSrc(optimized)

        // 如果不使用懒加载，立即开始加载
        if (!lazy) {
          loadImage(optimized)
        }
      } catch (error) {
        setLoadingState('error')
        if (onError) {
          onError(error as Error)
        }
      }
    }

    initializeImage()
  }, [src, quality, format, width, height, lazy, onError])

  // 设置懒加载
  useEffect(() => {
    if (!lazy || !optimizedSrc) return

    const img = imgRef.current
    if (!img) return

    // 创建Intersection Observer
    observerRef.current = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            loadImage(optimizedSrc)
            observerRef.current?.unobserve(img)
          }
        })
      },
      {
        rootMargin: '50px',
        threshold: 0.1,
      }
    )

    observerRef.current.observe(img)

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect()
      }
    }
  }, [lazy, optimizedSrc])

  // 加载图片
  const loadImage = (imageSrc: string) => {
    setLoadingState('loading')

    const img = new Image()
    
    img.onload = () => {
      setLoadingState('loaded')
      if (onLoad) {
        onLoad()
      }
    }

    img.onerror = () => {
      setLoadingState('error')
      if (onError) {
        onError(new Error(`Failed to load image: ${imageSrc}`))
      }
    }

    img.src = imageSrc
  }

  // 渲染占位符
  const renderPlaceholder = () => {
    if (!placeholder) return null

    const placeholderStyle = {
      width: width || '100%',
      height: height || 'auto',
      minHeight: height ? undefined : '200px',
    }

    if (loadingState === 'loading') {
      return (
        <Skeleton
          style={placeholderStyle}
          className={className}
        />
      )
    }

    if (loadingState === 'error') {
      return (
        <Alert
          color="red"
          icon={<IconAlertCircle size={16} />}
          style={placeholderStyle}
          className={className}
        >
          图片加载失败
        </Alert>
      )
    }

    if (loadingState === 'idle' && lazy) {
      return (
        <Box
          style={{
            ...placeholderStyle,
            backgroundColor: '#f8f9fa',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            border: '1px solid #e9ecef',
            borderRadius: '4px',
          }}
          className={className}
        >
          <IconPhoto size={32} color="#adb5bd" />
        </Box>
      )
    }

    return null
  }

  // 渲染图片
  const renderImage = () => {
    if (loadingState !== 'loaded') return null

    const imageProps: React.ImgHTMLAttributes<HTMLImageElement> = {
      src: optimizedSrc,
      alt,
      width,
      height,
      className,
      style,
      loading: lazy ? 'lazy' : 'eager',
      decoding: 'async',
    }

    // 添加响应式图片支持
    if (srcSet) {
      imageProps.srcSet = srcSet
    }
    if (sizes) {
      imageProps.sizes = sizes
    }

    return <img {...imageProps} />
  }

  return (
    <Box
      ref={imgRef}
      style={{
        position: 'relative',
        display: 'inline-block',
        ...style,
      }}
      className={className}
    >
      {renderPlaceholder()}
      {renderImage()}
      
      {/* 格式标识（开发模式） */}
      {process.env['NODE_ENV'] === 'development' && actualFormat && (
        <Box
          style={{
            position: 'absolute',
            top: 4,
            right: 4,
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
            color: 'white',
            padding: '2px 6px',
            borderRadius: '4px',
            fontSize: '10px',
            fontFamily: 'monospace',
            pointerEvents: 'none',
          }}
        >
          {actualFormat.toUpperCase()}
        </Box>
      )}
    </Box>
  )
}

// 响应式图片组件
interface ResponsiveImageProps extends Omit<OptimizedImageProps, 'width' | 'height'> {
  breakpoints?: {
    xs?: number
    sm?: number
    md?: number
    lg?: number
    xl?: number
  }
  aspectRatio?: number
}

export function ResponsiveImage({
  breakpoints = {
    xs: 320,
    sm: 768,
    md: 1024,
    lg: 1440,
    xl: 1920,
  },
  aspectRatio = 16 / 9,
  ...props
}: ResponsiveImageProps): JSX.Element {
  const [currentWidth, setCurrentWidth] = useState<number>(320)

  useEffect(() => {
    const updateWidth = () => {
      const width = window.innerWidth
      
      if (width >= (breakpoints.xl || 1920)) {
        setCurrentWidth(breakpoints.xl || 1920)
      } else if (width >= (breakpoints.lg || 1440)) {
        setCurrentWidth(breakpoints.lg || 1440)
      } else if (width >= (breakpoints.md || 1024)) {
        setCurrentWidth(breakpoints.md || 1024)
      } else if (width >= (breakpoints.sm || 768)) {
        setCurrentWidth(breakpoints.sm || 768)
      } else {
        setCurrentWidth(breakpoints.xs || 320)
      }
    }

    updateWidth()
    window.addEventListener('resize', updateWidth)
    
    return () => window.removeEventListener('resize', updateWidth)
  }, [breakpoints])

  const height = Math.round(currentWidth / aspectRatio)

  // 生成srcSet
  const srcSet = Object.values(breakpoints)
    .filter(Boolean)
    .map(width => {
      const optimizedUrl = imageOptimizer.getOptimizedUrl(props.src, {
        maxWidth: width,
        quality: props.quality,
        format: props.format === 'auto' ? undefined : props.format,
      })
      return `${optimizedUrl} ${width}w`
    })
    .join(', ')

  // 生成sizes
  const sizes = Object.entries(breakpoints)
    .filter(([_, width]) => width)
    .map(([breakpoint, width]) => {
      const mediaQuery = breakpoint === 'xs' 
        ? `(max-width: ${breakpoints.sm || 768}px)`
        : `(min-width: ${width}px)`
      return `${mediaQuery} ${width}px`
    })
    .reverse()
    .join(', ')

  return (
    <OptimizedImage
      {...props}
      width={currentWidth}
      height={height}
      srcSet={srcSet}
      sizes={sizes}
    />
  )
}

// 图片网格组件
interface ImageGridProps {
  images: Array<{
    src: string
    alt: string
    id: string
  }>
  columns?: number
  gap?: number
  aspectRatio?: number
  onImageClick?: (image: { src: string; alt: string; id: string }) => void
}

export function ImageGrid({
  images,
  columns = 3,
  gap = 16,
  aspectRatio = 1,
  onImageClick,
}: ImageGridProps): JSX.Element {
  return (
    <Box
      style={{
        display: 'grid',
        gridTemplateColumns: `repeat(${columns}, 1fr)`,
        gap,
      }}
    >
      {images.map((image) => (
        <Box
          key={image.id}
          style={{
            cursor: onImageClick ? 'pointer' : 'default',
            borderRadius: '8px',
            overflow: 'hidden',
          }}
          onClick={() => onImageClick?.(image)}
        >
          <ResponsiveImage
            src={image.src}
            alt={image.alt}
            aspectRatio={aspectRatio}
            style={{
              width: '100%',
              height: 'auto',
              display: 'block',
            }}
          />
        </Box>
      ))}
    </Box>
  )
}
