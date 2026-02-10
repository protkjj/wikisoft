import { useMemo } from 'react'
import type { AutoValidateResult } from '../types'

export interface EditableError {
  severity: 'error' | 'warning'
  message: string
  row?: number
  field?: string
  emp_info?: string
  source?: string        // "layer1" | "layer2" | "ai"
  question_id?: string   // Layer 2 질문 ID (e.g. "2-a.1")
  user_input?: number | string    // 사용자 입력값
  calculated?: number | string    // 명부 계산값
}

/**
 * Extract editable errors and warnings from validation result
 * @param validationResult - Validation result from API
 * @returns Array of editable errors/warnings
 */
export const useValidationErrors = (
  validationResult: AutoValidateResult | null
): EditableError[] => {
  return useMemo(() => {
    if (!validationResult) return []

    const allResults: EditableError[] = []

    // Errors from validation (행 번호 유무와 상관없이 모두 포함)
    validationResult.steps?.validation?.errors?.forEach((err) => {
      allResults.push({
        severity: 'error',
        message: err.message || err.error || err.reason || '알 수 없는 오류',
        row: err.row ?? undefined,  // null -> undefined로 변환
        field: err.field || err.column,
        emp_info: err.emp_info,
        source: err.source,
        question_id: err.question_id,
        user_input: err.user_input,
        calculated: err.calculated,
      })
    })

    // Warnings from validation (행 번호 유무와 상관없이 모두 포함)
    validationResult.steps?.validation?.warnings?.forEach((warn) => {
      allResults.push({
        severity: 'warning',
        message: warn.message || warn.warning || warn.reason || '알 수 없는 경고',
        row: warn.row ?? undefined,  // null -> undefined로 변환
        field: warn.field || warn.column,
        emp_info: warn.emp_info,
        source: warn.source,
        question_id: warn.question_id,
        user_input: warn.user_input,
        calculated: warn.calculated,
      })
    })

    return allResults
  }, [validationResult])
}
