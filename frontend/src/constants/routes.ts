// 路由常量定义
export const ROUTES = {
  // 公共路由
  HOME: '/',
  LOGIN: '/login',

  // 注册路由
  REGISTER_STUDENT: '/register/student',
  REGISTER_TEACHER: '/register/teacher',
  REGISTRATION_STATUS: '/registration/status',
  REGISTRATION_STATUS_WITH_ID: '/registration/status/:applicationId',

  // 学生路由
  STUDENT: {
    DASHBOARD: '/student/dashboard',
    TRAINING: '/student/training',
    PROGRESS: '/student/progress',
    PROFILE: '/student/profile',
  },

  // 教师路由
  TEACHER: {
    DASHBOARD: '/teacher/dashboard',
    COURSES: '/teacher/courses',
    ANALYTICS: '/teacher/analytics',
    ADJUSTMENTS: '/teacher/adjustments',
    SYLLABUS: '/teacher/syllabus',
    RESOURCES: '/teacher/resources',
    HOT_TOPICS: '/teacher/hot-topics',
    LESSON_PLANS: '/teacher/lesson-plans',
    SCHEDULE: '/teacher/schedule',
    TRAINING_WORKSHOP: '/teacher/training-workshop',
    PROFESSIONAL_DEVELOPMENT: '/teacher/professional-development',
    QUALIFICATION: '/teacher/qualification',
    PROFILE: '/teacher/profile',
  },

  // 管理员路由
  ADMIN: {
    DASHBOARD: '/admin/dashboard',
    USERS: '/admin/users',
    COURSES: '/admin/courses',
    REGISTRATION_REVIEW: '/admin/registration-review',

    // 需求2：基础信息管理
    STUDENTS: '/admin/students',
    TEACHERS: '/admin/teachers',
    CLASSROOMS: '/admin/classrooms',

    SYSTEM: '/admin/system',
    PROFILE: '/admin/profile',
  },
} as const

// 路由权限映射
export const ROUTE_PERMISSIONS = {
  [ROUTES.STUDENT.DASHBOARD]: 'student',
  [ROUTES.STUDENT.TRAINING]: 'student',
  [ROUTES.STUDENT.PROGRESS]: 'student',
  [ROUTES.STUDENT.PROFILE]: 'student',

  [ROUTES.TEACHER.DASHBOARD]: 'teacher',
  [ROUTES.TEACHER.COURSES]: 'teacher',
  [ROUTES.TEACHER.ANALYTICS]: 'teacher',
  [ROUTES.TEACHER.ADJUSTMENTS]: 'teacher',
  [ROUTES.TEACHER.SYLLABUS]: 'teacher',
  [ROUTES.TEACHER.RESOURCES]: 'teacher',
  [ROUTES.TEACHER.TRAINING_WORKSHOP]: 'teacher',
  [ROUTES.TEACHER.QUALIFICATION]: 'teacher',
  [ROUTES.TEACHER.PROFILE]: 'teacher',

  [ROUTES.ADMIN.DASHBOARD]: 'admin',
  [ROUTES.ADMIN.USERS]: 'admin',
  [ROUTES.ADMIN.COURSES]: 'admin',
  [ROUTES.ADMIN.REGISTRATION_REVIEW]: 'admin',

  // 需求2：基础信息管理权限
  [ROUTES.ADMIN.STUDENTS]: 'admin',
  [ROUTES.ADMIN.TEACHERS]: 'admin',
  [ROUTES.ADMIN.CLASSROOMS]: 'admin',

  [ROUTES.ADMIN.SYSTEM]: 'admin',
  [ROUTES.ADMIN.PROFILE]: 'admin',
} as const
