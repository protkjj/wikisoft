/**
 * Centralized error handling utilities
 */

export interface ErrorResponse {
  detail?: string
  message?: string
  error?: string
}

/**
 * Extract user-friendly error message from any error object
 * @param error - Error object (axios error, fetch error, or Error instance)
 * @param fallbackMessage - Default message if extraction fails
 * @returns User-friendly error message
 */
export const getErrorMessage = (error: unknown, fallbackMessage: string): string => {
  // Axios error with response
  if (typeof error === 'object' && error !== null && 'response' in error) {
    const axiosError = error as { response?: { data?: ErrorResponse } }
    const detail = axiosError.response?.data?.detail
    const message = axiosError.response?.data?.message
    const errorMsg = axiosError.response?.data?.error

    return detail || message || errorMsg || fallbackMessage
  }

  // Standard Error instance
  if (error instanceof Error) {
    return error.message || fallbackMessage
  }

  // String error
  if (typeof error === 'string') {
    return error
  }

  return fallbackMessage
}

/**
 * Log error to console in development
 * @param context - Context string (e.g., "Validation", "Download")
 * @param error - Error object
 */
export const logError = (context: string, error: unknown): void => {
  if (import.meta.env.MODE === 'development') {
    console.error(`[${context}]`, error)
  }
}

/**
 * Handle error with both logging and message extraction
 * @param context - Context string
 * @param error - Error object
 * @param fallbackMessage - Default user message
 * @returns User-friendly error message
 */
export const handleError = (
  context: string,
  error: unknown,
  fallbackMessage: string
): string => {
  logError(context, error)
  return getErrorMessage(error, fallbackMessage)
}
