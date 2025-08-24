/**
 * 教师注册页面 - 7项基础信息+3类资质材料上传
 */

import {
  Alert,
  Box,
  Button,
  Container,
  Group,
  Paper,
  SegmentedControl,
  Stack,
  Text,
  TextInput,
  Textarea,
  Title,
  Progress,
  Badge,
  ActionIcon,
  Tooltip,
  Card,
} from '@mantine/core'
import { Dropzone, FileWithPath } from '@mantine/dropzone'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import {
  IconCertificate,
  IconInfoCircle,
  IconUpload,
  IconUser,
  IconX,
  IconCheck,
  IconFile,
  IconPhoto,
} from '@tabler/icons-react'
import { useMutation } from '@tanstack/react-query'
import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { teacherRegistration, type TeacherRegistrationRequest } from '../../api/registration'

// 教师注册表单接口
interface TeacherRegistrationForm {
  // 账户基本信息
  username: string
  password: string
  confirmPassword: string
  email: string

  // 教师档案信息（7项基础信息）
  real_name: string
  age?: number
  gender?: string
  title?: string
  subject?: string
  introduction?: string
  phone?: string

  // 资质材料文件
  teacher_certificate?: File
  qualification_certificates: File[]
  honor_certificates: File[]
}

// 文件上传状态接口
interface FileUploadStatus {
  file: File
  progress: number
  status: 'uploading' | 'success' | 'error'
  url?: string
  error?: string
}

export function TeacherRegistrationPage(): JSX.Element {
  const navigate = useNavigate()
  const [currentStep, setCurrentStep] = useState<'basic' | 'profile' | 'certificates'>('basic')
  const [uploadStatus, setUploadStatus] = useState<Record<string, FileUploadStatus>>({})
  const [isUploading, setIsUploading] = useState(false)

  const form = useForm<TeacherRegistrationForm>({
    initialValues: {
      username: '',
      password: '',
      confirmPassword: '',
      email: '',
      real_name: '',
      age: undefined,
      gender: undefined,
      title: '',
      subject: '',
      introduction: '',
      phone: '',
      qualification_certificates: [],
      honor_certificates: [],
    },
    validate: {
      username: value => {
        if (!value) return '请输入用户名'
        if (value.length < 3) return '用户名至少3个字符'
        return null
      },
      password: value => {
        if (!value) return '请输入密码'
        if (value.length < 6) return '密码至少6个字符'
        return null
      },
      confirmPassword: (value, values) => {
        if (!value) return '请确认密码'
        if (value !== values.password) return '密码确认不一致'
        return null
      },
      email: value => {
        if (!value) return '请输入邮箱'
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) return '邮箱格式不正确'
        return null
      },
      real_name: value => {
        if (!value) return '请输入真实姓名'
        if (value.length < 2) return '姓名至少2个字符'
        return null
      },
      age: value => {
        if (value && (value < 22 || value > 80)) return '年龄应在22-80岁之间'
        return null
      },
      phone: value => {
        if (value && !/^1[3-9]\d{9}$/.test(value)) return '手机号格式不正确'
        return null
      },
    },
  })

  // 文件上传处理函数
  const handleFileUpload = useCallback(
    async (files: FileWithPath[], certificateType: string) => {
      setIsUploading(true)

      for (const file of files) {
        const fileKey = `${certificateType}_${file.name}`

        // 设置上传状态
        setUploadStatus(prev => ({
          ...prev,
          [fileKey]: {
            file,
            progress: 0,
            status: 'uploading',
          },
        }))

        try {
          // 模拟上传进度
          for (let progress = 0; progress <= 100; progress += 10) {
            await new Promise(resolve => setTimeout(resolve, 100))
            setUploadStatus(prev => ({
              ...prev,
              [fileKey]: {
                ...prev[fileKey]!,
                progress,
              },
            }))
          }

          // 上传成功
          setUploadStatus(prev => ({
            ...prev,
            [fileKey]: {
              ...prev[fileKey]!,
              status: 'success',
              url: URL.createObjectURL(file),
            },
          }))

          // 更新表单值
          if (certificateType === 'teacher_certificate') {
            form.setFieldValue('teacher_certificate', file)
          } else if (certificateType === 'qualification_certificates') {
            const currentFiles = form.values.qualification_certificates || []
            form.setFieldValue('qualification_certificates', [...currentFiles, file])
          } else if (certificateType === 'honor_certificates') {
            const currentFiles = form.values.honor_certificates || []
            form.setFieldValue('honor_certificates', [...currentFiles, file])
          }
        } catch (error) {
          setUploadStatus(prev => ({
            ...prev,
            [fileKey]: {
              ...prev[fileKey]!,
              status: 'error',
              error: '上传失败',
            },
          }))
        }
      }

      setIsUploading(false)
    },
    [form]
  )

  // 增强的文件上传组件
  const EnhancedFileUpload = ({
    label,
    certificateType,
    multiple = false,
  }: {
    label: string
    certificateType: string
    multiple?: boolean
  }) => {
    const relevantFiles = Object.entries(uploadStatus).filter(([key]) =>
      key.startsWith(certificateType)
    )

    return (
      <Stack>
        <Text fw={500}>{label}</Text>

        <Dropzone
          onDrop={(files: FileWithPath[]) => handleFileUpload(files, certificateType)}
          accept={['image/*', 'application/pdf']}
          maxSize={5 * 1024 * 1024} // 5MB
          multiple={multiple}
          loading={isUploading}
        >
          <Group justify="center" gap="xl" mih={120} style={{ pointerEvents: 'none' }}>
            <Dropzone.Accept>
              <IconUpload size={52} color="var(--mantine-color-blue-6)" />
            </Dropzone.Accept>
            <Dropzone.Reject>
              <IconX size={52} color="var(--mantine-color-red-6)" />
            </Dropzone.Reject>
            <Dropzone.Idle>
              <IconPhoto size={52} color="var(--mantine-color-dimmed)" />
            </Dropzone.Idle>

            <div>
              <Text size="xl" inline>
                拖拽文件到此处或点击选择文件
              </Text>
              <Text size="sm" c="dimmed" inline mt={7}>
                支持 JPG、PNG、PDF 格式，单个文件不超过 5MB
              </Text>
            </div>
          </Group>
        </Dropzone>

        {/* 文件上传状态显示 */}
        {relevantFiles.length > 0 && (
          <Stack gap="xs">
            {relevantFiles.map(([key, status]) => (
              <Card key={key} withBorder p="sm">
                <Group justify="space-between">
                  <Group>
                    <IconFile size={16} />
                    <Text size="sm" truncate style={{ maxWidth: 200 }}>
                      {status.file.name}
                    </Text>
                    {status.status === 'success' && (
                      <Badge color="green" size="sm">
                        <IconCheck size={12} />
                      </Badge>
                    )}
                    {status.status === 'error' && (
                      <Badge color="red" size="sm">
                        <IconX size={12} />
                      </Badge>
                    )}
                  </Group>

                  {status.status === 'uploading' && (
                    <Progress value={status.progress} size="sm" style={{ width: 100 }} />
                  )}

                  {status.status === 'error' && (
                    <Tooltip label={status.error}>
                      <ActionIcon color="red" variant="light" size="sm">
                        <IconX size={12} />
                      </ActionIcon>
                    </Tooltip>
                  )}
                </Group>
              </Card>
            ))}
          </Stack>
        )}
      </Stack>
    )
  }

  // 教师注册API调用
  const registrationMutation = useMutation<
    { application_id: number; message: string; estimated_review_time: string },
    Error,
    TeacherRegistrationForm
  >({
    mutationFn: async (formData: TeacherRegistrationForm) => {
      // 转换表单数据为API请求格式
      const requestData: TeacherRegistrationRequest = {
        username: formData.username,
        password: formData.password,
        email: formData.email,
        real_name: formData.real_name,
        age: formData.age,
        gender: formData.gender,
        title: formData.title,
        subject: formData.subject,
        phone: formData.phone,
        introduction: formData.introduction,
      }

      // 调用真实API
      return await teacherRegistration.register(requestData)
    },
    onSuccess: data => {
      notifications.show({
        title: '注册申请提交成功',
        message: `${data.message}，预计审核时间：${data.estimated_review_time}`,
        color: 'green',
      })

      // 跳转到状态查询页面
      navigate(`/registration/status/${data.application_id}`)
    },
    onError: (error: Error) => {
      notifications.show({
        title: '注册申请提交失败',
        message: error.message,
        color: 'red',
      })
    },
  })

  const handleSubmit = (values: TeacherRegistrationForm): void => {
    // 基础信息验证
    if (currentStep === 'basic') {
      if (!form.validate().hasErrors) {
        setCurrentStep('profile')
      }
      return
    }

    // 档案信息验证
    if (currentStep === 'profile') {
      if (!form.validate().hasErrors) {
        setCurrentStep('certificates')
      }
      return
    }

    // 资质材料验证和最终提交
    if (currentStep === 'certificates') {
      if (!form.validate().hasErrors) {
        registrationMutation.mutate(values)
      }
    }
  }

  const renderBasicInfoStep = () => (
    <Paper withBorder shadow="md" p="xl" radius="md">
      <Stack>
        <Group>
          <IconUser size={24} />
          <Title order={3}>账户基本信息</Title>
        </Group>

        <TextInput
          label="用户名"
          placeholder="请输入用户名"
          required
          {...form.getInputProps('username')}
        />

        <TextInput
          label="密码"
          type="password"
          placeholder="请输入密码"
          required
          {...form.getInputProps('password')}
        />

        <TextInput
          label="确认密码"
          type="password"
          placeholder="请再次输入密码"
          required
          {...form.getInputProps('confirmPassword')}
        />

        <TextInput
          label="邮箱地址"
          placeholder="请输入邮箱地址"
          required
          {...form.getInputProps('email')}
        />

        <Alert icon={<IconInfoCircle size="1rem" />} title="注册须知" color="blue">
          <Text size="sm">
            • 教师注册需要提供真实资料并等待管理员审核
            <br />
            • 审核通过后才能登录使用教师功能
            <br />• 请确保提供准确的联系方式以便审核通知
          </Text>
        </Alert>
      </Stack>
    </Paper>
  )

  const renderProfileStep = () => (
    <Paper withBorder shadow="md" p="xl" radius="md">
      <Stack>
        <Group>
          <IconUser size={24} />
          <Title order={3}>教师档案信息</Title>
          <Text size="sm" c="dimmed">
            （7项基础信息）
          </Text>
        </Group>

        <TextInput
          label="真实姓名"
          placeholder="请输入真实姓名"
          required
          {...form.getInputProps('real_name')}
        />

        <Group grow>
          <TextInput
            label="年龄"
            type="number"
            placeholder="请输入年龄"
            {...form.getInputProps('age')}
          />
          <Box>
            <Text size="sm" fw={500} mb="xs">
              性别
            </Text>
            <SegmentedControl
              data={[
                { label: '男', value: '男' },
                { label: '女', value: '女' },
                { label: '其他', value: '其他' },
              ]}
              {...form.getInputProps('gender')}
            />
          </Box>
        </Group>

        <Group grow>
          <TextInput
            label="职称"
            placeholder="如：助教、讲师、副教授等"
            {...form.getInputProps('title')}
          />
          <TextInput
            label="所授学科"
            placeholder="如：英语四级、大学英语等"
            {...form.getInputProps('subject')}
          />
        </Group>

        <TextInput label="联系电话" placeholder="请输入手机号码" {...form.getInputProps('phone')} />

        <Textarea
          label="自我介绍"
          placeholder="请简要介绍您的教学经历、专业背景等"
          rows={4}
          {...form.getInputProps('introduction')}
        />
      </Stack>
    </Paper>
  )

  const renderCertificatesStep = () => (
    <Paper withBorder shadow="md" p="xl" radius="md">
      <Stack>
        <Group>
          <IconCertificate size={24} />
          <Title order={3}>资质材料上传</Title>
          <Text size="sm" c="dimmed">
            （3类证书材料）
          </Text>
        </Group>

        <Alert icon={<IconInfoCircle size="1rem" />} title="文件要求" color="blue">
          <Text size="sm">
            • 支持格式：JPG、PNG、PDF
            <br />
            • 单个文件不超过5MB
            <br />• 请确保文件清晰可读，便于审核
          </Text>
        </Alert>

        <EnhancedFileUpload
          label="教师资格证书"
          certificateType="teacher_certificate"
          multiple={false}
        />

        <EnhancedFileUpload
          label="职业资格证书"
          certificateType="qualification_certificates"
          multiple={true}
        />

        <EnhancedFileUpload label="荣誉证书" certificateType="honor_certificates" multiple={true} />

        <Alert icon={<IconInfoCircle size="1rem" />} title="温馨提示" color="orange">
          <Text size="sm">
            资质材料是教师审核的重要依据，请认真上传相关证书。
            如暂时无法提供完整材料，可先提交申请，后续补充。
          </Text>
        </Alert>
      </Stack>
    </Paper>
  )

  const getStepContent = () => {
    switch (currentStep) {
      case 'basic':
        return renderBasicInfoStep()
      case 'profile':
        return renderProfileStep()
      case 'certificates':
        return renderCertificatesStep()
      default:
        return null
    }
  }

  return (
    <Container size="md" py="xl">
      <Title ta="center" mb="xl">
        教师注册申请
      </Title>

      {/* 步骤指示器 */}
      <Group justify="center" mb="xl">
        <SegmentedControl
          value={currentStep}
          data={[
            { label: '基本信息', value: 'basic' },
            { label: '档案信息', value: 'profile' },
            { label: '资质材料', value: 'certificates' },
          ]}
          disabled={registrationMutation.isPending}
        />
      </Group>

      <form onSubmit={form.onSubmit(handleSubmit)}>
        {getStepContent()}

        <Group justify="space-between" mt="xl">
          <Button
            variant="light"
            onClick={() => {
              if (currentStep === 'profile') setCurrentStep('basic')
              else if (currentStep === 'certificates') setCurrentStep('profile')
            }}
            disabled={currentStep === 'basic' || registrationMutation.isPending}
          >
            上一步
          </Button>

          <Button
            type="submit"
            loading={registrationMutation.isPending}
            disabled={registrationMutation.isPending}
          >
            {currentStep === 'certificates'
              ? '提交注册申请'
              : currentStep === 'profile'
                ? '下一步：上传资质材料'
                : '下一步：填写档案信息'}
          </Button>
        </Group>
      </form>

      {/* 帮助信息 */}
      <Paper withBorder p="md" mt="xl" bg="gray.0">
        <Text size="sm" c="dimmed" ta="center">
          如有疑问，请联系管理员邮箱：admin@cet4.com 或致电：400-123-4567
        </Text>
      </Paper>
    </Container>
  )
}
