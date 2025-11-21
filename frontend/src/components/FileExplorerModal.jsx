import { useState, useEffect } from 'react'
import { X, Folder, File, ChevronRight, HardDrive } from 'lucide-react'
import axios from 'axios'

export default function FileExplorerModal({ onSelect, onClose }) {
  const [currentPath, setCurrentPath] = useState('')
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    loadDirectory(currentPath)
  }, [currentPath])

  const loadDirectory = async (path) => {
    setLoading(true)
    setError('')
    
    try {
      const response = await axios.post('/api/explorer/list', { path })
      setItems(response.data.items || [])
    } catch (err) {
      setError(err.response?.data?.error || '디렉토리를 불러올 수 없습니다.')
    } finally {
      setLoading(false)
    }
  }

  const handleItemClick = (item) => {
    if (item.is_dir) {
      setCurrentPath(item.path)
    } else if (item.executable) {
      onSelect(item.path)
      onClose()
    }
  }

  const handleBack = () => {
    if (currentPath) {
      const parentPath = currentPath.split('\\').slice(0, -1).join('\\')
      setCurrentPath(parentPath || '')
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[80vh] flex flex-col">
        {/* 헤더 */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">파일 선택</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* 경로 표시 */}
        <div className="p-4 border-b border-gray-200 bg-gray-50">
          <div className="flex items-center gap-2 text-sm">
            <button
              onClick={handleBack}
              disabled={!currentPath}
              className="px-3 py-1 bg-white border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              ← 뒤로
            </button>
            <span className="text-gray-600">
              {currentPath || '드라이브 선택'}
            </span>
          </div>
        </div>

        {/* 에러 메시지 */}
        {error && (
          <div className="mx-4 mt-4 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-800">
            {error}
          </div>
        )}

        {/* 파일 목록 */}
        <div className="flex-1 overflow-y-auto p-4">
          {loading ? (
            <div className="text-center py-8 text-gray-500">로딩 중...</div>
          ) : items.length === 0 ? (
            <div className="text-center py-8 text-gray-500">항목이 없습니다.</div>
          ) : (
            <div className="space-y-1">
              {items.map((item, index) => (
                <button
                  key={index}
                  onClick={() => handleItemClick(item)}
                  className={`w-full flex items-center gap-3 p-3 rounded-lg text-left transition-colors ${
                    item.is_dir
                      ? 'hover:bg-blue-50'
                      : item.executable
                      ? 'hover:bg-green-50'
                      : 'hover:bg-gray-50 opacity-50 cursor-not-allowed'
                  }`}
                  disabled={!item.is_dir && !item.executable}
                >
                  {item.type === 'drive' ? (
                    <HardDrive className="w-5 h-5 text-blue-500 flex-shrink-0" />
                  ) : item.is_dir ? (
                    <Folder className="w-5 h-5 text-blue-500 flex-shrink-0" />
                  ) : (
                    <File className={`w-5 h-5 flex-shrink-0 ${
                      item.executable ? 'text-green-500' : 'text-gray-400'
                    }`} />
                  )}
                  <span className="flex-1 truncate text-sm">{item.name}</span>
                  {item.is_dir && (
                    <ChevronRight className="w-4 h-4 text-gray-400 flex-shrink-0" />
                  )}
                  {item.executable && (
                    <span className="text-xs text-green-600 flex-shrink-0">실행 가능</span>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* 안내 */}
        <div className="p-4 border-t border-gray-200 bg-gray-50 text-xs text-gray-600">
          💡 실행 파일(.exe, .bat 등)만 선택할 수 있습니다.
        </div>
      </div>
    </div>
  )
}
