import axios from 'axios'
import { API_BASE_URL } from '../config/api'

const API_BASE = `${API_BASE_URL}/v4/admin`

// 인증 헤더 가져오기
const getAuthHeaders = () => {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

// Types
export interface UserInfo {
  id: string
  email: string
  name: string
  role: string
  is_active: boolean
  scopes: string[]
}

export interface CreateUserRequest {
  username: string
  email: string
  password: string
  name: string
  role?: string
}

export interface UpdateUserRequest {
  email?: string
  name?: string
  role?: string
  is_active?: boolean
  password?: string
}

export interface AuditEntry {
  id: string
  timestamp: string
  action: string
  user_id: string | null
  user_email: string | null
  user_role: string | null
  resource_type: string | null
  resource_id: string | null
  ip_address: string | null
  user_agent: string | null
  details: Record<string, any>
  success: boolean
  error_message: string | null
}

export interface AuditLogQuery {
  action?: string
  user_id?: string
  start_date?: string
  end_date?: string
  limit?: number
  offset?: number
}

export interface AuditLogResponse {
  entries: AuditEntry[]
  total: number
  limit: number
  offset: number
}

export interface TrainingFile {
  filename: string
  file_type: string
  size_bytes: number
  created_at: string
  modified_at: string
}

export interface TrainingFileDetail extends TrainingFile {
  content: Record<string, any>
}

export interface TrainingDataStats {
  total_files: number
  total_size_bytes: number
  type_counts: Record<string, number>
}

export interface TrainingDataResponse {
  files: TrainingFile[]
  stats: TrainingDataStats
}

export interface SystemSettingsData {
  minimum_wage: number
  retirement_age: number
  validation_confidence_threshold: number
  max_file_size_mb: number
  allowed_extensions: string[]
}

// API functions
export const adminApi = {
  // User Management
  async getUsers(): Promise<UserInfo[]> {
    const response = await axios.get(`${API_BASE}/users`, { headers: getAuthHeaders() })
    return response.data
  },

  async createUser(data: CreateUserRequest): Promise<UserInfo> {
    const response = await axios.post(`${API_BASE}/users`, data, { headers: getAuthHeaders() })
    return response.data
  },

  async updateUser(userId: string, data: UpdateUserRequest): Promise<UserInfo> {
    const response = await axios.put(`${API_BASE}/users/${userId}`, data, { headers: getAuthHeaders() })
    return response.data
  },

  async deleteUser(userId: string): Promise<void> {
    await axios.delete(`${API_BASE}/users/${userId}`, { headers: getAuthHeaders() })
  },

  // Audit Log
  async getAuditLogs(query: AuditLogQuery = {}): Promise<AuditLogResponse> {
    const params = new URLSearchParams()
    if (query.action) params.append('action', query.action)
    if (query.user_id) params.append('user_id', query.user_id)
    if (query.start_date) params.append('start_date', query.start_date)
    if (query.end_date) params.append('end_date', query.end_date)
    if (query.limit) params.append('limit', query.limit.toString())
    if (query.offset) params.append('offset', query.offset.toString())

    const response = await axios.get(`${API_BASE}/audit?${params.toString()}`, { headers: getAuthHeaders() })
    return response.data
  },

  // Training Data
  async getTrainingData(fileType?: string): Promise<TrainingDataResponse> {
    const params = fileType ? `?file_type=${fileType}` : ''
    const response = await axios.get(`${API_BASE}/training-data${params}`, { headers: getAuthHeaders() })
    return response.data
  },

  async getTrainingDataFile(filename: string): Promise<TrainingFileDetail> {
    const response = await axios.get(`${API_BASE}/training-data/${filename}`, { headers: getAuthHeaders() })
    return response.data
  },

  async deleteTrainingData(filename: string): Promise<void> {
    await axios.delete(`${API_BASE}/training-data/${filename}`, { headers: getAuthHeaders() })
  },

  // System Settings
  async getSettings(): Promise<SystemSettingsData> {
    const response = await axios.get(`${API_BASE}/settings`, { headers: getAuthHeaders() })
    return response.data
  },

  async updateSettings(data: Partial<SystemSettingsData>): Promise<SystemSettingsData> {
    const response = await axios.put(`${API_BASE}/settings`, data, { headers: getAuthHeaders() })
    return response.data
  },
}
