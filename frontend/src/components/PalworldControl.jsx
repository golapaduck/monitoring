import { useState, useEffect } from 'react'
import axios from 'axios'
import { Server, Users, MessageSquare, Ban, Save, Power, AlertTriangle } from 'lucide-react'

export default function PalworldControl({ programId }) {
  const [plugin, setPlugin] = useState(null)
  const [loading, setLoading] = useState(true)
  const [serverInfo, setServerInfo] = useState(null)
  const [players, setPlayers] = useState([])
  const [message, setMessage] = useState('')
  const [actionLoading, setActionLoading] = useState(false)
  const [result, setResult] = useState(null)

  useEffect(() => {
    loadPlugin()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [programId])

  const loadPlugin = async () => {
    try {
      const response = await axios.get(`/api/plugins/program/${programId}`)
      const plugins = response.data.plugins || response.data || []
      const palworldPlugin = plugins.find(p => p.plugin_id === 'palworld' && p.enabled)
      
      if (palworldPlugin) {
        setPlugin(palworldPlugin)
        // 초기 로드 시 서버 정보와 플레이어 목록은 로드하지 않음
        // 사용자가 필요할 때 "새로고침" 버튼으로 로드하도록 변경
      }
    } catch (error) {
      console.error('플러그인 로드 실패:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadServerInfo = async (pluginData) => {
    try {
      const response = await axios.post(
        `/api/plugins/program/${programId}/${pluginData.plugin_id}/action`,
        { action: 'get_info', params: {} }
      )
      if (response.data.success && response.data.data) {
        setServerInfo(response.data.data)
      }
    } catch (error) {
      console.error('서버 정보 로드 실패:', error)
    }
  }

  const loadPlayers = async (pluginData) => {
    try {
      const response = await axios.post(
        `/api/plugins/program/${programId}/${pluginData.plugin_id}/action`,
        { action: 'get_players', params: {} }
      )
      if (response.data.success && response.data.data) {
        setPlayers(response.data.data.players || [])
      }
    } catch (error) {
      console.error('플레이어 목록 로드 실패:', error)
    }
  }

  const executeAction = async (action, params = {}) => {
    setActionLoading(true)
    setResult(null)

    try {
      const response = await axios.post(
        `/api/plugins/program/${programId}/${plugin.plugin_id}/action`,
        { action, params }
      )
      setResult(response.data)
      
      // 성공 시 데이터 새로고침
      if (response.data.success) {
        if (action === 'get_info') await loadServerInfo(plugin)
        if (action === 'get_players') await loadPlayers(plugin)
      }
    } catch (error) {
      setResult({
        success: false,
        message: error.response?.data?.error || '액션 실행 실패'
      })
    } finally {
      setActionLoading(false)
    }
  }

  const handleAnnounce = () => {
    if (!message.trim()) {
      alert('메시지를 입력하세요')
      return
    }
    executeAction('announce', { message })
  }

  const handleKickPlayer = (userId, playerName) => {
    if (confirm(`${playerName}을(를) 강퇴하시겠습니까?`)) {
      executeAction('kick_player', { userid: userId, message: '관리자에 의해 강퇴되었습니다' })
    }
  }

  const handleBanPlayer = (userId, playerName) => {
    if (confirm(`${playerName}을(를) 차단하시겠습니까?`)) {
      executeAction('ban_player', { userid: userId, message: '관리자에 의해 차단되었습니다' })
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-gray-500">로딩 중...</div>
      </div>
    )
  }

  if (!plugin) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-yellow-900 mb-1">Palworld 플러그인이 설정되지 않았습니다</h3>
            <p className="text-sm text-yellow-700 mb-3">
              플러그인 탭에서 Palworld REST API 플러그인을 추가하고 활성화하세요.
            </p>
            <p className="text-xs text-yellow-600">
              💡 PalWorldSettings.ini에서 RESTAPIEnabled=True, RESTAPIPort=8212로 설정되어 있어야 합니다.
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* 결과 메시지 */}
      {result && (
        <div className={`rounded-lg p-4 ${result.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
          <p className={`text-sm ${result.success ? 'text-green-800' : 'text-red-800'}`}>
            {result.message || (result.success ? '성공' : '실패')}
          </p>
        </div>
      )}

      {/* 서버 정보 */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Server className="w-5 h-5" />
            서버 정보
          </h3>
          <button
            onClick={() => executeAction('get_info')}
            disabled={actionLoading}
            className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {serverInfo ? '새로고침' : '조회'}
          </button>
        </div>
        {serverInfo ? (
          <dl className="grid grid-cols-2 gap-4">
            <div>
              <dt className="text-sm text-gray-500">서버 이름</dt>
              <dd className="font-medium text-gray-900">{serverInfo.servername || 'N/A'}</dd>
            </div>
            <div>
              <dt className="text-sm text-gray-500">버전</dt>
              <dd className="font-medium text-gray-900">{serverInfo.version || 'N/A'}</dd>
            </div>
          </dl>
        ) : (
          <p className="text-sm text-gray-500">💡 "조회" 버튼을 클릭하여 서버 정보를 불러오세요</p>
        )}
      </div>

      {/* 플레이어 목록 */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Users className="w-5 h-5" />
            접속 중인 플레이어 ({players.length})
          </h3>
          <button
            onClick={() => executeAction('get_players')}
            disabled={actionLoading}
            className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {players.length > 0 ? '새로고침' : '조회'}
          </button>
        </div>
        {players.length > 0 ? (
          <div className="space-y-2">
            {players.map((player, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium text-gray-900">{player.name}</p>
                  <p className="text-xs text-gray-500">Player ID: {player.playerId || player.playerid || 'N/A'}</p>
                  <p className="text-xs text-gray-400">User ID: {player.userId || player.userid || 'N/A'}</p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleKickPlayer(player.userId || player.userid, player.name)}
                    disabled={actionLoading}
                    className="px-3 py-1 text-sm bg-orange-600 text-white rounded hover:bg-orange-700 disabled:opacity-50"
                  >
                    강퇴
                  </button>
                  <button
                    onClick={() => handleBanPlayer(player.userId || player.userid, player.name)}
                    disabled={actionLoading}
                    className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
                  >
                    차단
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500">💡 "조회" 버튼을 클릭하여 플레이어 목록을 불러오세요</p>
        )}
      </div>

      {/* 공지사항 */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2 mb-4">
          <MessageSquare className="w-5 h-5" />
          공지사항 전송
        </h3>
        <div className="flex gap-2">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="전송할 메시지를 입력하세요"
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={handleAnnounce}
            disabled={actionLoading || !message.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            전송
          </button>
        </div>
      </div>

      {/* 서버 관리 */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">서버 관리</h3>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => executeAction('save_world')}
            disabled={actionLoading}
            className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            월드 저장
          </button>
          <button
            onClick={() => {
              if (confirm('서버를 종료하시겠습니까?')) {
                executeAction('shutdown_server')
              }
            }}
            disabled={actionLoading}
            className="inline-flex items-center gap-2 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50"
          >
            <Power className="w-4 h-4" />
            서버 종료
          </button>
          <button
            onClick={() => {
              if (confirm('서버를 강제 종료하시겠습니까?')) {
                executeAction('force_stop_server')
              }
            }}
            disabled={actionLoading}
            className="inline-flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
          >
            <Ban className="w-4 h-4" />
            강제 종료
          </button>
        </div>
      </div>
    </div>
  )
}
