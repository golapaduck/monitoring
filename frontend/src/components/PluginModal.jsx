import { useState, useEffect } from 'react'
import { X, Plus, Settings, Trash2, Play } from 'lucide-react'
import axios from 'axios'

export default function PluginModal({ program, onClose, onSuccess }) {
  const [availablePlugins, setAvailablePlugins] = useState([])
  const [programPlugins, setProgramPlugins] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedPlugin, setSelectedPlugin] = useState(null)
  const [showConfigModal, setShowConfigModal] = useState(false)
  const [showActionModal, setShowActionModal] = useState(false)

  useEffect(() => {
    loadData()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [program.id])

  const loadData = async () => {
    try {
      setLoading(true)
      const [availableRes, programRes] = await Promise.all([
        axios.get('/api/plugins/available'),
        axios.get(`/api/plugins/program/${program.id}`)
      ])
      
      setAvailablePlugins(availableRes.data.plugins || [])
      setProgramPlugins(programRes.data.plugins || [])
      setError('')
    } catch (err) {
      setError(err.response?.data?.error || '플러그인 정보를 불러올 수 없습니다.')
    } finally {
      setLoading(false)
    }
  }

  const handleAddPlugin = (plugin) => {
    setSelectedPlugin(plugin)
    setShowConfigModal(true)
  }

  const handleRemovePlugin = async (pluginId) => {
    if (!confirm('이 플러그인을 제거하시겠습니까?')) return

    try {
      await axios.delete(`/api/plugins/program/${program.id}/${pluginId}`)
      await loadData()
      onSuccess?.()
    } catch (err) {
      alert(`플러그인 제거 실패: ${err.response?.data?.error || err.message}`)
    }
  }

  const handleOpenActions = (plugin) => {
    setSelectedPlugin(plugin)
    setShowActionModal(true)
  }

  const isPluginInstalled = (pluginId) => {
    return programPlugins.some(p => p.plugin_id === pluginId)
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col">
        {/* 헤더 */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">
            플러그인 관리 - {program.name}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* 내용 */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="text-center py-8 text-gray-500">로딩 중...</div>
          ) : error ? (
            <div className="text-center py-8 text-red-600">{error}</div>
          ) : (
            <div className="space-y-6">
              {/* 설치된 플러그인 */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  설치된 플러그인 ({programPlugins.length})
                </h3>
                {programPlugins.length === 0 ? (
                  <p className="text-gray-500 text-sm">설치된 플러그인이 없습니다.</p>
                ) : (
                  <div className="space-y-3">
                    {programPlugins.map((plugin) => {
                      const pluginInfo = availablePlugins.find(p => p.id === plugin.plugin_id)
                      return (
                        <div key={plugin.plugin_id} className="border border-gray-200 rounded-lg p-4">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <h4 className="font-medium text-gray-900">
                                {pluginInfo?.name || plugin.plugin_id}
                              </h4>
                              <p className="text-sm text-gray-500 mt-1">
                                {pluginInfo?.description || '설명 없음'}
                              </p>
                              <div className="mt-2">
                                <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                                  plugin.enabled
                                    ? 'bg-green-100 text-green-800'
                                    : 'bg-gray-100 text-gray-800'
                                }`}>
                                  {plugin.enabled ? '활성화' : '비활성화'}
                                </span>
                              </div>
                            </div>
                            <div className="flex gap-2 ml-4">
                              {pluginInfo && (
                                <button
                                  onClick={() => handleOpenActions(pluginInfo)}
                                  className="p-2 text-blue-600 hover:bg-blue-50 rounded transition-colors"
                                  title="액션 실행"
                                >
                                  <Play className="w-4 h-4" />
                                </button>
                              )}
                              <button
                                onClick={() => handleRemovePlugin(plugin.plugin_id)}
                                className="p-2 text-red-600 hover:bg-red-50 rounded transition-colors"
                                title="제거"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>

              {/* 사용 가능한 플러그인 */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  사용 가능한 플러그인
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {availablePlugins.map((plugin) => (
                    <div key={plugin.id} className="border border-gray-200 rounded-lg p-4">
                      <h4 className="font-medium text-gray-900">{plugin.name}</h4>
                      <p className="text-sm text-gray-500 mt-1">{plugin.description}</p>
                      <button
                        onClick={() => handleAddPlugin(plugin)}
                        disabled={isPluginInstalled(plugin.id)}
                        className={`mt-3 inline-flex items-center gap-2 px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                          isPluginInstalled(plugin.id)
                            ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                            : 'bg-blue-600 text-white hover:bg-blue-700'
                        }`}
                      >
                        <Plus className="w-4 h-4" />
                        {isPluginInstalled(plugin.id) ? '설치됨' : '추가'}
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 푸터 */}
        <div className="flex justify-end gap-3 p-6 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-700 font-medium transition-colors"
          >
            닫기
          </button>
        </div>
      </div>

      {/* 플러그인 설정 모달 */}
      {showConfigModal && selectedPlugin && (
        <PluginConfigModal
          program={program}
          plugin={selectedPlugin}
          onClose={() => {
            setShowConfigModal(false)
            setSelectedPlugin(null)
          }}
          onSuccess={() => {
            setShowConfigModal(false)
            setSelectedPlugin(null)
            loadData()
            onSuccess?.()
          }}
        />
      )}

      {/* 플러그인 액션 모달 */}
      {showActionModal && selectedPlugin && (
        <PluginActionModal
          program={program}
          plugin={selectedPlugin}
          onClose={() => {
            setShowActionModal(false)
            setSelectedPlugin(null)
          }}
        />
      )}
    </div>
  )
}

// 플러그인 설정 모달
function PluginConfigModal({ program, plugin, onClose, onSuccess }) {
  const [config, setConfig] = useState({})
  const [enabled, setEnabled] = useState(true)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      await axios.post(`/api/plugins/program/${program.id}/${plugin.id}`, {
        config,
        enabled
      })
      onSuccess()
    } catch (err) {
      setError(err.response?.data?.error || '플러그인 설정 저장 실패')
    } finally {
      setLoading(false)
    }
  }

  const renderConfigField = (key, schema) => {
    const value = config[key] !== undefined ? config[key] : (schema.default !== undefined ? schema.default : '')
    const isNumberType = schema.type === 'integer' || schema.type === 'number'

    return (
      <div key={key} className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {schema.title || key}
          {schema.required && <span className="text-red-500 ml-1">*</span>}
        </label>
        {schema.description && (
          <p className="text-xs text-gray-500 mb-2">{schema.description}</p>
        )}
        <input
          type={schema.format === 'password' ? 'password' : isNumberType ? 'number' : 'text'}
          value={value}
          onChange={(e) => {
            const newValue = isNumberType ? (e.target.value === '' ? '' : Number(e.target.value)) : e.target.value
            setConfig({ ...config, [key]: newValue })
          }}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          required={schema.required}
          min={schema.minimum}
          max={schema.maximum}
          step={schema.type === 'number' ? 'any' : undefined}
        />
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60] p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">{plugin.name} 설정</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4">
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-800">
              {error}
            </div>
          )}

          {plugin.config_schema?.properties && Object.entries(plugin.config_schema.properties).map(([key, schema]) =>
            renderConfigField(key, schema)
          )}

          <div className="mb-4">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={enabled}
                onChange={(e) => setEnabled(e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm font-medium text-gray-700">플러그인 활성화</span>
            </label>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-700 font-medium"
            >
              취소
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium disabled:opacity-50"
            >
              {loading ? '저장 중...' : '저장'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// 플러그인 액션 모달
function PluginActionModal({ program, plugin, onClose }) {
  const [selectedAction, setSelectedAction] = useState(null)
  const [params, setParams] = useState({})
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const handleExecute = async () => {
    if (!selectedAction) return

    setLoading(true)
    setResult(null)

    try {
      const response = await axios.post(`/api/plugins/program/${program.id}/${plugin.id}/action`, {
        action: selectedAction,
        params
      })
      setResult(response.data)
    } catch (err) {
      setResult({
        success: false,
        message: err.response?.data?.message || '액션 실행 실패'
      })
    } finally {
      setLoading(false)
    }
  }

  const renderParamField = (key, schema) => {
    return (
      <div key={key} className="mb-3">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {schema.title || key}
        </label>
        {schema.description && (
          <p className="text-xs text-gray-500 mb-2">{schema.description}</p>
        )}
        <input
          type="text"
          value={params[key] || ''}
          onChange={(e) => setParams({ ...params, [key]: e.target.value })}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
        />
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60] p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-lg w-full max-h-[80vh] flex flex-col">
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">{plugin.name} 액션</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          {/* 액션 선택 */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">액션 선택</label>
            <select
              value={selectedAction || ''}
              onChange={(e) => {
                setSelectedAction(e.target.value)
                setParams({})
                setResult(null)
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">선택하세요</option>
              {Object.entries(plugin.actions || {}).map(([actionId, action]) => (
                <option key={actionId} value={actionId}>
                  {action.title}
                </option>
              ))}
            </select>
          </div>

          {/* 선택된 액션 정보 */}
          {selectedAction && plugin.actions[selectedAction] && (
            <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded">
              <p className="text-sm text-blue-900">
                {plugin.actions[selectedAction].description}
              </p>
            </div>
          )}

          {/* 파라미터 입력 */}
          {selectedAction && plugin.actions[selectedAction]?.params && (
            <div className="mb-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">파라미터</h4>
              {Object.entries(plugin.actions[selectedAction].params).map(([key, schema]) =>
                renderParamField(key, schema)
              )}
            </div>
          )}

          {/* 실행 결과 */}
          {result && (
            <div className={`p-3 rounded border ${
              result.success
                ? 'bg-green-50 border-green-200'
                : 'bg-red-50 border-red-200'
            }`}>
              <p className={`text-sm font-medium ${
                result.success ? 'text-green-900' : 'text-red-900'
              }`}>
                {result.message}
              </p>
              {result.data && (
                <pre className="mt-2 text-xs overflow-x-auto">
                  {JSON.stringify(result.data, null, 2)}
                </pre>
              )}
            </div>
          )}
        </div>

        <div className="flex justify-end gap-3 p-4 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-700 font-medium"
          >
            닫기
          </button>
          <button
            onClick={handleExecute}
            disabled={!selectedAction || loading}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium disabled:opacity-50"
          >
            {loading ? '실행 중...' : '실행'}
          </button>
        </div>
      </div>
    </div>
  )
}
