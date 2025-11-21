import { useState, useEffect } from 'react'
import { LogOut, Plus, RefreshCw } from 'lucide-react'
import { getProgramsStatus } from '../lib/api'
import ProgramCard from '../components/ProgramCard'
import AddProgramModal from '../components/AddProgramModal'

export default function DashboardPage({ user, onLogout }) {
  const [programs, setPrograms] = useState([])
  const [loading, setLoading] = useState(true)
  const [isAddModalOpen, setIsAddModalOpen] = useState(false)
  const [refreshing, setRefreshing] = useState(false)

  // 프로그램 상태 조회
  const fetchPrograms = async () => {
    try {
      const data = await getProgramsStatus()
      setPrograms(data.programs_status || [])
    } catch (error) {
      console.error('프로그램 상태 조회 실패:', error)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  // 초기 로드
  useEffect(() => {
    fetchPrograms()
  }, [])

  // 5초마다 자동 새로고침
  useEffect(() => {
    const interval = setInterval(() => {
      fetchPrograms()
    }, 5000)

    return () => clearInterval(interval)
  }, [])

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
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">로딩 중...</p>
        </div>
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

        {/* 프로그램 추가 버튼 */}
        <div className="mb-6">
          <button
            onClick={() => setIsAddModalOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
          >
            <Plus className="w-5 h-5" />
            프로그램 추가
          </button>
        </div>

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
