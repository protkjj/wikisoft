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

// 기술적 에러 메시지 → 사용자 친화적 메시지 매핑
const ERROR_MESSAGE_MAP: Record<string, string> = {
  // 파일 관련
  'No file uploaded': '파일을 선택해주세요.',
  'Invalid file type': 'Excel 파일(.xlsx, .xls)만 업로드 가능합니다.',
  'File too large': '파일 크기가 너무 큽니다. 10MB 이하의 파일을 선택해주세요.',
  'Empty file': '파일이 비어있습니다. 다른 파일을 선택해주세요.',
  'Unable to parse file': '파일을 읽을 수 없습니다. 파일이 손상되었거나 형식이 올바르지 않습니다.',
  'No data found': '파일에 데이터가 없습니다. 명부 데이터가 있는 파일을 선택해주세요.',

  // 헤더 매핑 관련
  'No headers found': '헤더 행을 찾을 수 없습니다. 첫 번째 행에 컬럼명이 있는지 확인해주세요.',
  'Required column missing': '필수 컬럼이 누락되었습니다. 사원번호, 성명, 입사일 등이 포함되어야 합니다.',
  'Header mapping failed': '컬럼 매핑에 실패했습니다. 컬럼명을 확인해주세요.',

  // 검증 관련
  'Validation failed': '데이터 검증에 실패했습니다. 파일 내용을 확인해주세요.',
  'Invalid date format': '날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식으로 입력해주세요.',
  'Invalid number format': '숫자 형식이 올바르지 않습니다.',

  // 서버 관련
  'Internal server error': '서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
  'Service unavailable': '서비스를 일시적으로 이용할 수 없습니다. 잠시 후 다시 시도해주세요.',
  'Request timeout': '요청 처리 시간이 초과되었습니다. 파일 크기를 줄이거나 다시 시도해주세요.',

  // 세션 관련
  'Session expired': '세션이 만료되었습니다. 페이지를 새로고침 후 다시 시도해주세요.',
  'Session not found': '검증 세션을 찾을 수 없습니다. 파일을 다시 업로드해주세요.',
}

/**
 * 기술적 메시지를 사용자 친화적 메시지로 변환
 */
const translateErrorMessage = (message: string): string => {
  // 정확히 일치하는 메시지 먼저 확인
  if (ERROR_MESSAGE_MAP[message]) {
    return ERROR_MESSAGE_MAP[message]
  }

  // 부분 일치 확인 (대소문자 무시)
  const lowerMessage = message.toLowerCase()
  for (const [key, value] of Object.entries(ERROR_MESSAGE_MAP)) {
    if (lowerMessage.includes(key.toLowerCase())) {
      return value
    }
  }

  // 일반적인 패턴 변환
  if (lowerMessage.includes('timeout') || lowerMessage.includes('timed out')) {
    return '요청 처리 시간이 초과되었습니다. 다시 시도해주세요.'
  }
  if (lowerMessage.includes('network') || lowerMessage.includes('connection')) {
    return '네트워크 연결을 확인해주세요.'
  }
  if (lowerMessage.includes('permission') || lowerMessage.includes('denied')) {
    return '접근 권한이 없습니다.'
  }
  if (lowerMessage.includes('not found')) {
    return '요청한 항목을 찾을 수 없습니다.'
  }

  return message
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

    // 일반 서버 응답 메시지 (사용자 친화적으로 변환)
    const detail = axiosError.response?.data?.detail
    const message = axiosError.response?.data?.message
    const errorMsg = axiosError.response?.data?.error
    const serverMsg = detail || message || errorMsg
    if (serverMsg) {
      return translateErrorMessage(serverMsg)
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
    // AbortError는 타임아웃
    if (error.name === 'AbortError') {
      return '요청 시간이 초과되었습니다. 다시 시도해주세요.'
    }
    return translateErrorMessage(error.message) || fallbackMessage
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
