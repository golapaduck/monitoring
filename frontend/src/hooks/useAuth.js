/**
 * useAuth 훅
 * 
 * AuthContext를 사용하기 위한 커스텀 훅
 */

import { useContext } from 'react'
import { AuthContext } from '../contexts/AuthContextValue'

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
