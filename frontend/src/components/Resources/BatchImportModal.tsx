import {
  Alert,
  Button,
  Card,
  Group,
  Modal,
  Progress,
  Select,
  Stack,
  Text,
  Title,
  Badge,
  Stepper,
  Table,
  ScrollArea,
} from '@mantine/core'
import { Dropzone, FileWithPath } from '@mantine/dropzone'
import { notifications } from '@mantine/notifications'
import {
  IconUpload,
  IconX,
  IconCheck,
  IconFile,
  IconDownload,
  IconAlertTriangle,
  IconFileSpreadsheet,
} from '@tabler/icons-react'
import { useState, useCallback } from 'react'

interface BatchImportModalProps {
  opened: boolean
  onClose: () => void
  resourceType: 'vocabulary' | 'knowledge'
  courseId: number
  onImportComplete: () => void
}

interface ImportResult {
  success: number
  failed: number
  errors: Array<{
    row: number
    field: string
    message: string
  }>
  warnings: Array<{
    row: number
    message: string
  }>
}

interface FileUploadStatus {
  file: File
  progress: number
  status: 'uploading' | 'processing' | 'success' | 'error'
  result?: ImportResult
  error?: string
}

export function BatchImportModal({
  opened,
  onClose,
  resourceType,
  courseId,
  onImportComplete,
}: BatchImportModalProps): JSX.Element {
  const [currentStep, setCurrentStep] = useState(0)
  const [uploadStatus, setUploadStatus] = useState<FileUploadStatus | null>(null)
  const [importMode, setImportMode] = useState<'replace' | 'append'>('append')

  const resourceTypeLabels = {
    vocabulary: '词汇库',
    knowledge: '知识点库',
  }

  const handleFileUpload = useCallback(
    async (files: FileWithPath[]) => {
      if (files.length === 0) return

      const file = files[0]
      if (!file) return

      // 验证文件类型
      const allowedTypes = [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // .xlsx
        'application/vnd.ms-excel', // .xls
        'application/pdf',
        'text/csv',
      ]

      if (!allowedTypes.includes(file.type)) {
        notifications.show({
          title: '文件格式错误',
          message: '请上传 Excel (.xlsx, .xls)、PDF 或 CSV 格式的文件',
          color: 'red',
        })
        return
      }

      // 设置上传状态
      setUploadStatus({
        file,
        progress: 0,
        status: 'uploading',
      })

      setCurrentStep(1)

      try {
        // 模拟上传进度
        for (let progress = 0; progress <= 100; progress += 10) {
          await new Promise(resolve => setTimeout(resolve, 100))
          setUploadStatus(prev => (prev ? { ...prev, progress } : null))
        }

        // 切换到处理状态
        setUploadStatus(prev => (prev ? { ...prev, status: 'processing', progress: 0 } : null))
        setCurrentStep(2)

        // 模拟处理进度
        for (let progress = 0; progress <= 100; progress += 20) {
          await new Promise(resolve => setTimeout(resolve, 200))
          setUploadStatus(prev => (prev ? { ...prev, progress } : null))
        }

        // 模拟导入结果
        const mockResult: ImportResult = {
          success: 85,
          failed: 5,
          errors: [
            { row: 3, field: 'word', message: '单词不能为空' },
            { row: 7, field: 'pronunciation', message: '音标格式错误' },
            { row: 12, field: 'chinese_meaning', message: '中文释义不能为空' },
          ],
          warnings: [
            { row: 15, message: '该单词已存在，已跳过' },
            { row: 23, message: '例句格式建议优化' },
          ],
        }

        setUploadStatus(prev =>
          prev
            ? {
                ...prev,
                status: 'success',
                result: mockResult,
              }
            : null
        )

        setCurrentStep(3)

        notifications.show({
          title: '导入完成',
          message: `成功导入 ${mockResult.success} 条记录，失败 ${mockResult.failed} 条`,
          color: mockResult.failed > 0 ? 'orange' : 'green',
        })
      } catch (error) {
        setUploadStatus(prev =>
          prev
            ? {
                ...prev,
                status: 'error',
                error: error instanceof Error ? error.message : '导入失败',
              }
            : null
        )

        notifications.show({
          title: '导入失败',
          message: error instanceof Error ? error.message : '文件处理失败',
          color: 'red',
        })
      }
    },
    [resourceType, courseId, importMode]
  )

  const handleDownloadTemplate = useCallback(async () => {
    try {
      // 模拟模板下载
      const templateData =
        resourceType === 'vocabulary'
          ? 'word,pronunciation,part_of_speech,chinese_meaning,english_meaning,example_sentences,tags\nhello,/həˈloʊ/,interjection,你好,greeting,"Hello, how are you?",greeting\n'
          : 'title,category,content,description,difficulty_level,learning_objectives,tags\n语法基础,grammar,英语语法基础知识,详细的语法说明,beginner,"掌握基本语法规则",grammar,basic\n'

      const blob = new Blob([templateData], { type: 'text/csv' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `${resourceTypeLabels[resourceType]}_导入模板.csv`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)

      notifications.show({
        title: '模板下载成功',
        message: '请按照模板格式准备数据',
        color: 'green',
      })
    } catch (error) {
      notifications.show({
        title: '模板下载失败',
        message: '请稍后重试',
        color: 'red',
      })
    }
  }, [resourceType])

  const handleReset = useCallback(() => {
    setCurrentStep(0)
    setUploadStatus(null)
    setImportMode('append')
  }, [])

  const handleComplete = useCallback(() => {
    onImportComplete()
    onClose()
    handleReset()
  }, [onImportComplete, onClose, handleReset])

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title={`批量导入${resourceTypeLabels[resourceType]}`}
      size="lg"
      centered
    >
      <Stack gap="md">
        {/* 进度指示器 */}
        <Stepper active={currentStep} size="sm">
          <Stepper.Step label="选择文件" description="上传数据文件" />
          <Stepper.Step label="文件上传" description="上传到服务器" />
          <Stepper.Step label="数据处理" description="解析和验证" />
          <Stepper.Step label="导入完成" description="查看结果" />
        </Stepper>

        {/* 步骤1: 文件选择 */}
        {currentStep === 0 && (
          <Stack gap="md">
            <Alert icon={<IconAlertTriangle size="1rem" />} color="blue">
              <Text size="sm">
                支持 Excel (.xlsx, .xls)、PDF 和 CSV 格式文件。建议先下载模板，按照格式准备数据。
              </Text>
            </Alert>

            <Group justify="space-between">
              <Button
                variant="light"
                leftSection={<IconDownload size={16} />}
                onClick={handleDownloadTemplate}
              >
                下载导入模板
              </Button>

              <Select
                label="导入模式"
                value={importMode}
                onChange={value => setImportMode(value as 'replace' | 'append')}
                data={[
                  { value: 'append', label: '追加模式 - 保留现有数据' },
                  { value: 'replace', label: '替换模式 - 清空后导入' },
                ]}
                style={{ minWidth: 200 }}
              />
            </Group>

            <Dropzone
              onDrop={handleFileUpload}
              accept={[
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'application/vnd.ms-excel',
                'application/pdf',
                'text/csv',
              ]}
              maxSize={10 * 1024 * 1024} // 10MB
              multiple={false}
            >
              <Group justify="center" gap="xl" mih={120} style={{ pointerEvents: 'none' }}>
                <Dropzone.Accept>
                  <IconUpload size={52} color="var(--mantine-color-blue-6)" />
                </Dropzone.Accept>
                <Dropzone.Reject>
                  <IconX size={52} color="var(--mantine-color-red-6)" />
                </Dropzone.Reject>
                <Dropzone.Idle>
                  <IconFileSpreadsheet size={52} color="var(--mantine-color-dimmed)" />
                </Dropzone.Idle>

                <div>
                  <Text size="xl" inline>
                    拖拽文件到此处或点击选择文件
                  </Text>
                  <Text size="sm" c="dimmed" inline mt={7}>
                    支持 Excel、PDF、CSV 格式，单个文件不超过 10MB
                  </Text>
                </div>
              </Group>
            </Dropzone>
          </Stack>
        )}

        {/* 步骤2-3: 上传和处理进度 */}
        {(currentStep === 1 || currentStep === 2) && uploadStatus && (
          <Stack gap="md">
            <Card withBorder p="md">
              <Group justify="space-between" mb="xs">
                <Group>
                  <IconFile size={16} />
                  <Text size="sm" fw={500}>
                    {uploadStatus.file.name}
                  </Text>
                </Group>
                <Text size="sm" c="dimmed">
                  {(uploadStatus.file.size / 1024 / 1024).toFixed(2)} MB
                </Text>
              </Group>

              <Progress
                value={uploadStatus.progress}
                size="sm"
                color={uploadStatus.status === 'error' ? 'red' : 'blue'}
                mb="xs"
              />

              <Text size="sm" c="dimmed">
                {uploadStatus.status === 'uploading' && '正在上传文件...'}
                {uploadStatus.status === 'processing' && '正在处理数据...'}
                {uploadStatus.status === 'success' && '处理完成'}
                {uploadStatus.status === 'error' && `错误: ${uploadStatus.error}`}
              </Text>
            </Card>
          </Stack>
        )}

        {/* 步骤4: 导入结果 */}
        {currentStep === 3 && uploadStatus?.result && (
          <Stack gap="md">
            <Group justify="center">
              <Badge color="green" size="lg" leftSection={<IconCheck size={16} />}>
                成功导入 {uploadStatus.result.success} 条
              </Badge>
              {uploadStatus.result.failed > 0 && (
                <Badge color="red" size="lg" leftSection={<IconX size={16} />}>
                  失败 {uploadStatus.result.failed} 条
                </Badge>
              )}
            </Group>

            {/* 错误详情 */}
            {uploadStatus.result.errors.length > 0 && (
              <Card withBorder>
                <Title order={6} mb="xs" c="red">
                  错误详情 ({uploadStatus.result.errors.length} 条)
                </Title>
                <ScrollArea h={150}>
                  <Table>
                    <Table.Thead>
                      <Table.Tr>
                        <Table.Th>行号</Table.Th>
                        <Table.Th>字段</Table.Th>
                        <Table.Th>错误信息</Table.Th>
                      </Table.Tr>
                    </Table.Thead>
                    <Table.Tbody>
                      {uploadStatus.result.errors.map((error, index) => (
                        <Table.Tr key={index}>
                          <Table.Td>{error.row}</Table.Td>
                          <Table.Td>{error.field}</Table.Td>
                          <Table.Td>{error.message}</Table.Td>
                        </Table.Tr>
                      ))}
                    </Table.Tbody>
                  </Table>
                </ScrollArea>
              </Card>
            )}

            {/* 警告信息 */}
            {uploadStatus.result.warnings.length > 0 && (
              <Card withBorder>
                <Title order={6} mb="xs" c="orange">
                  警告信息 ({uploadStatus.result.warnings.length} 条)
                </Title>
                <ScrollArea h={100}>
                  <Stack gap="xs">
                    {uploadStatus.result.warnings.map((warning, index) => (
                      <Text key={index} size="sm" c="orange">
                        第 {warning.row} 行: {warning.message}
                      </Text>
                    ))}
                  </Stack>
                </ScrollArea>
              </Card>
            )}

            <Group justify="space-between">
              <Button variant="light" onClick={handleReset}>
                重新导入
              </Button>
              <Button onClick={handleComplete}>完成</Button>
            </Group>
          </Stack>
        )}

        {/* 底部操作按钮 */}
        {currentStep === 0 && (
          <Group justify="flex-end">
            <Button variant="light" onClick={onClose}>
              取消
            </Button>
          </Group>
        )}
      </Stack>
    </Modal>
  )
}
