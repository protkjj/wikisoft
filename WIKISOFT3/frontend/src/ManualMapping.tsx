import { useState } from 'react'
import type { HeaderMatch, StandardField } from './types'
import './ManualMapping.css'

// 표준 필드 목록 (백엔드와 동기화 필요)
const STANDARD_FIELDS: StandardField[] = [
  { name: '사원번호', description: '직원을 고유하게 식별하는 번호', required: true, aliases: ['직원번호', '사번'], sheet: '재직자' },
  { name: '이름', description: '직원의 성명', required: true, aliases: ['성명', 'name'], sheet: '재직자' },
  { name: '생년월일', description: '직원의 출생일자', required: true, aliases: ['출생일', 'birth_date'], sheet: '재직자' },
  { name: '성별', description: '성별', required: true, aliases: ['gender', 'sex'], sheet: '재직자' },
  { name: '입사일자', description: '회사에 입사한 날짜', required: true, aliases: ['입사일', 'hire_date'], sheet: '재직자' },
  { name: '종업원구분', description: '직원 유형 구분', required: true, aliases: ['직원구분', 'employee_type'], sheet: '재직자' },
  { name: '기준급여', description: '퇴직금 계산 기준 급여', required: true, aliases: ['급여', 'salary'], sheet: '재직자' },
  { name: '제도구분', description: '퇴직연금 제도 유형', required: true, aliases: ['연금제도', 'DB', 'DC'], sheet: '재직자' },
  { name: '퇴직일자', description: '퇴직 날짜', required: false, aliases: ['퇴사일', 'termination_date'], sheet: '퇴직자' },
  { name: '전화번호', description: '연락처', required: false, aliases: ['연락처', 'phone'], sheet: '재직자' },
  { name: '이메일', description: '이메일 주소', required: false, aliases: ['email', 'e-mail'], sheet: '재직자' },
  { name: '부서', description: '소속 부서', required: false, aliases: ['부서명', 'department'], sheet: '재직자' },
  { name: '직급', description: '직급/직책', required: false, aliases: ['직책', 'position'], sheet: '재직자' },
]

interface ManualMappingProps {
  matches: HeaderMatch[]
  onConfirm: (updatedMatches: HeaderMatch[]) => void
  onCancel: () => void
}

export default function ManualMapping({ matches, onConfirm, onCancel }: ManualMappingProps) {
  const [localMatches, setLocalMatches] = useState<HeaderMatch[]>(matches)
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null)

  // 매핑 변경
  const handleMappingChange = (index: number, targetField: string | null) => {
    setLocalMatches(prev => prev.map((m, i) => 
      i === index 
        ? { ...m, target: targetField, confidence: targetField ? 1.0 : 0, unmapped: !targetField }
        : m
    ))
  }

  // 드래그 시작
  const handleDragStart = (index: number) => {
    setDraggedIndex(index)
  }

  // 드래그 오버
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
  }

  // 드롭
  const handleDrop = (targetField: string) => {
    if (draggedIndex !== null) {
      handleMappingChange(draggedIndex, targetField)
      setDraggedIndex(null)
    }
  }

  // 매핑 통계
  const mappedCount = localMatches.filter(m => m.target).length
  const unmappedCount = localMatches.filter(m => !m.target).length
  const requiredFields = STANDARD_FIELDS.filter(f => f.required)
  const mappedRequired = requiredFields.filter(f => 
    localMatches.some(m => m.target === f.name)
  )
  const missingRequired = requiredFields.filter(f => 
    !localMatches.some(m => m.target === f.name)
  )

  // 이미 매핑된 필드들
  const usedTargets = new Set(localMatches.filter(m => m.target).map(m => m.target))

  // 사용 가능한 필드들
  const availableFields = STANDARD_FIELDS.filter(f => !usedTargets.has(f.name))

  return (
    <div className="manual-mapping-overlay">
      <div className="manual-mapping-modal">
        <div className="mapping-header">
          <h2>📋 수동 헤더 매핑</h2>
          <p>고객 헤더를 표준 필드에 매핑하세요. 드래그하거나 선택하세요.</p>
        </div>

        {/* 통계 */}
        <div className="mapping-stats">
          <div className="stat-item">
            <span className="stat-value">{mappedCount}</span>
            <span className="stat-label">매핑됨</span>
          </div>
          <div className="stat-item warning">
            <span className="stat-value">{unmappedCount}</span>
            <span className="stat-label">미매핑</span>
          </div>
          <div className="stat-item success">
            <span className="stat-value">{mappedRequired.length}/{requiredFields.length}</span>
            <span className="stat-label">필수 필드</span>
          </div>
        </div>

        {/* 필수 필드 누락 경고 */}
        {missingRequired.length > 0 && (
          <div className="missing-warning">
            ⚠️ 필수 필드 누락: {missingRequired.map(f => f.name).join(', ')}
          </div>
        )}

        {/* 매핑 테이블 */}
        <div className="mapping-container">
          {/* 왼쪽: 고객 헤더 */}
          <div className="column-list">
            <h3>고객 헤더</h3>
            <div className="header-list">
              {localMatches.map((match, index) => (
                <div 
                  key={index}
                  className={`header-item ${match.target ? 'mapped' : 'unmapped'} ${draggedIndex === index ? 'dragging' : ''}`}
                  draggable
                  onDragStart={() => handleDragStart(index)}
                >
                  <div className="header-source">
                    <span className="drag-handle">⋮⋮</span>
                    <span className="header-name">{match.source}</span>
                  </div>
                  {match.target && (
                    <div className="header-target">
                      → {match.target}
                      <button 
                        className="remove-btn"
                        onClick={() => handleMappingChange(index, null)}
                      >
                        ✕
                      </button>
                    </div>
                  )}
                  {!match.target && (
                    <select 
                      className="field-select"
                      value=""
                      onChange={(e) => handleMappingChange(index, e.target.value || null)}
                    >
                      <option value="">선택하세요...</option>
                      {availableFields.map(field => (
                        <option key={field.name} value={field.name}>
                          {field.name} {field.required ? '(필수)' : ''}
                        </option>
                      ))}
                    </select>
                  )}
                  {match.confidence > 0 && match.confidence < 1 && (
                    <span className="confidence-badge">
                      {Math.round(match.confidence * 100)}%
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* 오른쪽: 표준 필드 */}
          <div className="field-list">
            <h3>표준 필드</h3>
            <div className="field-grid">
              {STANDARD_FIELDS.map(field => {
                const isMapped = usedTargets.has(field.name)
                return (
                  <div 
                    key={field.name}
                    className={`field-item ${field.required ? 'required' : ''} ${isMapped ? 'mapped' : 'available'}`}
                    onDragOver={handleDragOver}
                    onDrop={() => !isMapped && handleDrop(field.name)}
                  >
                    <span className="field-name">
                      {field.name}
                      {field.required && <span className="required-mark">*</span>}
                    </span>
                    <span className="field-desc">{field.description}</span>
                    {isMapped && <span className="mapped-mark">✓</span>}
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        {/* 버튼 */}
        <div className="mapping-actions">
          <button className="cancel-btn" onClick={onCancel}>
            취소
          </button>
          <button 
            className="confirm-btn"
            onClick={() => onConfirm(localMatches)}
            disabled={missingRequired.length > 0}
          >
            매핑 확인 ({mappedCount}개)
          </button>
        </div>
      </div>
    </div>
  )
}
