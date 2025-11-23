import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import ProgramDetail from './pages/ProgramDetail'

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // 세션 확인
  useEffect(() => {
    checkSession()
  }, [])

  const checkSession = async () => {
    try {
      // 세션 확인 전용 API 호출
      const response = await fetch('/api/session', {
        credentials: 'include'
      })
      
      if (response.ok) {
        const data = await response.json()
        
        // logged_in이 true인 경우에만 인증 처리
        if (data.logged_in && data.username) {
          setIsAuthenticated(true)
          setUser({
            username: data.username,
            role: data.role || 'admin'  // role 없으면 admin으로 기본값
          })
          console.log('✅ 세션 확인 성공:', data.username, data.role || 'admin')
        } else {
          // 세션은 있지만 로그인 정보가 없는 경우
          setIsAuthenticated(false)
          setUser(null)
          console.log('⚠️ 세션 정보 불완전')
        }
      } else {
        // 세션 없음
        setIsAuthenticated(false)
        setUser(null)
        console.log('❌ 세션 없음')
      }
    } catch (error) {
      console.error('세션 확인 실패:', error)
      setIsAuthenticated(false)
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  const handleLogin = (userData) => {
    setIsAuthenticated(true)
    setUser(userData)
  }

  const handleLogout = async () => {
    try {
      await fetch('/logout', {
        method: 'GET',
        credentials: 'include'
      })
      setIsAuthenticated(false)
      setUser(null)
    } catch (error) {
      console.error('로그아웃 실패:', error)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">로딩 중...</p>
        </div>
      </div>
    )
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route 
          path="/login" 
          element={
            isAuthenticated ? 
            <Navigate to="/dashboard" replace /> : 
            <LoginPage onLogin={handleLogin} />
          } 
        />
        <Route 
          path="/dashboard" 
          element={
            isAuthenticated ? 
            <DashboardPage user={user} onLogout={handleLogout} /> : 
            <Navigate to="/login" replace />
          } 
        />
        <Route 
          path="/program/:id" 
          element={
            isAuthenticated ? 
            <ProgramDetail user={user} onLogout={handleLogout} /> : 
            <Navigate to="/login" replace />
          } 
        />
        <Route 
          path="/" 
          element={<Navigate to={isAuthenticated ? "/dashboard" : "/login"} replace />} 
        />
      </Routes>
    </BrowserRouter>
  )
}

export default App
