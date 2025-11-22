/**
 * 디바운싱 유틸리티
 * 
 * 연속된 함수 호출을 제한하여 성능을 향상시킵니다.
 */

import React from 'react'

/**
 * 함수를 디바운스 처리
 * @param {Function} func - 실행할 함수
 * @param {number} delay - 지연 시간 (ms)
 * @returns {Function} 디바운스된 함수
 */
export function debounce(func, delay = 300) {
  let timeoutId = null

  return function debounced(...args) {
    // 기존 타이머 제거
    if (timeoutId) {
      clearTimeout(timeoutId)
    }

    // 새로운 타이머 설정
    timeoutId = setTimeout(() => {
      func.apply(this, args)
      timeoutId = null
    }, delay)
  }
}

/**
 * 함수를 쓰로틀 처리
 * @param {Function} func - 실행할 함수
 * @param {number} limit - 최소 간격 (ms)
 * @returns {Function} 쓰로틀된 함수
 */
export function throttle(func, limit = 300) {
  let inThrottle = false

  return function throttled(...args) {
    if (!inThrottle) {
      func.apply(this, args)
      inThrottle = true

      setTimeout(() => {
        inThrottle = false
      }, limit)
    }
  }
}

/**
 * React useCallback과 함께 사용할 디바운스 훅
 * @param {Function} callback - 콜백 함수
 * @param {number} delay - 지연 시간 (ms)
 * @returns {Function} 디바운스된 콜백
 */
export function useDebouncedCallback(callback, delay = 300) {
  const timeoutRef = React.useRef(null)

  React.useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [])

  return React.useCallback(
    (...args) => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }

      timeoutRef.current = setTimeout(() => {
        callback(...args)
      }, delay)
    },
    [callback, delay]
  )
}
