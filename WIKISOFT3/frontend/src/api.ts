import axios from 'axios'
import type { DiagnosticQuestionsResponse, ValidationResult, AutoValidateResult } from './types'

const API_BASE = '/api'

export const api = {
  // 24개 진단 질문 조회 (v3)
  async getDiagnosticQuestions(): Promise<DiagnosticQuestionsResponse> {
    const response = await axios.get(`${API_BASE}/diagnostic-questions`)
    return response.data
  },

  // 파일 자동 검증 (v3 - Tool Registry 사용)
  async autoValidate(file: File): Promise<AutoValidateResult> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await axios.post(`${API_BASE}/auto-validate`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  },

  // 명부 파일 + 챗봇 답변으로 교차 검증
  async validateWithRoster(
    file: File,
    chatbotAnswers: Record<string, string | number>
  ): Promise<AutoValidateResult> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('chatbot_answers', JSON.stringify(chatbotAnswers))

    console.log('📤 진단 답변 전송:', chatbotAnswers)

    const response = await axios.post(`${API_BASE}/auto-validate`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
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
  async downloadExcel(): Promise<Blob> {
    const response = await axios.get(`${API_BASE}/auto-validate/download-excel`, {
      responseType: 'blob'
    })
    return response.data
  },

  // 최종 수정본 다운로드 (매핑 완료된 데이터)
  async downloadFinalData(): Promise<Blob> {
    const response = await axios.get(`${API_BASE}/auto-validate/download-final-data`, {
      responseType: 'blob'
    })
    return response.data
  }
}
