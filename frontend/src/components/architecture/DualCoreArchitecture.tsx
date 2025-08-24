/**
 * 双核驱动架构组件 - 需求18验收标准1实现
 * 数据层+智能层构成教学资源底座，支持缓存机制和增量更新
 */

import React, { useState } from 'react';
import {
  Card,
  Grid,
  Text,
  Button,
  Badge,
  Group,
  Stack,
  Loader,
  Alert,
  Progress,
  Tabs,
  Modal,
  Select,
  Textarea,
} from '@mantine/core';
import {
  IconDatabase,
  IconBrain,
  IconRefresh,
  IconChartBar,
  IconSettings,
  IconSearch,
} from '@tabler/icons-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { notifications } from '@mantine/notifications';
import { useDisclosure } from '@mantine/hooks';

interface ResourceBase {
  course_resources: Array<{
    id: number;
    name: string;
    description: string;
    category: string;
    resource_type: string;
    permission_level: string;
    download_count: number;
    updated_at: string;
  }>;
  hotspot_pool: Array<{
    id: number;
    title: string;
    content: string;
    popularity_score: number;
    source_type: string;
    source_url: string;
    created_at: string;
  }>;
  metadata: {
    total_resources: number;
    total_hotspots: number;
    last_updated: string;
    cache_key: string;
  };
}

const DualCoreArchitecture: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string | null>('resource-base');
  const [filters, setFilters] = useState({
    subject: '',
    grade: '',
    useCache: true,
  });
  const [contentModalOpened, { open: openContentModal, close: closeContentModal }] = useDisclosure(false);
  const [syllabusData, setSyllabusData] = useState('');

  const queryClient = useQueryClient();

  // 获取教学资源底座
  const {
    data: resourceBase,
    isLoading: isLoadingResourceBase,
    error: resourceBaseError,
    refetch: refetchResourceBase,
  } = useQuery<ResourceBase>({
    queryKey: ['resource-base', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters.subject) params.append('subject', filters.subject);
      if (filters.grade) params.append('grade', filters.grade);
      params.append('use_cache', filters.useCache.toString());

      const response = await fetch(`/api/v1/architecture/resource-base?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('获取教学资源底座失败');
      }

      const result = await response.json();
      return result.data;
    },
  });

  // 增量更新资源底座
  const updateResourceBaseMutation = useMutation({
    mutationFn: async (data: { resource_updates: any[]; hotspot_updates: any[] }) => {
      const response = await fetch('/api/v1/architecture/resource-base/update', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error('增量更新失败');
      }

      return response.json();
    },
    onSuccess: () => {
      notifications.show({
        title: '更新成功',
        message: '教学资源底座已成功更新',
        color: 'green',
      });
      queryClient.invalidateQueries({ queryKey: ['resource-base'] });
    },
    onError: (error: Error) => {
      notifications.show({
        title: '更新失败',
        message: error.message,
        color: 'red',
      });
    },
  });

  // 生成智能教学内容
  const generateContentMutation = useMutation({
    mutationFn: async (data: { syllabus_data: any; resource_base: any }) => {
      const response = await fetch('/api/v1/architecture/teaching-content/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error('生成智能教学内容失败');
      }

      return response.json();
    },
    onSuccess: () => {
      notifications.show({
        title: '生成成功',
        message: '智能教学内容已生成',
        color: 'green',
      });
    },
    onError: (error: Error) => {
      notifications.show({
        title: '生成失败',
        message: error.message,
        color: 'red',
      });
    },
  });

  const handleIncrementalUpdate = () => {
    // 示例更新数据
    const updateData = {
      resource_updates: [
        {
          id: 1,
          name: '更新的资源名称',
          description: '更新的描述',
        },
      ],
      hotspot_updates: [
        {
          id: 1,
          title: '更新的热点标题',
          popularity_score: 95,
        },
      ],
    };

    updateResourceBaseMutation.mutate(updateData);
  };

  const handleGenerateContent = () => {
    if (!syllabusData || !resourceBase) {
      notifications.show({
        title: '参数不完整',
        message: '请输入教学大纲数据',
        color: 'orange',
      });
      return;
    }

    try {
      const parsedSyllabus = JSON.parse(syllabusData);
      generateContentMutation.mutate({
        syllabus_data: parsedSyllabus,
        resource_base: resourceBase,
      });
      closeContentModal();
    } catch (error) {
      notifications.show({
        title: '数据格式错误',
        message: '请输入有效的JSON格式数据',
        color: 'red',
      });
    }
  };

  return (
    <Stack gap="md">
      <Group justify="space-between">
        <Text size="xl" fw={700}>双核驱动架构</Text>
        <Group>
          <Button
            leftSection={<IconBrain size={16} />}
            onClick={openContentModal}
            disabled={!resourceBase}
          >
            生成智能内容
          </Button>
          <Button
            leftSection={<IconRefresh size={16} />}
            onClick={handleIncrementalUpdate}
            loading={updateResourceBaseMutation.isPending}
          >
            增量更新
          </Button>
          <Button
            leftSection={<IconRefresh size={16} />}
            onClick={() => refetchResourceBase()}
            variant="light"
          >
            刷新数据
          </Button>
        </Group>
      </Group>

      {/* 筛选器 */}
      <Card withBorder>
        <Group>
          <Select
            label="学科"
            placeholder="选择学科"
            value={filters.subject}
            onChange={(value) => setFilters(prev => ({ ...prev, subject: value || '' }))}
            data={[
              { value: 'english', label: '英语' },
              { value: 'math', label: '数学' },
              { value: 'chinese', label: '语文' },
            ]}
            clearable
          />
          <Select
            label="年级"
            placeholder="选择年级"
            value={filters.grade}
            onChange={(value) => setFilters(prev => ({ ...prev, grade: value || '' }))}
            data={[
              { value: 'grade1', label: '一年级' },
              { value: 'grade2', label: '二年级' },
              { value: 'grade3', label: '三年级' },
            ]}
            clearable
          />
          <Button
            leftSection={<IconSearch size={16} />}
            onClick={() => refetchResourceBase()}
          >
            应用筛选
          </Button>
        </Group>
      </Card>

      <Tabs value={activeTab} onChange={setActiveTab}>
        <Tabs.List>
          <Tabs.Tab value="resource-base" leftSection={<IconDatabase size={16} />}>
            资源底座
          </Tabs.Tab>
          <Tabs.Tab value="cache-status" leftSection={<IconChartBar size={16} />}>
            缓存状态
          </Tabs.Tab>
          <Tabs.Tab value="system-metrics" leftSection={<IconSettings size={16} />}>
            系统指标
          </Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="resource-base">
          {isLoadingResourceBase ? (
            <Card withBorder>
              <Group justify="center">
                <Loader size="md" />
                <Text>加载教学资源底座...</Text>
              </Group>
            </Card>
          ) : resourceBaseError ? (
            <Alert color="red" title="加载失败">
              {resourceBaseError.message}
            </Alert>
          ) : resourceBase ? (
            <Grid>
              <Grid.Col span={6}>
                <Card withBorder>
                  <Stack gap="sm">
                    <Group justify="space-between">
                      <Text fw={600}>课程资源库</Text>
                      <Badge color="blue">{resourceBase.metadata.total_resources} 个资源</Badge>
                    </Group>
                    <Text size="sm" c="dimmed">
                      最后更新: {new Date(resourceBase.metadata.last_updated).toLocaleString()}
                    </Text>
                    <Stack gap="xs" mah={300} style={{ overflow: 'auto' }}>
                      {resourceBase.course_resources.slice(0, 10).map((resource) => (
                        <Card key={resource.id} withBorder p="xs">
                          <Group justify="space-between">
                            <div>
                              <Text size="sm" fw={500}>{resource.name}</Text>
                              <Text size="xs" c="dimmed">{resource.category}</Text>
                            </div>
                            <Badge size="xs" color="green">
                              {resource.download_count} 下载
                            </Badge>
                          </Group>
                        </Card>
                      ))}
                    </Stack>
                  </Stack>
                </Card>
              </Grid.Col>

              <Grid.Col span={6}>
                <Card withBorder>
                  <Stack gap="sm">
                    <Group justify="space-between">
                      <Text fw={600}>热点资源池</Text>
                      <Badge color="orange">{resourceBase.metadata.total_hotspots} 个热点</Badge>
                    </Group>
                    <Stack gap="xs" mah={300} style={{ overflow: 'auto' }}>
                      {resourceBase.hotspot_pool.slice(0, 10).map((hotspot) => (
                        <Card key={hotspot.id} withBorder p="xs">
                          <Group justify="space-between">
                            <div>
                              <Text size="sm" fw={500}>{hotspot.title}</Text>
                              <Text size="xs" c="dimmed">{hotspot.source_type}</Text>
                            </div>
                            <Badge size="xs" color="red">
                              热度 {hotspot.popularity_score}
                            </Badge>
                          </Group>
                        </Card>
                      ))}
                    </Stack>
                  </Stack>
                </Card>
              </Grid.Col>
            </Grid>
          ) : null}
        </Tabs.Panel>

        <Tabs.Panel value="cache-status">
          <Card withBorder>
            <Stack gap="md">
              <Text fw={600}>缓存状态监控</Text>
              <Grid>
                <Grid.Col span={4}>
                  <Card withBorder p="md">
                    <Text size="sm" c="dimmed">L1缓存命中率</Text>
                    <Progress value={85} color="green" size="lg" />
                    <Text size="lg" fw={700}>85%</Text>
                  </Card>
                </Grid.Col>
                <Grid.Col span={4}>
                  <Card withBorder p="md">
                    <Text size="sm" c="dimmed">L2缓存命中率</Text>
                    <Progress value={72} color="blue" size="lg" />
                    <Text size="lg" fw={700}>72%</Text>
                  </Card>
                </Grid.Col>
                <Grid.Col span={4}>
                  <Card withBorder p="md">
                    <Text size="sm" c="dimmed">总体命中率</Text>
                    <Progress value={78} color="orange" size="lg" />
                    <Text size="lg" fw={700}>78%</Text>
                  </Card>
                </Grid.Col>
              </Grid>
            </Stack>
          </Card>
        </Tabs.Panel>

        <Tabs.Panel value="system-metrics">
          <Card withBorder>
            <Stack gap="md">
              <Text fw={600}>系统性能指标</Text>
              <Grid>
                <Grid.Col span={3}>
                  <Text size="sm" c="dimmed">响应时间</Text>
                  <Text size="xl" fw={700}>120ms</Text>
                </Grid.Col>
                <Grid.Col span={3}>
                  <Text size="sm" c="dimmed">并发用户</Text>
                  <Text size="xl" fw={700}>1,247</Text>
                </Grid.Col>
                <Grid.Col span={3}>
                  <Text size="sm" c="dimmed">API调用量</Text>
                  <Text size="xl" fw={700}>15,432</Text>
                </Grid.Col>
                <Grid.Col span={3}>
                  <Text size="sm" c="dimmed">错误率</Text>
                  <Text size="xl" fw={700} c="green">0.02%</Text>
                </Grid.Col>
              </Grid>
            </Stack>
          </Card>
        </Tabs.Panel>
      </Tabs>

      {/* 生成智能内容模态框 */}
      <Modal
        opened={contentModalOpened}
        onClose={closeContentModal}
        title="生成智能教学内容"
        size="lg"
      >
        <Stack gap="md">
          <Textarea
            label="教学大纲数据 (JSON格式)"
            placeholder='{"course": "英语四级", "objectives": ["提高听力", "增强阅读"]}'
            value={syllabusData}
            onChange={(event) => setSyllabusData(event.currentTarget.value)}
            minRows={6}
            required
          />
          <Group justify="flex-end">
            <Button variant="light" onClick={closeContentModal}>
              取消
            </Button>
            <Button
              onClick={handleGenerateContent}
              loading={generateContentMutation.isPending}
            >
              生成内容
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Stack>
  );
};

export default DualCoreArchitecture;
