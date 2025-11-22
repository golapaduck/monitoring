import { useState, useEffect, useCallback, useMemo, lazy, Suspense } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Play, Square, Trash2, Edit } from 'lucide-react'
import axios from 'axios'
import { startProgram, stopProgram, deleteProgram } from '../lib/api'
import EditProgramModal from '../components/EditProgramModal'
import TabNavigation from '../components/TabNavigation'

// Lazy loading으로 성능 최적화
const ResourceChart = lazy(() => import('../components/ResourceChart'))
const PluginTab = lazy(() => import('../components/PluginTab'))
const PalworldControl = lazy(() => import('../components/PalworldControl'))

export default function ProgramDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [program, setProgram] = useState(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [activeTab, setActiveTab] = useState('overview')

  // 탭 데이터 메모이제이션
  const tabs = useMemo(() => [
    { id: 'overview', label: '개요' },
    { id: 'metrics', label: '리소스 모니터링' },
    { id: 'control', label: '조작' },
    { id: 'plugins', label: '플러그인' }
  ], [])

  const loadProgram = useCallback(async () => {
    try {
      // 1단계: 프로그램 기본 정보 조회 (/api/programs)
      const programsResponse = await axios.get(`/api/programs`)
      const programs = programsResponse.data.programs || programsResponse.data
      const foundProgram = programs.find(p => p.id === parseInt(id))
      
      if (!foundProgram) {
        console.warn(`프로그램을 찾을 수 없습니다 (ID: ${id})`)
        setTimeout(() => navigate('/dashboard'), 2000)
        setLoading(false)
        return
      }
      
      // 2단계: 실시간 상태 정보 조회 (/api/status)
      try {
        const statusResponse = await axios.get(`/api/status`)
        const statusList = statusResponse.data.programs_status || []
        const programStatus = statusList.find(p => p.id === parseInt(id))
        
        if (programStatus) {
          // 기본 정보 + 실시간 상태 병합
          setProgram({
            ...foundProgram,
            running: programStatus.running,
            pid: programStatus.pid,
            cpu_percent: programStatus.cpu_percent,
            memory_mb: programStatus.memory_mb
          })
        } else {
          // 상태 정보가 없으면 기본 정보만 사용
          setProgram(foundProgram)
        }
      } catch (statusError) {
        console.warn('상태 정보 조회 실패, 기본 정보만 사용:', statusError)
        setProgram(foundProgram)
      }
    } catch (error) {
      console.error('프로그램 로드 실패:', error)
    } finally {
      setLoading(false)
    }
  }, [id, navigate])

  useEffect(() => {
    loadProgram()
    // 상세 페이지에서는 더 자주 상태 확인 (2초 간격)
    const interval = setInterval(loadProgram, 2000)
    return () => clearInterval(interval)
  }, [loadProgram])

  const handleToggle = useCallback(async () => {
    if (!program) return
    setActionLoading(true)
    try {
      if (program.running) {
        await stopProgram(program.id, false)
      } else {
        await startProgram(program.id)
      }
      // 액션 후 즉시 상태 갱신 (500ms 대기 후)
      setTimeout(() => loadProgram(), 500)
    } catch (error) {
      alert(`작업 실패: ${error.message}`)
    } finally {
      setActionLoading(false)
    }
  }, [program, loadProgram])

  const handleDelete = useCallback(async () => {
    if (!program) return
    if (!confirm('이 프로그램을 삭제하시겠습니까?')) return

    setActionLoading(true)
    try {
      await deleteProgram(program.id)
      navigate('/dashboard')
    } catch (error) {
      alert(`삭제 실패: ${error.message}`)
    } finally {
      setActionLoading(false)
    }
  }, [program, navigate])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-500">로딩 중...</div>
      </div>
    )
  }

  if (!program) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-xl font-semibold text-gray-900 mb-2">프로그램을 찾을 수 없습니다</div>
          <div className="text-gray-500 mb-4">ID: {id}</div>
          <button
            onClick={() => navigate('/dashboard')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            대시보드로 돌아가기
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 헤더 */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/dashboard')}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5 text-gray-600" />
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">{program.name}</h1>
                <p className="text-sm text-gray-500 mt-1">{program.path}</p>
              </div>
            </div>

            {/* 상태 배지 */}
            <div className="flex items-center gap-3">
              <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                program.running
                  ? 'bg-green-100 text-green-800'
                  : 'bg-gray-100 text-gray-800'
              }`}>
                {program.running ? '실행 중' : '중지됨'}
              </span>
            </div>
          </div>

          {/* 액션 버튼 */}
          <div className="flex gap-2 mt-4">
            {/* On/Off 토글 버튼 */}
            <button
              onClick={handleToggle}
              disabled={actionLoading}
              className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors disabled:opacity-50 ${
                program.running
                  ? 'bg-red-600 hover:bg-red-700 text-white'
                  : 'bg-green-600 hover:bg-green-700 text-white'
              }`}
            >
              {program.running ? (
                <>
                  <Square className="w-4 h-4" />
                  Off
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  On
                </>
              )}
            </button>

            <button
              onClick={() => setShowEditModal(true)}
              disabled={actionLoading}
              className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 hover:bg-gray-50 text-gray-700 rounded-lg font-medium transition-colors disabled:opacity-50"
            >
              <Edit className="w-4 h-4" />
              수정
            </button>
            <button
              onClick={handleDelete}
              disabled={actionLoading}
              className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 hover:bg-gray-50 text-red-600 rounded-lg font-medium transition-colors disabled:opacity-50"
            >
              <Trash2 className="w-4 h-4" />
              삭제
            </button>
          </div>

          {/* 탭 네비게이션 */}
          <div className="mt-6">
            <TabNavigation
              tabs={tabs}
              activeTab={activeTab}
              onTabChange={setActiveTab}
            />
          </div>
        </div>
      </div>

      {/* 탭 콘텐츠 */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* 프로그램 정보 */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">프로그램 정보</h2>
              <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <dt className="text-sm font-medium text-gray-500">프로그램 이름</dt>
                  <dd className="mt-1 text-sm text-gray-900">{program.name}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">실행 경로</dt>
                  <dd className="mt-1 text-sm text-gray-900 break-all">{program.path}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">실행 인자</dt>
                  <dd className="mt-1 text-sm text-gray-900">{program.args || '없음'}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">프로세스 ID</dt>
                  <dd className="mt-1 text-sm text-gray-900">{program.pid || 'N/A'}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">웹훅 URL</dt>
                  <dd className="mt-1 text-sm text-gray-900 break-all">{program.webhook_urls || '설정 안됨'}</dd>
                </div>
              </dl>
            </div>
          </div>
        )}

        {activeTab === 'metrics' && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">리소스 사용량</h2>
            <Suspense fallback={<div className="text-center py-8 text-gray-500">로딩 중...</div>}>
              <ResourceChart programId={program.id} />
            </Suspense>
          </div>
        )}

        {activeTab === 'control' && (
          <Suspense fallback={<div className="text-center py-8 text-gray-500">로딩 중...</div>}>
            <PalworldControl programId={program.id} />
          </Suspense>
        )}

        {activeTab === 'plugins' && (
          <div className="bg-white rounded-lg shadow p-6">
            {program && program.id ? (
              <Suspense fallback={<div className="text-center py-8 text-gray-500">로딩 중...</div>}>
                <PluginTab programId={program.id} />
              </Suspense>
            ) : (
              <div className="text-center py-8 text-gray-500">
                프로그램 정보를 불러오는 중...
              </div>
            )}
          </div>
        )}
      </div>

      {/* 수정 모달 */}
      {showEditModal && (
        <EditProgramModal
          program={program}
          onClose={() => setShowEditModal(false)}
          onSuccess={() => {
            setShowEditModal(false)
            loadProgram()
          }}
        />
      )}
    </div>
  )
}
