import axios from 'axios'
import type { DiagnosticQuestionsResponse, AutoValidateResult, ValidationRun } from './types'
import { API_BASE_URL } from './config/api'

const API_BASE = API_BASE_URL

export const api = {

  // 13개 진단 질문 조회 (v3)
  async getDiagnosticQuestions(): Promise<DiagnosticQuestionsResponse> {
    const response = await axios.get(`${API_BASE}/diagnostic-questions`)
    return response.data
  },

  // 파일 자동 검증 (v3 - Tool Registry 사용)
  async autoValidate(file: File): Promise<{ result: AutoValidateResult; sessionId: string | null }> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await axios.post(`${API_BASE}/auto-validate`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    return {
      result: response.data,
      sessionId: response.data.session_id || null
    }
  },

  // 명부 파일 + 챗봇 답변으로 교차 검증
  async validateWithRoster(
    file: File,
    chatbotAnswers: Record<string, string | number>
  ): Promise<{ result: AutoValidateResult; sessionId: string | null }> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('chatbot_answers', JSON.stringify(chatbotAnswers))

    const response = await axios.post(`${API_BASE}/auto-validate`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    return {
      result: response.data,
      sessionId: response.data.session_id || null
    }
  },

  // 배치 처리 상태 조회 (v3)
  async getBatchStatus(jobId: string): Promise<any> {
    const response = await axios.get(`${API_BASE}/batch-validate/${jobId}`)
    return response.data
  },

  // 헬스 체크
  async health(): Promise<{ status: string; version: string }> {
    const response = await axios.get(`${API_BASE}/health`)
    return response.data
  },

  // Excel 파일 다운로드 (검증 리포트)
  async downloadExcel(sessionId: string): Promise<Blob> {
    if (!sessionId) {
      throw new Error('세션이 없습니다. 먼저 파일을 검증해주세요.')
    }

    const response = await axios.get(`${API_BASE}/auto-validate/download-excel`, {
      responseType: 'blob',
      headers: {
        'X-Session-Id': sessionId
      }
    })
    return response.data
  },

  // 최종 수정본 다운로드 (매핑 완료된 데이터)
  async downloadFinalData(sessionId: string): Promise<Blob> {
    if (!sessionId) {
      throw new Error('세션이 없습니다. 먼저 파일을 검증해주세요.')
    }

    const response = await axios.get(`${API_BASE}/auto-validate/download-final-data`, {
      responseType: 'blob',
      headers: {
        'X-Session-Id': sessionId
      }
    })
    return response.data
  },

  // Windmill 최근 실행 기록 조회
  async getLatestRuns(limit = 5): Promise<ValidationRun[]> {
    const response = await axios.get(`${API_BASE}/windmill/latest`, {
      params: { limit }
    })
    return response.data?.runs ?? []
  },

  // 오류 목록만 엑셀로 내보내기
  async downloadErrorsExcel(
    filename: string,
    errors: Array<{ row?: number; field?: string; message: string; severity: 'error' | 'warning' }>
  ): Promise<Blob> {
    const response = await axios.post(`${API_BASE}/export/errors`, {
      filename,
      errors
    }, {
      responseType: 'blob'
    })
    return response.data
  }
}
