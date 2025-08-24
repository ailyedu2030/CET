import {
  AppShell,
  Avatar,
  Burger,
  Group,
  Menu,
  NavLink,
  Stack,
  Text,
  UnstyledButton,
} from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import {
  IconBook,
  IconChevronDown,
  IconDashboard,
  IconFileText,
  IconLogout,
  IconSettings,
  IconUser,
  IconUsers,
  IconBrain,
  IconChartLine,
  IconBulb,
  IconCertificate,
  IconShield,
  IconKey,
  IconEye,
  IconDatabase,
  IconClipboardList,
  IconNews,
  IconCalendar,
} from '@tabler/icons-react'
import { useNavigate } from 'react-router-dom'

import { PWAStatus } from '@/components/PWA/PWAStatus'
import { AppRouter } from '@/components/Router/AppRouter'
import { useAuthStore } from '@/stores/authStore'

export function AppLayout(): JSX.Element {
  const [opened, { toggle }] = useDisclosure()
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <AppShell
      header={{ height: 60 }}
      navbar={{
        width: 280,
        breakpoint: 'sm',
        collapsed: { mobile: !opened },
      }}
      padding="md"
    >
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <Group>
            <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" />
            <Text size="xl" fw={700} c="blue">
              英语四级学习系统
            </Text>
          </Group>

          <Group gap="md">
            <PWAStatus />
            {user && (
            <Menu shadow="md" width={200}>
              <Menu.Target>
                <UnstyledButton>
                  <Group gap="sm">
                    <Avatar size="sm" />
                    <Text size="sm">{user.username}</Text>
                    <IconChevronDown size={16} />
                  </Group>
                </UnstyledButton>
              </Menu.Target>

              <Menu.Dropdown>
                <Menu.Item leftSection={<IconUser size={16} />}>个人资料</Menu.Item>
                <Menu.Item leftSection={<IconSettings size={16} />}>设置</Menu.Item>
                <Menu.Divider />
                <Menu.Item
                  leftSection={<IconLogout size={16} />}
                  onClick={handleLogout}
                  color="red"
                >
                  退出登录
                </Menu.Item>
              </Menu.Dropdown>
            </Menu>
            )}
          </Group>
        </Group>
      </AppShell.Header>

      <AppShell.Navbar p="md">
        <Stack gap="xs">
          <Text size="sm" fw={500} c="dimmed" mb="xs">
            主导航
          </Text>

          <NavLink
            href="/"
            label="首页"
            leftSection={<IconDashboard size="1rem" />}
            onClick={() => navigate('/')}
          />

          {user?.userType === 'admin' && (
            <>
              <Text size="sm" fw={500} c="dimmed" mb="xs" mt="md">
                用户管理
              </Text>
              <NavLink
                href="/admin/users"
                label="用户管理"
                leftSection={<IconUsers size="1rem" />}
                onClick={() => navigate('/admin/users')}
              />
              <NavLink
                href="/admin/registration-review"
                label="注册审核"
                leftSection={<IconUser size="1rem" />}
                onClick={() => navigate('/admin/registration-review')}
              />
              <NavLink
                href="/admin/permissions"
                label="权限管理"
                leftSection={<IconShield size="1rem" />}
                onClick={() => navigate('/admin/permissions')}
              />
              <NavLink
                href="/admin/mfa"
                label="多因素认证"
                leftSection={<IconKey size="1rem" />}
                onClick={() => navigate('/admin/mfa')}
              />

              <Text size="sm" fw={500} c="dimmed" mb="xs" mt="md">
                课程与规则
              </Text>
              <NavLink
                href="/admin/courses"
                label="课程管理"
                leftSection={<IconBook size="1rem" />}
                onClick={() => navigate('/admin/courses')}
              />
              <NavLink
                href="/admin/rules"
                label="规则管理"
                leftSection={<IconClipboardList size="1rem" />}
                onClick={() => navigate('/admin/rules')}
              />

              <Text size="sm" fw={500} c="dimmed" mb="xs" mt="md">
                系统监控
              </Text>
              <NavLink
                href="/admin/audit-logs"
                label="审计日志"
                leftSection={<IconEye size="1rem" />}
                onClick={() => navigate('/admin/audit-logs')}
              />
              <NavLink
                href="/admin/backup"
                label="数据备份"
                leftSection={<IconDatabase size="1rem" />}
                onClick={() => navigate('/admin/backup')}
              />
            </>
          )}

          {user?.userType === 'teacher' && (
            <>
              <NavLink
                href="/teacher/dashboard"
                label="教师工作台"
                leftSection={<IconDashboard size="1rem" />}
                onClick={() => navigate('/teacher/dashboard')}
              />
              <NavLink
                href="/teacher/courses"
                label="我的课程"
                leftSection={<IconBook size="1rem" />}
                onClick={() => navigate('/teacher/courses')}
              />
              <Text size="sm" fw={500} c="dimmed" mb="xs" mt="md">
                AI智能助手
              </Text>
              <NavLink
                href="/teacher/analytics"
                label="学情分析"
                leftSection={<IconChartLine size="1rem" />}
                onClick={() => navigate('/teacher/analytics')}
              />
              <NavLink
                href="/teacher/adjustments"
                label="智能调整"
                leftSection={<IconBulb size="1rem" />}
                onClick={() => navigate('/teacher/adjustments')}
              />
              <NavLink
                href="/teacher/syllabus"
                label="课程大纲"
                leftSection={<IconBrain size="1rem" />}
                onClick={() => navigate('/teacher/syllabus')}
              />
              <Text size="sm" fw={500} c="dimmed" mb="xs" mt="md">
                资源管理
              </Text>
              <NavLink
                href="/teacher/resources"
                label="资源库"
                leftSection={<IconFileText size="1rem" />}
                onClick={() => navigate('/teacher/resources')}
              />
              <NavLink
                href="/teacher/hot-topics"
                label="热点资源"
                leftSection={<IconNews size="1rem" />}
                onClick={() => navigate('/teacher/hot-topics')}
              />
              <NavLink
                href="/teacher/lesson-plans"
                label="教案构建"
                leftSection={<IconFileText size="1rem" />}
                onClick={() => navigate('/teacher/lesson-plans')}
              />
              <NavLink
                href="/teacher/training-workshop"
                label="智能训练工坊"
                leftSection={<IconSettings size="1rem" />}
                onClick={() => navigate('/teacher/training-workshop')}
              />
              <Text size="sm" fw={500} c="dimmed" mb="xs" mt="md">
                专业发展
              </Text>
              <NavLink
                href="/teacher/professional-development"
                label="专业发展支持"
                leftSection={<IconUsers size="1rem" />}
                onClick={() => navigate('/teacher/professional-development')}
              />
              <NavLink
                href="/teacher/schedule"
                label="课程表"
                leftSection={<IconCalendar size="1rem" />}
                onClick={() => navigate('/teacher/schedule')}
              />
              <NavLink
                href="/teacher/qualification"
                label="资质认证"
                leftSection={<IconCertificate size="1rem" />}
                onClick={() => navigate('/teacher/qualification')}
              />
            </>
          )}

          {user?.userType === 'student' && (
            <>
              <NavLink
                href="/student/training"
                label="训练中心"
                leftSection={<IconBook size="1rem" />}
                onClick={() => navigate('/student/training')}
              />
              <NavLink
                href="/student/progress"
                label="学习进度"
                leftSection={<IconFileText size="1rem" />}
                onClick={() => navigate('/student/progress')}
              />
            </>
          )}
        </Stack>
      </AppShell.Navbar>

      <AppShell.Main>
        <AppRouter />
      </AppShell.Main>
    </AppShell>
  )
}
