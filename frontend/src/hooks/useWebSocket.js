/**
 * 웹소켓 연결 및 이벤트 관리 훅
 */

import { useEffect, useState } from 'react'
import { io } from 'socket.io-client'

const SOCKET_URL = import.meta.env.VITE_SOCKET_URL || 'http://localhost:8080'

// 싱글톤 WebSocket 인스턴스
let socketInstance = null
let connectionListeners = []
let disconnectionListeners = []

/**
 * 싱글톤 WebSocket 인스턴스 생성/반환
 */
function getSocketInstance() {
  if (!socketInstance) {
    socketInstance = io(SOCKET_URL, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5
    })

    // 연결 이벤트
    socketInstance.on('connect', () => {
      console.log('🔌 [WebSocket] 연결됨:', socketInstance.id)
      connectionListeners.forEach(callback => callback())
    })

    socketInstance.on('disconnect', () => {
      console.log('🔌 [WebSocket] 연결 해제')
      disconnectionListeners.forEach(callback => callback())
    })

    socketInstance.on('connected', (data) => {
      console.log('🔌 [WebSocket] 서버 응답:', data)
    })

    // 에러 처리
    socketInstance.on('connect_error', (error) => {
      console.error('🔌 [WebSocket] 연결 오류:', error)
    })
  }

  return socketInstance
}

export function useWebSocket() {
  const [isConnected, setIsConnected] = useState(false)

  useEffect(() => {
    const socket = getSocketInstance()

    // 연결 상태 업데이트
    const handleConnect = () => setIsConnected(true)
    const handleDisconnect = () => setIsConnected(false)

    connectionListeners.push(handleConnect)
    disconnectionListeners.push(handleDisconnect)

    // 현재 연결 상태 반영 (비동기로 처리)
    if (socket.connected) {
      // 다음 렌더링 사이클에서 상태 업데이트
      Promise.resolve().then(() => setIsConnected(true))
    }

    // 정리
    return () => {
      connectionListeners = connectionListeners.filter(cb => cb !== handleConnect)
      disconnectionListeners = disconnectionListeners.filter(cb => cb !== handleDisconnect)
    }
  }, [])

  // 이벤트 구독
  const subscribe = (event, callback) => {
    const socket = getSocketInstance()
    socket.on(event, callback)
  }

  // 이벤트 구독 해제
  const unsubscribe = (event, callback) => {
    const socket = getSocketInstance()
    socket.off(event, callback)
  }

  // 이벤트 전송
  const emit = (event, data) => {
    const socket = getSocketInstance()
    if (isConnected) {
      socket.emit(event, data)
    }
  }

  return {
    isConnected,
    subscribe,
    unsubscribe,
    emit
  }
}

/**
 * 프로그램 상태 실시간 업데이트 훅
 */
export function useProgramStatus(onStatusChange) {
  const { subscribe, unsubscribe, isConnected } = useWebSocket()

  useEffect(() => {
    const handleStatusChange = (data) => {
      console.log('📊 [WebSocket] 프로그램 상태 변경:', data)
      if (onStatusChange) {
        onStatusChange(data)
      }
    }

    subscribe('program_status', handleStatusChange)

    return () => {
      unsubscribe('program_status', handleStatusChange)
    }
  }, [subscribe, unsubscribe, onStatusChange])

  return { isConnected }
}

/**
 * 리소스 사용량 실시간 업데이트 훅
 */
export function useResourceUpdate(onResourceUpdate) {
  const { subscribe, unsubscribe, isConnected } = useWebSocket()

  useEffect(() => {
    const handleResourceUpdate = (data) => {
      console.log('📈 [WebSocket] 리소스 업데이트:', data)
      if (onResourceUpdate) {
        onResourceUpdate(data)
      }
    }

    subscribe('resource_update', handleResourceUpdate)

    return () => {
      unsubscribe('resource_update', handleResourceUpdate)
    }
  }, [subscribe, unsubscribe, onResourceUpdate])

  return { isConnected }
}

/**
 * 알림 실시간 수신 훅
 */
export function useNotification(onNotification) {
  const { subscribe, unsubscribe, isConnected } = useWebSocket()

  useEffect(() => {
    const handleNotification = (data) => {
      console.log('🔔 [WebSocket] 알림:', data)
      if (onNotification) {
        onNotification(data)
      }
    }

    subscribe('notification', handleNotification)

    return () => {
      unsubscribe('notification', handleNotification)
    }
  }, [subscribe, unsubscribe, onNotification])

  return { isConnected }
}
