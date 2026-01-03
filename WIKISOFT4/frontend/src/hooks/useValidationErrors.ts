import { useMemo } from 'react'
import type { AutoValidateResult } from '../types'

export interface EditableError {
  severity: 'error' | 'warning'
  message: string
  row?: number
  field?: string
  emp_info?: string
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

    // Errors from validation
    validationResult.steps?.validation?.errors?.forEach((err) => {
      // 행 번호가 있는 에러만 수정 가능
      if (err.row !== undefined) {
        allResults.push({
          severity: 'error',
          message: err.message || err.error || err.reason || '알 수 없는 오류',
          row: err.row,
          field: err.field || err.column,
          emp_info: err.emp_info
        })
      }
    })

    // Warnings from validation
    validationResult.steps?.validation?.warnings?.forEach((warn) => {
      // 행 번호가 있는 경고만 표시
      if (warn.row !== undefined) {
        allResults.push({
          severity: 'warning',
          message: warn.message || warn.warning || warn.reason || '알 수 없는 경고',
          row: warn.row,
          field: warn.field || warn.column,
          emp_info: warn.emp_info
        })
      }
    })

    return allResults
  }, [validationResult])
}
