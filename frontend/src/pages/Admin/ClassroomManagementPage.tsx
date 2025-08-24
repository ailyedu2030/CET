/**
 * 教室信息管理页面 - 需求2：基础信息管理
 * 实现教室信息的管理、容量配置、设备管理、排课冲突检测等功能
 */

import {
  ActionIcon,
  Badge,
  Button,
  Card,
  Container,
  Group,
  Modal,
  Pagination,
  Paper,
  Select,
  Stack,
  Table,
  Tabs,
  Text,
  TextInput,
  Textarea,
  Title,
  Tooltip,
  Alert,
} from '@mantine/core'
import { useForm } from '@mantine/form'
import { useDisclosure } from '@mantine/hooks'
import { notifications } from '@mantine/notifications'
import { DatePickerInput, TimeInput } from '@mantine/dates'
import {
  IconEye,
  IconBuilding,
  IconClock,
  IconCheck,
  IconX,
  IconPlus,
  IconSettings,
  IconChartBar,
  IconCalendar,
  IconClockHour4,
  IconRepeat,
} from '@tabler/icons-react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { useState } from 'react'

// 校区接口（预留给后续功能使用）
// interface Campus {
//   id: number
//   name: string
//   address?: string
//   description?: string
// }

// 楼栋接口
interface Building {
  id: number
  campus_id: number
  name: string
  building_number?: string
  floors: number
}

// 教室接口
interface Classroom {
  id: number
  building_id: number
  name: string
  room_number: string
  floor: number
  capacity: number
  area?: number
  equipment_list: Record<string, any>
  has_projector: boolean
  has_computer: boolean
  has_audio: boolean
  has_whiteboard: boolean
  is_available: boolean
  available_start_time?: string
  available_end_time?: string
  available_days: Record<string, any>
  maintenance_status: string
  last_maintenance_date?: string
  notes?: string
  building: Building
}

// 教室列表响应接口
interface ClassroomListResponse {
  items: Classroom[]
  total: number
  page: number
  size: number
  pages: number
}

// 冲突检查请求接口
interface ConflictCheckRequest {
  classroom_id: number
  start_time: Date
  end_time: Date
  exclude_schedule_id?: number
  repeat_type?: 'none' | 'daily' | 'weekly' | 'monthly'
  repeat_end_date?: Date
  repeat_days?: number[] // 周几重复 (0=周日, 1=周一, ...)
}

// 时间段预设接口
interface TimePreset {
  label: string
  start_time: string
  end_time: string
  duration: number // 分钟
}

// 冲突检查结果接口
interface ConflictCheckResult {
  has_conflict: boolean
  message: string
  classroom_id: number
  start_time: Date
  end_time: Date
  conflicts?: Array<{
    id: number
    title: string
    start_time: string
    end_time: string
    teacher_name?: string
  }>
}

// 设备接口 - 功能2：设备管理
interface Equipment {
  id: number
  classroom_id: number
  name: string
  equipment_type: string
  brand?: string
  model?: string
  serial_number?: string
  status: string
  purchase_date?: string
  warranty_end_date?: string
  last_maintenance_date?: string
  next_maintenance_date?: string
  total_usage_hours: number
  monthly_usage_hours: number
  failure_count: number
  specifications: Record<string, any>
  notes?: string
  created_at: string
  updated_at: string
}

// 设备创建/更新请求接口
interface EquipmentFormData {
  name: string
  equipment_type: string
  brand?: string
  model?: string
  serial_number?: string
  status?: string
  purchase_date?: Date
  warranty_end_date?: Date
  specifications?: Record<string, any>
  notes?: string
}

// 时间段预设数据
const TIME_PRESETS: TimePreset[] = [
  { label: '第一节课 (08:00-09:40)', start_time: '08:00', end_time: '09:40', duration: 100 },
  { label: '第二节课 (10:00-11:40)', start_time: '10:00', end_time: '11:40', duration: 100 },
  { label: '第三节课 (14:00-15:40)', start_time: '14:00', end_time: '15:40', duration: 100 },
  { label: '第四节课 (16:00-17:40)', start_time: '16:00', end_time: '17:40', duration: 100 },
  { label: '第五节课 (19:00-20:40)', start_time: '19:00', end_time: '20:40', duration: 100 },
  { label: '自定义时间', start_time: '', end_time: '', duration: 0 },
]

export function ClassroomManagementPage(): JSX.Element {
  const [page, setPage] = useState(1)
  const [buildingFilter, setBuildingFilter] = useState<string | null>(null)
  const [availabilityFilter, setAvailabilityFilter] = useState<string | null>(null)
  const [selectedClassroom, setSelectedClassroom] = useState<Classroom | null>(null)

  const [detailOpened, { open: openDetail, close: closeDetail }] = useDisclosure(false)
  const [conflictOpened, { open: openConflict, close: closeConflict }] = useDisclosure(false)
  const [equipmentFormOpened, { open: openEquipmentForm, close: closeEquipmentForm }] =
    useDisclosure(false)

  // 设备管理状态
  const [_selectedEquipment, setSelectedEquipment] = useState<Equipment | null>(null)
  const [isEditingEquipment, setIsEditingEquipment] = useState(false)

  // 冲突检查状态
  const [selectedTimePreset, setSelectedTimePreset] = useState<string>('')
  const [conflictResult, setConflictResult] = useState<ConflictCheckResult | null>(null)
  const [isCheckingConflict, setIsCheckingConflict] = useState(false)

  // 冲突检查表单
  const conflictForm = useForm<ConflictCheckRequest>({
    initialValues: {
      classroom_id: 0,
      start_time: new Date(),
      end_time: new Date(),
      repeat_type: 'none',
      repeat_end_date: undefined,
      repeat_days: [],
    },
    validate: {
      start_time: value => (value < new Date() ? '开始时间不能早于当前时间' : null),
      end_time: (value, values) => (value <= values.start_time ? '结束时间必须晚于开始时间' : null),
      repeat_end_date: (value, values) => {
        if (values.repeat_type !== 'none' && (!value || value <= values.start_time)) {
          return '重复结束日期必须晚于开始时间'
        }
        return null
      },
    },
  })

  // 设备表单
  const equipmentForm = useForm<EquipmentFormData>({
    initialValues: {
      name: '',
      equipment_type: '',
      brand: '',
      model: '',
      serial_number: '',
      status: 'normal',
      specifications: {},
      notes: '',
    },
    validate: {
      name: value => (value.length < 1 ? '设备名称不能为空' : null),
      equipment_type: value => (value.length < 1 ? '请选择设备类型' : null),
    },
  })

  // 获取校区列表（暂时不使用，为后续功能预留）
  // const { data: campusesData } = useQuery<{ campuses: Campus[] }>({
  //   queryKey: ['campuses'],
  //   queryFn: async () => {
  //     const response = await fetch('/api/v1/users/basic-info/campuses')
  //     if (!response.ok) {
  //       throw new Error('获取校区列表失败')
  //     }
  //     return response.json()
  //   },
  // })

  // 获取楼栋列表
  const { data: buildingsData } = useQuery<{ buildings: Building[] }>({
    queryKey: ['buildings'],
    queryFn: async () => {
      const response = await fetch('/api/v1/users/basic-info/buildings')
      if (!response.ok) {
        throw new Error('获取楼栋列表失败')
      }
      return response.json()
    },
  })

  // 获取教室列表
  const {
    data: classroomsData,
    isLoading,
    error,
  } = useQuery<ClassroomListResponse>({
    queryKey: ['classrooms', page, buildingFilter, availabilityFilter],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: page.toString(),
        size: '20',
      })

      if (buildingFilter) params.append('building_id', buildingFilter)
      if (availabilityFilter) params.append('is_available', availabilityFilter)

      const response = await fetch(`/api/v1/users/basic-info/classrooms?${params}`)
      if (!response.ok) {
        throw new Error('获取教室列表失败')
      }
      return response.json()
    },
  })

  // 冲突检查
  const conflictMutation = useMutation({
    mutationFn: async (data: ConflictCheckRequest) => {
      const response = await fetch('/api/v1/users/basic-info/classrooms/check-conflict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        throw new Error('冲突检查失败')
      }
      return response.json()
    },
    onSuccess: data => {
      notifications.show({
        title: '检查完成',
        message: data.message,
        color: data.has_conflict ? 'red' : 'green',
      })
    },
    onError: (error: Error) => {
      notifications.show({
        title: '检查失败',
        message: error.message,
        color: 'red',
      })
    },
  })

  // 时间预设处理函数
  const handleTimePresetChange = (presetLabel: string) => {
    setSelectedTimePreset(presetLabel)
    const preset = TIME_PRESETS.find(p => p.label === presetLabel)

    if (preset && preset.start_time && preset.end_time) {
      const today = new Date()
      const startTime = new Date(today)
      const endTime = new Date(today)

      const [startHour, startMinute] = preset.start_time.split(':').map(Number)
      const [endHour, endMinute] = preset.end_time.split(':').map(Number)

      if (startHour !== undefined && startMinute !== undefined) {
        startTime.setHours(startHour, startMinute, 0, 0)
      }
      if (endHour !== undefined && endMinute !== undefined) {
        endTime.setHours(endHour, endMinute, 0, 0)
      }

      conflictForm.setFieldValue('start_time', startTime)
      conflictForm.setFieldValue('end_time', endTime)
    }
  }

  const handleConflictCheck = (classroom: Classroom) => {
    setSelectedClassroom(classroom)
    conflictForm.setValues({
      classroom_id: classroom.id,
      start_time: new Date(),
      end_time: new Date(Date.now() + 2 * 60 * 60 * 1000), // 默认2小时后
      repeat_type: 'none',
      repeat_end_date: undefined,
      repeat_days: [],
    })
    setSelectedTimePreset('')
    setConflictResult(null)
    openConflict()
  }

  const handleConflictSubmit = async (values: ConflictCheckRequest) => {
    setIsCheckingConflict(true)
    try {
      const result = await conflictMutation.mutateAsync(values)
      setConflictResult(result)
    } catch (error) {
      notifications.show({
        title: '冲突检查失败',
        message: '请稍后重试',
        color: 'red',
      })
    } finally {
      setIsCheckingConflict(false)
    }
  }

  // 实时冲突检查
  const handleRealTimeConflictCheck = async () => {
    if (!conflictForm.isValid() || !selectedClassroom) return

    setIsCheckingConflict(true)
    try {
      const values = conflictForm.values
      const result = await conflictMutation.mutateAsync(values)
      setConflictResult(result)
    } catch (error) {
      notifications.show({
        title: '实时冲突检查失败',
        message: '请稍后重试',
        color: 'red',
      })
    } finally {
      setIsCheckingConflict(false)
    }
  }

  const getMaintenanceStatusColor = (status: string) => {
    switch (status) {
      case 'normal':
        return 'green'
      case 'maintenance':
        return 'orange'
      case 'repair':
        return 'red'
      case 'unavailable':
        return 'gray'
      default:
        return 'gray'
    }
  }

  const getMaintenanceStatusLabel = (status: string) => {
    switch (status) {
      case 'normal':
        return '正常'
      case 'maintenance':
        return '维护中'
      case 'repair':
        return '维修中'
      case 'unavailable':
        return '不可用'
      default:
        return '未知'
    }
  }

  const renderEquipmentBadges = (classroom: Classroom) => {
    const equipment = []
    if (classroom.has_projector) equipment.push('投影仪')
    if (classroom.has_computer) equipment.push('电脑')
    if (classroom.has_audio) equipment.push('音响')
    if (classroom.has_whiteboard) equipment.push('白板')

    return equipment.map(item => (
      <Badge key={item} size="xs" variant="light">
        {item}
      </Badge>
    ))
  }

  return (
    <Container size="xl" py="md">
      <Stack>
        <Title order={2}>教室信息管理</Title>

        {/* 搜索和过滤 */}
        <Paper withBorder p="md">
          <Group>
            <Select
              placeholder="选择楼栋"
              data={
                buildingsData?.buildings.map(building => ({
                  value: building.id.toString(),
                  label: `${building.name} (${building.building_number || '无编号'})`,
                })) || []
              }
              value={buildingFilter}
              onChange={setBuildingFilter}
              clearable
              leftSection={<IconBuilding size={16} />}
            />

            <Select
              placeholder="可用状态"
              data={[
                { value: 'true', label: '可用' },
                { value: 'false', label: '不可用' },
              ]}
              value={availabilityFilter}
              onChange={setAvailabilityFilter}
              clearable
            />
          </Group>
        </Paper>

        {/* 教室列表 */}
        <Paper withBorder>
          <Table striped highlightOnHover>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>教室信息</Table.Th>
                <Table.Th>容量配置</Table.Th>
                <Table.Th>设备配置</Table.Th>
                <Table.Th>可用状态</Table.Th>
                <Table.Th>维护状态</Table.Th>
                <Table.Th>操作</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {classroomsData?.items.map(classroom => (
                <Table.Tr key={classroom.id}>
                  <Table.Td>
                    <Stack gap="xs">
                      <Text fw={500}>{classroom.name}</Text>
                      <Text size="sm" c="dimmed">
                        {classroom.building.name} - {classroom.room_number}
                      </Text>
                      <Text size="xs" c="dimmed">
                        {classroom.floor}楼
                      </Text>
                    </Stack>
                  </Table.Td>

                  <Table.Td>
                    <Stack gap="xs">
                      <Text size="sm">座位数：{classroom.capacity}</Text>
                      {classroom.area && <Text size="sm">面积：{classroom.area}㎡</Text>}
                    </Stack>
                  </Table.Td>

                  <Table.Td>
                    <Group gap="xs">{renderEquipmentBadges(classroom)}</Group>
                  </Table.Td>

                  <Table.Td>
                    <Badge
                      color={classroom.is_available ? 'green' : 'red'}
                      variant="light"
                      leftSection={
                        classroom.is_available ? <IconCheck size={12} /> : <IconX size={12} />
                      }
                    >
                      {classroom.is_available ? '可用' : '不可用'}
                    </Badge>
                  </Table.Td>

                  <Table.Td>
                    <Badge
                      color={getMaintenanceStatusColor(classroom.maintenance_status)}
                      variant="light"
                    >
                      {getMaintenanceStatusLabel(classroom.maintenance_status)}
                    </Badge>
                  </Table.Td>

                  <Table.Td>
                    <Group gap="xs">
                      <Tooltip label="查看详情">
                        <ActionIcon
                          variant="light"
                          onClick={() => {
                            setSelectedClassroom(classroom)
                            openDetail()
                          }}
                        >
                          <IconEye size={16} />
                        </ActionIcon>
                      </Tooltip>

                      <Tooltip label="冲突检查">
                        <ActionIcon
                          variant="light"
                          color="blue"
                          onClick={() => handleConflictCheck(classroom)}
                        >
                          <IconClock size={16} />
                        </ActionIcon>
                      </Tooltip>
                    </Group>
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>

          {/* 分页 */}
          {classroomsData && classroomsData.pages > 1 && (
            <Group justify="center" p="md">
              <Pagination value={page} onChange={setPage} total={classroomsData.pages} />
            </Group>
          )}
        </Paper>

        {/* 加载状态 */}
        {isLoading && (
          <Paper withBorder p="xl" ta="center">
            <Text>正在加载教室信息...</Text>
          </Paper>
        )}

        {/* 错误状态 */}
        {error && (
          <Paper withBorder p="xl" ta="center">
            <Text c="red">加载失败：{error.message}</Text>
          </Paper>
        )}
      </Stack>

      {/* 教室详情模态框 */}
      <Modal opened={detailOpened} onClose={closeDetail} title="教室详细信息" size="xl">
        {selectedClassroom && (
          <Tabs defaultValue="basic">
            <Tabs.List>
              <Tabs.Tab value="basic" leftSection={<IconBuilding size={16} />}>
                基本信息
              </Tabs.Tab>
              <Tabs.Tab value="equipment" leftSection={<IconSettings size={16} />}>
                设备管理
              </Tabs.Tab>
              <Tabs.Tab value="statistics" leftSection={<IconChartBar size={16} />}>
                使用统计
              </Tabs.Tab>
            </Tabs.List>

            <Tabs.Panel value="basic" pt="md">
              <Stack>
                <Card withBorder>
                  <Stack>
                    <Title order={4}>基本信息</Title>
                    <Group>
                      <Text>
                        <strong>教室名称：</strong>
                        {selectedClassroom.name}
                      </Text>
                      <Text>
                        <strong>教室编号：</strong>
                        {selectedClassroom.room_number}
                      </Text>
                      <Text>
                        <strong>楼层：</strong>
                        {selectedClassroom.floor}楼
                      </Text>
                    </Group>
                    <Text>
                      <strong>所属楼栋：</strong>
                      {selectedClassroom.building.name}
                    </Text>
                    <Text>
                      <strong>座位数：</strong>
                      {selectedClassroom.capacity}
                    </Text>
                    {selectedClassroom.area && (
                      <Text>
                        <strong>面积：</strong>
                        {selectedClassroom.area}平方米
                      </Text>
                    )}
                  </Stack>
                </Card>

                <Card withBorder>
                  <Stack>
                    <Title order={4}>设备配置</Title>
                    <Group>
                      <Badge color={selectedClassroom.has_projector ? 'green' : 'gray'}>
                        投影仪：{selectedClassroom.has_projector ? '有' : '无'}
                      </Badge>
                      <Badge color={selectedClassroom.has_computer ? 'green' : 'gray'}>
                        电脑：{selectedClassroom.has_computer ? '有' : '无'}
                      </Badge>
                      <Badge color={selectedClassroom.has_audio ? 'green' : 'gray'}>
                        音响：{selectedClassroom.has_audio ? '有' : '无'}
                      </Badge>
                      <Badge color={selectedClassroom.has_whiteboard ? 'green' : 'gray'}>
                        白板：{selectedClassroom.has_whiteboard ? '有' : '无'}
                      </Badge>
                    </Group>
                  </Stack>
                </Card>

                <Card withBorder>
                  <Stack>
                    <Title order={4}>可用时间</Title>
                    {selectedClassroom.available_start_time &&
                      selectedClassroom.available_end_time && (
                        <Text>
                          <strong>可用时段：</strong>
                          {selectedClassroom.available_start_time} -{' '}
                          {selectedClassroom.available_end_time}
                        </Text>
                      )}
                    <Text>
                      <strong>可用状态：</strong>
                      {selectedClassroom.is_available ? '可用' : '不可用'}
                    </Text>
                    <Text>
                      <strong>维护状态：</strong>
                      {getMaintenanceStatusLabel(selectedClassroom.maintenance_status)}
                    </Text>
                  </Stack>
                </Card>

                {selectedClassroom.notes && (
                  <Card withBorder>
                    <Stack>
                      <Title order={4}>备注信息</Title>
                      <Text>{selectedClassroom.notes}</Text>
                    </Stack>
                  </Card>
                )}
              </Stack>
            </Tabs.Panel>

            <Tabs.Panel value="equipment" pt="md">
              <Stack>
                <Group justify="space-between">
                  <Title order={4}>设备列表</Title>
                  <Button
                    leftSection={<IconPlus size={16} />}
                    onClick={() => {
                      setSelectedEquipment(null)
                      setIsEditingEquipment(false)
                      equipmentForm.reset()
                      openEquipmentForm()
                    }}
                  >
                    添加设备
                  </Button>
                </Group>

                <Alert color="blue">
                  <Text size="sm">
                    设备管理功能正在开发中，将支持设备的增删改查、维护记录管理和使用统计。
                  </Text>
                </Alert>

                <Card withBorder>
                  <Text>设备列表将在此显示</Text>
                </Card>
              </Stack>
            </Tabs.Panel>

            <Tabs.Panel value="statistics" pt="md">
              <Stack>
                <Title order={4}>使用统计</Title>
                <Alert color="blue">
                  <Text size="sm">
                    使用统计功能正在开发中，将显示设备使用时长、故障率等统计信息。
                  </Text>
                </Alert>
              </Stack>
            </Tabs.Panel>
          </Tabs>
        )}
      </Modal>

      {/* 冲突检查模态框 */}
      <Modal opened={conflictOpened} onClose={closeConflict} title="教室排期冲突检查" size="lg">
        <form onSubmit={conflictForm.onSubmit(handleConflictSubmit)}>
          <Stack>
            <Group>
              <IconBuilding size={20} />
              <Text fw={500}>
                {selectedClassroom?.name} ({selectedClassroom?.room_number})
              </Text>
            </Group>

            {/* 时间段预设选择 */}
            <Select
              label="时间段预设"
              placeholder="选择常用时间段或自定义"
              data={TIME_PRESETS.map(preset => ({ value: preset.label, label: preset.label }))}
              value={selectedTimePreset}
              onChange={value => value && handleTimePresetChange(value)}
              leftSection={<IconClock size={16} />}
            />

            {/* 日期时间选择 */}
            <Group grow>
              <DatePickerInput
                label="开始日期"
                placeholder="选择开始日期"
                value={conflictForm.values.start_time}
                onChange={date => date && conflictForm.setFieldValue('start_time', date)}
                minDate={new Date()}
                leftSection={<IconCalendar size={16} />}
                error={conflictForm.errors['start_time']}
              />
              <TimeInput
                label="开始时间"
                value={conflictForm.values.start_time.toTimeString().slice(0, 5)}
                onChange={event => {
                  const timeValue = event.currentTarget.value
                  if (timeValue) {
                    const newDate = new Date(conflictForm.values.start_time)
                    const [hours, minutes] = timeValue.split(':').map(Number)
                    if (hours !== undefined && minutes !== undefined) {
                      newDate.setHours(hours, minutes, 0, 0)
                      conflictForm.setFieldValue('start_time', newDate)
                    }
                  }
                }}
                leftSection={<IconClockHour4 size={16} />}
              />
            </Group>

            <Group grow>
              <DatePickerInput
                label="结束日期"
                placeholder="选择结束日期"
                value={conflictForm.values.end_time}
                onChange={date => date && conflictForm.setFieldValue('end_time', date)}
                minDate={conflictForm.values.start_time}
                leftSection={<IconCalendar size={16} />}
                error={conflictForm.errors['end_time']}
              />
              <TimeInput
                label="结束时间"
                value={conflictForm.values.end_time.toTimeString().slice(0, 5)}
                onChange={event => {
                  const timeValue = event.currentTarget.value
                  if (timeValue) {
                    const newDate = new Date(conflictForm.values.end_time)
                    const [hours, minutes] = timeValue.split(':').map(Number)
                    if (hours !== undefined && minutes !== undefined) {
                      newDate.setHours(hours, minutes, 0, 0)
                      conflictForm.setFieldValue('end_time', newDate)
                    }
                  }
                }}
                leftSection={<IconClockHour4 size={16} />}
              />
            </Group>

            {/* 重复排课设置 */}
            <Select
              label="重复模式"
              placeholder="选择重复模式"
              data={[
                { value: 'none', label: '不重复' },
                { value: 'daily', label: '每日重复' },
                { value: 'weekly', label: '每周重复' },
                { value: 'monthly', label: '每月重复' },
              ]}
              value={conflictForm.values.repeat_type}
              onChange={value =>
                conflictForm.setFieldValue(
                  'repeat_type',
                  (value as ConflictCheckRequest['repeat_type']) || 'none'
                )
              }
              leftSection={<IconRepeat size={16} />}
            />

            {conflictForm.values.repeat_type !== 'none' && (
              <DatePickerInput
                label="重复结束日期"
                placeholder="选择重复结束日期"
                value={conflictForm.values.repeat_end_date}
                onChange={date => conflictForm.setFieldValue('repeat_end_date', date || undefined)}
                minDate={conflictForm.values.start_time}
                leftSection={<IconCalendar size={16} />}
                error={conflictForm.errors['repeat_end_date']}
              />
            )}

            {/* 冲突检查结果 */}
            {conflictResult && (
              <Alert
                color={conflictResult.has_conflict ? 'red' : 'green'}
                title={conflictResult.has_conflict ? '发现时间冲突' : '时间可用'}
                icon={conflictResult.has_conflict ? <IconX size={16} /> : <IconCheck size={16} />}
              >
                <Text size="sm">{conflictResult.message}</Text>
                {conflictResult.conflicts && conflictResult.conflicts.length > 0 && (
                  <Stack mt="sm" gap="xs">
                    <Text size="sm" fw={500}>
                      冲突详情：
                    </Text>
                    {conflictResult.conflicts.map((conflict, index) => (
                      <Paper key={index} p="xs" withBorder>
                        <Text size="sm">{conflict.title}</Text>
                        <Text size="xs" c="dimmed">
                          {conflict.start_time} - {conflict.end_time}
                          {conflict.teacher_name && ` | 教师：${conflict.teacher_name}`}
                        </Text>
                      </Paper>
                    ))}
                  </Stack>
                )}
              </Alert>
            )}

            <Group justify="space-between">
              <Button
                variant="light"
                onClick={handleRealTimeConflictCheck}
                loading={isCheckingConflict}
                disabled={!conflictForm.isValid()}
              >
                实时检查
              </Button>
              <Group>
                <Button variant="light" onClick={closeConflict}>
                  取消
                </Button>
                <Button
                  type="submit"
                  loading={conflictMutation.isPending}
                  disabled={conflictResult?.has_conflict}
                >
                  确认排课
                </Button>
              </Group>
            </Group>
          </Stack>
        </form>
      </Modal>

      {/* 设备表单模态框 */}
      <Modal
        opened={equipmentFormOpened}
        onClose={closeEquipmentForm}
        title={isEditingEquipment ? '编辑设备' : '添加设备'}
        size="md"
      >
        <form
          onSubmit={equipmentForm.onSubmit(() => {
            // 设备创建/更新逻辑将在后续实现
            notifications.show({
              title: '功能开发中',
              message: '设备管理功能正在开发中',
              color: 'blue',
            })
            closeEquipmentForm()
          })}
        >
          <Stack>
            <TextInput
              label="设备名称"
              required
              placeholder="请输入设备名称"
              {...equipmentForm.getInputProps('name')}
            />

            <Select
              label="设备类型"
              required
              placeholder="请选择设备类型"
              data={[
                { value: 'projector', label: '投影仪' },
                { value: 'computer', label: '电脑' },
                { value: 'audio', label: '音响设备' },
                { value: 'whiteboard', label: '白板' },
                { value: 'other', label: '其他' },
              ]}
              {...equipmentForm.getInputProps('equipment_type')}
            />

            <Group grow>
              <TextInput
                label="品牌"
                placeholder="请输入品牌"
                {...equipmentForm.getInputProps('brand')}
              />
              <TextInput
                label="型号"
                placeholder="请输入型号"
                {...equipmentForm.getInputProps('model')}
              />
            </Group>

            <TextInput
              label="序列号"
              placeholder="请输入序列号"
              {...equipmentForm.getInputProps('serial_number')}
            />

            <Select
              label="设备状态"
              data={[
                { value: 'normal', label: '正常' },
                { value: 'maintenance', label: '维护中' },
                { value: 'repair', label: '维修中' },
                { value: 'broken', label: '故障' },
                { value: 'retired', label: '已退役' },
              ]}
              {...equipmentForm.getInputProps('status')}
            />

            <Textarea
              label="备注"
              placeholder="请输入备注信息"
              rows={3}
              {...equipmentForm.getInputProps('notes')}
            />

            <Group justify="flex-end">
              <Button variant="light" onClick={closeEquipmentForm}>
                取消
              </Button>
              <Button type="submit">{isEditingEquipment ? '更新' : '创建'}</Button>
            </Group>
          </Stack>
        </form>
      </Modal>
    </Container>
  )
}
