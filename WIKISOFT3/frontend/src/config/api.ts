/**
 * API configuration with environment-aware fallbacks
 */

// Base API URL - fallback to /api for production builds
export const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

// Agent endpoints
export const AGENT_CHAT_URL = `${API_BASE_URL}/agent/chat`
export const AGENT_VALIDATE_URL = `${API_BASE_URL}/agent/validate`

// Validation endpoints
export const AUTO_VALIDATE_URL = `${API_BASE_URL}/auto-validate`
export const BATCH_VALIDATE_URL = `${API_BASE_URL}/batch-validate`

// Export endpoints
export const EXPORT_ERRORS_URL = `${API_BASE_URL}/export/errors`
export const EXPORT_SHEET_URL = `${API_BASE_URL}/export/sheet`

// Windmill endpoints
export const WINDMILL_LATEST_URL = `${API_BASE_URL}/windmill/latest`

/**
 * Check if running in development mode
 */
export const isDevelopment = import.meta.env.MODE === 'development'

/**
 * Log configuration on startup (development only)
 */
if (isDevelopment) {
  console.log('[Config] API Base URL:', API_BASE_URL)
}
