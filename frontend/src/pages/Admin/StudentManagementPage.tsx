/**
 * 学生信息管理页面 - 需求2：基础信息管理
 * 实现学生信息的CRUD操作、学习状态跟踪、成绩管理等功能
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
  Progress,
  Select,
  Stack,
  Table,
  Text,
  TextInput,
  Title,
  Tooltip,
  Alert,
  List,
} from '@mantine/core'
import { useDropzone } from 'react-dropzone'
import { useForm } from '@mantine/form'
import { useDisclosure } from '@mantine/hooks'
import { notifications } from '@mantine/notifications'
import {
  IconEdit,
  IconEye,
  IconSearch,
  IconUserCheck,
  IconUserX,
  IconSchool,
  IconUserPause,
  IconUpload,
  IconDownload,
  IconFileSpreadsheet,
  IconCheck,
  IconX,
  IconAlertCircle,
} from '@tabler/icons-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { adminReview, ImportResult } from '@/api/registration'

// 学生信息接口
interface Student {
  id: number
  username: string
  email: string
  is_active: boolean
  profile: {
    real_name: string
    age?: number
    gender?: string
    phone?: string
    school?: string
    department?: string
    major?: string
    grade?: string
    class_name?: string
    learning_status: string
    enrollment_date?: string
    graduation_date?: string
    average_score: number
    best_score: number
    total_exercises: number
    parent_name?: string
    parent_phone?: string
    parent_email?: string
    notes?: string
  }
  created_at: string
  updated_at: string
}

// 学生列表响应接口
interface StudentListResponse {
  items: Student[]
  total: number
  page: number
  size: number
  pages: number
}

// 状态更新请求接口
interface StatusUpdateRequest {
  learning_status: string
  notes?: string
}

export function StudentManagementPage(): JSX.Element {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string | null>(null)
  const [selectedStudent, setSelectedStudent] = useState<Student | null>(null)

  const [detailOpened, { open: openDetail, close: closeDetail }] = useDisclosure(false)
  const [statusOpened, { open: openStatus, close: closeStatus }] = useDisclosure(false)
  const [importOpened, { open: openImport, close: closeImport }] = useDisclosure(false)

  // 批量导入状态
  const [_importFile, setImportFile] = useState<File | null>(null)
  const [importResult, setImportResult] = useState<ImportResult | null>(null)
  const [isImporting, setIsImporting] = useState(false)

  // Dropzone配置
  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
    },
    maxSize: 10 * 1024 * 1024, // 10MB
    multiple: false,
    onDrop: (acceptedFiles: File[]) => {
      const file = acceptedFiles[0]
      if (file) {
        setImportFile(file)
        importMutation.mutate(file)
      }
    },
    onDropRejected: () => {
      notifications.show({
        title: '文件格式错误',
        message: '请上传Excel文件（.xlsx或.xls格式）',
        color: 'red',
      })
    },
  })

  // 状态更新表单
  const statusForm = useForm<StatusUpdateRequest>({
    initialValues: {
      learning_status: '',
      notes: '',
    },
  })

  // 获取学生列表
  const {
    data: studentsData,
    isLoading,
    error,
  } = useQuery<StudentListResponse>({
    queryKey: ['students', page, search, statusFilter],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: page.toString(),
        size: '20',
      })

      if (search) params.append('search', search)
      if (statusFilter) params.append('learning_status', statusFilter)

      const response = await fetch(`/api/v1/users/basic-info/students?${params}`)
      if (!response.ok) {
        throw new Error('获取学生列表失败')
      }
      return response.json()
    },
  })

  // 批量导入学生
  const importMutation = useMutation({
    mutationFn: async (file: File) => {
      setIsImporting(true)
      return await adminReview.importStudents(file)
    },
    onSuccess: result => {
      setImportResult(result)
      setIsImporting(false)

      if (result.success) {
        notifications.show({
          title: '导入成功',
          message: result.message,
          color: 'green',
        })
        queryClient.invalidateQueries({ queryKey: ['students'] })
      } else {
        notifications.show({
          title: '导入失败',
          message: result.message,
          color: 'red',
        })
      }
    },
    onError: (error: Error) => {
      setIsImporting(false)
      notifications.show({
        title: '导入失败',
        message: error.message,
        color: 'red',
      })
    },
  })

  // 下载Excel模板
  const downloadTemplate = async () => {
    try {
      const template = await adminReview.getImportTemplate()

      // 创建Excel文件并下载
      const headers = template.template.headers
      const sampleData = template.template.sample_data

      // 创建CSV内容（简化版，实际项目中可以使用xlsx库）
      const csvContent = [
        headers.join(','),
        ...sampleData.map((row: Record<string, any>) =>
          headers.map((header: string) => row[header] || '').join(',')
        ),
      ].join('\n')

      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = '学生信息导入模板.csv'
      link.click()

      notifications.show({
        title: '下载成功',
        message: '模板文件已下载',
        color: 'green',
      })
    } catch (error) {
      notifications.show({
        title: '下载失败',
        message: '模板下载失败，请稍后重试',
        color: 'red',
      })
    }
  }

  // 更新学生状态
  const statusMutation = useMutation({
    mutationFn: async ({ studentId, data }: { studentId: number; data: StatusUpdateRequest }) => {
      const response = await fetch(`/api/v1/users/basic-info/students/${studentId}/status`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        throw new Error('更新学生状态失败')
      }
      return response.json()
    },
    onSuccess: () => {
      notifications.show({
        title: '更新成功',
        message: '学生状态已更新',
        color: 'green',
      })
      queryClient.invalidateQueries({ queryKey: ['students'] })
      closeStatus()
    },
    onError: (error: Error) => {
      notifications.show({
        title: '更新失败',
        message: error.message,
        color: 'red',
      })
    },
  })

  const handleStatusUpdate = (student: Student) => {
    setSelectedStudent(student)
    statusForm.setValues({
      learning_status: student.profile.learning_status,
      notes: student.profile.notes || '',
    })
    openStatus()
  }

  const handleStatusSubmit = (values: StatusUpdateRequest) => {
    if (!selectedStudent) return

    statusMutation.mutate({
      studentId: selectedStudent.id,
      data: values,
    })
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'green'
      case 'inactive':
        return 'gray'
      case 'suspended':
        return 'red'
      case 'graduated':
        return 'blue'
      default:
        return 'gray'
    }
  }

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'active':
        return '在学'
      case 'inactive':
        return '休学'
      case 'suspended':
        return '停学'
      case 'graduated':
        return '毕业'
      default:
        return '未知'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <IconUserCheck size={16} />
      case 'inactive':
        return <IconUserPause size={16} />
      case 'suspended':
        return <IconUserX size={16} />
      case 'graduated':
        return <IconSchool size={16} />
      default:
        return <IconUserCheck size={16} />
    }
  }

  return (
    <Container size="xl" py="md">
      <Stack>
        <Title order={2}>学生信息管理</Title>

        {/* 搜索和过滤 */}
        <Paper withBorder p="md">
          <Group>
            <TextInput
              placeholder="搜索学生姓名、用户名或邮箱"
              leftSection={<IconSearch size={16} />}
              value={search}
              onChange={event => setSearch(event.currentTarget.value)}
              style={{ flex: 1 }}
            />

            <Select
              placeholder="学习状态"
              data={[
                { value: '', label: '全部状态' },
                { value: 'active', label: '在学' },
                { value: 'inactive', label: '休学' },
                { value: 'suspended', label: '停学' },
                { value: 'graduated', label: '毕业' },
              ]}
              value={statusFilter}
              onChange={setStatusFilter}
              clearable
            />

            <Button
              leftSection={<IconDownload size={16} />}
              variant="light"
              onClick={downloadTemplate}
            >
              下载模板
            </Button>

            <Button leftSection={<IconUpload size={16} />} onClick={openImport}>
              批量导入
            </Button>
          </Group>
        </Paper>

        {/* 学生列表 */}
        <Paper withBorder>
          <Table striped highlightOnHover>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>学生信息</Table.Th>
                <Table.Th>学习状态</Table.Th>
                <Table.Th>学习数据</Table.Th>
                <Table.Th>联系方式</Table.Th>
                <Table.Th>操作</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {studentsData?.items.map(student => (
                <Table.Tr key={student.id}>
                  <Table.Td>
                    <Stack gap="xs">
                      <Text fw={500}>{student.profile.real_name}</Text>
                      <Text size="sm" c="dimmed">
                        {student.username} • {student.email}
                      </Text>
                      {student.profile.school && (
                        <Text size="xs" c="dimmed">
                          {student.profile.school} - {student.profile.major}
                        </Text>
                      )}
                    </Stack>
                  </Table.Td>

                  <Table.Td>
                    <Badge
                      color={getStatusColor(student.profile.learning_status)}
                      variant="light"
                      leftSection={getStatusIcon(student.profile.learning_status)}
                    >
                      {getStatusLabel(student.profile.learning_status)}
                    </Badge>
                  </Table.Td>

                  <Table.Td>
                    <Stack gap="xs">
                      <Text size="sm">平均分：{student.profile.average_score.toFixed(1)}</Text>
                      <Text size="sm">最高分：{student.profile.best_score.toFixed(1)}</Text>
                      <Text size="sm">练习次数：{student.profile.total_exercises}</Text>
                    </Stack>
                  </Table.Td>

                  <Table.Td>
                    <Stack gap="xs">
                      {student.profile.phone && <Text size="sm">{student.profile.phone}</Text>}
                      {student.profile.parent_name && (
                        <Text size="xs" c="dimmed">
                          家长：{student.profile.parent_name}
                        </Text>
                      )}
                    </Stack>
                  </Table.Td>

                  <Table.Td>
                    <Group gap="xs">
                      <Tooltip label="查看详情">
                        <ActionIcon
                          variant="light"
                          onClick={() => {
                            setSelectedStudent(student)
                            openDetail()
                          }}
                        >
                          <IconEye size={16} />
                        </ActionIcon>
                      </Tooltip>

                      <Tooltip label="更新状态">
                        <ActionIcon
                          variant="light"
                          color="blue"
                          onClick={() => handleStatusUpdate(student)}
                        >
                          <IconEdit size={16} />
                        </ActionIcon>
                      </Tooltip>
                    </Group>
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>

          {/* 分页 */}
          {studentsData && studentsData.pages > 1 && (
            <Group justify="center" p="md">
              <Pagination value={page} onChange={setPage} total={studentsData.pages} />
            </Group>
          )}
        </Paper>

        {/* 加载状态 */}
        {isLoading && (
          <Paper withBorder p="xl" ta="center">
            <Text>正在加载学生信息...</Text>
          </Paper>
        )}

        {/* 错误状态 */}
        {error && (
          <Paper withBorder p="xl" ta="center">
            <Text c="red">加载失败：{error.message}</Text>
          </Paper>
        )}
      </Stack>

      {/* 学生详情模态框 */}
      <Modal opened={detailOpened} onClose={closeDetail} title="学生详细信息" size="lg">
        {selectedStudent && (
          <Stack>
            <Card withBorder>
              <Stack>
                <Title order={4}>基本信息</Title>
                <Group>
                  <Text>
                    <strong>姓名：</strong>
                    {selectedStudent.profile.real_name}
                  </Text>
                  <Text>
                    <strong>年龄：</strong>
                    {selectedStudent.profile.age || '未填写'}
                  </Text>
                  <Text>
                    <strong>性别：</strong>
                    {selectedStudent.profile.gender || '未填写'}
                  </Text>
                </Group>
                <Text>
                  <strong>学校：</strong>
                  {selectedStudent.profile.school || '未填写'}
                </Text>
                <Text>
                  <strong>专业：</strong>
                  {selectedStudent.profile.major || '未填写'}
                </Text>
                <Text>
                  <strong>年级：</strong>
                  {selectedStudent.profile.grade || '未填写'}
                </Text>
              </Stack>
            </Card>

            <Card withBorder>
              <Stack>
                <Title order={4}>学习数据</Title>
                <Group>
                  <Text>
                    <strong>平均分：</strong>
                    {selectedStudent.profile.average_score}
                  </Text>
                  <Text>
                    <strong>最高分：</strong>
                    {selectedStudent.profile.best_score}
                  </Text>
                  <Text>
                    <strong>练习次数：</strong>
                    {selectedStudent.profile.total_exercises}
                  </Text>
                </Group>
                <Text>
                  <strong>学习状态：</strong>
                  {getStatusLabel(selectedStudent.profile.learning_status)}
                </Text>
              </Stack>
            </Card>

            {selectedStudent.profile.parent_name && (
              <Card withBorder>
                <Stack>
                  <Title order={4}>家长信息</Title>
                  <Text>
                    <strong>家长姓名：</strong>
                    {selectedStudent.profile.parent_name}
                  </Text>
                  <Text>
                    <strong>家长电话：</strong>
                    {selectedStudent.profile.parent_phone || '未填写'}
                  </Text>
                  <Text>
                    <strong>家长邮箱：</strong>
                    {selectedStudent.profile.parent_email || '未填写'}
                  </Text>
                </Stack>
              </Card>
            )}
          </Stack>
        )}
      </Modal>

      {/* 状态更新模态框 */}
      <Modal opened={statusOpened} onClose={closeStatus} title="更新学生状态">
        <form onSubmit={statusForm.onSubmit(handleStatusSubmit)}>
          <Stack>
            <Select
              label="学习状态"
              required
              data={[
                { value: 'active', label: '在学' },
                { value: 'inactive', label: '休学' },
                { value: 'suspended', label: '停学' },
                { value: 'graduated', label: '毕业' },
              ]}
              {...statusForm.getInputProps('learning_status')}
            />

            <TextInput
              label="备注"
              placeholder="请输入状态变更备注"
              {...statusForm.getInputProps('notes')}
            />

            <Group justify="flex-end">
              <Button variant="light" onClick={closeStatus}>
                取消
              </Button>
              <Button type="submit" loading={statusMutation.isPending}>
                更新状态
              </Button>
            </Group>
          </Stack>
        </form>
      </Modal>

      {/* 批量导入模态框 */}
      <Modal opened={importOpened} onClose={closeImport} title="批量导入学生信息" size="lg">
        <Stack>
          {!importResult && (
            <>
              <Alert color="blue" icon={<IconAlertCircle size={16} />}>
                <Text size="sm">
                  请先下载Excel模板，按照模板格式填写学生信息后上传。
                  <br />
                  支持.xlsx和.xls格式，单次最多导入1000条记录。
                </Text>
              </Alert>

              <div
                {...getRootProps()}
                style={{
                  border: `2px dashed ${isDragActive ? 'var(--mantine-color-blue-6)' : isDragReject ? 'var(--mantine-color-red-6)' : 'var(--mantine-color-gray-4)'}`,
                  borderRadius: 'var(--mantine-radius-md)',
                  padding: '2rem',
                  textAlign: 'center',
                  cursor: 'pointer',
                  backgroundColor: isDragActive ? 'var(--mantine-color-blue-0)' : 'transparent',
                  transition: 'all 0.2s ease',
                }}
              >
                <input {...getInputProps()} />
                <Group justify="center" gap="xl" style={{ minHeight: 120 }}>
                  {isDragActive ? (
                    <IconUpload size={52} color="var(--mantine-color-blue-6)" />
                  ) : isDragReject ? (
                    <IconX size={52} color="var(--mantine-color-red-6)" />
                  ) : (
                    <IconFileSpreadsheet size={52} color="var(--mantine-color-dimmed)" />
                  )}

                  <div>
                    <Text size="xl">
                      {isDragActive ? '释放文件以上传' : '拖拽Excel文件到此处或点击选择文件'}
                    </Text>
                    <Text size="sm" c="dimmed" mt={7}>
                      支持.xlsx和.xls格式，文件大小不超过10MB
                    </Text>
                  </div>
                </Group>
              </div>

              {isImporting && (
                <Stack>
                  <Text ta="center">正在导入学生信息...</Text>
                  <Progress value={100} animated />
                </Stack>
              )}
            </>
          )}

          {importResult && (
            <Stack>
              <Alert
                color={importResult.success ? 'green' : 'red'}
                icon={importResult.success ? <IconCheck size={16} /> : <IconX size={16} />}
                title={importResult.success ? '导入完成' : '导入失败'}
              >
                <Text>{importResult.message}</Text>
              </Alert>

              <Card withBorder>
                <Stack>
                  <Title order={5}>导入统计</Title>
                  <Group>
                    <Text>总记录数：{importResult.total_records}</Text>
                    <Text c="green">成功：{importResult.successful_imports}</Text>
                    <Text c="red">失败：{importResult.failed_imports}</Text>
                  </Group>
                </Stack>
              </Card>

              {importResult.failed_records && importResult.failed_records.length > 0 && (
                <Card withBorder>
                  <Stack>
                    <Title order={5}>失败记录</Title>
                    <List size="sm">
                      {importResult.failed_records.slice(0, 10).map((record, index) => (
                        <List.Item key={index}>
                          第{record.row_number}行 - {record.real_name}({record.username}):{' '}
                          {record.error}
                        </List.Item>
                      ))}
                      {importResult.failed_records.length > 10 && (
                        <List.Item>
                          还有{importResult.failed_records.length - 10}条失败记录...
                        </List.Item>
                      )}
                    </List>
                  </Stack>
                </Card>
              )}

              <Group justify="flex-end">
                <Button
                  variant="light"
                  onClick={() => {
                    setImportResult(null)
                    setImportFile(null)
                    closeImport()
                  }}
                >
                  关闭
                </Button>
                <Button
                  onClick={() => {
                    setImportResult(null)
                    setImportFile(null)
                  }}
                >
                  继续导入
                </Button>
              </Group>
            </Stack>
          )}
        </Stack>
      </Modal>
    </Container>
  )
}
