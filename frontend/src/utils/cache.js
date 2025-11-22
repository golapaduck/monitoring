/**
 * API 응답 캐싱 시스템
 * 
 * 반복되는 API 요청을 캐시하여 성능을 향상시킵니다.
 */

class CacheManager {
  constructor() {
    this.cache = new Map()
    this.timers = new Map()
  }

  /**
   * 캐시에서 데이터 조회
   * @param {string} key - 캐시 키
   * @returns {any} 캐시된 데이터 또는 null
   */
  get(key) {
    return this.cache.get(key) || null
  }

  /**
   * 캐시에 데이터 저장
   * @param {string} key - 캐시 키
   * @param {any} data - 저장할 데이터
   * @param {number} ttl - TTL (초, 기본값: 60)
   */
  set(key, data, ttl = 60) {
    // 기존 타이머 제거
    if (this.timers.has(key)) {
      clearTimeout(this.timers.get(key))
    }

    // 데이터 저장
    this.cache.set(key, data)

    // TTL 타이머 설정
    const timer = setTimeout(() => {
      this.cache.delete(key)
      this.timers.delete(key)
    }, ttl * 1000)

    this.timers.set(key, timer)
  }

  /**
   * 캐시 제거
   * @param {string} key - 캐시 키
   */
  remove(key) {
    if (this.timers.has(key)) {
      clearTimeout(this.timers.get(key))
      this.timers.delete(key)
    }
    this.cache.delete(key)
  }

  /**
   * 모든 캐시 제거
   */
  clear() {
    this.timers.forEach(timer => clearTimeout(timer))
    this.cache.clear()
    this.timers.clear()
  }

  /**
   * 캐시 상태 확인
   * @param {string} key - 캐시 키
   * @returns {boolean} 캐시 존재 여부
   */
  has(key) {
    return this.cache.has(key)
  }
}

// 싱글톤 인스턴스
export const cacheManager = new CacheManager()

/**
 * 캐시된 API 요청 래퍼
 * @param {string} key - 캐시 키
 * @param {Function} fetcher - API 요청 함수
 * @param {number} ttl - TTL (초)
 * @returns {Promise} API 응답
 */
export async function cachedFetch(key, fetcher, ttl = 60) {
  // 캐시 확인
  const cached = cacheManager.get(key)
  if (cached) {
    console.log(`✅ [Cache] 캐시 히트: ${key}`)
    return cached
  }

  // API 요청
  console.log(`🔄 [Cache] 캐시 미스: ${key}`)
  const data = await fetcher()

  // 캐시 저장
  cacheManager.set(key, data, ttl)

  return data
}
