import { useState, useEffect, useRef, useMemo } from 'react'
import { useLocation } from 'react-router-dom'
import './App.css'
import { api } from './api'
import DiagnosticWizard from './components/DiagnosticWizard'
import FloatingChat, { FloatingChatHandle } from './components/FloatingChat'
import ManualMapping from './ManualMapping'
import SheetEditorPro from './components/SheetEditorPro'
import { useSession } from './contexts/SessionContext'
import { downloadBlob, generateTimestampedFilename } from './utils/download'
import { getRequiredFieldLabels } from './constants/fields'
import { handleError, isRetryableError } from './utils/errorHandler'
import { useValidationErrors } from './hooks/useValidationErrors'
import type { DiagnosticQuestion, AutoValidateResult, HeaderMatch, ValidationRun } from './types'

type Step = 'onboarding' | 'questions' | 'upload' | 'results' | 'download'
type ValidationMode = 'roster' | 'full'  // 명부만 / 전체 검증

// 명부만 모드에서 보여줄 질문 ID 목록
const ROSTER_MODE_QUESTION_IDS = [
  // 섹션 1: 일반사항 전체
  '1-1', '1-2', '1-3', '1-4', '1-5', '1-6',
  // 섹션 2: 작성기준일, 재직자수 개별 항목 (그룹 헤더 제외)
  '2-0', '2-a.1', '2-a.2', '2-a.3',
  // 섹션 4: 정년퇴직연령
  '4-1',
]

// 수정할 에러 정보
interface EditTarget {
  row: number
  field: string
  message: string
}

function App() {
  const { session, setSession, clearSession } = useSession()
  const location = useLocation()

  // localStorage에서 초기 상태 복원
  const [currentStep, setCurrentStep] = useState<Step>(() => {
    const savedStep = sessionStorage.getItem('currentStep') as Step | null
    return savedStep || 'onboarding'
  })
  const [validationMode, setValidationMode] = useState<ValidationMode>(() => {
    const savedMode = localStorage.getItem('validationMode') as ValidationMode | null
    return savedMode || 'full'
  })

  // 로그인 페이지에서 넘어올 때 모드 확인 (새로 로그인한 경우)
  useEffect(() => {
    const newLogin = sessionStorage.getItem('newLogin')
    if (newLogin) {
      sessionStorage.removeItem('newLogin')
      const savedMode = localStorage.getItem('validationMode') as ValidationMode | null
      if (savedMode) {
        setValidationMode(savedMode)
        // 온보딩 화면부터 시작 (사용자가 "검증 시작" 클릭 후 진행)
        setCurrentStep('onboarding')
      }
    }
  }, [location.key])

  // currentStep 변경 시 sessionStorage에 저장 (새로고침 시 복원용)
  useEffect(() => {
    if (currentStep !== 'onboarding') {
      sessionStorage.setItem('currentStep', currentStep)
    } else {
      sessionStorage.removeItem('currentStep')
    }
  }, [currentStep])
  const [questions, setQuestions] = useState<DiagnosticQuestion[]>([])
  const [answers, setAnswers] = useState<Record<string, string | number | string[]>>({})
  const [file, setFile] = useState<File | null>(null)
  const [validationResult, setValidationResult] = useState<AutoValidateResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [loadingMessage, setLoadingMessage] = useState<string>('처리 중...')
  const [error, setError] = useState<string>('')
  const [lastAction, setLastAction] = useState<(() => void) | null>(null)
  const [showManualMapping, setShowManualMapping] = useState(false)
  const [currentMatches, setCurrentMatches] = useState<HeaderMatch[]>([])

  // SheetEditor 상태
  const [showSheetEditor, setShowSheetEditor] = useState(false)
  const [editTarget, setEditTarget] = useState<EditTarget | null>(null)
  const [sheetData, setSheetData] = useState<string[][]>([])
  const [latestRuns, setLatestRuns] = useState<ValidationRun[]>([])
  const [runsLoading, setRunsLoading] = useState(false)

  // 접기/펼치기 상태
  const [showMappingDetails, setShowMappingDetails] = useState(false)
  const [showValidationDetails, setShowValidationDetails] = useState(false)

  // 다시 검증 다이얼로그
  const [showRetryDialog, setShowRetryDialog] = useState(false)

  // 고객이 "문제없음"으로 확인한 항목들 (key: "row-field-message")
  const [dismissedItems, setDismissedItems] = useState<Set<string>>(new Set())

  // 검증 결과에서 수정 가능한 에러/경고만 추출
  const allEditableErrors = useValidationErrors(validationResult)

  // 고객이 확인한 항목 제외
  const editableErrors = allEditableErrors.filter(err => {
    const key = `${err.row}-${err.field}-${err.message}`
    return !dismissedItems.has(key)
  })

  const chatRef = useRef<FloatingChatHandle>(null)

  // 검증 모드에 따라 질문 필터링
  const filteredQuestions = useMemo(() => {
    if (validationMode === 'roster') {
      return questions.filter(q => ROSTER_MODE_QUESTION_IDS.includes(q.id))
    }
    return questions
  }, [questions, validationMode])

  // 초기 로드: 진단 질문 조회
  useEffect(() => {
    loadQuestions()
    loadLatestRuns()
  }, [])

  const loadQuestions = async () => {
    const doLoad = async () => {
      try {
        setLoading(true)
        setLoadingMessage('📋 진단 질문 로딩 중...')
        setLastAction(() => doLoad)
        const data = await api.getDiagnosticQuestions()
        setQuestions(data.questions)
        setError('')
        setLastAction(null)
      } catch (err) {
        const message = handleError('DiagnosticQuestions', err, '진단 질문을 불러오는데 실패했습니다.')
        setError(message)
        if (!isRetryableError(err)) setLastAction(null)
      } finally {
        setLoading(false)
      }
    }
    doLoad()
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

  const handleValidate = async (overrideAnswers?: Record<string, string | number | string[]>) => {
    if (!file) {
      alert('명부 파일을 선택해주세요')
      return
    }

    // 전달받은 answers 또는 현재 상태의 answers 사용
    const currentAnswers = overrideAnswers ?? answers

    // 명부만 검증 모드가 아닐 때만 진단 질문 답변 체크
    if (validationMode === 'full') {
      // 조건부 질문 필터링 - 보이는 질문만 체크
      const visibleQuestions = questions.filter(q => {
        if (!q.condition) return true
        const { question_id, answer: requiredAnswer } = q.condition
        const currentAnswer = currentAnswers[question_id]
        if (currentAnswer === undefined) return false
        return currentAnswer === requiredAnswer
      })

      // 필수 답변 체크 (0도 유효한 답변으로 처리) - 보이는 질문만!
      const unansweredQuestions = visibleQuestions.filter(q => currentAnswers[q.id] === undefined)
      if (unansweredQuestions.length > 0) {
        alert(`${unansweredQuestions.length}개의 질문에 답변이 없습니다. 모든 질문에 답변해주세요.`)
        return
      }
    }

    const doValidate = async () => {
      try {
        setLoading(true)
        setLoadingMessage('📄 파일 분석 중...')
        setError('')
        setLastAction(() => doValidate)

        // 명부만 검증: 명부 관련 답변만 / 전체 검증: 모든 진단 질문 답변 포함
        const answersToSend = validationMode === 'roster'
          ? Object.fromEntries(
              Object.entries(currentAnswers).filter(([key]) => ROSTER_MODE_QUESTION_IDS.includes(key))
            )
          : currentAnswers
        setLoadingMessage(validationMode === 'roster' ? '📋 명부 검증 중...' : '🔍 데이터 검증 중...')
        const { result, sessionId } = await api.validateWithRoster(file, answersToSend, validationMode)
        if (sessionId) {
          setSession(sessionId)
        }
        setValidationResult(result)

        // 매칭 결과 저장 (수동 매핑용)
        setLoadingMessage('📊 결과 정리 중...')
        if (result.steps?.matches?.matches) {
          setCurrentMatches(result.steps.matches.matches)
        }

        // 스프레드시트 데이터 저장 (수정용)
        if (result.steps?.parsed_summary) {
          const headers = result.steps.parsed_summary.headers || []
          // all_rows는 steps.all_rows에 있음 (parsed_summary 바깥)
          const rows = result.steps.all_rows || result.steps.parsed_summary.all_rows || []
          if (rows.length > 0) {
            setSheetData([headers, ...rows.map((row) =>
              headers.map((h) => String(row[h] ?? ''))
            )])
          }
        }

        setLastAction(null)
        setCurrentStep('results')
      } catch (err) {
        const message = handleError('Validation', err, '검증 중 오류가 발생했습니다.')
        setError(message)
        if (!isRetryableError(err)) {
          setLastAction(null)
        }
      } finally {
        setLoading(false)
      }
    }
    doValidate()
  }

  const handleDownload = async () => {
    if (!validationResult || !session.sessionId) return
    const sessionId = session.sessionId

    const doDownload = async () => {
      try {
        setLoading(true)
        setLoadingMessage('📥 리포트 생성 중...')
        setError('')
        setLastAction(() => doDownload)

        const blob = await api.downloadExcel(sessionId)
        const filename = generateTimestampedFilename('검증리포트', 'xlsx')
        downloadBlob(blob, filename)
        setLastAction(null)
        setCurrentStep('download')
      } catch (err) {
        const message = handleError('DownloadExcel', err, 'Excel 리포트 다운로드에 실패했습니다.')
        setError(message)
        if (!isRetryableError(err)) setLastAction(null)
      } finally {
        setLoading(false)
      }
    }
    doDownload()
  }

  const handleDownloadFinalData = async () => {
    if (!validationResult || !session.sessionId) return
    const sessionId = session.sessionId

    const doDownload = async () => {
      try {
        setLoading(true)
        setLoadingMessage('📥 최종본 준비 중...')
        setError('')
        setLastAction(() => doDownload)

        const blob = await api.downloadFinalData(sessionId)
        const filename = generateTimestampedFilename('최종수정본', 'xlsx')
        downloadBlob(blob, filename)
        setLastAction(null)
      } catch (err) {
        const message = handleError('DownloadFinalData', err, '최종 수정본 다운로드에 실패했습니다.')
        setError(message)
        if (!isRetryableError(err)) setLastAction(null)
      } finally {
        setLoading(false)
      }
    }
    doDownload()
  }

  // 오류 목록만 다운로드
  const handleDownloadErrorsOnly = async () => {
    if (!validationResult || !file) return

    // editableErrors 사용 - error와 warning 모두 포함
    const errorsToExport = editableErrors.map(err => ({
      row: err.row ?? 0,
      field: err.field ?? '',
      message: err.message,
      severity: err.severity
    }))

    if (errorsToExport.length === 0) {
      alert('다운로드할 항목이 없습니다.')
      return
    }

    const doDownload = async () => {
      try {
        setLoading(true)
        setLoadingMessage('📥 의심 목록 생성 중...')
        setError('')
        setLastAction(() => doDownload)

        const blob = await api.downloadErrorsExcel(file.name, errorsToExport)
        const filename = generateTimestampedFilename('의심목록', 'xlsx')
        downloadBlob(blob, filename)
        setLastAction(null)
      } catch (err) {
        const message = handleError('DownloadErrors', err, '의심 목록 다운로드에 실패했습니다.')
        setError(message)
        if (!isRetryableError(err)) setLastAction(null)
      } finally {
        setLoading(false)
      }
    }
    doDownload()
  }

  const getStepStatus = (step: Step): 'active' | 'completed' | 'pending' => {
    // 파일 업로드는 온보딩에서 완료됨
    if (step === 'onboarding') return 'completed'

    const steps: Step[] = ['questions', 'results', 'download']
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
              <h1
                className="header-logo"
                onClick={() => {
                  setCurrentStep('onboarding')
                  setAnswers({})
                  setFile(null)
                  setValidationResult(null)
                  setCurrentMatches([])
                  setDismissedItems(new Set())
                  sessionStorage.removeItem('currentStep')
                  const input = document.getElementById('onboarding-file-input') as HTMLInputElement
                  if (input) input.value = ''
                }}
              >
                WIKI AGENT
                <span className={`mode-badge ${validationMode}`}>
                  {validationMode === 'roster' ? 'Basic' : 'Complete'}
                </span>
              </h1>
              <p>퇴직급여채무 명부 AI 자동검증 시스템</p>
            </div>
          </header>

          {/* 진행 단계 표시 */}
          <div className="steps">
        <div className={`step ${getStepStatus('onboarding')}`}>
          <div className="step-number">1</div>
          <h3>파일</h3>
          <p>Excel 명부 업로드</p>
        </div>
        <div className={`step ${getStepStatus('questions')}`}>
          <div className="step-number">2</div>
          <h3>진단</h3>
          <p>예/아니오 질문</p>
        </div>
        <div className={`step ${getStepStatus('results')}`}>
          <div className="step-number">3</div>
          <h3>검증</h3>
          <p>AI 자동 분석</p>
        </div>
        <div className={`step ${getStepStatus('download')}`}>
          <div className="step-number">4</div>
          <h3>다운로드</h3>
          <p>검증 결과 파일</p>
        </div>
      </div>
        </>
      )}

      {error && (
        <div className="content-section error-section" style={{ background: 'rgba(239, 68, 68, 0.1)', borderColor: '#ef4444' }}>
          <p style={{ color: '#ef4444', fontSize: '1.1rem', marginBottom: lastAction ? '1rem' : 0 }}>
            ❌ {error}
          </p>
          {lastAction && (
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <button
                className="btn-primary"
                onClick={() => {
                  setError('')
                  lastAction()
                }}
                style={{ padding: '0.5rem 1rem' }}
              >
                🔄 다시 시도
              </button>
              <button
                className="btn-secondary"
                onClick={() => {
                  setError('')
                  setLastAction(null)
                }}
                style={{ padding: '0.5rem 1rem' }}
              >
                취소
              </button>
            </div>
          )}
        </div>
      )}

      {loading && (
        <div className="loading">
          <div className="spinner"></div>
          <p>{loadingMessage}</p>
        </div>
      )}

      {/* Step 0: 온보딩 화면 */}
      {currentStep === 'onboarding' && (
        <div className="onboarding">
          <header className="onboarding-header-bar">
            <div className="onboarding-header-title">
              WIKI AGENT
              <span className={`mode-badge ${validationMode}`}>
                {validationMode === 'roster' ? 'Basic' : 'Complete'}
              </span>
            </div>
          </header>
          <div className="onboarding-header">
            <h1 className="onboarding-title">
              <span className="title-wiki">WIKI</span> <span className="title-soft">AGENT</span>
            </h1>
            <p className="onboarding-subtitle">퇴직급여채무 AI 자동검증</p>
          </div>

          <div className="onboarding-stepper">
            <div className="stepper-step">
              <div className="step-number-large">01</div>
              <h3 className="step-label">파일</h3>
              <p className="step-description">Excel 명부 업로드</p>
            </div>

            <div className="stepper-connector"></div>

            <div className="stepper-step">
              <div className="step-number-large">02</div>
              <h3 className="step-label">진단</h3>
              <p className="step-description">예/아니오 질문</p>
            </div>

            <div className="stepper-connector"></div>

            <div className="stepper-step">
              <div className="step-number-large">03</div>
              <h3 className="step-label">검증</h3>
              <p className="step-description">AI 자동 분석</p>
            </div>

            <div className="stepper-connector"></div>

            <div className="stepper-step">
              <div className="step-number-large">04</div>
              <h3 className="step-label">다운로드</h3>
              <p className="step-description">검증 결과 파일</p>
            </div>
          </div>

          {/* 가로 레이아웃: 업로드(왼쪽) + 버튼(오른쪽) */}
          <div className="onboarding-row">
            <div className="onboarding-upload-section">
              <h3 className="section-title">파일 업로드</h3>
              <div className="onboarding-dropzone">
                <div className="dropzone-icon">
                  <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                    <path d="M12 36 L12 12 C12 10 14 9 15 9 L27 9 L36 18 L36 36 C36 38 34 39 33 39 L15 39 C14 39 12 38 12 36Z" stroke="currentColor" strokeWidth="2" fill="none"/>
                    <path d="M27 9 L27 18 L36 18" stroke="currentColor" strokeWidth="2" fill="none"/>
                    <line x1="24" y1="24" x2="24" y2="33" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                    <polyline points="19,28 24,24 29,28" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </div>
                <p className="dropzone-text">Excel 파일을 드래그하거나 클릭</p>
                <div className="dropzone-formats">
                  <span className="format-tag">.xlsx</span>
                  <span className="format-tag">.xls</span>
                </div>
                <input
                  type="file"
                  accept=".xlsx,.xls"
                  onChange={handleFileChange}
                  className="file-input-hidden"
                  id="onboarding-file-input"
                />
                <label htmlFor="onboarding-file-input" className="dropzone-label">파일 선택</label>
              </div>

              {file && (
                <div className="onboarding-file-selected">
                  <div className="file-check-icon">✓</div>
                  <div className="file-info">
                    <span className="file-name">{file.name}</span>
                    <span className="file-size">({(file.size / 1024).toFixed(1)} KB)</span>
                  </div>
                  <button
                    className="file-remove-btn"
                    onClick={() => {
                      setFile(null)
                      const input = document.getElementById('onboarding-file-input') as HTMLInputElement
                      if (input) input.value = ''
                    }}
                  >
                    ✕
                  </button>
                </div>
              )}
            </div>

            <button
              className="btn-start"
              onClick={() => {
                if (!file) {
                  alert('먼저 Excel 파일을 업로드해주세요.')
                  return
                }
                setCurrentStep('questions')
                loadQuestions()
              }}
              disabled={!file}
            >
              검증 시작 →
            </button>
          </div>
        </div>
      )}

      {/* Step 1: 진단 질문 (7페이지 위자드) */}
      {currentStep === 'questions' && !loading && filteredQuestions.length > 0 && (
        <DiagnosticWizard
          questions={filteredQuestions}
          initialAnswers={answers}
          mode={validationMode}
          onComplete={(completedAnswers) => {
            setAnswers(completedAnswers)
            // 파일이 이미 업로드되어 있으므로 바로 검증 실행
            // 답변을 직접 전달하여 상태 업데이트 타이밍 문제 방지
            handleValidate(completedAnswers)
          }}
          onBack={() => {
            setCurrentStep('onboarding')
          }}
        />
      )}

      {/* Step 2: 검증 결과 */}
      {currentStep === 'results' && validationResult && (
        <div className="results-page">
          <div className="results-container">
            {/* 헤더 */}
            <div className="results-header">
              <h2 className="results-title">✅ 검증 결과</h2>
            </div>


          {/* 컬럼 매핑 테이블 - 100% 성공 시 숨김 */}
          {validationResult.steps?.matches && (() => {
            const matches = currentMatches.length > 0 ? currentMatches : validationResult.steps?.matches?.matches || []
            const mapped = matches.filter((m: HeaderMatch) => m.target && !m.skipped).length
            const total = matches.length
            const percent = total > 0 ? Math.round((mapped / total) * 100) : 0

            // 100% 매핑 성공 시 섹션 숨김
            if (percent >= 100) return null

            const requiredFields = getRequiredFieldLabels()
            const sortedMatches = [...matches].sort((a: HeaderMatch, b: HeaderMatch) => {
              const aRequired = requiredFields.includes(a.target || '')
              const bRequired = requiredFields.includes(b.target || '')
              if (aRequired && !bRequired) return -1
              if (!aRequired && bRequired) return 1
              return 0
            })

            return (
              <div className="mapping-section">
                <div className="section-header collapsible" onClick={() => setShowMappingDetails(!showMappingDetails)}>
                  <h3>
                    <span className={`collapse-icon ${showMappingDetails ? 'expanded' : ''}`}>▶</span>
                    컬럼 매핑 결과 ({mapped}/{total}, {percent}% 성공)
                  </h3>
                  <button
                    className="btn-secondary"
                    style={{ padding: '0.5rem 1rem', fontSize: '0.9rem' }}
                    onClick={(e) => { e.stopPropagation(); setShowManualMapping(true); }}
                  >
                    수동 매핑
                  </button>
                </div>
                {showMappingDetails && (
                  <table className="mapping-table">
                    <thead>
                      <tr>
                        <th>소스 헤더</th>
                        <th></th>
                        <th>타겟 필드</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sortedMatches.map((match: HeaderMatch, idx: number) => {
                        const isRequired = requiredFields.includes(match.target || '')
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
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                )}
              </div>
            )
          })()}

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
              emp_info?: string,
              originalMessage?: string,  // 원본 메시지 (dismiss key용)
              dismissKey?: string        // dismiss 체크용 키
            }> = [];
            const seenMessages = new Set<string>();

            // validation.errors & warnings (allEditableErrors 사용 - dismissed 포함)
            allEditableErrors.forEach((item, idx) => {
              // 행 번호가 없으면 "행 null" 표시 안함
              const prefix = item.emp_info
                ? item.emp_info
                : item.row != null
                  ? `행 ${item.row}`
                  : '';
              const msg = prefix
                ? `${prefix}: ${item.field} - ${item.message}`
                : `${item.field} - ${item.message}`;
              const dismissKey = `${item.row}-${item.field}-${item.message}`;
              if (!seenMessages.has(msg)) {
                seenMessages.add(msg);
                allResults.push({
                  severity: item.severity,
                  message: msg,
                  details: undefined,
                  key: `${item.severity}-${idx}`,
                  row: item.row,
                  field: item.field,
                  emp_info: item.emp_info,
                  originalMessage: item.message,
                  dismissKey: dismissKey
                });
              }
            });

            // anomalies (중복 체크)
            validationResult.anomalies?.anomalies?.forEach((a, idx) => {
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
            
            // 이상 없음
            if (allResults.length === 0) {
              return (
                <div className="anomalies-section success">
                  <div className="anomalies-header">
                    <h3>✅ 검증 완료 - 이상 없음</h3>
                  </div>
                  <div className="success-message">
                    <p>모든 검증 항목을 통과했습니다.</p>
                  </div>
                </div>
              );
            }

            // severity 순서로 정렬: question > error > warning > info
            const order = { question: 0, error: 1, warning: 2, info: 3 };
            allResults.sort((a, b) => order[a.severity] - order[b.severity]);

            return (
              <div className="anomalies-section">
                <div className="anomalies-header collapsible" onClick={() => setShowValidationDetails(!showValidationDetails)}>
                  <h3>
                    <span className={`collapse-icon ${showValidationDetails ? 'expanded' : ''}`}>▶</span>
                    ⚠️ 검증 결과 상세 ({allResults.length}건)
                  </h3>
                  {editableErrors.length > 0 && sheetData.length > 0 && (
                    <button
                      className="btn-edit-all"
                      onClick={(e) => {
                        e.stopPropagation();
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
                {showValidationDetails && <div className="anomalies-list">
                  {allResults.map((item) => {
                    const isDismissed = item.dismissKey && dismissedItems.has(item.dismissKey);
                    return (
                    <div key={item.key} className={`anomaly-item ${item.severity} ${isDismissed ? 'confirmed' : ''}`}>
                      <div className="anomaly-title">
                        <span className="anomaly-icon">{isDismissed ? '✓' : '!'}</span>
                        {item.severity === 'question' ? <strong>AI 질문:</strong> : null} {item.message}
                      </div>
                      {item.details && (
                        <div className="anomaly-details">
                          {item.severity === 'question' ? '' : '💡 '}{item.details}
                        </div>
                      )}
                      <div className="anomaly-actions">
                        {isDismissed ? (
                          <span className="confirmed-badge">✅ 확인완료</span>
                        ) : (
                          <>
                            {item.severity === 'question' && (
                              <button className="btn-ai-answer" onClick={() => {
                                chatRef.current?.setQuestion(item.message);
                              }}>💬 AI와 대화로 답변</button>
                            )}
                            {(item.severity === 'error' || item.severity === 'warning') && item.field && sheetData.length > 0 && (
                              <>
                                <button
                                  className={`btn-edit-value ${item.severity}`}
                                  onClick={() => {
                                    setEditTarget({
                                      row: item.row ?? 0,
                                      field: item.field ?? '',
                                      message: item.originalMessage || item.message
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
                                <button
                                  className="btn-dismiss-value"
                                  onClick={() => {
                                    if (item.dismissKey) {
                                      setDismissedItems(prev => new Set([...prev, item.dismissKey!]))
                                    }
                                  }}
                                  title="이 값이 정확함을 확인합니다"
                                >
                                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <polyline points="20 6 9 17 4 12"/>
                                  </svg>
                                  값 유지
                                </button>
                              </>
                            )}
                          </>
                        )}
                      </div>
                    </div>
                    );
                  })}
                </div>}
              </div>
            );
          })()}

          <div className="actions">
            <button
              className="btn-secondary"
              onClick={() => setShowRetryDialog(true)}
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
                    <td>{validationResult?.steps?.parsed_summary?.row_count ?? 0}행</td>
                  </tr>
                  <tr>
                    <td className="label">컬럼 매핑</td>
                    <td>
                      {(() => {
                        const matches = validationResult?.steps?.matches?.matches || []
                        const mapped = matches.filter((m: HeaderMatch) => m.target && !m.skipped).length
                        const total = matches.length
                        return `${mapped}/${total} 매핑됨`
                      })()}
                    </td>
                  </tr>
                  <tr>
                    <td className="label">매칭 신뢰도</td>
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
                  setCurrentStep('onboarding')
                  setAnswers({})
                  setFile(null)
                  setValidationResult(null)
                  setCurrentMatches([])
                  setDismissedItems(new Set())
                  clearSession()
                  // 세션 상태 초기화
                  sessionStorage.removeItem('currentStep')
                  const input = document.getElementById('onboarding-file-input') as HTMLInputElement
                  if (input) input.value = ''
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
                    const obj: Record<string, string | number | null> = {};
                    (newData[0] || []).forEach((header, idx) => {
                      obj[header] = row[idx] ?? null;
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
            const headers = updatedData[0];
            const rows = updatedData.slice(1);

            const result = await api.revalidate(
              headers,
              rows,
              Object.keys(answers).length > 0 ? answers : null
            );

            // 에러/경고 합치기 (ValidationItem 형식으로 변환)
            const newErrors = [
              ...(result.errors || []).map((e) => ({
                severity: 'error' as const,
                message: e.message || e.error || e.reason || '오류',
                row: e.row,
                field: e.field,
                emp_info: e.emp_info,
              })),
              ...(result.warnings || []).map((w) => ({
                severity: 'warning' as const,
                message: w.message || w.warning || w.reason || '경고',
                row: w.row,
                field: w.field,
                emp_info: w.emp_info,
              })),
            ];

            // 부모 상태 업데이트
            if (validationResult) {
              setValidationResult({
                ...validationResult,
                steps: {
                  ...validationResult.steps,
                  ...(result.validation && { validation: result.validation }),
                },
                ...(result.confidence && { confidence: result.confidence }),
                ...(result.anomalies && { anomalies: result.anomalies }),
              });
            }

            return newErrors;
          } catch (error) {
            console.error('재검증 오류:', error);
            return editableErrors;
          }
        }}
      />

      {/* 다시 검증 다이얼로그 */}
      {showRetryDialog && (
        <div className="dialog-overlay" onClick={() => setShowRetryDialog(false)}>
          <div className="dialog-content" onClick={(e) => e.stopPropagation()}>
            <h3>다시 검증</h3>
            <p>이전 답변을 유지하시겠습니까?</p>
            <div className="dialog-actions">
              <button
                className="btn-secondary"
                onClick={() => {
                  // 아니오: 답변 초기화, 질문 화면으로
                  setShowRetryDialog(false)
                  setValidationResult(null)
                  setFile(null)
                  setAnswers({})
                  setDismissedItems(new Set())
                  setCurrentStep('onboarding')
                  const input = document.getElementById('onboarding-file-input') as HTMLInputElement
                  if (input) input.value = ''
                }}
              >
                아니오 (처음부터)
              </button>
              <button
                className="btn-primary"
                onClick={() => {
                  // 예: 답변 유지, 파일만 다시 업로드
                  setShowRetryDialog(false)
                  setValidationResult(null)
                  setFile(null)
                  setDismissedItems(new Set())
                  setCurrentStep('onboarding')
                  const input = document.getElementById('onboarding-file-input') as HTMLInputElement
                  if (input) input.value = ''
                }}
              >
                예 (답변 유지)
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Floating AI Chat */}
      <FloatingChat ref={chatRef} validationContext={validationResult} />
    </div>
  )
}

export default App

