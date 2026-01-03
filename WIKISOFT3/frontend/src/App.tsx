import { useState, useEffect, useRef } from 'react'
import './App.css'
import { api } from './api'
import ChatBot from './ChatBot'
import FloatingChat, { FloatingChatHandle } from './components/FloatingChat'
import ManualMapping from './ManualMapping'
import SheetEditorPro from './components/SheetEditorPro'
// ValidationResults 컴포넌트는 현재 사용하지 않음
// import ValidationResults from './ValidationResults'
import ThemeToggle from './components/ThemeToggle'
import { useSession } from './contexts/SessionContext'
import { downloadBlob, generateTimestampedFilename } from './utils/download'
import { getRequiredFieldLabels } from './constants/fields'
import { handleError } from './utils/errorHandler'
import { useValidationErrors } from './hooks/useValidationErrors'
import type { DiagnosticQuestion, AutoValidateResult, HeaderMatch, ValidationRun } from './types'

type Step = 'onboarding' | 'questions' | 'upload' | 'results' | 'download'

// 수정할 에러 정보
interface EditTarget {
  row: number
  field: string
  message: string
}

function App() {
  const { session, setSession, clearSession } = useSession()

  const [currentStep, setCurrentStep] = useState<Step>('onboarding')
  const [questions, setQuestions] = useState<DiagnosticQuestion[]>([])
  const [answers, setAnswers] = useState<Record<string, string | number>>({})
  const [file, setFile] = useState<File | null>(null)
  const [validationResult, setValidationResult] = useState<AutoValidateResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string>('')
  const [showManualMapping, setShowManualMapping] = useState(false)
  const [currentMatches, setCurrentMatches] = useState<HeaderMatch[]>([])

  // SheetEditor 상태
  const [showSheetEditor, setShowSheetEditor] = useState(false)
  const [editTarget, setEditTarget] = useState<EditTarget | null>(null)
  const [sheetData, setSheetData] = useState<string[][]>([])
  const [latestRuns, setLatestRuns] = useState<ValidationRun[]>([])
  const [runsLoading, setRunsLoading] = useState(false)

  // 검증 결과에서 수정 가능한 에러/경고만 추출
  const editableErrors = useValidationErrors(validationResult)

  const chatRef = useRef<FloatingChatHandle>(null)

  // 초기 로드: 진단 질문 조회
  useEffect(() => {
    loadQuestions()
    loadLatestRuns()
  }, [])

  const loadQuestions = async () => {
    try {
      setLoading(true)
      const data = await api.getDiagnosticQuestions()
      setQuestions(data.questions)
      setError('')
    } catch (err) {
      const message = handleError('DiagnosticQuestions', err, '진단 질문을 불러오는데 실패했습니다. 서버가 실행 중인지 확인해주세요.')
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  const loadLatestRuns = async () => {
    try {
      setRunsLoading(true)
      const runs = await api.getLatestRuns(6)
      setLatestRuns(runs)
    } catch (err) {
      handleError('LatestRuns', err, '최근 실행 이력 로드 실패')
    } finally {
      setRunsLoading(false)
    }
  }

  // TODO: 진단 질문 기능 복원 시 사용
  // const handleAnswerChange = (questionId: string, value: string | number) => {
  //   setAnswers(prev => ({ ...prev, [questionId]: value }))
  // }

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

    // 필수 답변 체크 (0도 유효한 답변으로 처리)
    const unansweredQuestions = questions.filter(q => answers[q.id] === undefined)
    if (unansweredQuestions.length > 0) {
      alert(`${unansweredQuestions.length}개의 질문에 답변이 없습니다. 모든 질문에 답변해주세요.`)
      return
    }

    try {
      setLoading(true)
      setError('')
      // 진단 질문 답변을 함께 전송하여 교차 검증
      const { result, sessionId } = await api.validateWithRoster(file, answers)
      if (sessionId) {
        setSession(sessionId)
      }
      setValidationResult(result)
      
      // 매칭 결과 저장 (수동 매핑용)
      if (result.steps?.matches?.matches) {
        setCurrentMatches(result.steps.matches.matches)
      }
      
      // 스프레드시트 데이터 저장 (수정용)
      if (result.steps?.parsed_summary) {
        const headers = result.steps.parsed_summary.headers || []
        // API에서 all_rows 제공
        const stepsAny = result.steps as any
        const rows = stepsAny.all_rows || []
        if (rows.length > 0) {
          setSheetData([headers, ...rows.map((row: any) => 
            headers.map((h: string) => String(row[h] ?? ''))
          )])
        }
      }
      
      setCurrentStep('results')
    } catch (err) {
      const message = handleError('Validation', err, '검증 중 오류가 발생했습니다.')
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = async () => {
    if (!validationResult || !session.sessionId) return

    try {
      setLoading(true)
      const blob = await api.downloadExcel(session.sessionId)
      const filename = generateTimestampedFilename('검증리포트', 'xlsx')
      downloadBlob(blob, filename)
      setCurrentStep('download')
    } catch (err) {
      const message = handleError('DownloadExcel', err, 'Excel 리포트 다운로드에 실패했습니다.')
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  const handleDownloadFinalData = async () => {
    if (!validationResult || !session.sessionId) return

    try {
      setLoading(true)
      const blob = await api.downloadFinalData(session.sessionId)
      const filename = generateTimestampedFilename('최종수정본', 'xlsx')
      downloadBlob(blob, filename)
    } catch (err) {
      const message = handleError('DownloadFinalData', err, '최종 수정본 다운로드에 실패했습니다.')
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  // 오류 목록만 다운로드
  const handleDownloadErrorsOnly = async () => {
    if (!validationResult || !file) return

    try {
      setLoading(true)

      // editableErrors 사용 (validationResult 변경 시 자동 계산됨)
      const errorsToExport = editableErrors.filter((e) => e.severity === 'error').map(err => ({
        row: err.row ?? 0,
        field: err.field ?? '',
        message: err.message,
        severity: err.severity
      }))

      if (errorsToExport.length === 0) {
        alert('다운로드할 오류가 없습니다.')
        return
      }

      const blob = await api.downloadErrorsExcel(file.name, errorsToExport)
      const filename = generateTimestampedFilename('의심목록', 'xlsx')
      downloadBlob(blob, filename)
    } catch (err) {
      const message = handleError('DownloadErrors', err, '의심 목록 다운로드에 실패했습니다.')
      setError(message)
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

  const formatConfidence = (value?: number | null) => {
    if (value === null || value === undefined) return '-'
    return value > 1 ? `${Math.round(value)}%` : `${Math.round(value * 100)}%`
  }

  // TODO: 카테고리 레이블 사용 시 복원
  // const categoryLabels: Record<string, string> = {
  //   'data_quality': '📊 데이터 품질',
  //   ...
  // }

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

      {loading && currentStep !== 'upload' && (
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

          {/* 시작하기 버튼 + 준비물 - 최근 검증상태 위로 이동 */}
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

          {/* 최근 검증 상태 - 하단으로 이동 */}
          <div style={{ marginTop: '1.5rem', padding: '1rem', border: '1px solid var(--border-color, #e5e7eb)', borderRadius: '12px', background: 'var(--bg-secondary, #f9fafb)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
              <h3 style={{ margin: 0 }}>최근 검증 상태 (Windmill)</h3>
              {runsLoading && <span style={{ color: 'var(--text-secondary)' }}>불러오는 중...</span>}
            </div>
            {latestRuns.length === 0 ? (
              <p style={{ color: 'var(--text-secondary)' }}>최근 실행 기록이 없습니다.</p>
            ) : (
              <div style={{ display: 'grid', gap: '0.5rem' }}>
                {latestRuns.map((run, idx) => (
                  <div
                    key={`${run.run_id || run.timestamp}-${idx}`}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '0.75rem',
                      borderRadius: '10px',
                      background: 'var(--bg-primary, #fff)',
                      border: '1px solid var(--border-color, #e5e7eb)'
                    }}
                  >
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                      <span style={{ fontWeight: 600 }}>
                        {run.action || run.status}
                      </span>
                      <span style={{ color: 'var(--text-secondary)' }}>
                        {new Date(run.timestamp).toLocaleString('ko-KR')}
                      </span>
                    </div>
                    <div style={{ textAlign: 'right', display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                      <span style={{ fontWeight: 600 }}>
                        {formatConfidence(run.confidence)}
                      </span>
                      <span style={{ color: 'var(--text-secondary)' }}>
                        {run.auto_approve ? '자동 승인' : '수동 검토'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
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

            {loading && (
              <div className="file-processing">
                <div className="spinner-small"></div>
                <span>처리 중...</span>
              </div>
            )}
          </div>

          <div className="upload-actions">
            <button
              className="btn-secondary"
              onClick={() => {
                setCurrentStep('questions')
              }}
            >
              ← 이전
            </button>
            <button
              className="btn-primary"
              onClick={() => {
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
              <div className="result-stat-label">정상 데이터 비율</div>
            </div>
            <div className="result-stat warning">
              <div className="result-stat-value">
                {(validationResult.anomalies?.anomalies?.length ?? 0) + 
                 (validationResult.steps?.validation?.errors?.length ?? 0) + 
                 (validationResult.steps?.validation?.warnings?.length ?? 0)}
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
                    <th>소스 헤더</th>
                    <th></th>
                    <th>타겟 필드</th>
                    <th>매칭율</th>
                  </tr>
                </thead>
                <tbody>
                  {(currentMatches.length > 0 ? currentMatches : validationResult.steps.matches.matches || [])
                    .sort((a: HeaderMatch, b: HeaderMatch) => {
                      // 필수 필드 먼저 표시
                      const requiredFields = getRequiredFieldLabels();
                      const aRequired = requiredFields.includes(a.target || '');
                      const bRequired = requiredFields.includes(b.target || '');
                      if (aRequired && !bRequired) return -1;
                      if (!aRequired && bRequired) return 1;
                      return 0;
                    })
                    .map((match: HeaderMatch, idx: number) => {
                      const requiredFields = getRequiredFieldLabels();
                      const isRequired = requiredFields.includes(match.target || '');
                      return (
                    <tr key={idx}>
                      <td>{match.source}</td>
                      <td className="arrow">→</td>
                      <td>
                        {match.target ? (
                          <span className={isRequired ? 'required-field' : 'optional-field'}>
                            {match.target} {isRequired ? '(필수)' : '[선택]'}
                          </span>
                        ) : '-'}
                      </td>
                      <td className={`mapping-confidence ${match.confidence >= 0.95 ? 'high' : match.confidence >= 0.85 ? 'medium' : 'low'}`}>
                        {match.confidence > 0 && match.confidence < 1 ? `${Math.round(match.confidence * 100)}%` : match.target ? '100%' : '-'}
                      </td>
                    </tr>
                      );
                    })}
                </tbody>
              </table>
            </div>
          )}

          {/* 통합 검증 결과 (validation + anomalies 합쳐서 중복 제거) */}
          {(() => {
            // 모든 결과 수집
            const allResults: Array<{
              severity: 'error' | 'warning' | 'info' | 'question',
              message: string,
              details?: string,
              key: string,
              row?: number,
              field?: string,
              emp_info?: string
            }> = [];
            const seenMessages = new Set<string>();

            // validation.errors & warnings (use hook)
            const rawErrors = useValidationErrors(validationResult);
            rawErrors.forEach((item, idx) => {
              const msg = `${item.emp_info || `행 ${item.row}`}: ${item.field} - ${item.message}`;
              if (!seenMessages.has(msg)) {
                seenMessages.add(msg);
                allResults.push({
                  severity: item.severity,
                  message: msg,
                  details: undefined,
                  key: `${item.severity}-${idx}`,
                  row: item.row,
                  field: item.field,
                  emp_info: item.emp_info
                });
              }
            });

            // anomalies (중복 체크)
            validationResult.anomalies?.anomalies?.forEach((a: any, idx: number) => {
              const msg = a.message;
              // 이미 유사한 메시지가 있으면 스킵 (예: "중복 사원번호 2건"이 이미 상세 정보로 있으면)
              const isDuplicate = Array.from(seenMessages).some(seen => 
                seen.includes(msg) || msg.includes('중복') && seen.includes('중복')
              );
              if (!isDuplicate && !seenMessages.has(msg)) {
                seenMessages.add(msg);
                const severity = a.severity === 'error' ? 'error' : a.severity === 'warning' ? 'warning' : a.severity === 'question' ? 'question' : 'info';
                allResults.push({ severity, message: msg, details: a.auto_fix, key: `anom-${idx}` });
              }
            });
            
            if (allResults.length === 0) return null;

            // severity 순서로 정렬: question > error > warning > info
            const order = { question: 0, error: 1, warning: 2, info: 3 };
            allResults.sort((a, b) => order[a.severity] - order[b.severity]);

            return (
              <div className="anomalies-section">
                <div className="anomalies-header">
                  <h3>⚠️ 검증 결과 상세</h3>
                  {editableErrors.length > 0 && sheetData.length > 0 && (
                    <button
                      className="btn-edit-all"
                      onClick={() => {
                        setEditTarget(null);
                        setShowSheetEditor(true);
                      }}
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                      </svg>
                      전체 수정하기 ({editableErrors.length}건)
                    </button>
                  )}
                </div>
                <div className="anomalies-list">
                  {allResults.map((item) => (
                    <div key={item.key} className={`anomaly-item ${item.severity}`}>
                      <div className="anomaly-title">
                        <span className="anomaly-icon">!</span>
                        {item.severity === 'question' ? <strong>AI 질문:</strong> : null} {item.message}
                      </div>
                      {item.details && (
                        <div className="anomaly-details">
                          {item.severity === 'question' ? '' : '💡 '}{item.details}
                        </div>
                      )}
                      <div className="anomaly-actions">
                        {item.severity === 'question' && (
                          <button className="btn-ai-answer" onClick={() => {
                            chatRef.current?.setQuestion(item.message);
                          }}>💬 AI와 대화로 답변</button>
                        )}
                        {(item.severity === 'error' || item.severity === 'warning') && item.field && sheetData.length > 0 && (
                          <button 
                            className={`btn-edit-value ${item.severity}`}
                            onClick={() => {
                              setEditTarget({
                                row: item.row ?? 0,
                                field: item.field ?? '',
                                message: item.message
                              });
                              setShowSheetEditor(true);
                            }}
                          >
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                            </svg>
                            값 수정
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
                {validationResult.anomalies?.recommendation && (
                  <div style={{ marginTop: '1.5rem', padding: '1rem', background: 'var(--success-light)', borderRadius: 'var(--radius-md)', color: 'var(--success)' }}>
                    💡 {validationResult.anomalies.recommendation}
                  </div>
                )}
              </div>
            );
          })()}

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
            {editableErrors.length > 0 && (
              <button
                className="btn-secondary"
                onClick={handleDownloadErrorsOnly}
                disabled={loading}
                title={`${editableErrors.length}건의 의심 항목 다운로드`}
              >
                ⚠️ 의심 목록 ({editableErrors.length})
              </button>
            )}
            <button
              className="btn-secondary"
              onClick={handleDownloadFinalData}
              disabled={loading}
            >
              📄 최종 수정본
            </button>
            <button
              className="btn-primary"
              onClick={handleDownload}
              disabled={loading}
            >
              📊 검증 리포트 →
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
                    <td className="label">헤더 매칭율</td>
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
                  clearSession()
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

      {/* 스프레드시트 에디터 모달 */}
      <SheetEditorPro
        isOpen={showSheetEditor}
        onClose={() => {
          setShowSheetEditor(false);
          setEditTarget(null);
        }}
        data={sheetData}
        targetRow={editTarget?.row ? editTarget.row - 1 : undefined}
        targetField={editTarget?.field}
        errorMessage={editTarget?.message}
        allErrors={editableErrors}
        filename={file?.name || 'export.xlsx'}
        onSave={(updatedData) => {
          // 새 배열로 복사하여 상태 업데이트 강제
          const newData = updatedData.map(row => [...row]);
          setSheetData(newData);
          
          // validationResult도 함께 업데이트 (화면 반영용)
          if (validationResult) {
            setValidationResult({
              ...validationResult,
              steps: {
                ...validationResult.steps,
                parsed_summary: {
                  ...validationResult.steps?.parsed_summary,
                  headers: newData[0],
                  all_rows: newData.slice(1).map(row => {
                    const obj: any = {};
                    (newData[0] || []).forEach((header, idx) => {
                      obj[header] = row[idx];
                    });
                    return obj;
                  })
                }
              }
            });
          }

          // 강제 리렌더링을 위해 짧은 지연 후 재검증
          setTimeout(() => {
            setShowSheetEditor(false);
          }, 100);
        }}
        onRevalidate={async (updatedData) => {
          // 수정된 데이터로 재검증 API 호출
          try {
            // 현재는 간단히 빈 배열 반환 (실제 구현 필요)
            // TODO: 백엔드에 수정된 데이터 전송하여 재검증

            // 임시: 수정된 셀의 에러만 제거
            const newErrors = editableErrors.filter(err => {
              // 수정된 행/필드가 있으면 해당 에러 제거
              const headers = updatedData[0];
              const colIdx = headers.indexOf(err.field || '');
              if (colIdx === -1 || !err.row) return true;

              const dataRowIdx = err.row - 2; // API row → 데이터 인덱스
              if (dataRowIdx < 0 || dataRowIdx >= updatedData.length - 1) return true;

              // 값이 변경되었으면 에러 제거 (실제로는 재검증 필요)
              return false;
            });

            return newErrors;
          } catch (error) {
            return editableErrors;
          }
        }}
      />

      {/* Floating AI Chat */}
      <FloatingChat ref={chatRef} validationContext={validationResult} />
    </div>
  )
}

export default App

