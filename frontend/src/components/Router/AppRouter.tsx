/**
 * 应用路由器组件 - 管理所有页面路由
 */
import { Routes, Route, Navigate } from 'react-router-dom'

import { useAuthStore } from '@/stores/authStore'
import { HomePage } from '@/pages/Home/HomePage'
import { LoginPage } from '@/pages/Auth/LoginPage'
import { StudentRegistrationPage } from '@/pages/Auth/StudentRegistrationPage'
import { RegistrationStatusPage } from '@/pages/Auth/RegistrationStatusPage'
import { ActivationPage } from '@/pages/Auth/ActivationPage'

// 管理员页面
import { AdminUsersPage } from '@/pages/Admin/AdminUsersPage'
import { AdminCoursesPage } from '@/pages/Admin/AdminCoursesPage'
import { RegistrationReviewPage } from '@/pages/Admin/RegistrationReviewPage'
import { StudentManagementPage } from '@/pages/Admin/StudentManagementPage'
import { TeacherManagementPage } from '@/pages/Admin/TeacherManagementPage'
import { ClassroomManagementPage } from '@/pages/Admin/ClassroomManagementPage'
import { AuditLogPage } from '@/pages/Admin/AuditLogPage'
import { PermissionManagementPage } from '@/pages/Admin/PermissionManagementPage'
import { BackupManagementPage } from '@/pages/Admin/BackupManagementPage'
import { RuleManagementPage } from '@/pages/Admin/RuleManagementPage'
import { MFAManagementPage } from '@/pages/Admin/MFAManagementPage'
import { TeacherRegistrationPage } from '@/pages/Auth/TeacherRegistrationPage'
import { TeacherQualificationPage } from '@/pages/Teacher/TeacherQualificationPage'

// 教师页面
import { TeacherDashboard } from '@/pages/Teacher/TeacherDashboard'
import { TeacherCoursesPage } from '@/pages/Teacher/TeacherCoursesPage'
import { TeacherResourcesPage } from '@/pages/Teacher/TeacherResourcesPage'
import { HotTopicsPage } from '@/pages/Teacher/HotTopicsPage'
import { LessonPlanPage } from '@/pages/Teacher/LessonPlanPage'
import { SchedulePage } from '@/pages/Teacher/SchedulePage'
import { LearningAnalyticsPage } from '@/pages/Teacher/LearningAnalyticsPage'
import { TeachingAdjustmentsPage } from '@/pages/Teacher/TeachingAdjustmentsPage'
import { SyllabusGeneratorPage } from '@/pages/Teacher/SyllabusGeneratorPage'
import { TrainingWorkshopPage } from '@/pages/Teacher/TrainingWorkshopPage'
import { ProfessionalDevelopmentPage } from '@/pages/Teacher/ProfessionalDevelopmentPage'

// 学生页面
import { StudentTrainingPage } from '@/pages/Student/StudentTrainingPage'
import { StudentProgressPage } from '@/pages/Student/StudentProgressPage'

// 路由守卫组件
function ProtectedRoute({
  children,
  allowedRoles,
}: {
  children: React.ReactNode
  allowedRoles?: string[]
}) {
  const { user, isAuthenticated } = useAuthStore()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (allowedRoles && user && !allowedRoles.includes(user.userType)) {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}

export function AppRouter(): JSX.Element {
  const { isAuthenticated } = useAuthStore()

  return (
    <Routes>
      {/* 公开路由 */}
      <Route
        path="/login"
        element={isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />}
      />

      {/* 注册相关路由（公开访问） */}
      <Route
        path="/register/student"
        element={isAuthenticated ? <Navigate to="/" replace /> : <StudentRegistrationPage />}
      />
      <Route
        path="/register/teacher"
        element={isAuthenticated ? <Navigate to="/" replace /> : <TeacherRegistrationPage />}
      />

      {/* 注册状态查询（公开访问，无需登录） */}
      <Route path="/registration/status" element={<RegistrationStatusPage />} />
      <Route path="/registration/status/:applicationId" element={<RegistrationStatusPage />} />

      {/* 用户激活路由（公开访问，无需登录） - 🔥需求20验收标准5 */}
      <Route path="/activate/:token" element={<ActivationPage />} />

      {/* 首页（公开访问） */}
      <Route path="/" element={<HomePage />} />

      {/* 管理员路由 */}
      <Route
        path="/admin/users"
        element={
          <ProtectedRoute allowedRoles={['admin']}>
            <AdminUsersPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/courses"
        element={
          <ProtectedRoute allowedRoles={['admin']}>
            <AdminCoursesPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/registration-review"
        element={
          <ProtectedRoute allowedRoles={['admin']}>
            <RegistrationReviewPage />
          </ProtectedRoute>
        }
      />

      {/* 需求3：权限与角色管理路由 */}
      <Route
        path="/admin/permissions"
        element={
          <ProtectedRoute allowedRoles={['admin']}>
            <PermissionManagementPage />
          </ProtectedRoute>
        }
      />

      {/* 需求4：多因素认证管理路由 */}
      <Route
        path="/admin/mfa"
        element={
          <ProtectedRoute allowedRoles={['admin']}>
            <MFAManagementPage />
          </ProtectedRoute>
        }
      />

      {/* 需求5：审计日志管理路由 */}
      <Route
        path="/admin/audit-logs"
        element={
          <ProtectedRoute allowedRoles={['admin']}>
            <AuditLogPage />
          </ProtectedRoute>
        }
      />

      {/* 需求8：规则管理路由 */}
      <Route
        path="/admin/rules"
        element={
          <ProtectedRoute allowedRoles={['admin']}>
            <RuleManagementPage />
          </ProtectedRoute>
        }
      />

      {/* 需求9：数据备份与恢复管理路由 */}
      <Route
        path="/admin/backup"
        element={
          <ProtectedRoute allowedRoles={['admin']}>
            <BackupManagementPage />
          </ProtectedRoute>
        }
      />

      {/* 需求2：基础信息管理路由 */}
      <Route
        path="/admin/students"
        element={
          <ProtectedRoute allowedRoles={['admin']}>
            <StudentManagementPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/teachers"
        element={
          <ProtectedRoute allowedRoles={['admin']}>
            <TeacherManagementPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/classrooms"
        element={
          <ProtectedRoute allowedRoles={['admin']}>
            <ClassroomManagementPage />
          </ProtectedRoute>
        }
      />

      {/* 教师路由 */}
      <Route
        path="/teacher/dashboard"
        element={
          <ProtectedRoute allowedRoles={['teacher']}>
            <TeacherDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/teacher/courses"
        element={
          <ProtectedRoute allowedRoles={['teacher']}>
            <TeacherCoursesPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/teacher/analytics"
        element={
          <ProtectedRoute allowedRoles={['teacher']}>
            <LearningAnalyticsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/teacher/adjustments"
        element={
          <ProtectedRoute allowedRoles={['teacher']}>
            <TeachingAdjustmentsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/teacher/syllabus"
        element={
          <ProtectedRoute allowedRoles={['teacher']}>
            <SyllabusGeneratorPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/teacher/resources"
        element={
          <ProtectedRoute allowedRoles={['teacher']}>
            <TeacherResourcesPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/teacher/hot-topics"
        element={
          <ProtectedRoute allowedRoles={['teacher']}>
            <HotTopicsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/teacher/lesson-plans"
        element={
          <ProtectedRoute allowedRoles={['teacher']}>
            <LessonPlanPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/teacher/schedule"
        element={
          <ProtectedRoute allowedRoles={['teacher']}>
            <SchedulePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/teacher/qualification"
        element={
          <ProtectedRoute allowedRoles={['teacher']}>
            <TeacherQualificationPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/teacher/training-workshop"
        element={
          <ProtectedRoute allowedRoles={['teacher']}>
            <TrainingWorkshopPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/teacher/professional-development"
        element={
          <ProtectedRoute allowedRoles={['teacher']}>
            <ProfessionalDevelopmentPage />
          </ProtectedRoute>
        }
      />

      {/* 学生路由 */}
      <Route
        path="/student/training"
        element={
          <ProtectedRoute allowedRoles={['student']}>
            <StudentTrainingPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/student/progress"
        element={
          <ProtectedRoute allowedRoles={['student']}>
            <StudentProgressPage />
          </ProtectedRoute>
        }
      />

      {/* 404页面 */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
