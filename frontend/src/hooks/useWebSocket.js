/**
 * REST API 폴링 기반 실시간 업데이트 훅
 * (Socket.IO 제거, REST API 폴링으로 대체)
 */

import { useState } from 'react'

// Socket.IO 제거 - REST API 폴링 사용
// import { io } from 'socket.io-client'

export function useWebSocket() {
  // 항상 연결된 것으로 간주 (REST API 사용)
  const [isConnected] = useState(true)

  // 더미 함수들 (호환성 유지)
  const subscribe = () => {}
  const unsubscribe = () => {}
  const emit = () => {}

  return {
    isConnected,
    subscribe,
    unsubscribe,
    emit
  }
}

/**
 * 프로그램 상태 실시간 업데이트 훅
 * (REST API 폴링으로 대체 - 더미 함수)
 */
export function useProgramStatus() {
  const { isConnected } = useWebSocket()
  
  // Socket.IO 제거 - REST API 폴링 사용
  // 실제 폴링은 각 컴포넌트에서 구현
  
  return { isConnected }
}

/**
 * 리소스 사용량 실시간 업데이트 훅
 * (REST API 폴링으로 대체 - 더미 함수)
 */
export function useResourceUpdate() {
  const { isConnected } = useWebSocket()
  
  // Socket.IO 제거 - REST API 폴링 사용
  // 실제 폴링은 각 컴포넌트에서 구현
  
  return { isConnected }
}

/**
 * 알림 실시간 수신 훅
 * (REST API 폴링으로 대체 - 더미 함수)
 */
export function useNotification() {
  const { isConnected } = useWebSocket()
  
  // Socket.IO 제거 - REST API 폴링 사용
  // 실제 폴링은 각 컴포넌트에서 구현
  
  return { isConnected }
}
