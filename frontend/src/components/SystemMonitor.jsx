import { useState, useEffect } from 'react'
import { Activity, Cpu, HardDrive, Zap } from 'lucide-react'
import axios from 'axios'

/**
 * 시스템 모니터링 컴포넌트
 * 전체 시스템 리소스 사용량을 표시합니다
 */
export default function SystemMonitor() {
  const [systemStats, setSystemStats] = useState({
    cpu_percent: 0,
    memory_percent: 0,
    memory_mb: 0,
    memory_total_mb: 0,
    disk_percent: 0,
    disk_free_gb: 0,
    disk_total_gb: 0,
    uptime_seconds: 0
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // 시스템 통계 조회
  useEffect(() => {
    const fetchSystemStats = async () => {
      try {
        const response = await axios.get('/api/system/stats')
        console.log('📊 [SystemMonitor] API 응답:', response.data)
        setSystemStats(response.data.data || {})
        setError(null)
      } catch (err) {
        console.error('❌ [SystemMonitor] 시스템 통계 조회 실패:', err)
        setError('시스템 통계를 조회할 수 없습니다')
      } finally {
        setLoading(false)
      }
    }

    fetchSystemStats()
    // 5초마다 갱신
    const interval = setInterval(fetchSystemStats, 5000)
    return () => clearInterval(interval)
  }, [])

  // 가동 시간 포맷팅
  const formatUptime = (seconds) => {
    const days = Math.floor(seconds / 86400)
    const hours = Math.floor((seconds % 86400) / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    
    if (days > 0) {
      return `${days}일 ${hours}시간`
    } else if (hours > 0) {
      return `${hours}시간 ${minutes}분`
    } else {
      return `${minutes}분`
    }
  }

  // 진행 바 색상 결정
  const getProgressColor = (percent) => {
    if (percent < 50) return 'bg-green-500'
    if (percent < 75) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <div className="flex items-center justify-center h-32">
          <div className="text-gray-500">로딩 중...</div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <div className="text-red-600 text-sm">{error}</div>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* CPU 사용률 */}
      <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Cpu className="w-5 h-5 text-blue-600" />
            <span className="text-sm font-medium text-gray-700">CPU</span>
          </div>
          <span className="text-lg font-bold text-gray-900">
            {systemStats.cpu_percent?.toFixed(1) || 0}%
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all ${getProgressColor(systemStats.cpu_percent || 0)}`}
            style={{ width: `${Math.min(systemStats.cpu_percent || 0, 100)}%` }}
          />
        </div>
      </div>

      {/* 메모리 사용률 */}
      <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-purple-600" />
            <span className="text-sm font-medium text-gray-700">메모리</span>
          </div>
          <span className="text-lg font-bold text-gray-900">
            {systemStats.memory_percent?.toFixed(1) || 0}%
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all ${getProgressColor(systemStats.memory_percent || 0)}`}
            style={{ width: `${Math.min(systemStats.memory_percent || 0, 100)}%` }}
          />
        </div>
        <div className="text-xs text-gray-500 mt-2">
          {systemStats.memory_mb?.toFixed(0) || 0}MB / {systemStats.memory_total_mb?.toFixed(0) || 0}MB
        </div>
      </div>

      {/* 디스크 사용률 */}
      <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <HardDrive className="w-5 h-5 text-green-600" />
            <span className="text-sm font-medium text-gray-700">디스크</span>
          </div>
          <span className="text-lg font-bold text-gray-900">
            {systemStats.disk_percent?.toFixed(1) || 0}%
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all ${getProgressColor(systemStats.disk_percent || 0)}`}
            style={{ width: `${Math.min(systemStats.disk_percent || 0, 100)}%` }}
          />
        </div>
        <div className="text-xs text-gray-500 mt-2">
          여유: {systemStats.disk_free_gb?.toFixed(1) || 0}GB / {systemStats.disk_total_gb?.toFixed(1) || 0}GB
        </div>
      </div>

      {/* 가동 시간 */}
      <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-yellow-600" />
            <span className="text-sm font-medium text-gray-700">가동 시간</span>
          </div>
        </div>
        <div className="text-2xl font-bold text-gray-900">
          {formatUptime(systemStats.uptime_seconds || 0)}
        </div>
      </div>
    </div>
  )
}
