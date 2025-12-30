import { useState, useEffect } from 'react'
import './App.css'
import { api } from './api'
import ChatBot from './ChatBot'
import type { DiagnosticQuestion, ValidationResult, CompanyInfo } from './types'

type Step = 'questions' | 'upload' | 'results' | 'download'

function App() {
  const [currentStep, setCurrentStep] = useState<Step>('questions')
  const [questions, setQuestions] = useState<DiagnosticQuestion[]>([])
  const [answers, setAnswers] = useState<Record<string, string | number>>({})
  const [file, setFile] = useState<File | null>(null)
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null)
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
      const result = await api.validateWithRoster(file, answers)
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

    // 회사 정보 입력 체크
    if (!companyInfo.company_name || !companyInfo.phone || !companyInfo.email) {
      alert('회사 정보를 모두 입력해주세요')
      return
    }

    try {
      setLoading(true)
      const blob = await api.generateWithValidation(validationResult.session_id, companyInfo)
      
      // 파일 다운로드
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `퇴직급여채무_${companyInfo.company_name}_${companyInfo.작성기준일}.xlsx`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      
      setCurrentStep('download')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Excel 파일 생성 중 오류가 발생했습니다.')
      console.error(err)
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
      <header className="header">
        <h1>🏢 WIKISOFT2</h1>
        <p>퇴직급여채무 명부 교차검증 시스템</p>
      </header>

      {/* 진행 단계 표시 */}
      <div className="steps">
        <div className={`step ${getStepStatus('questions')}`}>
          <div className="step-number">1</div>
          <h3>진단 질문</h3>
          <p>28개 질문에 답변</p>
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

          <div className="result-summary">
            <div className={`result-stat ${validationResult.validation.status === 'passed' ? 'success' : 'error'}`}>
              <div className="result-stat-value">
                {validationResult.validation.status === 'passed' ? '통과' : '실패'}
              </div>
              <div className="result-stat-label">검증 상태</div>
            </div>
            <div className="result-stat success">
              <div className="result-stat-value">{validationResult.validation.passed}</div>
              <div className="result-stat-label">통과한 항목</div>
            </div>
            <div className="result-stat warning">
              <div className="result-stat-value">{validationResult.validation.warnings.length}</div>
              <div className="result-stat-label">경고 항목</div>
            </div>
            <div className="result-stat">
              <div className="result-stat-value">{validationResult.validation.total_checks}</div>
              <div className="result-stat-label">총 검증 항목</div>
            </div>
          </div>

          {validationResult.validation.warnings.length > 0 && (
            <div>
              <h3 style={{ marginBottom: '1rem' }}>⚠️ 경고 사항</h3>
              <ul className="warnings-list">
                {validationResult.validation.warnings.map((warning, idx) => (
                  <li key={idx} className={`warning-item severity-${warning.severity}`}>
                    <div className="warning-message">{warning.message}</div>
                    <div className="warning-details">
                      <span>📝 입력값: {warning.user_input ?? 'N/A'}</span>
                      <span>📊 계산값: {warning.calculated ?? 'N/A'}</span>
                      <span>📈 차이: {warning.diff_percent ? `${warning.diff_percent.toFixed(1)}%` : 'N/A'}</span>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {validationResult.parsing_warnings.length > 0 && (
            <div style={{ marginTop: '2rem' }}>
              <h3 style={{ marginBottom: '1rem' }}>ℹ️ 파싱 정보</h3>
              <ul className="warnings-list">
                {validationResult.parsing_warnings.map((warning, idx) => (
                  <li key={idx} className="warning-item severity-low">
                    <div className="warning-message">{warning.message}</div>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div style={{ marginTop: '2rem', padding: '1.5rem', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '8px' }}>
            <h3 style={{ marginBottom: '1rem' }}>🏢 회사 정보 입력</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', color: '#888' }}>회사명</label>
                <input
                  type="text"
                  value={companyInfo.company_name}
                  onChange={(e) => setCompanyInfo({ ...companyInfo, company_name: e.target.value })}
                  placeholder="예: 세라젬"
                  style={{ width: '100%' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', color: '#888' }}>전화번호</label>
                <input
                  type="text"
                  value={companyInfo.phone}
                  onChange={(e) => setCompanyInfo({ ...companyInfo, phone: e.target.value })}
                  placeholder="예: 02-1234-5678"
                  style={{ width: '100%' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', color: '#888' }}>이메일</label>
                <input
                  type="email"
                  value={companyInfo.email}
                  onChange={(e) => setCompanyInfo({ ...companyInfo, email: e.target.value })}
                  placeholder="예: hr@example.com"
                  style={{ width: '100%' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', color: '#888' }}>작성기준일</label>
                <input
                  type="text"
                  value={companyInfo.작성기준일}
                  onChange={(e) => setCompanyInfo({ ...companyInfo, 작성기준일: e.target.value })}
                  placeholder="YYYYMMDD"
                  style={{ width: '100%' }}
                />
              </div>
            </div>
          </div>

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
              Excel 다운로드 →
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
            퇴직급여채무 Excel 파일이 생성되었습니다.
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
