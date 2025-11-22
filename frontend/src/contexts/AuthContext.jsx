/**
 * 인증 Context Provider
 * 
 * 사용자 인증 상태를 전역으로 관리합니다.
 * Props drilling을 방지하고 어디서든 사용자 정보에 접근할 수 있습니다.
 */

import { useState, useEffect } from 'react'
import { checkSession } from '../lib/api'
import { AuthContext } from './AuthContextValue'

// AuthProvider 컴포넌트
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // 세션 확인
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const data = await checkSession()
        if (data.logged_in) {
          setUser({
            username: data.username,
            role: data.role
          })
        }
      } catch (error) {
        console.error('세션 확인 실패:', error)
      } finally {
        setLoading(false)
      }
    }

    checkAuth()
  }, [])

  const login = (userData) => {
    setUser(userData)
  }

  const logout = () => {
    setUser(null)
  }

  const value = {
    user,
    loading,
    login,
    logout,
    isAuthenticated: !!user,
    isAdmin: user?.role === 'admin'
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

