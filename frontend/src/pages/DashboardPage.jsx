import { useState, useEffect, useCallback, useMemo } from 'react'
import { LogOut, Plus, RefreshCw, Wifi, WifiOff } from 'lucide-react'
import { getProgramsStatus } from '../lib/api'
import ProgramCard from '../components/ProgramCard'
import AddProgramModal from '../components/AddProgramModal'
import LoadingSkeleton from '../components/LoadingSkeleton'
import { useProgramStatus, useNotification } from '../hooks/useWebSocket'
import { throttle } from '../utils/debounce'

export default function DashboardPage({ user, onLogout }) {
  const [programs, setPrograms] = useState([])
  const [loading, setLoading] = useState(true)
  const [isAddModalOpen, setIsAddModalOpen] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const isAdmin = user?.role === 'admin'

  // 프로그램 상태 조회 (쓰로틀 적용)
  const fetchPrograms = useCallback(async () => {
    try {
      const data = await getProgramsStatus()
      setPrograms(data.programs_status || [])
    } catch (error) {
      console.error('프로그램 상태 조회 실패:', error)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  // 쓰로틀된 fetchPrograms
  const throttledFetchPrograms = useMemo(
    () => throttle(fetchPrograms, 1000),
    [fetchPrograms]
  )

  // 웹소켓 프로그램 상태 업데이트 핸들러
  const handleProgramStatusChange = useCallback((data) => {
    console.log('🔄 [WebSocket] 프로그램 상태 업데이트:', data)
    const { program_id, data: statusData } = data
    
    setPrograms(prevPrograms => 
      prevPrograms.map(program => 
        program.id === program_id
          ? { ...program, ...statusData }
          : program
      )
    )
  }, [])

  // 웹소켓 알림 핸들러
  const handleNotification = useCallback((data) => {
    console.log('알림:', data)
    // 필요시 토스트 알림 표시
  }, [])

  // 웹소켓 연결
  const { isConnected } = useProgramStatus(handleProgramStatusChange)
  useNotification(handleNotification)

  // 초기 로드
  useEffect(() => {
    fetchPrograms()
  }, [])

  // 웹소켓이 연결되지 않은 경우에만 폴링
  useEffect(() => {
    if (!isConnected) {
      const interval = setInterval(() => {
        fetchPrograms()
      }, 5000)

      return () => clearInterval(interval)
    }
  }, [isConnected])

  // 수동 새로고침
  const handleRefresh = () => {
    setRefreshing(true)
    fetchPrograms()
  }

  // 통계 계산
  const stats = {
    total: programs.length,
    running: programs.filter(p => p.running).length,
    stopped: programs.filter(p => !p.running).length,
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow-sm border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  프로그램 모니터링 시스템
                </h1>
                <p className="text-sm text-gray-600 mt-1">
                  {user?.username || 'Guest'} 님, 환영합니다
                </p>
              </div>
            </div>
          </div>
        </header>
        
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <LoadingSkeleton />
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 헤더 */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                프로그램 모니터링 시스템
              </h1>
              <p className="text-sm text-gray-600 mt-1">
                {user?.username || 'Guest'} 님, 환영합니다
              </p>
            </div>
            <div className="flex items-center gap-3">
              {/* 웹소켓 연결 상태 */}
              <div className={`inline-flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium ${
                isConnected 
                  ? 'bg-green-100 text-green-700' 
                  : 'bg-gray-100 text-gray-600'
              }`}>
                {isConnected ? (
                  <>
                    <Wifi className="w-4 h-4" />
                    실시간 연결
                  </>
                ) : (
                  <>
                    <WifiOff className="w-4 h-4" />
                    폴링 모드
                  </>
                )}
              </div>
              
              <button
                onClick={handleRefresh}
                disabled={refreshing}
                className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
                새로고침
              </button>
              <button
                onClick={onLogout}
                className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors"
              >
                <LogOut className="w-4 h-4" />
                로그아웃
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* 메인 컨텐츠 */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 통계 카드 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">전체 프로그램</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{stats.total}</p>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="text-2xl">📊</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">실행 중</p>
                <p className="text-3xl font-bold text-green-600 mt-2">{stats.running}</p>
              </div>
              <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                <span className="text-2xl">✅</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">중지됨</p>
                <p className="text-3xl font-bold text-red-600 mt-2">{stats.stopped}</p>
              </div>
              <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
                <span className="text-2xl">⏹️</span>
              </div>
            </div>
          </div>
        </div>

        {/* 프로그램 추가 버튼 (관리자만) */}
        {isAdmin && (
          <div className="mb-6">
            <button
              onClick={() => setIsAddModalOpen(true)}
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
            >
              <Plus className="w-5 h-5" />
              프로그램 추가
            </button>
          </div>
        )}

        {/* 프로그램 목록 */}
        {programs.length === 0 ? (
          <div className="bg-white rounded-lg shadow-sm p-12 text-center border border-gray-200">
            <p className="text-gray-500 text-lg">등록된 프로그램이 없습니다.</p>
            <p className="text-gray-400 text-sm mt-2">프로그램 추가 버튼을 클릭하여 시작하세요.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {programs.map((program) => (
              <ProgramCard
                key={program.id}
                program={program}
                onUpdate={fetchPrograms}
                user={user}
              />
            ))}
          </div>
        )}
      </main>

      {/* 프로그램 추가 모달 */}
      {isAddModalOpen && (
        <AddProgramModal
          onClose={() => setIsAddModalOpen(false)}
          onSuccess={() => {
            setIsAddModalOpen(false)
            fetchPrograms()
          }}
        />
      )}
    </div>
  )
}
