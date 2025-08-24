/**
 * 动态调整机制组件 - 需求18验收标准2实现
 * 教案自动演进、智能题目生成、反馈周期、历史追踪
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
  Tabs,
  Modal,
  TextInput,
  Select,
  Textarea,
  NumberInput,
  Timeline,
  Table,
  Progress,
} from '@mantine/core';
import {
  IconBrain,
  IconHistory,
  IconQuestionMark,
  IconTrendingUp,
  IconCalendar,
  IconEdit,
  IconEye,
  IconChartLine,
} from '@tabler/icons-react';
import { useMutation } from '@tanstack/react-query';
import { notifications } from '@mantine/notifications';
import { useDisclosure } from '@mantine/hooks';

const DynamicAdjustment: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string | null>('lesson-evolution');
  const [evolutionModalOpened, { open: openEvolutionModal, close: closeEvolutionModal }] = useDisclosure(false);
  const [questionModalOpened, { open: openQuestionModal, close: closeQuestionModal }] = useDisclosure(false);

  const [evolutionForm, setEvolutionForm] = useState({
    lessonPlanId: '',
    masteryData: '',
  });

  const [questionForm, setQuestionForm] = useState({
    teachingProgress: '',
    difficultyLevel: 'medium',
    questionCount: 5,
  });

  // 教案自动演进
  const evolveLessonPlanMutation = useMutation({
    mutationFn: async (data: { lesson_plan_id: number; student_mastery_data: any }) => {
      const response = await fetch('/api/v1/architecture/lesson-plan/evolve', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error('教案演进失败');
      }

      return response.json();
    },
    onSuccess: () => {
      notifications.show({
        title: '演进成功',
        message: '教案已根据学生掌握度自动演进',
        color: 'green',
      });
      closeEvolutionModal();
    },
    onError: (error: Error) => {
      notifications.show({
        title: '演进失败',
        message: error.message,
        color: 'red',
      });
    },
  });

  // 智能题目生成
  const generateQuestionsMutation = useMutation({
    mutationFn: async (data: { teaching_progress: any; difficulty_level: string; question_count: number }) => {
      const response = await fetch('/api/v1/architecture/questions/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error('题目生成失败');
      }

      return response.json();
    },
    onSuccess: () => {
      notifications.show({
        title: '生成成功',
        message: '题目生成完成',
        color: 'green',
      });
      closeQuestionModal();
    },
    onError: (error: Error) => {
      notifications.show({
        title: '生成失败',
        message: error.message,
        color: 'red',
      });
    },
  });

  // 每周自动分析
  const weeklyAnalysisMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch('/api/v1/architecture/analysis/weekly', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('每周分析失败');
      }

      return response.json();
    },
    onSuccess: () => {
      notifications.show({
        title: '分析完成',
        message: '每周自动分析已完成，请查看调整建议',
        color: 'green',
      });
    },
    onError: (error: Error) => {
      notifications.show({
        title: '分析失败',
        message: error.message,
        color: 'red',
      });
    },
  });

  const handleEvolveLessonPlan = () => {
    if (!evolutionForm.lessonPlanId || !evolutionForm.masteryData) {
      notifications.show({
        title: '参数不完整',
        message: '请填写完整的教案ID和掌握度数据',
        color: 'orange',
      });
      return;
    }

    try {
      const masteryData = JSON.parse(evolutionForm.masteryData);
      evolveLessonPlanMutation.mutate({
        lesson_plan_id: parseInt(evolutionForm.lessonPlanId),
        student_mastery_data: masteryData,
      });
    } catch (error) {
      notifications.show({
        title: '数据格式错误',
        message: '请输入有效的JSON格式掌握度数据',
        color: 'red',
      });
    }
  };

  const handleGenerateQuestions = () => {
    if (!questionForm.teachingProgress) {
      notifications.show({
        title: '参数不完整',
        message: '请填写教学进度数据',
        color: 'orange',
      });
      return;
    }

    try {
      const teachingProgress = JSON.parse(questionForm.teachingProgress);
      generateQuestionsMutation.mutate({
        teaching_progress: teachingProgress,
        difficulty_level: questionForm.difficultyLevel,
        question_count: questionForm.questionCount,
      });
    } catch (error) {
      notifications.show({
        title: '数据格式错误',
        message: '请输入有效的JSON格式教学进度数据',
        color: 'red',
      });
    }
  };

  return (
    <Stack gap="md">
      <Group justify="space-between">
        <Text size="xl" fw={700}>动态调整机制</Text>
        <Group>
          <Button
            leftSection={<IconEdit size={16} />}
            onClick={openEvolutionModal}
          >
            教案演进
          </Button>
          <Button
            leftSection={<IconQuestionMark size={16} />}
            onClick={openQuestionModal}
          >
            生成题目
          </Button>
          <Button
            leftSection={<IconChartLine size={16} />}
            onClick={() => weeklyAnalysisMutation.mutate()}
            loading={weeklyAnalysisMutation.isPending}
          >
            每周分析
          </Button>
        </Group>
      </Group>

      <Tabs value={activeTab} onChange={setActiveTab}>
        <Tabs.List>
          <Tabs.Tab value="lesson-evolution" leftSection={<IconEdit size={16} />}>
            教案演进
          </Tabs.Tab>
          <Tabs.Tab value="question-generation" leftSection={<IconQuestionMark size={16} />}>
            题目生成
          </Tabs.Tab>
          <Tabs.Tab value="feedback-cycle" leftSection={<IconCalendar size={16} />}>
            反馈周期
          </Tabs.Tab>
          <Tabs.Tab value="history-tracking" leftSection={<IconHistory size={16} />}>
            历史追踪
          </Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="lesson-evolution">
          <Grid>
            <Grid.Col span={6}>
              <Card withBorder>
                <Stack gap="md">
                  <Text fw={600}>教案自动演进</Text>
                  <Text size="sm" c="dimmed">
                    根据学生掌握度数据自动调整教案内容，教师仅需审核确认
                  </Text>
                  <Group>
                    <Badge color="blue">自动化程度: 95%</Badge>
                    <Badge color="green">准确率: 92%</Badge>
                  </Group>
                  <Timeline active={2}>
                    <Timeline.Item title="数据收集" bullet={<IconTrendingUp size={12} />}>
                      <Text size="xs" c="dimmed">收集学生学习数据和掌握度信息</Text>
                    </Timeline.Item>
                    <Timeline.Item title="AI分析" bullet={<IconBrain size={12} />}>
                      <Text size="xs" c="dimmed">AI分析学习薄弱点和优势领域</Text>
                    </Timeline.Item>
                    <Timeline.Item title="教案调整" bullet={<IconEdit size={12} />}>
                      <Text size="xs" c="dimmed">自动生成教案调整建议</Text>
                    </Timeline.Item>
                    <Timeline.Item title="教师审核" bullet={<IconEye size={12} />}>
                      <Text size="xs" c="dimmed">教师审核并确认调整方案</Text>
                    </Timeline.Item>
                  </Timeline>
                </Stack>
              </Card>
            </Grid.Col>

            <Grid.Col span={6}>
              <Card withBorder>
                <Stack gap="md">
                  <Text fw={600}>演进统计</Text>
                  <Grid>
                    <Grid.Col span={6}>
                      <Text size="sm" c="dimmed">本周演进次数</Text>
                      <Text size="xl" fw={700}>12</Text>
                    </Grid.Col>
                    <Grid.Col span={6}>
                      <Text size="sm" c="dimmed">平均改进幅度</Text>
                      <Text size="xl" fw={700}>15%</Text>
                    </Grid.Col>
                    <Grid.Col span={6}>
                      <Text size="sm" c="dimmed">教师采纳率</Text>
                      <Text size="xl" fw={700}>88%</Text>
                    </Grid.Col>
                    <Grid.Col span={6}>
                      <Text size="sm" c="dimmed">学生满意度</Text>
                      <Text size="xl" fw={700}>4.6/5</Text>
                    </Grid.Col>
                  </Grid>
                </Stack>
              </Card>
            </Grid.Col>
          </Grid>
        </Tabs.Panel>

        <Tabs.Panel value="question-generation">
          <Grid>
            <Grid.Col span={8}>
              <Card withBorder>
                <Stack gap="md">
                  <Text fw={600}>智能题目生成</Text>
                  <Text size="sm" c="dimmed">
                    根据教学进度智能匹配生成训练题目，无需教师干预
                  </Text>
                  
                  <Table>
                    <Table.Thead>
                      <Table.Tr>
                        <Table.Th>难度级别</Table.Th>
                        <Table.Th>生成数量</Table.Th>
                        <Table.Th>质量评分</Table.Th>
                        <Table.Th>使用率</Table.Th>
                      </Table.Tr>
                    </Table.Thead>
                    <Table.Tbody>
                      <Table.Tr>
                        <Table.Td>
                          <Badge color="green" size="sm">简单</Badge>
                        </Table.Td>
                        <Table.Td>156</Table.Td>
                        <Table.Td>4.5/5</Table.Td>
                        <Table.Td>
                          <Progress value={85} size="sm" />
                        </Table.Td>
                      </Table.Tr>
                      <Table.Tr>
                        <Table.Td>
                          <Badge color="yellow" size="sm">中等</Badge>
                        </Table.Td>
                        <Table.Td>234</Table.Td>
                        <Table.Td>4.3/5</Table.Td>
                        <Table.Td>
                          <Progress value={78} size="sm" />
                        </Table.Td>
                      </Table.Tr>
                      <Table.Tr>
                        <Table.Td>
                          <Badge color="red" size="sm">困难</Badge>
                        </Table.Td>
                        <Table.Td>89</Table.Td>
                        <Table.Td>4.7/5</Table.Td>
                        <Table.Td>
                          <Progress value={92} size="sm" />
                        </Table.Td>
                      </Table.Tr>
                    </Table.Tbody>
                  </Table>
                </Stack>
              </Card>
            </Grid.Col>

            <Grid.Col span={4}>
              <Card withBorder>
                <Stack gap="md">
                  <Text fw={600}>生成效率</Text>
                  <div>
                    <Text size="sm" c="dimmed">平均生成时间</Text>
                    <Text size="lg" fw={700}>2.3秒</Text>
                  </div>
                  <div>
                    <Text size="sm" c="dimmed">今日生成总数</Text>
                    <Text size="lg" fw={700}>479题</Text>
                  </div>
                  <div>
                    <Text size="sm" c="dimmed">质量通过率</Text>
                    <Text size="lg" fw={700}>94%</Text>
                  </div>
                </Stack>
              </Card>
            </Grid.Col>
          </Grid>
        </Tabs.Panel>

        <Tabs.Panel value="feedback-cycle">
          <Card withBorder>
            <Stack gap="md">
              <Text fw={600}>反馈周期管理</Text>
              <Text size="sm" c="dimmed">
                系统每周自动分析数据，提供调整建议
              </Text>
              
              <Grid>
                <Grid.Col span={3}>
                  <Card withBorder p="md">
                    <Text size="sm" c="dimmed">本周反馈</Text>
                    <Text size="xl" fw={700}>已完成</Text>
                    <Badge color="green" size="sm">100%</Badge>
                  </Card>
                </Grid.Col>
                <Grid.Col span={3}>
                  <Card withBorder p="md">
                    <Text size="sm" c="dimmed">下次分析</Text>
                    <Text size="xl" fw={700}>3天后</Text>
                    <Badge color="blue" size="sm">自动</Badge>
                  </Card>
                </Grid.Col>
                <Grid.Col span={3}>
                  <Card withBorder p="md">
                    <Text size="sm" c="dimmed">建议采纳</Text>
                    <Text size="xl" fw={700}>85%</Text>
                    <Badge color="orange" size="sm">良好</Badge>
                  </Card>
                </Grid.Col>
                <Grid.Col span={3}>
                  <Card withBorder p="md">
                    <Text size="sm" c="dimmed">效果提升</Text>
                    <Text size="xl" fw={700}>+12%</Text>
                    <Badge color="green" size="sm">显著</Badge>
                  </Card>
                </Grid.Col>
              </Grid>
            </Stack>
          </Card>
        </Tabs.Panel>

        <Tabs.Panel value="history-tracking">
          <Card withBorder>
            <Stack gap="md">
              <Text fw={600}>历史追踪</Text>
              <Text size="sm" c="dimmed">
                记录所有调整历史，支持效果对比和经验积累
              </Text>
              
              <Timeline active={-1}>
                <Timeline.Item title="2024-01-15 教案演进" bullet={<IconEdit size={12} />}>
                  <Text size="xs" c="dimmed">
                    根据学生听力薄弱调整教学重点，增加听力练习比重
                  </Text>
                  <Badge size="xs" color="green">效果: +18%</Badge>
                </Timeline.Item>
                <Timeline.Item title="2024-01-12 题目生成" bullet={<IconQuestionMark size={12} />}>
                  <Text size="xs" c="dimmed">
                    生成25道阅读理解题目，难度中等，覆盖词汇和语法
                  </Text>
                  <Badge size="xs" color="blue">使用率: 92%</Badge>
                </Timeline.Item>
                <Timeline.Item title="2024-01-08 每周分析" bullet={<IconChartLine size={12} />}>
                  <Text size="xs" c="dimmed">
                    分析显示学生写作能力有所提升，建议增加高级词汇训练
                  </Text>
                  <Badge size="xs" color="orange">已采纳</Badge>
                </Timeline.Item>
                <Timeline.Item title="2024-01-05 教案演进" bullet={<IconEdit size={12} />}>
                  <Text size="xs" c="dimmed">
                    调整语法教学顺序，优先讲解学生错误率高的时态
                  </Text>
                  <Badge size="xs" color="green">效果: +15%</Badge>
                </Timeline.Item>
              </Timeline>
            </Stack>
          </Card>
        </Tabs.Panel>
      </Tabs>

      {/* 教案演进模态框 */}
      <Modal
        opened={evolutionModalOpened}
        onClose={closeEvolutionModal}
        title="教案自动演进"
        size="lg"
      >
        <Stack gap="md">
          <TextInput
            label="教案ID"
            placeholder="输入教案ID"
            value={evolutionForm.lessonPlanId}
            onChange={(event) => setEvolutionForm(prev => ({ 
              ...prev, 
              lessonPlanId: event.currentTarget.value 
            }))}
            required
          />
          <Textarea
            label="学生掌握度数据 (JSON格式)"
            placeholder='{"listening": 0.75, "reading": 0.82, "writing": 0.68}'
            value={evolutionForm.masteryData}
            onChange={(event) => setEvolutionForm(prev => ({ 
              ...prev, 
              masteryData: event.currentTarget.value 
            }))}
            minRows={4}
            required
          />
          <Group justify="flex-end">
            <Button variant="light" onClick={closeEvolutionModal}>
              取消
            </Button>
            <Button
              onClick={handleEvolveLessonPlan}
              loading={evolveLessonPlanMutation.isPending}
            >
              开始演进
            </Button>
          </Group>
        </Stack>
      </Modal>

      {/* 题目生成模态框 */}
      <Modal
        opened={questionModalOpened}
        onClose={closeQuestionModal}
        title="智能题目生成"
        size="lg"
      >
        <Stack gap="md">
          <Textarea
            label="教学进度数据 (JSON格式)"
            placeholder='{"current_unit": "Unit 3", "topics": ["Past Tense", "Vocabulary"]}'
            value={questionForm.teachingProgress}
            onChange={(event) => setQuestionForm(prev => ({ 
              ...prev, 
              teachingProgress: event.currentTarget.value 
            }))}
            minRows={4}
            required
          />
          <Select
            label="难度级别"
            value={questionForm.difficultyLevel}
            onChange={(value) => setQuestionForm(prev => ({ 
              ...prev, 
              difficultyLevel: value || 'medium' 
            }))}
            data={[
              { value: 'easy', label: '简单' },
              { value: 'medium', label: '中等' },
              { value: 'hard', label: '困难' },
            ]}
          />
          <NumberInput
            label="题目数量"
            value={questionForm.questionCount}
            onChange={(value) => setQuestionForm(prev => ({
              ...prev,
              questionCount: typeof value === 'number' ? value : 5
            }))}
            min={1}
            max={20}
          />
          <Group justify="flex-end">
            <Button variant="light" onClick={closeQuestionModal}>
              取消
            </Button>
            <Button
              onClick={handleGenerateQuestions}
              loading={generateQuestionsMutation.isPending}
            >
              生成题目
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Stack>
  );
};

export default DynamicAdjustment;
