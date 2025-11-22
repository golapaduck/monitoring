import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Play, Square, RotateCw, AlertTriangle, ExternalLink } from 'lucide-react'
import { startProgram, stopProgram, restartProgram } from '../lib/api'

export default function ProgramCard({ program, onUpdate }) {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [showForceStop, setShowForceStop] = useState(false)

  const handleStart = async () => {
    setLoading(true)
    try {
      await startProgram(program.id)
      onUpdate()
    } catch (error) {
      alert(`시작 실패: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleStop = async (force = false) => {
    setLoading(true)
    try {
      await stopProgram(program.id, force)
      setShowForceStop(false)
      onUpdate()
    } catch (error) {
      alert(`종료 실패: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleRestart = async () => {
    setLoading(true)
    try {
      await restartProgram(program.id)
      onUpdate()
    } catch (error) {
      alert(`재시작 실패: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
      {/* 헤더 */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-semibold text-gray-900 mb-1">
              {program.name}
            </h3>
            <button
              onClick={() => navigate(`/program/${program.id}`)}
              className="p-1 text-gray-400 hover:text-blue-600 transition-colors"
              title="상세 페이지"
            >
              <ExternalLink className="w-4 h-4" />
            </button>
          </div>
          <p className="text-sm text-gray-500 truncate" title={program.path}>
            {program.path || 'N/A'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {/* 상태 배지 */}
          <span
            className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
              program.running
                ? 'bg-green-100 text-green-800'
                : 'bg-red-100 text-red-800'
            }`}
          >
            {program.running ? '● 실행 중' : '● 중지됨'}
          </span>
        </div>
      </div>

      {/* 리소스 정보 */}
      {program.running && (
        <div className="grid grid-cols-3 gap-4 mb-4 p-3 bg-gray-50 rounded-lg">
          <div>
            <p className="text-xs text-gray-500 mb-1">CPU</p>
            <p className="text-sm font-semibold text-gray-900">
              {program.cpu_percent?.toFixed(1) || 0}%
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500 mb-1">메모리</p>
            <p className="text-sm font-semibold text-gray-900">
              {program.memory_mb?.toFixed(0) || 0} MB
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500 mb-1">PID</p>
            <p className="text-sm font-semibold text-gray-900">
              {program.pid || 'N/A'}
            </p>
          </div>
        </div>
      )}

      {/* 가동 시간 */}
      {program.uptime && (
        <div className="mb-4">
          <p className="text-xs text-gray-500">가동 시간</p>
          <p className="text-sm text-gray-700">{program.uptime}</p>
        </div>
      )}

      {/* 액션 버튼 */}
      <div className="flex flex-wrap gap-2">
        {!program.running ? (
          <button
            onClick={handleStart}
            disabled={loading}
            className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
          >
            <Play className="w-4 h-4" />
            시작
          </button>
        ) : (
          <>
            <button
              onClick={() => setShowForceStop(!showForceStop)}
              disabled={loading}
              className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
            >
              <Square className="w-4 h-4" />
              종료
            </button>
            {showForceStop && (
              <button
                onClick={() => handleStop(true)}
                disabled={loading}
                className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
              >
                <AlertTriangle className="w-4 h-4" />
                강제 종료
              </button>
            )}
          </>
        )}

        <button
          onClick={handleRestart}
          disabled={loading}
          className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
        >
          <RotateCw className="w-4 h-4" />
          재시작
        </button>
      </div>

      {/* 로딩 오버레이 */}
      {loading && (
        <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center rounded-lg">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      )}
    </div>
  )
}
