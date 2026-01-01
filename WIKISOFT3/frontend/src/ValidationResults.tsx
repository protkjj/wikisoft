import { useMemo } from 'react'
import type { AutoValidateResultExtended, HeaderMatch } from './types'
import './ValidationResults.css'

interface ValidationResultsProps {
  result: AutoValidateResultExtended
  onDownloadExcel: () => void
  onDownloadFinalData: () => void
  onManualMapping: () => void
  onBack: () => void
}

export default function ValidationResults({
  result,
  onDownloadExcel,
  onDownloadFinalData,
  onManualMapping,
  onBack
}: ValidationResultsProps) {
  // 신뢰도 계산
  const confidenceScore = useMemo(() => {
    const score = result.confidence?.score ?? 0
    return Math.round(score * 100)
  }, [result.confidence])

  // 등급 결정
  const confidenceGrade = useMemo(() => {
    if (confidenceScore >= 95) return { grade: 'A', label: '매우 높음', color: '#51CF66' }
    if (confidenceScore >= 80) return { grade: 'B', label: '높음', color: '#69DB7C' }
    if (confidenceScore >= 70) return { grade: 'C', label: '보통', color: '#FFE066' }
    if (confidenceScore >= 50) return { grade: 'D', label: '낮음', color: '#FF8787' }
    return { grade: 'F', label: '매우 낮음', color: '#FF6B6B' }
  }, [confidenceScore])

  // 통계 계산
  const stats = useMemo(() => {
    const matches: HeaderMatch[] = result.steps?.matches?.matches || []
    const anomalies = result.anomalies?.anomalies || []
    const rowCount = result.steps?.parsed_summary?.row_count || 0
    
    const mappedCount = matches.filter((m: HeaderMatch) => m.target && !m.unmapped).length
    const totalHeaders = matches.length
    const errorCount = anomalies.filter((a) => a.severity === 'error' || a.severity === 'high').length
    const warningCount = anomalies.filter((a) => a.severity === 'warning' || a.severity === 'medium').length
    
    return {
      rowCount,
      mappedCount,
      totalHeaders,
      mappingRate: totalHeaders > 0 ? Math.round((mappedCount / totalHeaders) * 100) : 0,
      errorCount,
      warningCount,
      anomalyCount: anomalies.length
    }
  }, [result])

  // 매칭 결과 분류
  const matchGroups = useMemo(() => {
    const matches: HeaderMatch[] = result.steps?.matches?.matches || []
    return {
      mapped: matches.filter((m: HeaderMatch) => m.target && !m.unmapped),
      unmapped: matches.filter((m: HeaderMatch) => !m.target || m.unmapped),
      lowConfidence: matches.filter((m: HeaderMatch) => m.target && (m.confidence || 0) < 0.7)
    }
  }, [result])

  return (
    <div className="validation-results">
      {/* 헤더 */}
      <div className="results-header">
        <button className="back-btn" onClick={onBack}>
          ← 돌아가기
        </button>
        <h2>검증 결과</h2>
        <div className="header-actions">
          <button className="action-btn secondary" onClick={onManualMapping}>
            ✏️ 수동 매핑
          </button>
          <button className="action-btn primary" onClick={onDownloadFinalData}>
            📄 최종 수정본
          </button>
          <button className="action-btn primary" onClick={onDownloadExcel}>
            📊 검증 리포트
          </button>
        </div>
      </div>

      {/* 메인 대시보드 */}
      <div className="results-dashboard">
        {/* 신뢰도 게이지 */}
        <div className="confidence-card">
          <h3>신뢰도</h3>
          <div className="confidence-gauge">
            <svg viewBox="0 0 200 120" className="gauge-svg">
              {/* 배경 아크 */}
              <path
                d="M 20 100 A 80 80 0 0 1 180 100"
                fill="none"
                stroke="var(--bg-secondary)"
                strokeWidth="16"
                strokeLinecap="round"
              />
              {/* 값 아크 */}
              <path
                d="M 20 100 A 80 80 0 0 1 180 100"
                fill="none"
                stroke={confidenceGrade.color}
                strokeWidth="16"
                strokeLinecap="round"
                strokeDasharray={`${(confidenceScore / 100) * 251.2} 251.2`}
              />
            </svg>
            <div className="gauge-value">
              <span className="score">{confidenceScore}%</span>
              <span className="grade" style={{ color: confidenceGrade.color }}>
                {confidenceGrade.label}
              </span>
            </div>
          </div>
        </div>

        {/* 통계 카드들 */}
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon">📊</div>
            <div className="stat-info">
              <span className="stat-value">{stats.rowCount.toLocaleString()}</span>
              <span className="stat-label">분석 행</span>
            </div>
          </div>
          
          <div className="stat-card">
            <div className="stat-icon">🔗</div>
            <div className="stat-info">
              <span className="stat-value">{stats.mappedCount}/{stats.totalHeaders}</span>
              <span className="stat-label">컬럼 매핑</span>
            </div>
          </div>
          
          <div className="stat-card error">
            <div className="stat-icon">🔴</div>
            <div className="stat-info">
              <span className="stat-value">{stats.errorCount}</span>
              <span className="stat-label">오류</span>
            </div>
          </div>
          
          <div className="stat-card warning">
            <div className="stat-icon">🟠</div>
            <div className="stat-info">
              <span className="stat-value">{stats.warningCount}</span>
              <span className="stat-label">경고</span>
            </div>
          </div>
        </div>
      </div>

      {/* 컬럼 매핑 테이블 */}
      <div className="section">
        <h3>📋 컬럼 매핑 결과</h3>
        <div className="mapping-table-container">
          <table className="mapping-table">
            <thead>
              <tr>
                <th>원본 헤더</th>
                <th>매칭된 필드</th>
                <th>신뢰도</th>
                <th>상태</th>
              </tr>
            </thead>
            <tbody>
              {matchGroups.mapped.map((match: HeaderMatch, idx: number) => (
                <tr key={idx} className="mapped">
                  <td>{match.source}</td>
                  <td>{match.target}</td>
                  <td>
                    <div className="confidence-bar">
                      <div 
                        className="confidence-fill"
                        style={{ 
                          width: `${(match.confidence || 0) * 100}%`,
                          backgroundColor: (match.confidence || 0) >= 0.8 ? '#51CF66' : '#FFE066'
                        }}
                      />
                      <span>{Math.round((match.confidence || 0) * 100)}%</span>
                    </div>
                  </td>
                  <td><span className="status-badge success">✅ 매핑됨</span></td>
                </tr>
              ))}
              {matchGroups.unmapped.map((match: HeaderMatch, idx: number) => (
                <tr key={`unmapped-${idx}`} className="unmapped">
                  <td>{match.source}</td>
                  <td className="empty">—</td>
                  <td>—</td>
                  <td><span className="status-badge error">❌ 미매핑</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 이상 탐지 목록 */}
      {stats.anomalyCount > 0 && (
        <div className="section">
          <h3>⚠️ 이상 탐지 ({stats.anomalyCount}건)</h3>
          <div className="anomaly-list">
            {(result.anomalies?.anomalies || []).map((anomaly, idx: number) => (
              <div 
                key={idx} 
                className={`anomaly-item ${anomaly.severity || 'info'}`}
              >
                <div className="anomaly-icon">
                  {anomaly.severity === 'error' || anomaly.severity === 'high' ? '🔴' :
                   anomaly.severity === 'warning' || anomaly.severity === 'medium' ? '🟠' :
                   anomaly.severity === 'question' ? '❓' : 'ℹ️'}
                </div>
                <div className="anomaly-content">
                  <span className="anomaly-type">{anomaly.type}</span>
                  <span className="anomaly-message">{anomaly.message}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 검증 오류/경고 상세 목록 */}
      {(result.steps?.validation?.errors?.length > 0 || result.steps?.validation?.warnings?.length > 0) && (
        <div className="section">
          <h3>🔍 검증 상세 결과</h3>
          
          {/* 오류 목록 */}
          {result.steps?.validation?.errors?.length > 0 && (
            <div className="validation-errors">
              <h4>🔴 오류 ({result.steps.validation.errors.length}건)</h4>
              <div className="error-list">
                {result.steps.validation.errors.slice(0, 20).map((error: any, idx: number) => (
                  <div key={idx} className="validation-item error">
                    <span className="item-row">행 {error.row}</span>
                    <span className="item-field">{error.field}</span>
                    <span className="item-message">{error.message}</span>
                    {error.reason && <span className="item-reason">💡 {error.reason}</span>}
                  </div>
                ))}
                {result.steps.validation.errors.length > 20 && (
                  <div className="more-items">... 외 {result.steps.validation.errors.length - 20}건 더</div>
                )}
              </div>
            </div>
          )}

          {/* 경고 목록 */}
          {result.steps?.validation?.warnings?.length > 0 && (
            <div className="validation-warnings">
              <h4>🟠 경고 ({result.steps.validation.warnings.length}건)</h4>
              <div className="warning-list">
                {result.steps.validation.warnings.slice(0, 20).map((warning: any, idx: number) => (
                  <div key={idx} className="validation-item warning">
                    {typeof warning === 'string' ? (
                      <span className="item-message">{warning}</span>
                    ) : (
                      <>
                        {warning.row && <span className="item-row">행 {warning.row}</span>}
                        {warning.field && <span className="item-field">{warning.field}</span>}
                        <span className="item-message">{warning.message || warning}</span>
                      </>
                    )}
                  </div>
                ))}
                {result.steps.validation.warnings.length > 20 && (
                  <div className="more-items">... 외 {result.steps.validation.warnings.length - 20}건 더</div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* AI 에이전트 추론 과정 (있으면) */}
      {result.agent_reasoning && result.agent_reasoning.length > 0 && (
        <div className="section">
          <h3>🤖 AI 에이전트 추론 과정</h3>
          <div className="reasoning-timeline">
            {result.agent_reasoning.map((step: any, idx: number) => (
              <div key={idx} className="reasoning-step">
                <div className="step-number">{step.step}</div>
                <div className="step-content">
                  <div className="step-thought">{step.thought}</div>
                  <div className="step-action">
                    Action: <code>{step.action}</code>
                    {step.result_success ? ' ✅' : ' ❌'}
                    {step.confidence > 0 && (
                      <span className="step-confidence">
                        ({Math.round(step.confidence * 100)}%)
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 추천 액션 */}
      <div className="section recommendation">
        <h3>📌 권장 조치</h3>
        <div className="recommendation-content">
          {confidenceScore >= 95 ? (
            <p>✅ <strong>자동 완료 가능</strong>: 신뢰도가 매우 높습니다. Excel을 다운로드하여 바로 사용할 수 있습니다.</p>
          ) : confidenceScore >= 80 ? (
            <p>🔍 <strong>검토 권장</strong>: 신뢰도가 높지만, 경고 항목을 한번 확인해주세요.</p>
          ) : confidenceScore >= 50 ? (
            <p>⚠️ <strong>수동 검토 필요</strong>: 일부 매핑이 불확실합니다. 수동 매핑 버튼을 클릭하여 확인해주세요.</p>
          ) : (
            <p>🚨 <strong>주의 필요</strong>: 매핑 신뢰도가 낮습니다. 파일 형식을 확인하고 수동 매핑을 진행해주세요.</p>
          )}
        </div>
      </div>
    </div>
  )
}
