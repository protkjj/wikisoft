/**
 * Centralized error handling utilities
 */

export interface ErrorResponse {
  detail?: string
  message?: string
  error?: string
}

// HTTP 상태 코드별 사용자 친화적 메시지
const HTTP_STATUS_MESSAGES: Record<number, string> = {
  400: '요청 형식이 올바르지 않습니다.',
  401: '로그인이 필요합니다. 다시 로그인해주세요.',
  403: '접근 권한이 없습니다.',
  404: '요청한 리소스를 찾을 수 없습니다.',
  408: '요청 시간이 초과되었습니다. 다시 시도해주세요.',
  413: '파일이 너무 큽니다. 10MB 이하로 업로드해주세요.',
  422: '파일 형식이 올바르지 않습니다. .xlsx 또는 .xls 파일만 지원됩니다.',
  429: '요청이 너무 많습니다. 잠시 후 다시 시도해주세요.',
  500: '서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
  502: '서버에 연결할 수 없습니다. 잠시 후 다시 시도해주세요.',
  503: '서비스가 일시적으로 이용 불가합니다. 잠시 후 다시 시도해주세요.',
  504: '서버 응답 시간이 초과되었습니다. 다시 시도해주세요.',
}

/**
 * Extract user-friendly error message from any error object
 * @param error - Error object (axios error, fetch error, or Error instance)
 * @param fallbackMessage - Default message if extraction fails
 * @returns User-friendly error message
 */
export const getErrorMessage = (error: unknown, fallbackMessage: string): string => {
  // 네트워크 오류 체크
  if (!navigator.onLine) {
    return '인터넷 연결을 확인해주세요.'
  }

  // Axios error with response
  if (typeof error === 'object' && error !== null && 'response' in error) {
    const axiosError = error as {
      response?: {
        status?: number
        data?: ErrorResponse
      }
      code?: string
    }

    // HTTP 상태 코드별 메시지
    const status = axiosError.response?.status
    if (status && HTTP_STATUS_MESSAGES[status]) {
      // 서버에서 구체적인 메시지를 제공하면 그것 사용
      const serverMessage = axiosError.response?.data?.detail ||
                           axiosError.response?.data?.message ||
                           axiosError.response?.data?.error
      if (serverMessage) {
        return serverMessage
      }
      return HTTP_STATUS_MESSAGES[status]
    }

    // 일반 서버 응답 메시지
    const detail = axiosError.response?.data?.detail
    const message = axiosError.response?.data?.message
    const errorMsg = axiosError.response?.data?.error
    if (detail || message || errorMsg) {
      return detail || message || errorMsg || fallbackMessage
    }

    // Axios 에러 코드 (네트워크 오류 등)
    if (axiosError.code === 'ECONNABORTED') {
      return '요청 시간이 초과되었습니다. 다시 시도해주세요.'
    }
    if (axiosError.code === 'ERR_NETWORK') {
      return '서버에 연결할 수 없습니다. 네트워크 상태를 확인해주세요.'
    }
  }

  // Standard Error instance
  if (error instanceof Error) {
    // TypeError는 보통 네트워크 문제
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      return '서버에 연결할 수 없습니다. 네트워크 상태를 확인해주세요.'
    }
    return error.message || fallbackMessage
  }

  // String error
  if (typeof error === 'string') {
    return error
  }

  return fallbackMessage
}

/**
 * 재시도 가능한 에러인지 확인
 */
export const isRetryableError = (error: unknown): boolean => {
  if (typeof error === 'object' && error !== null && 'response' in error) {
    const axiosError = error as { response?: { status?: number }; code?: string }
    const status = axiosError.response?.status
    // 5xx 서버 에러, 408 타임아웃, 429 레이트 리밋은 재시도 가능
    if (status && (status >= 500 || status === 408 || status === 429)) {
      return true
    }
    // 네트워크 에러는 재시도 가능
    if (axiosError.code === 'ECONNABORTED' || axiosError.code === 'ERR_NETWORK') {
      return true
    }
  }
  return !navigator.onLine // 오프라인이면 재시도 가능
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
