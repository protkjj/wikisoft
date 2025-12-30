// API 타입 정의
export interface DiagnosticQuestion {
  id: string
  category: string
  question: string
  type: 'number' | 'text' | 'choice'
  unit?: string
  choices?: string[]
  validate_against?: string
}

export interface DiagnosticQuestionsResponse {
  questions: DiagnosticQuestion[]
  summary: {
    total: number
    categories: Record<string, number>
  }
}

export interface ValidationWarning {
  question_id: string
  severity: 'low' | 'medium' | 'high'
  message: string
  user_input: string
  calculated: string
  diff: number
  diff_percent: number
}

export interface ValidationResult {
  validation: {
    status: 'passed' | 'failed'
    total_checks: number
    passed: number
    warnings: ValidationWarning[]
  }
  calculated_aggregates: {
    counts_I26_I39: number[]
    sums_I40_I51: number[]
  }
  parsing_warnings: Array<{
    severity: string
    message: string
  }>
  session_id: string
  message: string
}

export interface CompanyInfo {
  company_name: string
  phone: string
  email: string
  작성기준일: string
}
