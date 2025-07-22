/**
 * API utility functions with error handling and caching
 */

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://127.0.0.1:5000'
const API_TIMEOUT = parseInt(process.env.REACT_APP_API_TIMEOUT) || 10000
const CACHE_TTL = parseInt(process.env.REACT_APP_CACHE_TTL) || 300000 // 5 minutes

// Simple in-memory cache
const cache = new Map()

/**
 * API Client with error handling, timeout, and caching
 */
export class ApiClient {
  constructor(baseUrl = API_BASE_URL, timeout = API_TIMEOUT) {
    this.baseUrl = baseUrl
    this.timeout = timeout
  }

  /**
   * Make HTTP request with timeout and error handling
   */
  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`
    const controller = new AbortController()
    
    // Set timeout
    const timeoutId = setTimeout(() => controller.abort(), this.timeout)

    try {
      const config = {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        signal: controller.signal,
        ...options,
      }

      const response = await fetch(url, config)
      clearTimeout(timeoutId)

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new ApiError(
          errorData.message || `HTTP error! status: ${response.status}`,
          response.status,
          errorData
        )
      }

      return await response.json()
    } catch (error) {
      clearTimeout(timeoutId)
      
      if (error.name === 'AbortError') {
        throw new ApiError('Request timeout', 408)
      }
      
      if (error instanceof ApiError) {
        throw error
      }

      // Network or other errors
      throw new ApiError(
        'Network error: Please check your connection',
        0,
        { originalError: error.message }
      )
    }
  }

  /**
   * GET request with caching
   */
  async get(endpoint, useCache = true) {
    const cacheKey = `GET:${endpoint}`
    
    if (useCache && cache.has(cacheKey)) {
      const { data, timestamp } = cache.get(cacheKey)
      if (Date.now() - timestamp < CACHE_TTL) {
        return data
      }
      cache.delete(cacheKey)
    }

    const data = await this.request(endpoint, { method: 'GET' })
    
    if (useCache) {
      cache.set(cacheKey, { data, timestamp: Date.now() })
    }
    
    return data
  }

  /**
   * POST request
   */
  async post(endpoint, body) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(body),
    })
  }

  /**
   * Clear cache
   */
  clearCache(pattern = null) {
    if (pattern) {
      for (const key of cache.keys()) {
        if (key.includes(pattern)) {
          cache.delete(key)
        }
      }
    } else {
      cache.clear()
    }
  }
}

/**
 * Custom API Error class
 */
export class ApiError extends Error {
  constructor(message, status = 0, details = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.details = details
  }

  get isNetworkError() {
    return this.status === 0
  }

  get isClientError() {
    return this.status >= 400 && this.status < 500
  }

  get isServerError() {
    return this.status >= 500
  }

  get isTimeout() {
    return this.status === 408
  }

  get isRateLimit() {
    return this.status === 429
  }
}

/**
 * Input validation utilities
 */
export const validators = {
  email: (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!email || !email.trim()) {
      throw new Error('Email is required')
    }
    if (!emailRegex.test(email.trim())) {
      throw new Error('Please enter a valid email address')
    }
    return email.trim()
  },

  required: (value, fieldName) => {
    if (!value || !value.toString().trim()) {
      throw new Error(`${fieldName} is required`)
    }
    return value.toString().trim()
  },

  json: (jsonString, fieldName) => {
    if (!jsonString || !jsonString.trim()) {
      return null
    }
    try {
      const parsed = JSON.parse(jsonString)
      if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
        throw new Error(`${fieldName} must be a valid JSON object`)
      }
      return parsed
    } catch (error) {
      throw new Error(`${fieldName} contains invalid JSON: ${error.message}`)
    }
  },

  maxLength: (value, maxLen, fieldName) => {
    if (value && value.length > maxLen) {
      throw new Error(`${fieldName} must be ${maxLen} characters or less`)
    }
    return value
  },
}

// Global API client instance
export const apiClient = new ApiClient()

// Convenience methods for common API calls
export const api = {
  healthCheck: () => apiClient.get('/'),
  getAccount: () => apiClient.get('/api/account'),
  getContacts: (limit = 5, offset = 0) => 
    apiClient.get(`/api/contacts?limit=${limit}&offset=${offset}`, false),
  sendEmail: (emailData) => apiClient.post('/api/send-test-email', emailData),
  sendEvent: (eventData) => apiClient.post('/api/send-custom-event', eventData),
}