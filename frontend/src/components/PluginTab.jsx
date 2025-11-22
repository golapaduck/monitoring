import { useState, useEffect } from 'react'
import { Plus, Settings, Play, Trash2, AlertCircle } from 'lucide-react'
import axios from 'axios'

export default function PluginTab({ programId }) {
  const [availablePlugins, setAvailablePlugins] = useState([])
  const [configuredPlugins, setConfiguredPlugins] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedPlugin, setSelectedPlugin] = useState(null)
  const [showConfigModal, setShowConfigModal] = useState(false)
  const [showActionModal, setShowActionModal] = useState(false)

  useEffect(() => {
    if (programId) {
      loadPlugins()
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [programId])

  const loadPlugins = async () => {
    try {
      setError(null)
      console.log('플러그인 로딩 시작, programId:', programId)
      
      const [availableRes, configuredRes] = await Promise.all([
        axios.get('/api/plugins/available'),
        axios.get(`/api/plugins/program/${programId}`)
      ])
      
      console.log('사용 가능한 플러그인:', availableRes.data)
      console.log('설정된 플러그인:', configuredRes.data)
      
      setAvailablePlugins(availableRes.data)
      setConfiguredPlugins(configuredRes.data)
    } catch (error) {
      console.error('플러그인 로드 실패:', error)
      setError(error.message || '플러그인을 불러오는데 실패했습니다')
    } finally {
      setLoading(false)
    }
  }

  const handleDeletePlugin = async (pluginId) => {
    if (!confirm('이 플러그인 설정을 삭제하시겠습니까?')) return

    try {
      await axios.delete(`/api/plugins/config/${pluginId}`)
      await loadPlugins()
    } catch (error) {
      alert(`삭제 실패: ${error.response?.data?.error || error.message}`)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-gray-500">로딩 중...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-3" />
          <p className="text-red-600 font-medium mb-2">플러그인 로드 실패</p>
          <p className="text-sm text-gray-500 mb-4">{error}</p>
          <button
            onClick={loadPlugins}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            다시 시도
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* 설정된 플러그인 */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">설정된 플러그인</h3>
        {configuredPlugins.length === 0 ? (
          <div className="bg-gray-50 rounded-lg p-8 text-center">
            <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <p className="text-gray-500">설정된 플러그인이 없습니다.</p>
            <p className="text-sm text-gray-400 mt-1">아래에서 플러그인을 추가해보세요.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {configuredPlugins.map((plugin) => (
              <div
                key={plugin.id}
                className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h4 className="font-semibold text-gray-900">{plugin.plugin_id}</h4>
                    <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium mt-1 ${
                      plugin.enabled
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {plugin.enabled ? '활성화' : '비활성화'}
                    </span>
                  </div>
                  <div className="flex gap-1">
                    <button
                      onClick={() => {
                        setSelectedPlugin(plugin)
                        setShowActionModal(true)
                      }}
                      className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                      title="액션 실행"
                    >
                      <Play className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => {
                        setSelectedPlugin(plugin)
                        setShowConfigModal(true)
                      }}
                      className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                      title="설정"
                    >
                      <Settings className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDeletePlugin(plugin.id)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      title="삭제"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <div className="text-sm text-gray-600">
                  <p className="line-clamp-2">{JSON.stringify(plugin.config, null, 2)}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 사용 가능한 플러그인 */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">사용 가능한 플러그인</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {availablePlugins.map((plugin) => {
            const isConfigured = configuredPlugins.some(p => p.plugin_id === plugin.id)
            return (
              <div
                key={plugin.id}
                className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <h4 className="font-semibold text-gray-900">{plugin.name}</h4>
                    <p className="text-sm text-gray-600 mt-1">{plugin.description}</p>
                  </div>
                  <button
                    onClick={() => {
                      setSelectedPlugin({ plugin_id: plugin.id, ...plugin })
                      setShowConfigModal(true)
                    }}
                    disabled={isConfigured}
                    className={`p-2 rounded-lg transition-colors ${
                      isConfigured
                        ? 'text-gray-400 cursor-not-allowed'
                        : 'text-blue-600 hover:bg-blue-50'
                    }`}
                    title={isConfigured ? '이미 설정됨' : '플러그인 추가'}
                  >
                    <Plus className="w-5 h-5" />
                  </button>
                </div>
                {isConfigured && (
                  <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800">
                    설정됨
                  </span>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* 플러그인 설정 모달 */}
      {showConfigModal && selectedPlugin && (
        <PluginConfigModal
          programId={programId}
          plugin={selectedPlugin}
          onClose={() => {
            setShowConfigModal(false)
            setSelectedPlugin(null)
          }}
          onSuccess={() => {
            setShowConfigModal(false)
            setSelectedPlugin(null)
            loadPlugins()
          }}
        />
      )}

      {/* 플러그인 액션 모달 */}
      {showActionModal && selectedPlugin && (
        <PluginActionModal
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
function PluginConfigModal({ programId, plugin, onClose, onSuccess }) {
  const [config, setConfig] = useState({})
  const [enabled, setEnabled] = useState(true)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [schema, setSchema] = useState(null)

  useEffect(() => {
    loadSchema()
    if (plugin.config) {
      setConfig(plugin.config)
      setEnabled(plugin.enabled)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const loadSchema = async () => {
    try {
      const response = await axios.get(`/api/plugins/available`)
      const pluginData = response.data.find(p => p.id === plugin.plugin_id)
      if (pluginData) {
        setSchema(pluginData.config_schema)
      }
    } catch (error) {
      console.error('스키마 로드 실패:', error)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      if (plugin.id) {
        // 업데이트
        await axios.put(`/api/plugins/config/${plugin.id}`, {
          config,
          enabled
        })
      } else {
        // 생성
        await axios.post('/api/plugins/config', {
          program_id: programId,
          plugin_id: plugin.plugin_id,
          config,
          enabled
        })
      }
      onSuccess()
    } catch (err) {
      setError(err.response?.data?.error || '플러그인 설정 저장 실패')
    } finally {
      setLoading(false)
    }
  }

  const renderConfigField = (key, fieldSchema) => {
    const value = config[key] !== undefined ? config[key] : (fieldSchema.default !== undefined ? fieldSchema.default : '')
    const isNumberType = fieldSchema.type === 'integer' || fieldSchema.type === 'number'
    const isBooleanType = fieldSchema.type === 'boolean'
    const isEnumType = fieldSchema.enum && fieldSchema.enum.length > 0

    if (isBooleanType) {
      return (
        <div key={key} className="mb-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={config[key] || false}
              onChange={(e) => setConfig({ ...config, [key]: e.target.checked })}
              className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
            />
            <span className="text-sm font-medium text-gray-700">
              {fieldSchema.title || key}
              {fieldSchema.required && <span className="text-red-500 ml-1">*</span>}
            </span>
          </label>
          {fieldSchema.description && (
            <p className="text-xs text-gray-500 ml-6 mt-1">{fieldSchema.description}</p>
          )}
        </div>
      )
    }

    if (isEnumType) {
      return (
        <div key={key} className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {fieldSchema.title || key}
            {fieldSchema.required && <span className="text-red-500 ml-1">*</span>}
          </label>
          {fieldSchema.description && (
            <p className="text-xs text-gray-500 mb-2">{fieldSchema.description}</p>
          )}
          <select
            value={value}
            onChange={(e) => setConfig({ ...config, [key]: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            required={fieldSchema.required}
          >
            {fieldSchema.enum.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </div>
      )
    }

    return (
      <div key={key} className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {fieldSchema.title || key}
          {fieldSchema.required && <span className="text-red-500 ml-1">*</span>}
        </label>
        {fieldSchema.description && (
          <p className="text-xs text-gray-500 mb-2">{fieldSchema.description}</p>
        )}
        <input
          type={fieldSchema.format === 'password' ? 'password' : isNumberType ? 'number' : 'text'}
          value={value}
          onChange={(e) => {
            const newValue = isNumberType ? (e.target.value === '' ? '' : Number(e.target.value)) : e.target.value
            setConfig({ ...config, [key]: newValue })
          }}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          required={fieldSchema.required}
          min={fieldSchema.minimum}
          max={fieldSchema.maximum}
          step={fieldSchema.type === 'number' ? 'any' : undefined}
        />
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4">
          <h3 className="text-lg font-semibold text-gray-900">
            {plugin.id ? '플러그인 설정 수정' : '플러그인 추가'}
          </h3>
          <p className="text-sm text-gray-500 mt-1">{plugin.name || plugin.plugin_id}</p>
        </div>

        <form onSubmit={handleSubmit} className="p-6">
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-800">
              {error}
            </div>
          )}

          {/* 활성화 토글 */}
          <div className="mb-6">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={enabled}
                onChange={(e) => setEnabled(e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
              />
              <span className="text-sm font-medium text-gray-700">플러그인 활성화</span>
            </label>
          </div>

          {/* 설정 필드 */}
          {schema && schema.properties && (
            <div className="space-y-4">
              <h4 className="font-medium text-gray-900 mb-3">플러그인 설정</h4>
              {Object.entries(schema.properties).map(([key, fieldSchema]) =>
                renderConfigField(key, fieldSchema)
              )}
            </div>
          )}

          {/* 버튼 */}
          <div className="flex gap-3 mt-6 pt-6 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 font-medium transition-colors"
            >
              취소
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium transition-colors disabled:opacity-50"
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
function PluginActionModal({ plugin, onClose }) {
  const [actions, setActions] = useState({})
  const [selectedAction, setSelectedAction] = useState(null)
  const [params, setParams] = useState({})
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  useEffect(() => {
    loadActions()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const loadActions = async () => {
    try {
      const response = await axios.get('/api/plugins/available')
      const pluginData = response.data.find(p => p.id === plugin.plugin_id)
      if (pluginData) {
        setActions(pluginData.actions)
      }
    } catch (error) {
      console.error('액션 로드 실패:', error)
    }
  }

  const handleExecute = async () => {
    if (!selectedAction) return

    setLoading(true)
    setResult(null)

    try {
      const response = await axios.post(`/api/plugins/config/${plugin.id}/execute`, {
        action: selectedAction,
        params
      })
      setResult(response.data)
    } catch (error) {
      setResult({
        success: false,
        message: error.response?.data?.error || '액션 실행 실패'
      })
    } finally {
      setLoading(false)
    }
  }

  const renderParamField = (key, paramSchema) => {
    const value = params[key] || ''

    return (
      <div key={key} className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {paramSchema.title || key}
        </label>
        {paramSchema.description && (
          <p className="text-xs text-gray-500 mb-2">{paramSchema.description}</p>
        )}
        <input
          type="text"
          value={value}
          onChange={(e) => setParams({ ...params, [key]: e.target.value })}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          placeholder={paramSchema.description}
        />
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4">
          <h3 className="text-lg font-semibold text-gray-900">플러그인 액션 실행</h3>
          <p className="text-sm text-gray-500 mt-1">{plugin.plugin_id}</p>
        </div>

        <div className="p-6">
          {/* 액션 선택 */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">액션 선택</label>
            <select
              value={selectedAction || ''}
              onChange={(e) => {
                setSelectedAction(e.target.value)
                setParams({})
                setResult(null)
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">액션을 선택하세요</option>
              {Object.entries(actions).map(([key, action]) => (
                <option key={key} value={key}>
                  {action.title}
                </option>
              ))}
            </select>
            {selectedAction && actions[selectedAction]?.description && (
              <p className="text-sm text-gray-600 mt-2">{actions[selectedAction].description}</p>
            )}
          </div>

          {/* 파라미터 입력 */}
          {selectedAction && actions[selectedAction]?.params && (
            <div className="mb-6">
              <h4 className="font-medium text-gray-900 mb-3">파라미터</h4>
              {Object.entries(actions[selectedAction].params).map(([key, paramSchema]) =>
                renderParamField(key, paramSchema)
              )}
            </div>
          )}

          {/* 실행 버튼 */}
          <button
            onClick={handleExecute}
            disabled={!selectedAction || loading}
            className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium transition-colors disabled:opacity-50 mb-4"
          >
            {loading ? '실행 중...' : '실행'}
          </button>

          {/* 결과 표시 */}
          {result && (
            <div className={`p-4 rounded-lg ${
              result.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
            }`}>
              <h4 className={`font-medium mb-2 ${
                result.success ? 'text-green-900' : 'text-red-900'
              }`}>
                {result.success ? '✓ 성공' : '✗ 실패'}
              </h4>
              <p className={`text-sm ${
                result.success ? 'text-green-800' : 'text-red-800'
              }`}>
                {result.message}
              </p>
              {result.data && (
                <pre className="mt-3 p-3 bg-white rounded text-xs overflow-x-auto">
                  {JSON.stringify(result.data, null, 2)}
                </pre>
              )}
            </div>
          )}

          {/* 닫기 버튼 */}
          <button
            onClick={onClose}
            className="w-full mt-4 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 font-medium transition-colors"
          >
            닫기
          </button>
        </div>
      </div>
    </div>
  )
}
