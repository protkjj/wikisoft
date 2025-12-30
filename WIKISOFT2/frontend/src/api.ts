import axios from 'axios'
import type { DiagnosticQuestionsResponse, ValidationResult, CompanyInfo } from './types'

const API_BASE = '/api'

export const api = {
  // 28개 진단 질문 조회
  async getDiagnosticQuestions(): Promise<DiagnosticQuestionsResponse> {
    const response = await axios.get(`${API_BASE}/diagnostic-questions`)
    return response.data
  },

  // 명부 파일 + 챗봇 답변으로 교차 검증
  async validateWithRoster(
    file: File,
    chatbotAnswers: Record<string, string | number>
  ): Promise<ValidationResult> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('chatbot_answers', JSON.stringify(chatbotAnswers))

    const response = await axios.post(`${API_BASE}/validate-with-roster`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  },

  // 검증 완료 세션으로 최종 Excel 생성
  async generateWithValidation(
    sessionId: string,
    companyInfo: CompanyInfo
  ): Promise<Blob> {
    const formData = new URLSearchParams()
    formData.append('session_id', sessionId)
    formData.append('company_name', companyInfo.company_name)
    formData.append('phone', companyInfo.phone)
    formData.append('email', companyInfo.email)
    formData.append('작성기준일', companyInfo.작성기준일)

    const response = await axios.post(`${API_BASE}/generate-with-validation`, formData, {
      responseType: 'blob',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    })
    return response.data
  }
}
