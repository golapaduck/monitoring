/**
 * API 서비스 레이어
 * 
 * axios를 래핑하여 일관된 에러 처리와 요청/응답 처리를 제공합니다.
 */

import axios from 'axios'

class ApiService {
  constructor(baseURL = '/api') {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json'
      },
      withCredentials: true // 세션 쿠키 포함
    })

    // 응답 인터셉터
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        return Promise.reject(this.handleError(error))
      }
    )
  }

  /**
   * 에러 처리
   */
  handleError(error) {
    if (error.response) {
      // 서버 응답이 있는 경우
      const { data, status } = error.response
      
      return {
        message: data.error || data.message || '서버 오류가 발생했습니다',
        status,
        code: data.error_code,
        details: data.details
      }
    } else if (error.request) {
      // 요청은 보냈지만 응답이 없는 경우
      return {
        message: '서버에 연결할 수 없습니다',
        status: 0,
        code: 'NETWORK_ERROR'
      }
    } else {
      // 요청 설정 중 오류
      return {
        message: error.message || '요청 처리 중 오류가 발생했습니다',
        status: 0,
        code: 'REQUEST_ERROR'
      }
    }
  }

  /**
   * GET 요청
   */
  async get(url, config = {}) {
    try {
      const response = await this.client.get(url, config)
      return response.data
    } catch (error) {
      throw error
    }
  }

  /**
   * POST 요청
   */
  async post(url, data = {}, config = {}) {
    try {
      const response = await this.client.post(url, data, config)
      return response.data
    } catch (error) {
      throw error
    }
  }

  /**
   * PUT 요청
   */
  async put(url, data = {}, config = {}) {
    try {
      const response = await this.client.put(url, data, config)
      return response.data
    } catch (error) {
      throw error
    }
  }

  /**
   * DELETE 요청
   */
  async delete(url, config = {}) {
    try {
      const response = await this.client.delete(url, config)
      return response.data
    } catch (error) {
      throw error
    }
  }

  /**
   * PATCH 요청
   */
  async patch(url, data = {}, config = {}) {
    try {
      const response = await this.client.patch(url, data, config)
      return response.data
    } catch (error) {
      throw error
    }
  }
}

// 싱글톤 인스턴스
export const api = new ApiService()

// 기본 export
export default api
