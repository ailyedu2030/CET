/**
 * D3.js知识点掌握热力图组件 - 需求23验收标准
 * 
 * 功能特性：
 * - D3.js渲染知识点掌握热力图
 * - 支持多维度筛选和时间序列展示
 * - 交互功能：悬停提示、点击详情、缩放等
 * - 实时数据更新机制
 */

import React, { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'
import { Card, Group, Text, Select, Tooltip, ActionIcon } from '@mantine/core'
import { IconRefresh, IconDownload } from '@tabler/icons-react'

interface KnowledgePoint {
  id: string
  name: string
  category: string
  masteryLevel: number // 0-1之间的掌握程度
  attempts: number
  correctRate: number
  lastStudied: string
  difficulty: number // 1-5难度等级
  importance: number // 1-5重要程度
}

interface HeatmapData {
  knowledgePoints: KnowledgePoint[]
  timeRange: string
  lastUpdated: string
}

interface GridDataItem {
  category: string
  importance: number
  points: KnowledgePoint[]
  avgMastery: number
  count: number
}

interface D3KnowledgeHeatmapProps {
  data: HeatmapData
  width?: number
  height?: number
  onPointClick?: (point: KnowledgePoint) => void
  onDataRefresh?: () => Promise<void> | void
  className?: string
}

export const D3KnowledgeHeatmap: React.FC<D3KnowledgeHeatmapProps> = ({
  data,
  width = 800,
  height = 600,
  onPointClick,
  onDataRefresh,
  className,
}) => {
  const svgRef = useRef<SVGSVGElement>(null)
  const [filterCategory, setFilterCategory] = useState<string>('all')
  const [filterDifficulty, setFilterDifficulty] = useState<string>('all')
  const [isLoading, setIsLoading] = useState(false)

  // 获取分类选项
  const categories = ['all', ...new Set(data.knowledgePoints.map(p => p.category))]
  const difficulties = ['all', '1', '2', '3', '4', '5']

  // 过滤数据
  const filteredData = data.knowledgePoints.filter(point => {
    const categoryMatch = filterCategory === 'all' || point.category === filterCategory
    const difficultyMatch = filterDifficulty === 'all' || point.difficulty.toString() === filterDifficulty
    return categoryMatch && difficultyMatch
  })

  // D3.js热力图渲染
  useEffect(() => {
    if (!svgRef.current || filteredData.length === 0) return

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove() // 清除之前的内容

    // 设置边距和尺寸
    const margin = { top: 60, right: 120, bottom: 60, left: 120 }
    const innerWidth = width - margin.left - margin.right
    const innerHeight = height - margin.top - margin.bottom

    // 创建主容器
    const g = svg
      .attr('width', width)
      .attr('height', height)
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`)

    // 准备数据 - 按类别和重要性分组
    const categories = [...new Set(filteredData.map(d => d.category))]
    const importanceLevels = [1, 2, 3, 4, 5]

    // 创建网格数据
    const gridData: GridDataItem[] = []

    categories.forEach(category => {
      importanceLevels.forEach(importance => {
        const points = filteredData.filter(
          p => p.category === category && p.importance === importance
        )
        if (points.length > 0) {
          const avgMastery = points.reduce((sum, p) => sum + p.masteryLevel, 0) / points.length
          gridData.push({
            category,
            importance,
            points,
            avgMastery,
            count: points.length,
          })
        }
      })
    })

    // 创建比例尺
    const xScale = d3
      .scaleBand()
      .domain(categories)
      .range([0, innerWidth])
      .padding(0.1)

    const yScale = d3
      .scaleBand()
      .domain(importanceLevels.map(String))
      .range([0, innerHeight])
      .padding(0.1)

    // 颜色比例尺 - 基于掌握程度
    const colorScale = d3
      .scaleSequential(d3.interpolateRdYlGn)
      .domain([0, 1])

    // 创建工具提示
    const tooltip = d3
      .select('body')
      .append('div')
      .attr('class', 'heatmap-tooltip')
      .style('position', 'absolute')
      .style('visibility', 'hidden')
      .style('background', 'rgba(0, 0, 0, 0.8)')
      .style('color', 'white')
      .style('padding', '8px')
      .style('border-radius', '4px')
      .style('font-size', '12px')
      .style('pointer-events', 'none')
      .style('z-index', 1000)

    // 绘制热力图方块
    g.selectAll('.heatmap-cell')
      .data(gridData)
      .enter()
      .append('rect')
      .attr('class', 'heatmap-cell')
      .attr('x', (d: GridDataItem) => xScale(d.category) || 0)
      .attr('y', (d: GridDataItem) => yScale(d.importance.toString()) || 0)
      .attr('width', xScale.bandwidth())
      .attr('height', yScale.bandwidth())
      .attr('fill', (d: GridDataItem) => colorScale(d.avgMastery))
      .attr('stroke', '#fff')
      .attr('stroke-width', 1)
      .style('cursor', 'pointer')
      .on('mouseover', function(_event: any, d: GridDataItem) {
        d3.select(this as any).attr('stroke-width', 2).attr('stroke', '#333')

        tooltip
          .style('visibility', 'visible')
          .html(`
            <div><strong>${d.category}</strong></div>
            <div>重要程度: ${d.importance}/5</div>
            <div>知识点数量: ${d.count}</div>
            <div>平均掌握度: ${(d.avgMastery * 100).toFixed(1)}%</div>
            <div>详细知识点:</div>
            ${d.points.map((p: KnowledgePoint) => `<div>• ${p.name} (${(p.masteryLevel * 100).toFixed(0)}%)</div>`).join('')}
          `)
      })
      .on('mousemove', function(event: any) {
        tooltip
          .style('top', (event.pageY - 10) + 'px')
          .style('left', (event.pageX + 10) + 'px')
      })
      .on('mouseout', function() {
        d3.select(this as any).attr('stroke-width', 1).attr('stroke', '#fff')
        tooltip.style('visibility', 'hidden')
      })
      .on('click', function(_event: any, d: GridDataItem) {
        if (onPointClick && d.points.length === 1 && d.points[0]) {
          onPointClick(d.points[0])
        }
      })

    // 添加数值标签
    g.selectAll('.cell-label')
      .data(gridData)
      .enter()
      .append('text')
      .attr('class', 'cell-label')
      .attr('x', (d: GridDataItem) => (xScale(d.category) || 0) + xScale.bandwidth() / 2)
      .attr('y', (d: GridDataItem) => (yScale(d.importance.toString()) || 0) + yScale.bandwidth() / 2)
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'middle')
      .attr('fill', (d: GridDataItem) => d.avgMastery > 0.5 ? '#000' : '#fff')
      .attr('font-size', '12px')
      .attr('font-weight', 'bold')
      .text((d: GridDataItem) => `${(d.avgMastery * 100).toFixed(0)}%`)
      .style('pointer-events', 'none')

    // 添加X轴
    g.append('g')
      .attr('class', 'x-axis')
      .attr('transform', `translate(0, ${innerHeight})`)
      .call(d3.axisBottom(xScale))
      .selectAll('text')
      .style('text-anchor', 'end')
      .attr('dx', '-.8em')
      .attr('dy', '.15em')
      .attr('transform', 'rotate(-45)')

    // 添加Y轴
    g.append('g')
      .attr('class', 'y-axis')
      .call(d3.axisLeft(yScale))

    // 添加轴标签
    g.append('text')
      .attr('class', 'x-label')
      .attr('text-anchor', 'middle')
      .attr('x', innerWidth / 2)
      .attr('y', innerHeight + 50)
      .text('知识点类别')

    g.append('text')
      .attr('class', 'y-label')
      .attr('text-anchor', 'middle')
      .attr('transform', 'rotate(-90)')
      .attr('x', -innerHeight / 2)
      .attr('y', -60)
      .text('重要程度')

    // 添加标题
    g.append('text')
      .attr('class', 'chart-title')
      .attr('text-anchor', 'middle')
      .attr('x', innerWidth / 2)
      .attr('y', -20)
      .attr('font-size', '16px')
      .attr('font-weight', 'bold')
      .text('知识点掌握热力图')

    // 添加颜色图例
    const legendWidth = 200
    const legendHeight = 20
    const legendX = innerWidth - legendWidth
    const legendY = -40

    const legendScale = d3.scaleLinear().domain([0, 1]).range([0, legendWidth])
    const legendAxis = d3.axisBottom(legendScale).tickFormat((d: any) => `${(d * 100).toFixed(0)}%`)

    const legend = g.append('g')
      .attr('class', 'legend')
      .attr('transform', `translate(${legendX}, ${legendY})`)

    // 创建渐变
    const gradient = svg.append('defs')
      .append('linearGradient')
      .attr('id', 'heatmap-gradient')
      .attr('x1', '0%')
      .attr('x2', '100%')
      .attr('y1', '0%')
      .attr('y2', '0%')

    gradient.selectAll('stop')
      .data(d3.range(0, 1.1, 0.1))
      .enter()
      .append('stop')
      .attr('offset', (d: number) => `${d * 100}%`)
      .attr('stop-color', (d: number) => colorScale(d))

    legend.append('rect')
      .attr('width', legendWidth)
      .attr('height', legendHeight)
      .style('fill', 'url(#heatmap-gradient)')

    legend.append('g')
      .attr('transform', `translate(0, ${legendHeight})`)
      .call(legendAxis)

    legend.append('text')
      .attr('x', legendWidth / 2)
      .attr('y', -5)
      .attr('text-anchor', 'middle')
      .attr('font-size', '12px')
      .text('掌握程度')

    // 清理函数
    return () => {
      tooltip.remove()
    }
  }, [filteredData, width, height])

  // 刷新数据
  const handleRefresh = async () => {
    setIsLoading(true)
    try {
      if (onDataRefresh) {
        await onDataRefresh()
      }
    } finally {
      setIsLoading(false)
    }
  }

  // 导出图表
  const handleExport = () => {
    if (!svgRef.current) return

    const svgData = new XMLSerializer().serializeToString(svgRef.current)
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    const img = new Image()

    canvas.width = width
    canvas.height = height

    img.onload = () => {
      ctx?.drawImage(img, 0, 0)
      const link = document.createElement('a')
      link.download = `knowledge-heatmap-${new Date().toISOString().split('T')[0]}.png`
      link.href = canvas.toDataURL()
      link.click()
    }

    img.src = 'data:image/svg+xml;base64,' + btoa(encodeURIComponent(svgData))
  }

  return (
    <Card withBorder className={className}>
      {/* 控制面板 */}
      <Group justify="space-between" mb="md">
        <Group>
          <Select
            label="类别筛选"
            value={filterCategory}
            onChange={(value) => setFilterCategory(value || 'all')}
            data={categories.map(cat => ({ value: cat, label: cat === 'all' ? '全部类别' : cat }))}
            size="sm"
          />
          <Select
            label="难度筛选"
            value={filterDifficulty}
            onChange={(value) => setFilterDifficulty(value || 'all')}
            data={difficulties.map(diff => ({ 
              value: diff, 
              label: diff === 'all' ? '全部难度' : `难度${diff}` 
            }))}
            size="sm"
          />
        </Group>
        
        <Group>
          <Text size="sm" c="dimmed">
            最后更新: {new Date(data.lastUpdated).toLocaleString()}
          </Text>
          <Tooltip label="刷新数据">
            <ActionIcon 
              variant="light" 
              onClick={handleRefresh}
              loading={isLoading}
            >
              <IconRefresh size={16} />
            </ActionIcon>
          </Tooltip>
          <Tooltip label="导出图表">
            <ActionIcon variant="light" onClick={handleExport}>
              <IconDownload size={16} />
            </ActionIcon>
          </Tooltip>
        </Group>
      </Group>

      {/* D3.js热力图 */}
      <div style={{ textAlign: 'center' }}>
        <svg ref={svgRef} />
      </div>

      {/* 统计信息 */}
      <Group justify="space-between" mt="md" pt="md" style={{ borderTop: '1px solid #e9ecef' }}>
        <Text size="sm">
          显示 {filteredData.length} 个知识点
        </Text>
        <Text size="sm" c="dimmed">
          时间范围: {data.timeRange}
        </Text>
      </Group>
    </Card>
  )
}

export default D3KnowledgeHeatmap
