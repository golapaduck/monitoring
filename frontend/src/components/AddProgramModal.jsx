import { useState } from 'react'
import { X, FolderOpen } from 'lucide-react'
import { addProgram } from '../lib/api'

export default function AddProgramModal({ onClose, onSuccess }) {
  const [formData, setFormData] = useState({
    name: '',
    path: '',
    args: '',
    webhook_urls: [''],
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      // 빈 웹훅 URL 필터링
      const webhookUrls = formData.webhook_urls.filter(url => url.trim())
      
      await addProgram({
        ...formData,
        webhook_urls: webhookUrls.length > 0 ? webhookUrls : undefined,
      })
      onSuccess()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const addWebhookUrl = () => {
    setFormData({
      ...formData,
      webhook_urls: [...formData.webhook_urls, ''],
    })
  }

  const removeWebhookUrl = (index) => {
    setFormData({
      ...formData,
      webhook_urls: formData.webhook_urls.filter((_, i) => i !== index),
    })
  }

  const updateWebhookUrl = (index, value) => {
    const newUrls = [...formData.webhook_urls]
    newUrls[index] = value
    setFormData({
      ...formData,
      webhook_urls: newUrls,
    })
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* 헤더 */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">프로그램 추가</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* 폼 */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-800">
              {error}
            </div>
          )}

          {/* 프로그램 이름 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              프로그램 이름 *
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="예: 메모장"
              required
            />
          </div>

          {/* 프로그램 경로 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              프로그램 경로 *
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={formData.path}
                onChange={(e) => setFormData({ ...formData, path: e.target.value })}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="예: C:\Windows\System32\notepad.exe"
                required
              />
              <button
                type="button"
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                title="파일 탐색기 (추후 구현)"
              >
                <FolderOpen className="w-5 h-5 text-gray-600" />
              </button>
            </div>
          </div>

          {/* 실행 인자 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              실행 인자 (선택사항)
            </label>
            <input
              type="text"
              value={formData.args}
              onChange={(e) => setFormData({ ...formData, args: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="예: --config config.ini"
            />
          </div>

          {/* 웹훅 URL */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              웹훅 URL (선택사항)
            </label>
            {formData.webhook_urls.map((url, index) => (
              <div key={index} className="flex gap-2 mb-2">
                <input
                  type="url"
                  value={url}
                  onChange={(e) => updateWebhookUrl(index, e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="https://discord.com/api/webhooks/..."
                />
                {formData.webhook_urls.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeWebhookUrl(index)}
                    className="px-3 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                )}
              </div>
            ))}
            <button
              type="button"
              onClick={addWebhookUrl}
              className="text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              + 웹훅 URL 추가
            </button>
          </div>

          {/* 버튼 */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
            >
              취소
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
            >
              {loading ? '추가 중...' : '추가'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
