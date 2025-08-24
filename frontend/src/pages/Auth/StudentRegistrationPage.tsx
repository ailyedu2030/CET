/**
 * 学生注册页面 - 11项基础信息收集
 * 严格按照需求1验收标准实现
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
  Title,
} from '@mantine/core'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import { IconInfoCircle, IconUser, IconSchool } from '@tabler/icons-react'
import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { studentRegistration, type StudentRegistrationRequest } from '../../api/registration'
import { PhoneVerification } from '../../components/Auth/PhoneVerification'

// 学生注册表单接口 - 需求1要求的11项基础信息
interface StudentRegistrationForm {
  // 账户基本信息
  username: string
  password: string
  confirmPassword: string
  email: string

  // 学生档案信息（11项基础信息）
  real_name: string // 1. 姓名
  age?: number // 2. 年龄
  gender?: string // 3. 性别
  id_number?: string // 4. 身份证号
  phone?: string // 5. 联系电话
  emergency_contact_name?: string // 6. 紧急联系人姓名
  emergency_contact_phone?: string // 7. 紧急联系人电话
  school?: string // 8. 学校
  department?: string // 9. 院系
  major?: string // 10. 专业
  grade?: string // 11. 年级
  class_name?: string // 12. 班级
}

export function StudentRegistrationPage(): JSX.Element {
  const navigate = useNavigate()
  const [currentStep, setCurrentStep] = useState<'basic' | 'profile' | 'phone' | 'academic'>('basic')
  const [isPhoneVerified, setIsPhoneVerified] = useState(false)
  const [verifiedPhone, setVerifiedPhone] = useState('')

  const form = useForm<StudentRegistrationForm>({
    initialValues: {
      username: '',
      password: '',
      confirmPassword: '',
      email: '',
      real_name: '',
      age: undefined,
      gender: undefined,
      id_number: '',
      phone: '',
      emergency_contact_name: '',
      emergency_contact_phone: '',
      school: '',
      department: '',
      major: '',
      grade: '',
      class_name: '',
    },
    validate: {
      username: value => {
        if (!value) return '请输入用户名'
        if (value.length < 3) return '用户名至少3个字符'
        if (!/^[a-zA-Z0-9_]+$/.test(value)) return '用户名只能包含字母、数字和下划线'
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
        if (value && (value < 16 || value > 35)) return '年龄应在16-35岁之间'
        return null
      },
      id_number: value => {
        if (
          value &&
          !/^[1-9]\d{5}(18|19|20)\d{2}((0[1-9])|(1[0-2]))(([0-2][1-9])|10|20|30|31)\d{3}[0-9Xx]$/.test(
            value
          )
        ) {
          return '身份证号格式不正确'
        }
        return null
      },
      phone: value => {
        if (value && !/^1[3-9]\d{9}$/.test(value)) return '手机号格式不正确'
        return null
      },
      emergency_contact_phone: value => {
        if (value && !/^1[3-9]\d{9}$/.test(value)) return '紧急联系人手机号格式不正确'
        return null
      },
    },
  })

  // 学生注册API调用
  const registrationMutation = useMutation<
    { application_id: number; message: string; estimated_review_time: string },
    Error,
    StudentRegistrationForm
  >({
    mutationFn: async (formData: StudentRegistrationForm) => {
      // 转换表单数据为API请求格式
      const requestData: StudentRegistrationRequest = {
        username: formData.username,
        password: formData.password,
        email: formData.email,
        real_name: formData.real_name,
        age: formData.age,
        gender: formData.gender,
        id_number: formData.id_number,
        phone: formData.phone,
        emergency_contact_name: formData.emergency_contact_name,
        emergency_contact_phone: formData.emergency_contact_phone,
        school: formData.school,
        department: formData.department,
        major: formData.major,
        grade: formData.grade,
        class_name: formData.class_name,
      }

      // 调用真实API
      return await studentRegistration.register(requestData)
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

  const handleSubmit = (values: StudentRegistrationForm): void => {
    // 基础信息验证
    if (currentStep === 'basic') {
      const basicFields = ['username', 'password', 'confirmPassword', 'email']
      const hasBasicErrors = basicFields.some(field => form.validateField(field).hasError)
      if (!hasBasicErrors) {
        setCurrentStep('profile')
      }
      return
    }

    // 个人信息验证
    if (currentStep === 'profile') {
      const profileFields = ['real_name', 'age', 'id_number', 'phone']
      const hasProfileErrors = profileFields.some(field => form.validateField(field).hasError)
      if (!hasProfileErrors) {
        setCurrentStep('phone')
      }
      return
    }

    // 手机验证步骤 - 由PhoneVerification组件处理，这里不需要额外逻辑
    if (currentStep === 'phone') {
      // 手机验证由组件内部处理，验证成功后会自动跳转到academic步骤
      return
    }

    // 学术信息验证和最终提交
    if (currentStep === 'academic') {
      if (!form.validate().hasErrors && isPhoneVerified) {
        // 使用验证过的手机号
        const submitData = {
          ...values,
          phone: verifiedPhone || values.phone,
        }
        registrationMutation.mutate(submitData)
      } else if (!isPhoneVerified) {
        notifications.show({
          title: '提交失败',
          message: '请先完成手机号验证',
          color: 'red',
        })
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
          placeholder="请输入用户名（字母、数字、下划线）"
          required
          {...form.getInputProps('username')}
        />

        <TextInput
          label="密码"
          type="password"
          placeholder="请输入密码（至少6位）"
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
            • 学生注册需要提供真实信息并等待管理员审核
            <br />
            • 审核通过后才能登录使用学习功能
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
          <Title order={3}>个人基础信息</Title>
          <Text size="sm" c="dimmed">
            （需求1：11项基础信息中的个人部分）
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

        <TextInput
          label="身份证号"
          placeholder="请输入身份证号码"
          {...form.getInputProps('id_number')}
        />

        <TextInput label="联系电话" placeholder="请输入手机号码" {...form.getInputProps('phone')} />

        <Group grow>
          <TextInput
            label="紧急联系人姓名"
            placeholder="请输入紧急联系人姓名"
            {...form.getInputProps('emergency_contact_name')}
          />
          <TextInput
            label="紧急联系人电话"
            placeholder="请输入紧急联系人电话"
            {...form.getInputProps('emergency_contact_phone')}
          />
        </Group>
      </Stack>
    </Paper>
  )

  const renderPhoneVerificationStep = () => (
    <PhoneVerification
      onVerificationSuccess={(phoneNumber) => {
        setIsPhoneVerified(true)
        setVerifiedPhone(phoneNumber)
        // 自动跳转到下一步
        setCurrentStep('academic')
      }}
      onVerificationError={(_error) => {
        // 错误已在PhoneVerification组件中处理
      }}
      purpose="register"
      disabled={registrationMutation.isPending}
    />
  )

  const renderAcademicStep = () => (
    <Paper withBorder shadow="md" p="xl" radius="md">
      <Stack>
        <Group>
          <IconSchool size={24} />
          <Title order={3}>学术信息</Title>
          <Text size="sm" c="dimmed">
            （需求1：11项基础信息中的学术部分）
          </Text>
        </Group>

        <TextInput label="学校" placeholder="请输入学校名称" {...form.getInputProps('school')} />

        <Group grow>
          <TextInput
            label="院系"
            placeholder="请输入院系名称"
            {...form.getInputProps('department')}
          />
          <TextInput label="专业" placeholder="请输入专业名称" {...form.getInputProps('major')} />
        </Group>

        <Group grow>
          <TextInput label="年级" placeholder="如：大一、大二等" {...form.getInputProps('grade')} />
          <TextInput
            label="班级"
            placeholder="请输入班级名称"
            {...form.getInputProps('class_name')}
          />
        </Group>

        <Alert icon={<IconInfoCircle size="1rem" />} title="温馨提示" color="orange">
          <Text size="sm">
            学术信息有助于系统为您推荐合适的学习内容和班级。
            请尽量填写完整，如有变动可在审核通过后联系管理员修改。
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
      case 'phone':
        return renderPhoneVerificationStep()
      case 'academic':
        return renderAcademicStep()
      default:
        return null
    }
  }

  return (
    <Container size="md" py="xl">
      <Title ta="center" mb="xl">
        学生注册申请
      </Title>

      {/* 步骤指示器 */}
      <Group justify="center" mb="xl">
        <SegmentedControl
          value={currentStep}
          data={[
            { label: '基本信息', value: 'basic' },
            { label: '个人信息', value: 'profile' },
            { label: '手机验证', value: 'phone' },
            { label: '学术信息', value: 'academic' },
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
              else if (currentStep === 'phone') setCurrentStep('profile')
              else if (currentStep === 'academic') setCurrentStep('phone')
            }}
            disabled={currentStep === 'basic' || registrationMutation.isPending}
          >
            上一步
          </Button>

          <Button
            type="submit"
            loading={registrationMutation.isPending}
            disabled={registrationMutation.isPending || (currentStep === 'phone' && !isPhoneVerified)}
          >
            {currentStep === 'academic'
              ? '提交注册申请'
              : currentStep === 'phone'
                ? '下一步：填写学术信息'
                : currentStep === 'profile'
                  ? '下一步：手机验证'
                  : '下一步：填写个人信息'}
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
