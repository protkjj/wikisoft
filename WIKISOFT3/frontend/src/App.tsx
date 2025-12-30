import { useState, useEffect } from 'react'
import './App.css'
import { api } from './api'
import ChatBot from './ChatBot'
import FloatingChat from './components/FloatingChat'
import ManualMapping from './ManualMapping'
import ThemeToggle from './components/ThemeToggle'
import type { DiagnosticQuestion, AutoValidateResult, CompanyInfo, HeaderMatch } from './types'

type Step = 'onboarding' | 'questions' | 'upload' | 'results' | 'download'

function App() {
  const [currentStep, setCurrentStep] = useState<Step>('onboarding')
  const [questions, setQuestions] = useState<DiagnosticQuestion[]>([])
  const [answers, setAnswers] = useState<Record<string, string | number>>({})
  const [file, setFile] = useState<File | null>(null)
  const [validationResult, setValidationResult] = useState<AutoValidateResult | null>(null)
  const [companyInfo, setCompanyInfo] = useState<CompanyInfo>({
    company_name: '',
    phone: '',
    email: '',
    작성기준일: new Date().toISOString().split('T')[0].replace(/-/g, '')
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string>('')
  const [showManualMapping, setShowManualMapping] = useState(false)
  const [currentMatches, setCurrentMatches] = useState<HeaderMatch[]>([])

  // 초기 로드: 진단 질문 조회
  useEffect(() => {
    loadQuestions()
  }, [])

  const loadQuestions = async () => {
    try {
      setLoading(true)
      const data = await api.getDiagnosticQuestions()
      setQuestions(data.questions)
      setError('')
    } catch (err) {
      setError('진단 질문을 불러오는데 실패했습니다. 서버가 실행 중인지 확인해주세요.')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleAnswerChange = (questionId: string, value: string | number) => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: value
    }))
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
    }
  }

  const handleValidate = async () => {
    if (!file) {
      alert('명부 파일을 선택해주세요')
      return
    }

    // 필수 답변 체크
    const unansweredQuestions = questions.filter(q => !answers[q.id])
    if (unansweredQuestions.length > 0) {
      alert(`${unansweredQuestions.length}개의 질문에 답변이 없습니다. 모든 질문에 답변해주세요.`)
      return
    }

    console.log('🚀 검증 시작:', { file: file.name, answers })

    try {
      setLoading(true)
      setError('')
      console.log('📤 API 호출 중... (진단 답변 포함)')
      // 진단 질문 답변을 함께 전송하여 교차 검증
      const result = await api.validateWithRoster(file, answers)
      console.log('✅ API 응답:', result)
      setValidationResult(result)
      
      // 매칭 결과 저장 (수동 매핑용)
      if (result.steps?.matches?.matches) {
        setCurrentMatches(result.steps.matches.matches)
      }
      
      setCurrentStep('results')
      console.log('✅ Step 변경 완료: results')
    } catch (err: any) {
      console.error('❌ 검증 오류:', err)
      console.error('❌ 오류 상세:', err.response?.data)
      setError(err.response?.data?.detail || '검증 중 오류가 발생했습니다.')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = async () => {
    if (!validationResult) return

    try {
      setLoading(true)
      // Excel 파일 다운로드
      const blob = await api.downloadExcel()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `검증결과_${new Date().toISOString().split('T')[0]}.xlsx`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      
      setCurrentStep('download')
    } catch (err: any) {
      console.error('Excel 다운로드 오류:', err)
      // 실패시 JSON 다운로드로 폴백
      const dataStr = JSON.stringify(validationResult, null, 2)
      const blob = new Blob([dataStr], { type: 'application/json' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `검증결과_${new Date().toISOString().split('T')[0]}.json`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      
      setCurrentStep('download')
    } finally {
      setLoading(false)
    }
  }

  const getStepStatus = (step: Step): 'active' | 'completed' | 'pending' => {
    const steps: Step[] = ['questions', 'upload', 'results', 'download']
    const currentIndex = steps.indexOf(currentStep)
    const stepIndex = steps.indexOf(step)
    
    if (stepIndex < currentIndex) return 'completed'
    if (stepIndex === currentIndex) return 'active'
    return 'pending'
  }

  const categoryLabels: Record<string, string> = {
    'data_quality': '📊 데이터 품질',
    'financial_assumptions': '💰 재무 가정',
    'retirement_settings': '🏖️ 퇴직 설정',
    'headcount_aggregates': '👥 인원 집계',
    'amount_aggregates': '💵 금액 집계'
  }

  return (
    <div className="app">
      {currentStep !== 'onboarding' && (
        <>
          <header className="header">
            <div className="header-content">
              <h1>🏢 WIKISOFT3</h1>
              <p>퇴직급여채무 명부 AI 자동검증 시스템</p>
            </div>
            <ThemeToggle />
          </header>

          {/* 진행 단계 표시 */}
          <div className="steps">
        <div className={`step ${getStepStatus('questions')}`}>
          <div className="step-number">1</div>
          <h3>진단 질문</h3>
          <p>13개 질문에 답변</p>
        </div>
        <div className={`step ${getStepStatus('upload')}`}>
          <div className="step-number">2</div>
          <h3>파일 업로드</h3>
          <p>명부 Excel 선택</p>
        </div>
        <div className={`step ${getStepStatus('results')}`}>
          <div className="step-number">3</div>
          <h3>검증 결과</h3>
          <p>경고 및 차이 확인</p>
        </div>
        <div className={`step ${getStepStatus('download')}`}>
          <div className="step-number">4</div>
          <h3>파일 다운로드</h3>
          <p>최종 Excel 생성</p>
        </div>
      </div>
        </>
      )}

      {error && (
        <div className="content-section" style={{ background: 'rgba(239, 68, 68, 0.1)', borderColor: '#ef4444' }}>
          <p style={{ color: '#ef4444', fontSize: '1.1rem' }}>❌ {error}</p>
        </div>
      )}

      {loading && (
        <div className="loading">
          <div className="spinner"></div>
          <p>처리 중입니다...</p>
        </div>
      )}

      {/* Step 0: 온보딩 화면 */}
      {currentStep === 'onboarding' && (
        <div className="onboarding">
          <header className="onboarding-header-bar">
            <div className="onboarding-header-title">WIKISOFT</div>
            <ThemeToggle />
          </header>
          <div className="onboarding-header">
            <h1 className="onboarding-title">
              <span className="title-wiki">WIKI</span><span className="title-soft">SOFT</span>
            </h1>
            <p className="onboarding-subtitle">퇴직급여채무 AI 자동검증</p>
          </div>

          <h2 className="onboarding-section-title">시작하기 전에</h2>

          <div className="onboarding-steps">
            <div className="onboarding-card">
              <div className="card-number">1</div>
              <div className="card-icon">
                <svg width="80" height="80" viewBox="0 0 80 80" fill="none">
                  <rect x="20" y="10" width="40" height="50" rx="4" stroke="currentColor" strokeWidth="3"/>
                  <path d="M30 25 L35 30 L50 20" stroke="currentColor" strokeWidth="3" fill="none"/>
                  <line x1="30" y1="35" x2="50" y2="35" stroke="currentColor" strokeWidth="2"/>
                  <line x1="30" y1="42" x2="50" y2="42" stroke="currentColor" strokeWidth="2"/>
                  <line x1="30" y1="49" x2="45" y2="49" stroke="currentColor" strokeWidth="2"/>
                </svg>
              </div>
              <h3 className="card-title">진단 질문</h3>
              <p className="card-description">13개 질문에 답변</p>
            </div>

            <div className="onboarding-card">
              <div className="card-number">2</div>
              <div className="card-icon">
                <svg width="80" height="80" viewBox="0 0 80 80" fill="none">
                  <path d="M25 35 L25 60 C25 62 26 63 28 63 L52 63 C54 63 55 62 55 60 L55 35" stroke="currentColor" strokeWidth="3" fill="none"/>
                  <path d="M20 35 L40 20 L60 35" stroke="currentColor" strokeWidth="3" fill="none"/>
                  <path d="M35 45 L35 30 L45 30 L45 45" stroke="currentColor" strokeWidth="3"/>
                  <polyline points="38,38 40,40 42,36" stroke="currentColor" strokeWidth="2" fill="none"/>
                </svg>
              </div>
              <h3 className="card-title">파일 업로드</h3>
              <p className="card-description">Excel 명부 파일 업로드</p>
            </div>

            <div className="onboarding-card">
              <div className="card-number">3</div>
              <div className="card-icon">
                <svg width="80" height="80" viewBox="0 0 80 80" fill="none">
                  <circle cx="35" cy="35" r="18" stroke="currentColor" strokeWidth="3" fill="none"/>
                  <line x1="48" y1="48" x2="60" y2="60" stroke="currentColor" strokeWidth="3" strokeLinecap="round"/>
                  <path d="M28 35 L32 39 L42 29" stroke="currentColor" strokeWidth="2.5" fill="none" strokeLinecap="round"/>
                  <circle cx="55" cy="25" r="4" fill="currentColor"/>
                  <circle cx="60" cy="30" r="3" fill="currentColor" opacity="0.7"/>
                </svg>
              </div>
              <h3 className="card-title">AI 검증</h3>
              <p className="card-description">자동 컬럼 매핑 및 이상 탐지</p>
            </div>

            <div className="onboarding-card">
              <div className="card-number">4</div>
              <div className="card-icon">
                <svg width="80" height="80" viewBox="0 0 80 80" fill="none">
                  <rect x="25" y="20" width="30" height="35" rx="2" stroke="currentColor" strokeWidth="3" fill="none"/>
                  <line x1="30" y1="28" x2="50" y2="28" stroke="currentColor" strokeWidth="2"/>
                  <line x1="30" y1="35" x2="50" y2="35" stroke="currentColor" strokeWidth="2"/>
                  <line x1="30" y1="42" x2="45" y2="42" stroke="currentColor" strokeWidth="2"/>
                  <path d="M35 50 L40 55 L45 50" stroke="currentColor" strokeWidth="3" fill="none" strokeLinecap="round"/>
                  <line x1="40" y1="55" x2="40" y2="65" stroke="currentColor" strokeWidth="3" strokeLinecap="round"/>
                </svg>
              </div>
              <h3 className="card-title">결과 다운로드</h3>
              <p className="card-description">검증된 Excel 파일 다운로드</p>
            </div>
          </div>

          <div className="onboarding-footer">
            <div className="file-requirements">
              <div className="file-icon">
                <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
                  <path d="M10 5 L25 5 L30 10 L30 35 L10 35 Z" stroke="currentColor" strokeWidth="2" fill="none"/>
                  <path d="M25 5 L25 10 L30 10" stroke="currentColor" strokeWidth="2" fill="none"/>
                  <text x="15" y="23" fontSize="8" fill="currentColor" fontWeight="bold">.xlsx</text>
                  <text x="15" y="30" fontSize="8" fill="currentColor" fontWeight="bold">.xls</text>
                </svg>
              </div>
              <div className="file-text">
                <strong>준비물</strong>
                <p>.xlsx 또는 .xls 파일</p>
              </div>
            </div>
            <button 
              className="btn-start"
              onClick={() => {
                setCurrentStep('questions')
                loadQuestions()
              }}
            >
              시작하기
            </button>
          </div>
        </div>
      )}

      {/* Step 1: 진단 질문 (챗봇) */}
      {currentStep === 'questions' && !loading && questions.length > 0 && (
        <ChatBot
          questions={questions}
          onComplete={(completedAnswers) => {
            setAnswers(completedAnswers)
            setTimeout(() => setCurrentStep('upload'), 1000)
          }}
          onBack={() => {
            setAnswers({})
            loadQuestions()
          }}
        />
      )}

      {/* Step 2: 파일 업로드 */}
      {currentStep === 'upload' && (
        <div className="content-section">
          <div className="upload-container">
            <div className="upload-dropzone">
              <div className="upload-icon">
                <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
                  <path d="M16 48 L16 16 C16 13 18 12 20 12 L36 12 L48 24 L48 48 C48 50 46 51 44 51 L20 51 C18 51 16 50 16 48Z" stroke="currentColor" strokeWidth="2" fill="none"/>
                  <path d="M36 12 L36 24 L48 24" stroke="currentColor" strokeWidth="2" fill="none"/>
                  <line x1="32" y1="32" x2="32" y2="44" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                  <polyline points="24,36 32,44 40,36" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round"/>
                </svg>
              </div>
              <h3 className="upload-title">Excel 파일을 여기에 드래그하세요</h3>
              <div className="file-formats">
                <span className="format-badge">.xlsx</span>
                <span className="format-badge">.xls</span>
              </div>
              <input
                type="file"
                accept=".xlsx,.xls"
                onChange={handleFileChange}
                className="file-input-hidden"
                id="file-input"
              />
              <label htmlFor="file-input" className="file-input-label">또는 파일 선택하기</label>
            </div>

            {file && (
              <div className="file-selected">
                <div className="file-check">✓</div>
                <div className="file-details">
                  <p className="file-name">{file.name}</p>
                  <p className="file-size">({(file.size / 1024).toFixed(1)} KB)</p>
                </div>
              </div>
            )}
          </div>

          <div className="upload-actions">
            <button
              className="btn-secondary"
              onClick={() => {
                console.log('⬅️ 이전 버튼 클릭')
                setCurrentStep('questions')
              }}
            >
              ← 이전
            </button>
            <button
              className="btn-primary"
              onClick={() => {
                console.log('🔘 검증 시작 버튼 클릭됨!')
                console.log('파일:', file)
                console.log('답변:', answers)
                console.log('disabled:', !file || loading)
                handleValidate()
              }}
              disabled={!file || loading}
            >
              검증 시작 →
            </button>
          </div>
        </div>
      )}

      {/* Step 3: 검증 결과 */}
      {currentStep === 'results' && validationResult && (
        <div className="results-page">
          <div className="results-container">
            {/* 헤더 */}
            <div className="results-header">
              <h2 className="results-title">✅ 검증 결과</h2>
            </div>

            {/* 메트릭 카드들 */}
            <div className="result-summary">
              <div className={`result-stat ${validationResult.status === 'ok' ? 'success' : 'error'}`}>
              <div className="result-stat-value">
                {validationResult.status === 'ok' ? '완료' : '오류'}
              </div>
              <div className="result-stat-label">검증 상태</div>
            </div>
            <div className="result-stat success">
              <div className="result-stat-value">
                {(validationResult.confidence?.score * 100).toFixed(0)}%
              </div>
              <div className="result-stat-label">신뢰도</div>
            </div>
            <div className="result-stat warning">
              <div className="result-stat-value">
                {validationResult.anomalies?.anomalies?.length ?? 0}
              </div>
              <div className="result-stat-label">이상 탐지</div>
            </div>
            <div className="result-stat">
              <div className="result-stat-value">
                {validationResult.steps?.parsed_summary?.row_count ?? 0}
              </div>
              <div className="result-stat-label">분석 행 수</div>
            </div>
          </div>

          {/* 컬럼 매핑 테이블 */}
          {validationResult.steps?.matches && (
            <div className="mapping-section">
              <div className="section-header">
                <h3>컬럼 매핑 결과</h3>
                <button
                  className="btn-secondary"
                  style={{ padding: '0.5rem 1rem', fontSize: '0.9rem' }}
                  onClick={() => setShowManualMapping(true)}
                >
                  수동 매핑
                </button>
              </div>
              <table className="mapping-table">
                <thead>
                  <tr>
                    <th>소스 컬럼</th>
                    <th></th>
                    <th>타겟 컬럼</th>
                    <th>매핑 신뢰도</th>
                    <th>상태</th>
                  </tr>
                </thead>
                <tbody>
                  {(currentMatches.length > 0 ? currentMatches : validationResult.steps.matches.matches || []).slice(0, 6).map((match: HeaderMatch, idx: number) => (
                    <tr key={idx}>
                      <td>{match.source}</td>
                      <td className="arrow">→</td>
                      <td>{match.target || '-'}</td>
                      <td className={`mapping-confidence ${match.confidence >= 0.95 ? 'high' : match.confidence >= 0.85 ? 'medium' : 'low'}`}>
                        {match.confidence > 0 && match.confidence < 1 ? `${Math.round(match.confidence * 100)}%` : match.target ? '100%' : '-'}
                      </td>
                      <td className="mapping-status">
                        {match.target ? <span style={{ color: 'var(--success)' }}>✓ 일치</span> : <span style={{ color: 'var(--error)' }}>✕</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* 이상 목록 */}
          {validationResult.anomalies?.detected && validationResult.anomalies.anomalies.length > 0 && (
            <div className="anomalies-section">
              <h3>🤖 AI 분석 결과</h3>
              <div className="anomalies-list">
                {/* AI 질문 (고객 확인 필요) */}
                {validationResult.anomalies.anomalies
                  .filter((a: any) => a.severity === 'question')
                  .map((anomaly: any, idx: number) => (
                  <div key={`q-${idx}`} className="anomaly-item question">
                    <div className="anomaly-title">
                      <span className="anomaly-icon">❓</span>
                      <strong>AI 질문:</strong> {anomaly.message}
                    </div>
                    <div className="ai-question-actions">
                      <button className="btn-ai-answer" onClick={() => {
                        // FloatingChat 열기
                        const chatBtn = document.querySelector('.floating-chat-button') as HTMLButtonElement;
                        if (chatBtn) chatBtn.click();
                      }}>💬 AI와 대화로 답변</button>
                    </div>
                  </div>
                ))}
                
                {/* 오류/경고 */}
                {validationResult.anomalies.anomalies
                  .filter((a: any) => a.severity !== 'question')
                  .map((anomaly: any, idx: number) => (
                  <div key={idx} className={`anomaly-item ${anomaly.severity === 'error' ? 'error' : anomaly.severity === 'warning' ? 'warning' : 'info'}`}>
                    <div className="anomaly-title">
                      <span className="anomaly-icon">
                        {anomaly.severity === 'error' ? '🔴' : anomaly.severity === 'warning' ? '🟠' : 'ℹ️'}
                      </span>
                      {anomaly.message}
                    </div>
                    {anomaly.auto_fix && (
                      <div className="anomaly-fix">
                        💡 수정 제안: {anomaly.auto_fix}
                      </div>
                    )}
                    <div className="anomaly-details">
                      유형: {anomaly.type}
                    </div>
                  </div>
                ))}
              </div>
              {validationResult.anomalies.recommendation && (
                <div style={{ marginTop: '1.5rem', padding: '1rem', background: 'var(--success-light)', borderRadius: 'var(--radius-md)', color: 'var(--success)' }}>
                  💡 {validationResult.anomalies.recommendation}
                </div>
              )}
            </div>
          )}

          {/* 파싱 요약 */}
          {validationResult.steps?.parsed_summary && (
            <div style={{ marginTop: '2rem' }}>
              <h3 style={{ marginBottom: '1rem' }}>📊 파싱 정보</h3>
              <p style={{ color: 'var(--text-secondary)' }}>
                인식된 헤더: {validationResult.steps.parsed_summary.headers.slice(0, 5).join(', ')}
                {validationResult.steps.parsed_summary.headers.length > 5 && ` 외 ${validationResult.steps.parsed_summary.headers.length - 5}개`}
              </p>
            </div>
          )}

          <div className="actions">
            <button
              className="btn-secondary"
              onClick={() => {
                setCurrentStep('upload')
                setValidationResult(null)
              }}
            >
              ← 다시 검증
            </button>
            <button
              className="btn-primary"
              onClick={handleDownload}
              disabled={loading}
            >
              📥 Excel 다운로드 →
            </button>
          </div>
        </div>
      </div>
      )}

      {/* Step 4: 완료 */}
      {currentStep === 'download' && (
        <div className="completion-page">
          <div className="completion-container">
            {/* 스텝 표시 */}
            <div className="completion-steps">
              {['upload', 'results', 'download'].map((step) => (
                <div key={step} className="completion-step completed">
                  <div className="step-check">✓</div>
                </div>
              ))}
            </div>

            {/* 완료 메시지 */}
            <div className="completion-message">
              <div className="completion-icon">✓</div>
              <h1>검증 완료</h1>
              <p>Excel 파일이 준비되었습니다</p>
            </div>

            {/* 검증 정보 테이블 */}
            <div className="completion-info">
              <table className="completion-table">
                <tbody>
                  <tr>
                    <td className="label">검증 일시</td>
                    <td>{new Date().toLocaleString('ko-KR')}</td>
                  </tr>
                  <tr>
                    <td className="label">처리된 행</td>
                    <td>{validationResult?.steps?.parsed_summary?.row_count ?? 0}</td>
                  </tr>
                  <tr>
                    <td className="label">신뢰도</td>
                    <td>{Math.round((validationResult?.steps?.matches?.matches?.reduce((sum: number, m: HeaderMatch) => sum + m.confidence, 0) ?? 0) / (validationResult?.steps?.matches?.matches?.length ?? 1) * 100)}%</td>
                  </tr>
                  <tr>
                    <td className="label">파일명</td>
                    <td>검증결과_{new Date().toISOString().split('T')[0]}.xlsx</td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* 액션 버튼 */}
            <div className="completion-actions">
              <button
                className="btn-primary"
                onClick={() => {
                  handleDownload()
                }}
                disabled={loading}
              >
                ⬇️ 다운로드
              </button>
              <button
                className="btn-secondary"
                onClick={() => {
                  setCurrentStep('questions')
                  setAnswers({})
                  setFile(null)
                  setValidationResult(null)
                  setCurrentMatches([])
                  setCompanyInfo({
                    company_name: '',
                    phone: '',
                    email: '',
                    작성기준일: new Date().toISOString().split('T')[0].replace(/-/g, '')
                  })
                }}
              >
                새로 시작
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 수동 매핑 모달 */}
      {showManualMapping && currentMatches.length > 0 && (
        <ManualMapping
          matches={currentMatches}
          onConfirm={(updatedMatches) => {
            setCurrentMatches(updatedMatches)
            setShowManualMapping(false)
            // TODO: 업데이트된 매핑으로 재검증 가능
          }}
          onCancel={() => setShowManualMapping(false)}
        />
      )}

      {/* Floating AI Chat */}
      <FloatingChat />
    </div>
  )
}

export default App

