import {
  Container,
  Title,
  Text,
  Button,
  Stack,
  Group,
  Card,
  Grid,
  Paper,
  Center,
  Divider,
} from '@mantine/core'
import { IconUserPlus, IconLogin, IconSchool, IconUsers } from '@tabler/icons-react'
import { useNavigate } from 'react-router-dom'

export function HomePage(): JSX.Element {
  const navigate = useNavigate()

  return (
    <Container size="lg" py="xl">
      <Stack gap="xl">
        {/* 主标题区域 */}
        <Center>
          <Stack gap="md" ta="center">
            <Title order={1} size="3rem" c="blue">
              英语四级学习系统
            </Title>
            <Text size="xl" c="dimmed">
              AI驱动的智能学习平台，助您轻松通过英语四级考试
            </Text>
          </Stack>
        </Center>

        {/* 快速入口区域 */}
        <Paper withBorder shadow="md" p="xl" radius="lg">
          <Stack gap="lg">
            <Title order={2} ta="center" c="dark">
              快速入口
            </Title>

            <Grid>
              {/* 学生注册入口 - 🔥需求20验收标准1 */}
              <Grid.Col span={{ base: 12, md: 6 }}>
                <Card
                  withBorder
                  shadow="sm"
                  p="lg"
                  radius="md"
                  style={{ height: '100%', cursor: 'pointer' }}
                  onClick={() => navigate('/register/student')}
                >
                  <Stack gap="md" ta="center">
                    <IconUserPlus size={48} color="var(--mantine-color-blue-6)" />
                    <Title order={3} c="blue">学生注册</Title>
                    <Text c="dimmed">
                      新学生用户注册申请，提交个人信息和学术背景，
                      等待审核通过后即可开始学习
                    </Text>
                    <Button
                      variant="filled"
                      size="md"
                      leftSection={<IconUserPlus size={16} />}
                      onClick={(e) => {
                        e.stopPropagation()
                        navigate('/register/student')
                      }}
                    >
                      立即注册
                    </Button>
                  </Stack>
                </Card>
              </Grid.Col>

              {/* 用户登录入口 */}
              <Grid.Col span={{ base: 12, md: 6 }}>
                <Card
                  withBorder
                  shadow="sm"
                  p="lg"
                  radius="md"
                  style={{ height: '100%', cursor: 'pointer' }}
                  onClick={() => navigate('/login')}
                >
                  <Stack gap="md" ta="center">
                    <IconLogin size={48} color="var(--mantine-color-green-6)" />
                    <Title order={3} c="green">用户登录</Title>
                    <Text c="dimmed">
                      已有账号的学生和教师用户登录，
                      访问个人学习中心和教学管理功能
                    </Text>
                    <Button
                      variant="filled"
                      color="green"
                      size="md"
                      leftSection={<IconLogin size={16} />}
                      onClick={(e) => {
                        e.stopPropagation()
                        navigate('/login')
                      }}
                    >
                      立即登录
                    </Button>
                  </Stack>
                </Card>
              </Grid.Col>
            </Grid>
          </Stack>
        </Paper>

        <Divider />

        {/* 其他功能区域 */}
        <Paper withBorder shadow="md" p="xl" radius="lg">
          <Stack gap="lg">
            <Title order={2} ta="center" c="dark">
              更多功能
            </Title>

            <Grid>
              {/* 教师注册 */}
              <Grid.Col span={{ base: 12, md: 6 }}>
                <Card withBorder shadow="sm" p="md" radius="md">
                  <Group gap="md">
                    <IconSchool size={32} color="var(--mantine-color-orange-6)" />
                    <Stack gap="xs" style={{ flex: 1 }}>
                      <Text fw={600} c="orange">教师注册</Text>
                      <Text size="sm" c="dimmed">
                        教育工作者申请注册，提供教学资质证明
                      </Text>
                      <Button
                        variant="outline"
                        color="orange"
                        size="xs"
                        onClick={() => navigate('/register/teacher')}
                      >
                        申请注册
                      </Button>
                    </Stack>
                  </Group>
                </Card>
              </Grid.Col>

              {/* 注册状态查询 */}
              <Grid.Col span={{ base: 12, md: 6 }}>
                <Card withBorder shadow="sm" p="md" radius="md">
                  <Group gap="md">
                    <IconUsers size={32} color="var(--mantine-color-violet-6)" />
                    <Stack gap="xs" style={{ flex: 1 }}>
                      <Text fw={600} c="violet">注册状态查询</Text>
                      <Text size="sm" c="dimmed">
                        查询注册申请的审核进度和结果
                      </Text>
                      <Button
                        variant="outline"
                        color="violet"
                        size="xs"
                        onClick={() => navigate('/registration/status')}
                      >
                        查询状态
                      </Button>
                    </Stack>
                  </Group>
                </Card>
              </Grid.Col>
            </Grid>
          </Stack>
        </Paper>
      </Stack>
    </Container>
  )
}
