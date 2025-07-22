/**
 * Custom React hook for API calls with loading and error states
 */

import { useState, useCallback, useRef } from 'react'
import { ApiError } from '../utils/api'

export const useApi = () => {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [data, setData] = useState(null)
  const abortController = useRef(null)

  /**
   * Execute an async function with loading and error handling
   */
  const execute = useCallback(async (apiFunction, ...args) => {
    // Cancel previous request if still running
    if (abortController.current) {
      abortController.current.abort()
    }

    abortController.current = new AbortController()
    setLoading(true)
    setError(null)

    try {
      const result = await apiFunction(...args)
      setData(result)
      return result
    } catch (err) {
      // Don't set error if request was aborted
      if (err.name !== 'AbortError') {
        const errorMessage = err instanceof ApiError 
          ? err.message 
          : 'An unexpected error occurred'
        setError(errorMessage)
        setData(null)
      }
      throw err
    } finally {
      setLoading(false)
      abortController.current = null
    }
  }, [])

  /**
   * Clear error state
   */
  const clearError = useCallback(() => {
    setError(null)
  }, [])

  /**
   * Reset all state
   */
  const reset = useCallback(() => {
    if (abortController.current) {
      abortController.current.abort()
    }
    setLoading(false)
    setError(null)
    setData(null)
  }, [])

  return {
    loading,
    error,
    data,
    execute,
    clearError,
    reset,
  }
}

/**
 * Specialized hook for form submissions with debouncing
 */
export const useApiForm = (submitFunction, debounceMs = 300) => {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)
  const debounceTimer = useRef(null)

  const submit = useCallback(async (formData) => {
    // Clear previous timer
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current)
    }

    // Debounce the submission
    return new Promise((resolve, reject) => {
      debounceTimer.current = setTimeout(async () => {
        setIsSubmitting(true)
        setError(null)
        setSuccess(false)

        try {
          const result = await submitFunction(formData)
          setSuccess(true)
          resolve(result)
        } catch (err) {
          const errorMessage = err instanceof ApiError 
            ? err.message 
            : 'Failed to submit form'
          setError(errorMessage)
          reject(err)
        } finally {
          setIsSubmitting(false)
        }
      }, debounceMs)
    })
  }, [submitFunction, debounceMs])

  const clearMessages = useCallback(() => {
    setError(null)
    setSuccess(false)
  }, [])

  return {
    isSubmitting,
    error,
    success,
    submit,
    clearMessages,
  }
}