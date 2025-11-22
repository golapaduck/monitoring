import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Play, Square, RotateCw, Trash2, Edit, AlertTriangle } from 'lucide-react'
import axios from 'axios'
import { startProgram, stopProgram, restartProgram, deleteProgram } from '../lib/api'
import EditProgramModal from '../components/EditProgramModal'
import ResourceChart from '../components/ResourceChart'
import PluginTab from '../components/PluginTab'

export default function ProgramDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [program, setProgram] = useState(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [showForceStop, setShowForceStop] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    loadProgram()
    const interval = setInterval(loadProgram, 5000)
    return () => clearInterval(interval)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  const loadProgram = async () => {
    try {
      const response = await axios.get(`/api/programs`)
      // API 응답이 {programs: [...]} 형태
      const programs = response.data.programs || response.data
      const foundProgram = programs.find(p => p.id === parseInt(id))
      
      if (foundProgram) {
        setProgram(foundProgram)
      } else {
        console.warn(`프로그램을 찾을 수 없습니다 (ID: ${id})`)
        setTimeout(() => navigate('/dashboard'), 2000)
      }
    } catch (error) {
      console.error('프로그램 로드 실패:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleStart = async () => {
    setActionLoading(true)
    try {
      await startProgram(program.id)
      await loadProgram()
    } catch (error) {
      alert(`시작 실패: ${error.message}`)
    } finally {
      setActionLoading(false)
    }
  }

  const handleStop = async (force = false) => {
    setActionLoading(true)
    try {
      await stopProgram(program.id, force)
      await loadProgram()
      setShowForceStop(false)
    } catch (error) {
      alert(`종료 실패: ${error.message}`)
    } finally {
      setActionLoading(false)
    }
  }

  const handleRestart = async () => {
    setActionLoading(true)
    try {
      await restartProgram(program.id)
      await loadProgram()
    } catch (error) {
      alert(`재시작 실패: ${error.message}`)
    } finally {
      setActionLoading(false)
    }
  }

  const handleDelete = async () => {
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
  }

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
            {!program.running ? (
              <button
                onClick={handleStart}
                disabled={actionLoading}
                className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
              >
                <Play className="w-4 h-4" />
                시작
              </button>
            ) : (
              <>
                <button
                  onClick={() => setShowForceStop(!showForceStop)}
                  disabled={actionLoading}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                >
                  <Square className="w-4 h-4" />
                  종료
                </button>
                <button
                  onClick={handleRestart}
                  disabled={actionLoading}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                >
                  <RotateCw className="w-4 h-4" />
                  재시작
                </button>
              </>
            )}
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

          {/* 강제 종료 옵션 */}
          {showForceStop && (
            <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
              <div className="flex items-start gap-2">
                <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm text-yellow-800 font-medium">강제 종료 옵션</p>
                  <p className="text-xs text-yellow-700 mt-1">
                    일반 종료가 실패할 경우 강제 종료를 시도하세요.
                  </p>
                  <div className="flex gap-2 mt-2">
                    <button
                      onClick={() => handleStop(false)}
                      disabled={actionLoading}
                      className="px-3 py-1 bg-yellow-600 hover:bg-yellow-700 text-white rounded text-sm font-medium transition-colors disabled:opacity-50"
                    >
                      일반 종료
                    </button>
                    <button
                      onClick={() => handleStop(true)}
                      disabled={actionLoading}
                      className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded text-sm font-medium transition-colors disabled:opacity-50"
                    >
                      강제 종료
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 탭 네비게이션 */}
          <div className="flex gap-4 mt-6 border-b border-gray-200">
            <button
              onClick={() => setActiveTab('overview')}
              className={`px-4 py-2 font-medium transition-colors ${
                activeTab === 'overview'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              개요
            </button>
            <button
              onClick={() => setActiveTab('metrics')}
              className={`px-4 py-2 font-medium transition-colors ${
                activeTab === 'metrics'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              리소스 모니터링
            </button>
            <button
              onClick={() => setActiveTab('plugins')}
              className={`px-4 py-2 font-medium transition-colors ${
                activeTab === 'plugins'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              플러그인
            </button>
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
            <ResourceChart programId={program.id} />
          </div>
        )}

        {activeTab === 'plugins' && (
          <div className="bg-white rounded-lg shadow p-6">
            {program && program.id ? (
              <PluginTab programId={program.id} />
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
