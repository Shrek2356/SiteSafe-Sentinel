/**
 * 登录 / 用户信息接口
 */
import { USE_MOCK, mockDelay } from '@/utils/request'
import request from '@/utils/request'

/**
 * 登录
 * @param {{ username: string, password: string, role?: string }} data
 * @returns {Promise<{code:number,data:{token:string,user:object}}>}
 *
 * Mock 账号（密码任意）：
 *   admin / safety / director
 */
export function login(data) {
  if (USE_MOCK) {
    const role = data.role || data.username || 'admin'
    const nameMap = { admin: '系统管理员', safety: '张安全', director: '赵总监' }
    return mockDelay({
      token: 'mock-token-' + role,
      user: {
        id: 'u-' + role,
        username: data.username,
        name: nameMap[role] || data.username,
        role,
      },
    })
  }
  const username = { admin: 'admin', safety: 'safety', director: 'director' }[data.role] || data.username
  const defaultPasswords = { admin: 'admin123', safety: 'safety123', director: 'viewer123' }
  return request.post('/auth/login', {
    ...data,
    username,
    password: data.password === 'admin123' ? defaultPasswords[data.role] || data.password : data.password,
  })
}

/**
 * 获取当前用户信息
 */
export function fetchProfile() {
  if (USE_MOCK) {
    const raw = localStorage.getItem('znt_user')
    return mockDelay(raw ? JSON.parse(raw) : null)
  }
  return request.get('/whoami')
}
