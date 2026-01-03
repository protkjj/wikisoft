import { useState } from 'react'
import type { HeaderMatch } from './types'
import { STANDARD_FIELDS } from './constants/fields'
import './ManualMapping.css'

interface ManualMappingProps {
  matches: HeaderMatch[]
  onConfirm: (updatedMatches: HeaderMatch[]) => void
  onCancel: () => void
}

// 무시할 헤더 키워드 (종업원구분, 제도구분 등 의미있는 '구분'은 제외)
const IGNORE_KEYWORDS = ['참고사항', '비고', '메모', 'note', 'remark', 'comment', 'unnamed', 'column', '컬럼']

function shouldIgnoreHeader(header: string): boolean {
  const lower = header.toLowerCase().trim()
  // 완전히 무시할 패턴
  if (lower.startsWith('unnamed') || lower === '') return true
  // 키워드 매칭
  return IGNORE_KEYWORDS.some(kw => lower.includes(kw.toLowerCase()))
}

export default function ManualMapping({ matches, onConfirm, onCancel }: ManualMappingProps) {
  // ignored 컬럼은 제외하고 시작
  const filteredMatches = matches.filter(m => !shouldIgnoreHeader(m.source))
  const [localMatches, setLocalMatches] = useState<HeaderMatch[]>(filteredMatches)
  const [draggedItem, setDraggedItem] = useState<{ type: 'source' | 'target', index: number, value: string } | null>(null)
  const [dropTarget, setDropTarget] = useState<{ type: 'source' | 'target', index: number } | null>(null)

  // 매핑 변경
  const handleMappingChange = (index: number, targetField: string | null) => {
    setLocalMatches(prev => prev.map((m, i) => 
      i === index 
        ? { ...m, target: targetField, confidence: targetField ? 1.0 : 0, unmapped: !targetField, skipped: false }
        : m
    ))
  }

  // 소스 헤더 드래그 시작
  const handleSourceDragStart = (e: React.DragEvent, index: number, source: string) => {
    e.dataTransfer.effectAllowed = 'move'
    setDraggedItem({ type: 'source', index, value: source })
    // 드래그 이미지 설정
    const elem = e.target as HTMLElement
    elem.classList.add('dragging')
  }

  // 타겟 필드 드래그 시작 (사용 가능한 필드 목록에서)
  const handleTargetDragStart = (e: React.DragEvent, fieldName: string) => {
    e.dataTransfer.effectAllowed = 'copy'
    setDraggedItem({ type: 'target', index: -1, value: fieldName })
  }

  // 드래그 종료
  const handleDragEnd = (e: React.DragEvent) => {
    const elem = e.target as HTMLElement
    elem.classList.remove('dragging')
    setDraggedItem(null)
    setDropTarget(null)
  }

  // 드롭 영역 오버
  const handleDragOver = (e: React.DragEvent, type: 'source' | 'target', index: number) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
    setDropTarget({ type, index })
  }

  // 드롭 영역 떠남
  const handleDragLeave = () => {
    setDropTarget(null)
  }

  // 드롭 처리
  const handleDrop = (e: React.DragEvent, targetIndex: number) => {
    e.preventDefault()
    
    if (draggedItem?.type === 'target') {
      // 타겟 필드를 소스 행에 드롭
      handleMappingChange(targetIndex, draggedItem.value)
    } else if (draggedItem?.type === 'source') {
      // 소스 행 순서 변경 (선택적)
      // 현재는 순서 변경 안 함
    }
    
    setDraggedItem(null)
    setDropTarget(null)
  }

  // 매핑 해제
  const handleUnmap = (index: number) => {
    setLocalMatches(prev => prev.map((m, i) => 
      i === index 
        ? { ...m, target: null, confidence: 0, unmapped: true, skipped: false }
        : m
    ))
  }

  // 건너뛰기 설정
  const handleSkip = (index: number) => {
    setLocalMatches(prev => prev.map((m, i) => 
      i === index 
        ? { ...m, target: null, confidence: 0, unmapped: true, skipped: true }
        : m
    ))
  }

  // 매핑 통계
  const mappedCount = localMatches.filter(m => m.target).length
  const skippedCount = localMatches.filter(m => m.skipped).length
  const unmappedCount = localMatches.filter(m => !m.target && !m.skipped).length
  const requiredFields = STANDARD_FIELDS.filter(f => f.required)
  const mappedRequired = requiredFields.filter(f => 
    localMatches.some(m => m.target === f.name)
  )
  const missingRequired = requiredFields.filter(f => 
    !localMatches.some(m => m.target === f.name)
  )

  // 이미 매핑된 필드들
  const usedTargets = new Set(localMatches.filter(m => m.target).map(m => m.target))

  return (
    <div className="manual-mapping-overlay">
      <div className="manual-mapping-modal">
        <div className="mapping-header">
          <h2>📋 수동 헤더 매핑</h2>
          <p>오른쪽 표준 필드를 왼쪽 소스 헤더로 드래그하거나, 드롭다운에서 선택하세요.</p>
        </div>

        {/* 통계 */}
        <div className="mapping-stats">
          <div className="stat-item">
            <span className="stat-value">{mappedCount}</span>
            <span className="stat-label">매핑됨</span>
          </div>
          <div className="stat-item" style={{ background: 'rgba(156, 163, 175, 0.1)' }}>
            <span className="stat-value">{skippedCount}</span>
            <span className="stat-label">건너뛰기</span>
          </div>
          <div className="stat-item warning">
            <span className="stat-value">{unmappedCount}</span>
            <span className="stat-label">미처리</span>
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

        {/* 드래그앤드롭 영역 */}
        <div className="dnd-container">
          {/* 왼쪽: 소스 헤더 목록 */}
          <div className="dnd-source-panel">
            <h4>📄 소스 헤더 (고객 파일)</h4>
            <div className="dnd-source-list">
              {localMatches.map((match, index) => (
                <div
                  key={index}
                  className={`dnd-source-item ${match.target ? 'mapped' : match.skipped ? 'skipped' : 'unmapped'} ${dropTarget?.index === index ? 'drop-hover' : ''}`}
                  draggable
                  onDragStart={(e) => handleSourceDragStart(e, index, match.source)}
                  onDragEnd={handleDragEnd}
                  onDragOver={(e) => handleDragOver(e, 'source', index)}
                  onDragLeave={handleDragLeave}
                  onDrop={(e) => handleDrop(e, index)}
                >
                  <div className="source-info">
                    <span className="drag-handle">⋮⋮</span>
                    <span className="source-name">{match.source}</span>
                  </div>
                  <div className="source-mapping">
                    {match.target ? (
                      <div className="mapped-target">
                        <span className="target-badge">→ {match.target}</span>
                        <button className="unmap-btn" onClick={() => handleUnmap(index)} title="매핑 해제">×</button>
                      </div>
                    ) : match.skipped ? (
                      <div className="skipped-label">
                        <span>건너뛰기</span>
                        <button className="unmap-btn" onClick={() => handleUnmap(index)} title="취소">×</button>
                      </div>
                    ) : (
                      <div className="unmapped-actions">
                        <span className="drop-hint">여기에 드롭</span>
                        <button className="skip-btn" onClick={() => handleSkip(index)} title="건너뛰기">⊘</button>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 오른쪽: 표준 필드 목록 */}
          <div className="dnd-target-panel">
            <h4>🎯 표준 필드 (드래그하여 매핑)</h4>
            <div className="dnd-target-list">
              {STANDARD_FIELDS.map((field) => {
                const isUsed = usedTargets.has(field.name)
                return (
                  <div
                    key={field.name}
                    className={`dnd-target-item ${isUsed ? 'used' : 'available'} ${field.required ? 'required' : ''}`}
                    draggable={!isUsed}
                    onDragStart={(e) => handleTargetDragStart(e, field.name)}
                    onDragEnd={handleDragEnd}
                  >
                    <div className="target-info">
                      <span className={`field-name ${field.required ? 'required' : ''}`}>
                        {field.name}
                        {field.required && <span className="required-star">*</span>}
                      </span>
                      <span className="field-desc">{field.description}</span>
                    </div>
                    <div className="target-status">
                      {isUsed ? (
                        <span className="used-badge">✓ 사용됨</span>
                      ) : (
                        <span className="drag-hint">⇄</span>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        {/* 빠른 선택 (드롭다운 방식도 유지) */}
        <details className="quick-select-section">
          <summary>📝 드롭다운으로 매핑하기 (펼치기)</summary>
          <div className="mapping-table-container">
            <table className="mapping-table">
              <thead>
                <tr>
                  <th>소스 헤더</th>
                  <th></th>
                  <th>타겟 필드</th>
                  <th>신뢰도</th>
                </tr>
              </thead>
              <tbody>
                {localMatches.map((match, index) => (
                  <tr key={index} className={!match.target ? 'unmapped' : ''}>
                    <td className="source-cell">{match.source}</td>
                    <td className="arrow-cell">→</td>
                    <td className="target-cell">
                      <select 
                        className="target-select"
                        value={match.target || (match.skipped ? '__skip__' : '')}
                        onChange={(e) => {
                          const val = e.target.value
                          if (val === '__skip__') {
                            handleSkip(index)
                          } else if (val === '') {
                            handleUnmap(index)
                          } else {
                            handleMappingChange(index, val)
                          }
                        }}
                      >
                        <option value="">[선택]</option>
                        <option value="__skip__">⊘ 건너뛰기</option>
                        {STANDARD_FIELDS.map(field => (
                          <option 
                            key={field.name} 
                            value={field.name}
                            disabled={usedTargets.has(field.name) && match.target !== field.name}
                          >
                            {field.name} {field.required ? '(필수)' : ''}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="confidence-cell">
                      {match.target ? (
                        <span className="confidence-badge">{Math.round(match.confidence * 100)}%</span>
                      ) : match.skipped ? (
                        <span className="skipped-badge">✓ 생략</span>
                      ) : (
                        <span className="unmapped-badge">--</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>

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
            확인 {unmappedCount > 0 && `(${unmappedCount}개 미처리)`}
          </button>
        </div>
      </div>
    </div>
  )
}

