import { memo } from 'react'

/**
 * 탭 네비게이션 컴포넌트
 * 
 * 중복된 탭 버튼 코드를 제거하고 재사용 가능하게 만듭니다.
 */
function TabNavigation({ tabs, activeTab, onTabChange }) {
  return (
    <div className="flex gap-4 border-b border-gray-200 overflow-x-auto">
      {tabs.map(tab => (
        <button
          key={tab.id}
          onClick={() => onTabChange(tab.id)}
          className={`px-4 py-2 font-medium transition-colors whitespace-nowrap ${
            activeTab === tab.id
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  )
}

export default memo(TabNavigation)
