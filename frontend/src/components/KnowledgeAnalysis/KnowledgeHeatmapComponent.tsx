import React, { useEffect, useRef, useState, useCallback } from 'react'
import {
  Card,
  Text,
  Group,
  Stack,
  Select,
  Badge,
  ActionIcon,
  LoadingOverlay,
  Alert,
} from '@mantine/core'
import { useQuery } from '@tanstack/react-query'
import { notifications } from '@mantine/notifications'
import { IconRefresh, IconDownload } from '@tabler/icons-react'
import * as d3 from 'd3'
import { knowledgeAnalysisApi, type HeatmapData } from '../../api/knowledgeAnalysis'

// D3相关类型定义
type KnowledgePointData = HeatmapData['knowledge_points'][0]

interface KnowledgeHeatmapComponentProps {
  studentId: number
  height?: number
  width?: number
  onPointClick?: (point: KnowledgePointData) => void
  showFilters?: boolean
  autoRefresh?: boolean
}

export const KnowledgeHeatmapComponent: React.FC<KnowledgeHeatmapComponentProps> = ({
  studentId,
  height = 600,
  width = 800,
  onPointClick,
  showFilters = true,
  autoRefresh = false,
}) => {
  const svgRef = useRef<SVGSVGElement>(null)
  const [filters, setFilters] = useState({
    time_range: 'month' as 'month' | 'week' | 'semester',
    categories: [] as string[],
    difficulty_levels: [] as string[],
    layout: 'grid' as 'grid' | 'tree' | 'force',
  })
  const [selectedPoint, setSelectedPoint] = useState<KnowledgePointData | null>(null)

  // 获取热力图数据
  const {
    data: heatmapData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['knowledge-heatmap', studentId, filters],
    queryFn: () => knowledgeAnalysisApi.getHeatmapData(studentId, filters),
    refetchInterval: autoRefresh ? 30000 : false, // 30秒自动刷新
  })

  // 渲染热力图
  const renderHeatmap = useCallback(
    (data: HeatmapData) => {
      if (!svgRef.current) return

      const svg = d3.select(svgRef.current)
      svg.selectAll('*').remove() // 清除之前的内容

      const margin = { top: 20, right: 20, bottom: 40, left: 60 }
      const innerWidth = width - margin.left - margin.right
      const innerHeight = height - margin.top - margin.bottom

      // 创建主容器
      const g = svg
        .attr('width', width)
        .attr('height', height)
        .append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`)

      // 颜色比例尺
      const colorScale = d3.scaleSequential(d3.interpolateRdYlGn).domain([0, 100])

      // 大小比例尺
      const sizeScale = d3
        .scaleSqrt()
        .domain([0, d3.max(data.knowledge_points, d => d.metadata.practice_count) || 1])
        .range([5, 25])

      // 根据布局类型渲染
      if (filters.layout === 'grid') {
        renderGridLayout(g, data, innerWidth, innerHeight, colorScale, sizeScale)
      } else if (filters.layout === 'tree') {
        renderTreeLayout(g, data, innerWidth, innerHeight, colorScale, sizeScale)
      } else {
        renderForceLayout(g, data, innerWidth, innerHeight, colorScale, sizeScale)
      }

      // 添加图例
      addLegend(svg, colorScale, width, height, margin)
    },
    [width, height, filters.layout]
  )

  // 网格布局
  const renderGridLayout = (
    g: d3.Selection<SVGGElement, unknown, null, undefined>,
    data: HeatmapData,
    width: number,
    height: number,
    colorScale: d3.ScaleSequential<string, never>,
    sizeScale: d3.ScalePower<number, number, never>
  ) => {
    const cols = Math.ceil(Math.sqrt(data.knowledge_points.length))
    const rows = Math.ceil(data.knowledge_points.length / cols)
    const cellWidth = width / cols
    const cellHeight = height / rows

    const cells = g
      .selectAll('.knowledge-cell')
      .data(data.knowledge_points)
      .enter()
      .append('g')
      .attr('class', 'knowledge-cell')
      .attr('transform', (_d: any, i: number) => {
        const col = i % cols
        const row = Math.floor(i / cols)
        return `translate(${col * cellWidth + cellWidth / 2}, ${row * cellHeight + cellHeight / 2})`
      })

    // 添加矩形背景
    cells
      .append('rect')
      .attr('x', -cellWidth / 2 + 5)
      .attr('y', -cellHeight / 2 + 5)
      .attr('width', cellWidth - 10)
      .attr('height', cellHeight - 10)
      .attr('fill', (d: any) => colorScale(d.value))
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .attr('rx', 5)
      .style('cursor', 'pointer')
      .on('click', handlePointClick)
      .on('mouseover', handleMouseOver)
      .on('mouseout', handleMouseOut)

    // 添加圆点表示练习次数
    cells
      .append('circle')
      .attr('cx', cellWidth / 2 - 15)
      .attr('cy', -cellHeight / 2 + 15)
      .attr('r', (d: any) => sizeScale(d.metadata.practice_count))
      .attr('fill', '#333')
      .attr('opacity', 0.7)

    // 添加文本标签
    cells
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .style('font-size', '12px')
      .style('font-weight', 'bold')
      .style('fill', '#333')
      .text((d: any) => (d.name.length > 8 ? d.name.substring(0, 8) + '...' : d.name))

    // 添加掌握度文本
    cells
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '1.5em')
      .style('font-size', '10px')
      .style('fill', '#666')
      .text((d: any) => `${d.value}%`)
  }

  // 树形布局（简化版）
  const renderTreeLayout = (
    g: d3.Selection<SVGGElement, unknown, null, undefined>,
    data: HeatmapData,
    _width: number,
    height: number,
    colorScale: d3.ScaleSequential<string, never>,
    sizeScale: d3.ScalePower<number, number, never>
  ) => {
    // 按类别分组
    const categories = d3.group(data.knowledge_points, d => d.category)
    const categoryArray = Array.from(categories.entries())

    categoryArray.forEach((category, categoryIndex) => {
      const [categoryName, points] = category
      const categoryY = ((categoryIndex + 1) * height) / (categoryArray.length + 1)

      // 类别标签
      g.append('text')
        .attr('x', 10)
        .attr('y', categoryY)
        .style('font-size', '14px')
        .style('font-weight', 'bold')
        .style('fill', '#333')
        .text(categoryName)

      // 知识点
      points.forEach((point, pointIndex) => {
        const pointX = 100 + pointIndex * 80

        const pointGroup = g
          .append('g')
          .attr('transform', `translate(${pointX}, ${categoryY})`)
          .style('cursor', 'pointer')
          .on('click', () => handlePointClick(point))

        pointGroup
          .append('circle')
          .attr('r', sizeScale(point.metadata.practice_count))
          .attr('fill', colorScale(point.value))
          .attr('stroke', '#fff')
          .attr('stroke-width', 2)

        pointGroup
          .append('text')
          .attr('text-anchor', 'middle')
          .attr('dy', '0.35em')
          .style('font-size', '10px')
          .style('fill', '#333')
          .text(point.name.substring(0, 6))
      })
    })
  }

  // 力导向布局（简化版）
  const renderForceLayout = (
    g: d3.Selection<SVGGElement, unknown, null, undefined>,
    data: HeatmapData,
    width: number,
    height: number,
    colorScale: d3.ScaleSequential<string, never>,
    sizeScale: d3.ScalePower<number, number, never>
  ) => {
    const simulation = d3
      .forceSimulation(data.knowledge_points)
      .force('charge', d3.forceManyBody().strength(-100))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force(
        'collision',
        d3.forceCollide().radius((d: any) => sizeScale(d.metadata.practice_count) + 2)
      )

    const nodes = g
      .selectAll('.force-node')
      .data(data.knowledge_points)
      .enter()
      .append('g')
      .attr('class', 'force-node')
      .style('cursor', 'pointer')
      .on('click', handlePointClick)

    nodes
      .append('circle')
      .attr('r', (d: any) => sizeScale(d.metadata.practice_count))
      .attr('fill', (d: any) => colorScale(d.value))
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)

    nodes
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .style('font-size', '10px')
      .style('fill', '#333')
      .text((d: any) => d.name.substring(0, 6))

    simulation.on('tick', () => {
      nodes.attr('transform', (d: any) => `translate(${d.x}, ${d.y})`)
    })
  }

  // 添加图例
  const addLegend = (
    svg: d3.Selection<SVGSVGElement, unknown, null, undefined>,
    colorScale: d3.ScaleSequential<string, never>,
    width: number,
    height: number,
    margin: { top: number; right: number; bottom: number; left: number }
  ) => {
    const legendWidth = 200
    const legendHeight = 20
    const legendX = width - legendWidth - margin.right
    const legendY = height - margin.bottom + 10

    const legend = svg.append('g').attr('transform', `translate(${legendX}, ${legendY})`)

    // 渐变定义
    const gradient = svg
      .append('defs')
      .append('linearGradient')
      .attr('id', 'heatmap-gradient')
      .attr('x1', '0%')
      .attr('x2', '100%')

    gradient
      .selectAll('stop')
      .data([0, 25, 50, 75, 100])
      .enter()
      .append('stop')
      .attr('offset', (d: number) => `${d}%`)
      .attr('stop-color', (d: number) => colorScale(d))

    // 图例矩形
    legend
      .append('rect')
      .attr('width', legendWidth)
      .attr('height', legendHeight)
      .style('fill', 'url(#heatmap-gradient)')
      .attr('stroke', '#ccc')

    // 图例标签
    legend
      .selectAll('.legend-label')
      .data([0, 50, 100])
      .enter()
      .append('text')
      .attr('class', 'legend-label')
      .attr('x', (d: number) => (d / 100) * legendWidth)
      .attr('y', legendHeight + 15)
      .attr('text-anchor', 'middle')
      .style('font-size', '12px')
      .text((d: number) => `${d}%`)

    legend
      .append('text')
      .attr('x', legendWidth / 2)
      .attr('y', -5)
      .attr('text-anchor', 'middle')
      .style('font-size', '12px')
      .style('font-weight', 'bold')
      .text('掌握程度')
  }

  // 处理点击事件
  const handlePointClick = useCallback(
    (event: KnowledgePointData | Event, d?: KnowledgePointData) => {
      const point = d || (event as KnowledgePointData)
      setSelectedPoint(point)
      if (onPointClick) {
        onPointClick(point)
      }
    },
    [onPointClick]
  )

  // 处理鼠标悬停
  const handleMouseOver = useCallback((_event: any, _d: any) => {
    // 可以添加tooltip显示详细信息
  }, [])

  const handleMouseOut = useCallback(() => {
    // 隐藏tooltip
  }, [])

  // 渲染热力图
  useEffect(() => {
    if (heatmapData) {
      renderHeatmap(heatmapData)
    }
  }, [heatmapData, renderHeatmap])

  // 导出热力图
  const handleExport = useCallback(async () => {
    try {
      const blob = await knowledgeAnalysisApi.exportAnalysisReport(studentId, {
        format: 'pdf',
        include_heatmap: true,
        time_range: filters.time_range,
      })

      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `knowledge-heatmap-${studentId}-${Date.now()}.pdf`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)

      notifications.show({
        title: '导出成功',
        message: '知识点热力图已导出',
        color: 'green',
      })
    } catch (error) {
      notifications.show({
        title: '导出失败',
        message: '导出过程中发生错误',
        color: 'red',
      })
    }
  }, [studentId, filters.time_range])

  if (error) {
    return (
      <Alert color="red" title="加载失败">
        无法加载知识点热力图数据
      </Alert>
    )
  }

  return (
    <Card withBorder padding="lg">
      <Stack gap="md">
        <Group justify="space-between" align="center">
          <Text fw={500} size="lg">
            知识点掌握热力图
          </Text>
          <Group gap="xs">
            <ActionIcon variant="outline" onClick={() => refetch()}>
              <IconRefresh size={16} />
            </ActionIcon>
            <ActionIcon variant="outline" onClick={handleExport}>
              <IconDownload size={16} />
            </ActionIcon>
          </Group>
        </Group>

        {showFilters && (
          <Group grow>
            <Select
              label="时间范围"
              value={filters.time_range}
              onChange={value =>
                setFilters(prev => ({
                  ...prev,
                  time_range: (value as 'month' | 'week' | 'semester') || 'month',
                }))
              }
              data={[
                { value: 'week', label: '最近一周' },
                { value: 'month', label: '最近一月' },
                { value: 'semester', label: '本学期' },
              ]}
            />
            <Select
              label="布局方式"
              value={filters.layout}
              onChange={value =>
                setFilters(prev => ({
                  ...prev,
                  layout: (value as 'grid' | 'tree' | 'force') || 'grid',
                }))
              }
              data={[
                { value: 'grid', label: '网格布局' },
                { value: 'tree', label: '树形布局' },
                { value: 'force', label: '力导向布局' },
              ]}
            />
          </Group>
        )}

        {heatmapData && (
          <Group gap="xs" mb="sm">
            {heatmapData.categories.map(category => (
              <Badge
                key={category.name}
                variant="light"
                style={{ backgroundColor: category.color + '20', color: category.color }}
              >
                {category.name} ({category.point_count})
              </Badge>
            ))}
          </Group>
        )}

        <div style={{ position: 'relative' }}>
          <LoadingOverlay visible={isLoading} />
          <svg ref={svgRef} style={{ border: '1px solid #e9ecef', borderRadius: '8px' }} />
        </div>

        {selectedPoint && (
          <Alert color="blue" title={`知识点：${selectedPoint.name}`}>
            <Stack gap="xs">
              <Text size="sm">
                掌握程度: <strong>{selectedPoint.value}%</strong>
              </Text>
              <Text size="sm">
                练习次数: <strong>{selectedPoint.metadata.practice_count}</strong>
              </Text>
              <Text size="sm">
                正确率: <strong>{(selectedPoint.metadata.accuracy_rate * 100).toFixed(1)}%</strong>
              </Text>
              <Text size="sm">
                最后练习:{' '}
                <strong>
                  {new Date(selectedPoint.metadata.last_practiced).toLocaleDateString()}
                </strong>
              </Text>
            </Stack>
          </Alert>
        )}
      </Stack>
    </Card>
  )
}
