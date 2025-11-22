import { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import axios from 'axios'

export default function ResourceChart({ programId }) {
  const [metrics, setMetrics] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [timeRange, setTimeRange] = useState(24) // 기본 24시간

  useEffect(() => {
    loadMetrics()
    // 30초마다 자동 새로고침
    const interval = setInterval(loadMetrics, 30000)
    return () => clearInterval(interval)
  }, [programId, timeRange])

  const loadMetrics = async () => {
    try {
      setLoading(true)
      const response = await axios.get(`/api/metrics/${programId}?hours=${timeRange}`)
      
      // 타임스탬프를 시간 형식으로 변환
      const formattedMetrics = response.data.metrics.map(m => ({
        ...m,
        time: new Date(m.timestamp).toLocaleTimeString('ko-KR', { 
          hour: '2-digit', 
          minute: '2-digit' 
        }),
        cpu: parseFloat(m.cpu_percent.toFixed(1)),
        memory: parseFloat(m.memory_mb.toFixed(1))
      }))
      
      setMetrics(formattedMetrics)
      setError('')
    } catch (err) {
      setError(err.response?.data?.error || '메트릭을 불러올 수 없습니다.')
    } finally {
      setLoading(false)
    }
  }

  if (loading && metrics.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center text-gray-500">로딩 중...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center text-red-600">{error}</div>
      </div>
    )
  }

  if (metrics.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center text-gray-500">
          아직 수집된 데이터가 없습니다. 프로그램을 실행하면 데이터가 수집됩니다.
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">리소스 사용량</h3>
        
        {/* 시간 범위 선택 */}
        <div className="flex gap-2">
          {[1, 6, 12, 24, 48, 168].map(hours => (
            <button
              key={hours}
              onClick={() => setTimeRange(hours)}
              className={`px-3 py-1 text-sm rounded transition-colors ${
                timeRange === hours
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {hours < 24 ? `${hours}시간` : `${hours / 24}일`}
            </button>
          ))}
        </div>
      </div>

      {/* CPU 차트 */}
      <div className="mb-8">
        <h4 className="text-sm font-medium text-gray-700 mb-3">CPU 사용률 (%)</h4>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={metrics}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="time" 
              tick={{ fontSize: 12 }}
              interval="preserveStartEnd"
            />
            <YAxis 
              tick={{ fontSize: 12 }}
              domain={[0, 'auto']}
            />
            <Tooltip />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="cpu" 
              stroke="#3b82f6" 
              strokeWidth={2}
              dot={false}
              name="CPU %"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* 메모리 차트 */}
      <div>
        <h4 className="text-sm font-medium text-gray-700 mb-3">메모리 사용량 (MB)</h4>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={metrics}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="time" 
              tick={{ fontSize: 12 }}
              interval="preserveStartEnd"
            />
            <YAxis 
              tick={{ fontSize: 12 }}
              domain={[0, 'auto']}
            />
            <Tooltip />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="memory" 
              stroke="#10b981" 
              strokeWidth={2}
              dot={false}
              name="메모리 MB"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* 통계 정보 */}
      {metrics.length > 0 && (
        <div className="mt-6 grid grid-cols-2 gap-4 pt-4 border-t border-gray-200">
          <div>
            <div className="text-sm text-gray-500">평균 CPU</div>
            <div className="text-lg font-semibold text-gray-900">
              {(metrics.reduce((sum, m) => sum + m.cpu, 0) / metrics.length).toFixed(1)}%
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-500">평균 메모리</div>
            <div className="text-lg font-semibold text-gray-900">
              {(metrics.reduce((sum, m) => sum + m.memory, 0) / metrics.length).toFixed(1)} MB
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
