/**
 * API 유틸리티 함수들
 */

import { cachedFetch } from '../utils/cache'

const API_BASE = ''

/**
 * API 요청 헬퍼 함수
 * 
 * 타임아웃: 30초 (기본값)
 */
async function apiRequest(url, options = {}) {
  const timeout = options.timeout || 30000  // 30초 기본 타임아웃
  
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeout)

  const defaultOptions = {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    signal: controller.signal,
  }

  try {
    const response = await fetch(`${API_BASE}${url}`, {
      ...defaultOptions,
      ...options,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Unknown error' }))
      throw new Error(error.error || `HTTP ${response.status}`)
    }

    return response.json()
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new Error(`요청 타임아웃 (${timeout}ms)`)
    }
    throw error
  } finally {
    clearTimeout(timeoutId)
  }
}

/**
 * 프로그램 목록 조회 (캐싱 적용)
 */
export async function getPrograms() {
  return cachedFetch('programs', () => apiRequest('/api/programs'), 10)
}

/**
 * 프로그램 상태 조회
 */
export async function getProgramsStatus() {
  return apiRequest('/api/programs/status')
}

/**
 * 프로그램 추가
 */
export async function addProgram(programData) {
  return apiRequest('/api/programs', {
    method: 'POST',
    body: JSON.stringify(programData),
  })
}

/**
 * 프로그램 수정
 */
export async function updateProgram(id, programData) {
  return apiRequest(`/api/programs/${id}`, {
    method: 'PUT',
    body: JSON.stringify(programData),
  })
}

/**
 * 프로그램 삭제
 */
export async function deleteProgram(id) {
  return apiRequest(`/api/programs/${id}/delete`, {
    method: 'DELETE',
  })
}

/**
 * 프로그램 시작
 */
export async function startProgram(id) {
  return apiRequest(`/api/programs/${id}/start`, {
    method: 'POST',
  })
}

/**
 * 프로그램 종료
 */
export async function stopProgram(id, force = false) {
  return apiRequest(`/api/programs/${id}/stop${force ? '?force=true' : ''}`, {
    method: 'POST',
  })
}

/**
 * 프로그램 재시작
 */
export async function restartProgram(id) {
  return apiRequest(`/api/programs/${id}/restart`, {
    method: 'POST',
  })
}

/**
 * 경로 유효성 검증
 */
export async function validatePath(path) {
  return apiRequest('/api/programs/validate-path', {
    method: 'POST',
    body: JSON.stringify({ path }),
  })
}

/**
 * 디렉토리 목록 조회
 */
export async function listDirectory(path) {
  return apiRequest('/api/explorer/list', {
    method: 'POST',
    body: JSON.stringify({ path }),
  })
}

/**
 * 파일 검색
 */
export async function searchFiles(path, query, maxResults = 50) {
  return apiRequest('/api/explorer/search', {
    method: 'POST',
    body: JSON.stringify({ path, query, max_results: maxResults }),
  })
}

/**
 * 자주 사용하는 경로 조회
 */
export async function getCommonPaths() {
  return apiRequest('/api/explorer/common-paths')
}

/**
 * 웹훅 설정 조회
 */
export async function getWebhookConfig() {
  return apiRequest('/api/webhook/config')
}

/**
 * 웹훅 설정 저장
 */
export async function saveWebhookConfig(config) {
  return apiRequest('/api/webhook/config', {
    method: 'POST',
    body: JSON.stringify(config),
  })
}

/**
 * 웹훅 테스트
 */
export async function testWebhook(url) {
  return apiRequest('/api/webhook/test', {
    method: 'POST',
    body: JSON.stringify({ url }),
  })
}
