/**
 * 权限控制工具函数 - 需求15任务3.3实现
 */

// 用户类型枚举
export enum UserType {
  ADMIN = 'admin',
  TEACHER = 'teacher',
  STUDENT = 'student',
}

// 权限代码枚举
export enum Permission {
  // 训练工坊权限
  TRAINING_WORKSHOP_TEMPLATE_CREATE = 'training_workshop_template_create',
  TRAINING_WORKSHOP_TEMPLATE_READ = 'training_workshop_template_read',
  TRAINING_WORKSHOP_TEMPLATE_UPDATE = 'training_workshop_template_update',
  TRAINING_WORKSHOP_TEMPLATE_DELETE = 'training_workshop_template_delete',

  TRAINING_WORKSHOP_TASK_CREATE = 'training_workshop_task_create',
  TRAINING_WORKSHOP_TASK_READ = 'training_workshop_task_read',
  TRAINING_WORKSHOP_TASK_UPDATE = 'training_workshop_task_update',
  TRAINING_WORKSHOP_TASK_DELETE = 'training_workshop_task_delete',

  TRAINING_WORKSHOP_ANALYTICS_VIEW = 'training_workshop_analytics_view',
  TRAINING_WORKSHOP_ANALYTICS_EXPORT = 'training_workshop_analytics_export',

  TRAINING_WORKSHOP_SUBMISSION_CREATE = 'training_workshop_submission_create',
  TRAINING_WORKSHOP_SUBMISSION_READ = 'training_workshop_submission_read',
}

// 用户信息接口
export interface User {
  id: number
  username: string
  userType: UserType
  permissions?: string[]
  roles?: string[]
}

// 权限检查函数
export class PermissionChecker {
  /**
   * 检查用户是否有指定权限
   */
  static hasPermission(user: User | null, permission: Permission): boolean {
    if (!user) return false

    // 管理员拥有所有权限
    if (user.userType === UserType.ADMIN) {
      return true
    }

    // 检查用户权限列表
    if (user.permissions?.includes(permission)) {
      return true
    }

    // 基于用户类型的默认权限
    return this.hasDefaultPermission(user.userType, permission)
  }

  /**
   * 检查用户是否有教师权限
   */
  static hasTeacherPermission(user: User | null): boolean {
    if (!user) return false
    return user.userType === UserType.TEACHER || user.userType === UserType.ADMIN
  }

  /**
   * 检查用户是否有学生权限
   */
  static hasStudentPermission(user: User | null): boolean {
    if (!user) return false
    return user.userType === UserType.STUDENT || user.userType === UserType.ADMIN
  }

  /**
   * 检查用户是否有管理员权限
   */
  static hasAdminPermission(user: User | null): boolean {
    if (!user) return false
    return user.userType === UserType.ADMIN
  }

  /**
   * 检查用户是否可以访问指定班级的数据
   */
  static canAccessClassData(user: User | null, _classId: number): boolean {
    if (!user) return false

    // 管理员可以访问所有班级数据
    if (user.userType === UserType.ADMIN) {
      return true
    }

    // 教师只能访问自己的班级数据
    if (user.userType === UserType.TEACHER) {
      // TODO: 这里应该检查教师是否被分配到该班级
      // 目前简化为允许所有教师访问
      // 未来实现: return user.assignedClasses?.includes(classId) ?? false
      return true
    }

    return false
  }

  /**
   * 检查用户是否可以操作指定的模板
   */
  static canOperateTemplate(user: User | null, templateCreatorId: number): boolean {
    if (!user) return false

    // 管理员可以操作所有模板
    if (user.userType === UserType.ADMIN) {
      return true
    }

    // 用户只能操作自己创建的模板
    return user.id === templateCreatorId
  }

  /**
   * 基于用户类型的默认权限检查
   */
  private static hasDefaultPermission(userType: UserType, permission: Permission): boolean {
    const teacherPermissions = [
      Permission.TRAINING_WORKSHOP_TEMPLATE_CREATE,
      Permission.TRAINING_WORKSHOP_TEMPLATE_READ,
      Permission.TRAINING_WORKSHOP_TEMPLATE_UPDATE,
      Permission.TRAINING_WORKSHOP_TEMPLATE_DELETE,
      Permission.TRAINING_WORKSHOP_TASK_CREATE,
      Permission.TRAINING_WORKSHOP_TASK_READ,
      Permission.TRAINING_WORKSHOP_TASK_UPDATE,
      Permission.TRAINING_WORKSHOP_TASK_DELETE,
      Permission.TRAINING_WORKSHOP_ANALYTICS_VIEW,
      Permission.TRAINING_WORKSHOP_ANALYTICS_EXPORT,
      Permission.TRAINING_WORKSHOP_SUBMISSION_READ,
    ]

    const studentPermissions = [
      Permission.TRAINING_WORKSHOP_SUBMISSION_CREATE,
      Permission.TRAINING_WORKSHOP_SUBMISSION_READ,
    ]

    switch (userType) {
      case UserType.ADMIN:
        return true // 管理员拥有所有权限
      case UserType.TEACHER:
        return teacherPermissions.includes(permission)
      case UserType.STUDENT:
        return studentPermissions.includes(permission)
      default:
        return false
    }
  }
}

// 权限检查装饰器函数
export function requirePermission(permission: Permission) {
  return function (_target: any, _propertyKey: string, descriptor: PropertyDescriptor) {
    const originalMethod = descriptor.value

    descriptor.value = function (...args: any[]) {
      // 这里应该从认证上下文获取当前用户
      const currentUser = getCurrentUser() // TODO: 实现获取当前用户的函数

      if (!PermissionChecker.hasPermission(currentUser, permission)) {
        throw new Error(`权限不足: 需要权限 ${permission}`)
      }

      return originalMethod.apply(this, args)
    }

    return descriptor
  }
}

// 获取当前用户的函数 - 需要根据实际的认证系统实现
function getCurrentUser(): User | null {
  // TODO: 从localStorage、sessionStorage或认证上下文获取用户信息
  // 这里返回一个模拟的用户对象
  return {
    id: 1,
    username: 'teacher001',
    userType: UserType.TEACHER,
    permissions: [],
    roles: ['teacher'],
  }
}

// 导出工具函数
export { getCurrentUser }

// React Hook for permission checking
export function usePermissions() {
  const currentUser = getCurrentUser()

  return {
    user: currentUser,
    hasPermission: (permission: Permission) =>
      PermissionChecker.hasPermission(currentUser, permission),
    hasTeacherPermission: () => PermissionChecker.hasTeacherPermission(currentUser),
    hasStudentPermission: () => PermissionChecker.hasStudentPermission(currentUser),
    hasAdminPermission: () => PermissionChecker.hasAdminPermission(currentUser),
    canAccessClassData: (classId: number) =>
      PermissionChecker.canAccessClassData(currentUser, classId),
    canOperateTemplate: (templateCreatorId: number) =>
      PermissionChecker.canOperateTemplate(currentUser, templateCreatorId),
  }
}
