/**
 * 웹소켓 연결 및 이벤트 관리 훅
 */

import { useEffect, useRef, useState } from 'react'
import { io } from 'socket.io-client'

const SOCKET_URL = import.meta.env.VITE_SOCKET_URL || 'http://localhost:8080'

export function useWebSocket() {
  const socketRef = useRef(null)
  const [isConnected, setIsConnected] = useState(false)

  useEffect(() => {
    // 소켓 연결
    socketRef.current = io(SOCKET_URL, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5
    })

    const socket = socketRef.current

    // 연결 이벤트
    socket.on('connect', () => {
      console.log('🔌 [WebSocket] 연결됨:', socket.id)
      setIsConnected(true)
    })

    socket.on('disconnect', () => {
      console.log('🔌 [WebSocket] 연결 해제')
      setIsConnected(false)
    })

    socket.on('connected', (data) => {
      console.log('🔌 [WebSocket] 서버 응답:', data)
    })

    // 에러 처리
    socket.on('connect_error', (error) => {
      console.error('🔌 [WebSocket] 연결 오류:', error)
      setIsConnected(false)
    })

    // 정리
    return () => {
      if (socket) {
        socket.disconnect()
      }
    }
  }, [])

  // 이벤트 구독
  const subscribe = (event, callback) => {
    if (socketRef.current) {
      socketRef.current.on(event, callback)
    }
  }

  // 이벤트 구독 해제
  const unsubscribe = (event, callback) => {
    if (socketRef.current) {
      socketRef.current.off(event, callback)
    }
  }

  // 이벤트 전송
  const emit = (event, data) => {
    if (socketRef.current && isConnected) {
      socketRef.current.emit(event, data)
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
