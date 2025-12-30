import { useState, useEffect } from 'react'
import './App.css'
import { api } from './api'
import ChatBot from './ChatBot'
import type { DiagnosticQuestion, AutoValidateResult, CompanyInfo } from './types'

type Step = 'questions' | 'upload' | 'results' | 'download'

function App() {
  const [currentStep, setCurrentStep] = useState<Step>('questions')
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
      console.log('📤 API 호출 중...')
      const result = await api.autoValidate(file)
      console.log('✅ API 응답:', result)
      setValidationResult(result)
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

    // v3에서는 Excel 생성 기능이 아직 미구현
    // 결과를 JSON으로 다운로드
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
      <header className="header">
        <h1>🏢 WIKISOFT3</h1>
        <p>퇴직급여채무 명부 AI 자동검증 시스템</p>
      </header>

      {/* 진행 단계 표시 */}
      <div className="steps">
        <div className={`step ${getStepStatus('questions')}`}>
          <div className="step-number">1</div>
          <h3>진단 질문</h3>
          <p>24개 질문에 답변</p>
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
          <h2>📁 명부 파일 업로드</h2>
          <p style={{ marginBottom: '2rem', color: '#888' }}>
            직원 명부가 포함된 Excel 파일을 선택해주세요.
          </p>

          {/* 디버깅 정보 */}
          <div style={{ background: 'rgba(0,255,0,0.1)', padding: '1rem', marginBottom: '1rem', borderRadius: '8px' }}>
            <p style={{ margin: 0, fontSize: '0.9rem' }}>
              ✅ 답변 완료: {Object.keys(answers).length}/{questions.length}개
            </p>
            <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.9rem' }}>
              {file ? `📄 파일: ${file.name}` : '❌ 파일 미선택'}
            </p>
          </div>

          <div className="file-upload">
            <div className="file-input-wrapper">
              <input
                type="file"
                accept=".xlsx,.xls"
                onChange={handleFileChange}
              />
            </div>
            
            {file && (
              <div className="file-info">
                <span>✅</span>
                <span>{file.name} ({(file.size / 1024).toFixed(1)} KB)</span>
              </div>
            )}
          </div>

          <div className="actions">
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
        <div className="content-section">
          <h2>✅ 검증 결과</h2>

          {/* 신뢰도 및 상태 요약 */}
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

          {/* 헤더 매칭 정보 */}
          {validationResult.steps?.matches && (
            <div style={{ marginTop: '2rem' }}>
              <h3 style={{ marginBottom: '1rem' }}>🔗 컬럼 매칭 결과</h3>
              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1rem', borderRadius: '8px', maxHeight: '200px', overflow: 'auto' }}>
                {Object.entries(validationResult.steps.matches).map(([header, match]: [string, any]) => (
                  <div key={header} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                    <span style={{ color: '#888' }}>{header}</span>
                    <span style={{ color: match ? '#4ade80' : '#ef4444' }}>
                      {match ? `→ ${match}` : '매칭 안됨'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 이상 탐지 정보 */}
          {validationResult.anomalies?.detected && validationResult.anomalies.anomalies.length > 0 && (
            <div style={{ marginTop: '2rem' }}>
              <h3 style={{ marginBottom: '1rem' }}>⚠️ 이상 탐지</h3>
              <ul className="warnings-list">
                {validationResult.anomalies.anomalies.map((anomaly, idx) => (
                  <li key={idx} className={`warning-item severity-${anomaly.severity}`}>
                    <div className="warning-message">{anomaly.message}</div>
                    <div className="warning-details">
                      <span>유형: {anomaly.type}</span>
                    </div>
                  </li>
                ))}
              </ul>
              {validationResult.anomalies.recommendation && (
                <p style={{ marginTop: '1rem', color: '#4ade80' }}>
                  💡 추천: {validationResult.anomalies.recommendation}
                </p>
              )}
            </div>
          )}

          {/* 파싱 요약 */}
          {validationResult.steps?.parsed_summary && (
            <div style={{ marginTop: '2rem' }}>
              <h3 style={{ marginBottom: '1rem' }}>📊 파싱 정보</h3>
              <p style={{ color: '#888' }}>
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
              JSON 다운로드 →
            </button>
          </div>
        </div>
      )}

      {/* Step 4: 다운로드 완료 */}
      {currentStep === 'download' && (
        <div className="content-section" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>✅</div>
          <h2>파일 다운로드 완료!</h2>
          <p style={{ marginTop: '1rem', color: '#888' }}>
            검증 결과 JSON 파일이 생성되었습니다.
          </p>
          <p style={{ marginTop: '0.5rem', color: '#888' }}>
            경고가 표시된 셀을 확인하고 필요시 수정해주세요.
          </p>

          <div className="actions" style={{ justifyContent: 'center', marginTop: '2rem' }}>
            <button
              className="btn-primary"
              onClick={() => {
                setCurrentStep('questions')
                setAnswers({})
                setFile(null)
                setValidationResult(null)
                setCompanyInfo({
                  company_name: '',
                  phone: '',
                  email: '',
                  작성기준일: new Date().toISOString().split('T')[0].replace(/-/g, '')
                })
              }}
            >
              새로운 검증 시작
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
