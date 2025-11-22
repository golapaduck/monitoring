import { useState, memo } from 'react'
import { useNavigate } from 'react-router-dom'
import { Play, Square, ExternalLink, Zap } from 'lucide-react'
import { startProgram, stopProgram, executePluginAction } from '../lib/api'

function ProgramCard({ program, onUpdate, user }) {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [showPluginActions, setShowPluginActions] = useState(false)
  const isAdmin = user?.role === 'admin'
  
  // 펠월드 플러그인 여부 확인
  const hasPalworldPlugin = program.plugins?.some(p => p.plugin_id === 'palworld')

  const handleToggle = async () => {
    setLoading(true)
    try {
      if (program.running) {
        await stopProgram(program.id, false)
      } else {
        await startProgram(program.id)
      }
      onUpdate()
    } catch (error) {
      alert(`작업 실패: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }

  // 펠월드 플러그인 액션 실행
  const handlePalworldAction = async (actionName) => {
    setLoading(true)
    try {
      const result = await executePluginAction(program.id, 'palworld', actionName, {})
      if (result.success) {
        alert(`✅ ${actionName} 성공`)
        onUpdate()
      } else {
        alert(`❌ 실패: ${result.message}`)
      }
    } catch (error) {
      alert(`작업 실패: ${error.message}`)
    } finally {
      setLoading(false)
      setShowPluginActions(false)
    }
  }

  return (
    <div className={`bg-white rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow ${
      hasPalworldPlugin 
        ? 'border-2 border-purple-200 hover:border-purple-300' 
        : 'border border-gray-200'
    }`}>
      {/* 헤더 */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-semibold text-gray-900 mb-1">
              {program.name}
            </h3>
            {/* 펠월드 배지 */}
            {hasPalworldPlugin && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                <Zap className="w-3 h-3 mr-1" />
                Palworld
              </span>
            )}
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
            className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium transition-all duration-300 ${
              program.status === 'shutting_down'
                ? 'bg-yellow-100 text-yellow-800 animate-pulse'
                : program.running
                ? 'bg-green-100 text-green-800'
                : 'bg-red-100 text-red-800'
            }`}
          >
            {program.status === 'shutting_down' 
              ? `⏳ ${program.status_text}` 
              : program.running ? '● 실행 중' : '● 중지됨'}
          </span>
        </div>
      </div>

      {/* Graceful Shutdown 프로그레스 바 */}
      {program.status === 'shutting_down' && program.shutdown_remaining !== null && (
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-yellow-700">서버 종료 진행 중</span>
            <span className="text-xs font-semibold text-yellow-800">{program.shutdown_remaining}초</span>
          </div>
          <div className="w-full bg-yellow-100 rounded-full h-2 overflow-hidden">
            <div 
              className="bg-yellow-500 h-2 rounded-full transition-all duration-1000 ease-linear"
              style={{ 
                width: `${((30 - program.shutdown_remaining) / 30) * 100}%` 
              }}
            />
          </div>
        </div>
      )}

      {/* 리소스 정보 */}
      {(program.running || program.status === 'shutting_down') && (
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
        {isAdmin && (
          <>
            <button
              onClick={handleToggle}
              disabled={loading || program.status === 'shutting_down'}
              className={`flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                program.status === 'shutting_down'
                  ? 'bg-yellow-600 text-white'
                  : program.running
                  ? 'bg-red-600 hover:bg-red-700 text-white'
                  : 'bg-green-600 hover:bg-green-700 text-white'
              }`}
            >
              {program.status === 'shutting_down' ? (
                <>
                  <Square className="w-4 h-4 animate-spin" />
                  종료 중...
                </>
              ) : program.running ? (
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

            {/* 펠월드 플러그인 토글 버튼 */}
            {hasPalworldPlugin && program.running && (
              <button
                onClick={() => setShowPluginActions(!showPluginActions)}
                disabled={loading}
                className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-purple-600 hover:bg-purple-700 text-white transition-colors disabled:opacity-50"
                title="펠월드 서버 관리"
              >
                <Zap className="w-4 h-4" />
                {showPluginActions ? '조작 닫기' : '조작 열기'}
              </button>
            )}
          </>
        )}
      </div>

      {/* 펠월드 조작 패널 (확장형) */}
      {hasPalworldPlugin && program.running && showPluginActions && (
        <div className="mt-4 p-4 bg-purple-50 rounded-lg border border-purple-200">
          <h4 className="text-sm font-semibold text-purple-900 mb-3 flex items-center gap-2">
            <Zap className="w-4 h-4" />
            펠월드 서버 조작
          </h4>
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => handlePalworldAction('get_info')}
              disabled={loading}
              className="flex items-center gap-2 px-3 py-2 text-sm bg-white hover:bg-purple-100 text-purple-700 rounded-lg border border-purple-200 transition-colors disabled:opacity-50"
            >
              📊 서버 정보
            </button>
            <button
              onClick={() => handlePalworldAction('get_players')}
              disabled={loading}
              className="flex items-center gap-2 px-3 py-2 text-sm bg-white hover:bg-purple-100 text-purple-700 rounded-lg border border-purple-200 transition-colors disabled:opacity-50"
            >
              👥 플레이어 목록
            </button>
            <button
              onClick={() => handlePalworldAction('save_world')}
              disabled={loading}
              className="flex items-center gap-2 px-3 py-2 text-sm bg-white hover:bg-purple-100 text-purple-700 rounded-lg border border-purple-200 transition-colors disabled:opacity-50"
            >
              💾 월드 저장
            </button>
            <button
              onClick={() => {
                const message = prompt('공지사항을 입력하세요:')
                if (message) {
                  setLoading(true)
                  executePluginAction(program.id, 'palworld', 'announce', { message })
                    .then(result => {
                      if (result.success) {
                        alert('✅ 공지사항 전송 성공')
                      } else {
                        alert(`❌ 실패: ${result.message}`)
                      }
                    })
                    .catch(error => alert(`작업 실패: ${error.message}`))
                    .finally(() => setLoading(false))
                }
              }}
              disabled={loading}
              className="flex items-center gap-2 px-3 py-2 text-sm bg-white hover:bg-purple-100 text-purple-700 rounded-lg border border-purple-200 transition-colors disabled:opacity-50"
            >
              📢 공지사항
            </button>
            <button
              onClick={() => handlePalworldAction('shutdown_server')}
              disabled={loading}
              className="col-span-2 flex items-center justify-center gap-2 px-3 py-2 text-sm bg-red-50 hover:bg-red-100 text-red-700 rounded-lg border border-red-200 transition-colors disabled:opacity-50"
            >
              🛑 서버 종료 (Graceful)
            </button>
          </div>
        </div>
      )}

      {/* 로딩 오버레이 */}
      {loading && (
        <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center rounded-lg">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      )}
    </div>
  )
}

// 메모이제이션 적용 (props 변경 시에만 리렌더링)
export default memo(ProgramCard, (prevProps, nextProps) => {
  // program과 user가 같으면 리렌더링 스킵
  return (
    prevProps.program.id === nextProps.program.id &&
    prevProps.program.running === nextProps.program.running &&
    prevProps.program.status === nextProps.program.status &&
    prevProps.program.shutdown_remaining === nextProps.program.shutdown_remaining &&
    prevProps.program.cpu_percent === nextProps.program.cpu_percent &&
    prevProps.program.memory_mb === nextProps.program.memory_mb &&
    prevProps.user?.role === nextProps.user?.role
  )
})
