export interface LoginForm {
  username: string
  password: string
  userType: 'student' | 'teacher' | 'admin'
  agreedToPolicy: boolean
}

export interface LoginTimeValidation {
  isValid: boolean
  message?: string
}

export interface User {
  id: string
  username: string
  userType: 'student' | 'teacher' | 'admin'
  lastLogin: string
  permissions?: string[]
  profile?: Record<string, unknown>
}

export interface LoginResponse {
  success: boolean
  user: User
  token: string
  expiresIn?: number
}
