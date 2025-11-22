/**
 * 로딩 스켈레톤 컴포넌트
 * 데이터 로딩 중 표시되는 플레이스홀더
 */

export default function LoadingSkeleton() {
  return (
    <div className="animate-pulse">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
            {/* 헤더 */}
            <div className="flex items-center justify-between mb-4">
              <div className="h-6 bg-gray-200 rounded w-1/2"></div>
              <div className="h-8 w-8 bg-gray-200 rounded-full"></div>
            </div>
            
            {/* 경로 */}
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
            
            {/* 상태 */}
            <div className="flex items-center gap-2 mb-4">
              <div className="h-6 w-16 bg-gray-200 rounded-full"></div>
              <div className="h-4 w-24 bg-gray-200 rounded"></div>
            </div>
            
            {/* 버튼들 */}
            <div className="flex gap-2">
              <div className="h-10 bg-gray-200 rounded flex-1"></div>
              <div className="h-10 bg-gray-200 rounded flex-1"></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
