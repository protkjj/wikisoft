import { useState, useEffect, useRef } from 'react'
import './ChatBot.css'
import type { DiagnosticQuestion } from '../types'

// 검증 규칙
const VALIDATION_RULES: Record<string, (value: string) => string | null> = {
  email: (value) => {
    if (!value || value === '') return null
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(value) ? null : '올바른 이메일 형식이 아닙니다 (예: example@email.com)'
  },
  phone: (value) => {
    if (!value || value === '') return null
    const phoneRegex = /^[\d\-\s]+$/
    return phoneRegex.test(value) ? null : '올바른 전화번호 형식이 아닙니다 (예: 02-1234-5678)'
  },
  number: (value) => {
    if (!value || value === '') return '숫자를 입력해주세요'
    const num = parseFloat(value)
    if (isNaN(num)) return '올바른 숫자 형식이 아닙니다'
    if (num < 0) return '음수는 입력할 수 없습니다'
    return null
  }
}

// 질문 ID별 검증 규칙 매핑
const QUESTION_VALIDATION_MAP: Record<string, string> = {
  '1-3': 'phone',
  '1-4': 'email',
}

interface ChatBotProps {
  questions: DiagnosticQuestion[]
  onComplete: (answers: Record<string, string | number | string[]>) => void
  onBack: () => void
  initialAnswers?: Record<string, string | number | string[]>
}

export default function ChatBot({ questions, onComplete, onBack, initialAnswers = {} }: ChatBotProps) {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [answers, setAnswers] = useState<Record<string, string | number | string[]>>(initialAnswers)
  const [userInput, setUserInput] = useState('')
  const [isEditing, setIsEditing] = useState(false)  // 답변 수정 모드
  const [validationError, setValidationError] = useState<string | null>(null)
  const questionRefs = useRef<(HTMLLIElement | null)[]>([])

  // 질문이 없으면 빈 화면 표시
  if (!questions || questions.length === 0) {
    return (
      <div className="chatbot-layout">
        <div className="question-main">
          <div className="completion-screen">
            <div className="completion-icon">⚠️</div>
            <h2 className="completion-title">질문이 없습니다</h2>
            <p className="completion-subtitle">진단 질문을 불러오지 못했습니다.</p>
            <button className="completion-next-button" onClick={onBack}>
              ← 돌아가기
            </button>
          </div>
        </div>
      </div>
    )
  }

  const currentQuestion = questions[currentQuestionIndex]
  const progress = ((Object.keys(answers).length) / questions.length) * 100
  const allAnswered = Object.keys(answers).length === questions.length

  // 현재 질문이 변경되면 해당 항목으로 스크롤 (사이드바만)
  useEffect(() => {
    const currentRef = questionRefs.current[currentQuestionIndex]
    if (currentRef) {
      // scrollIntoView를 사이드바 컨테이너 기준으로 제한
      currentRef.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  }, [currentQuestionIndex])

  const handleAnswer = (value: string | number | string[]) => {
    if (!currentQuestion) return

    const newAnswers = {
      ...answers,
      [currentQuestion.id]: value
    }
    setAnswers(newAnswers)
    setUserInput('')

    // 마지막 질문이 아니면 다음으로 이동
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1)
    }
    // 마지막 질문 완료 시 자동으로 완료 처리하지 않고 현재 화면 유지
  }

  const handleChoiceClick = (choice: string) => {
    handleAnswer(choice)
  }

  const handleInputSubmit = () => {
    // 빈 입력 무시
    if (!userInput.trim()) return

    // 숫자 타입인 경우 숫자 검증
    if (currentQuestion.type === 'number') {
      const error = VALIDATION_RULES.number(userInput)
      if (error) {
        setValidationError(error)
        return
      }
    }

    // 특수 검증 규칙 확인 (이메일, 전화번호 등)
    const ruleKey = QUESTION_VALIDATION_MAP[currentQuestion.id]
    if (ruleKey && VALIDATION_RULES[ruleKey]) {
      const error = VALIDATION_RULES[ruleKey](userInput)
      if (error) {
        setValidationError(error)
        return
      }
    }
    setValidationError(null)

    const value = currentQuestion.type === 'number'
      ? parseFloat(userInput) || 0
      : userInput
    handleAnswer(value)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleInputSubmit()
    }
  }

  const handleQuestionClick = (index: number) => {
    setCurrentQuestionIndex(index)
    setUserInput('')
  }

  const handleComplete = () => {
    onComplete(answers)
  }

  const categoryLabels: Record<string, string> = {
    'data_quality': '📊 데이터 품질',
    'financial_assumptions': '💰 재무 가정',
    'retirement_settings': '🏖️ 퇴직 설정',
    'headcount_aggregates': '👥 인원 집계',
    'amount_aggregates': '💵 금액 집계'
  }

  const getQuestionStatus = (index: number): 'answered' | 'current' | 'pending' => {
    if (answers[questions[index].id] !== undefined) return 'answered'
    if (index === currentQuestionIndex) return 'current'
    return 'pending'
  }

  return (
    <div className="chatbot-layout">
      {/* 왼쪽 사이드바: 질문 목록 */}
      <div className="question-sidebar">
        <div className="sidebar-header">
          <h3>📋 질문 목록</h3>
          <p>{Object.keys(answers).length} / {questions.length} 완료</p>
        </div>

        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${progress}%` }}></div>
        </div>

        <ul className="question-list">
          {questions.map((q, index) => {
            const status = getQuestionStatus(index)
            // '-' 이전 내용만 추출 (없으면 앞 15자)
            const preview = q.question.includes(' - ')
              ? q.question.split(' - ')[0]
              : q.question.substring(0, 15)
            return (
              <li
                key={q.id}
                ref={(el) => { questionRefs.current[index] = el }}
                className={`question-item ${status}`}
                onClick={() => handleQuestionClick(index)}
              >
                <span className="question-number">{index + 1}</span>
                <span className="question-preview">{preview}</span>
                {status === 'answered' && <span className="check-mark">✓</span>}
              </li>
            )
          })}
        </ul>
      </div>

      {/* 오른쪽 메인: 현재 질문 또는 완료 화면 */}
      <div className="question-main">
        {allAnswered && !isEditing ? (
          // 모든 질문 완료 시 완료 화면 표시
          <div className="completion-screen">
            <div className="completion-icon-wrapper">
              <svg width="50" height="50" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
            </div>
            <h2 className="completion-title">모든 질문 완료!</h2>
            <p className="completion-subtitle">{questions.length}개 질문에 모두 답변하셨습니다.</p>

            <div className="completion-buttons">
              <button
                className="completion-edit-button"
                onClick={() => {
                  setIsEditing(true)
                  setCurrentQuestionIndex(0)
                }}
              >
                ✏️ 답변 수정
              </button>
              <button
                className="completion-next-button"
                onClick={handleComplete}
              >
                검증 시작 →
              </button>
            </div>
          </div>
        ) : currentQuestion ? (
          // 질문 진행 중
          <>
            <div className="main-header">
              <div className={`category-badge ${currentQuestion.category || ''}`}>
                {categoryLabels[currentQuestion.category || ''] || currentQuestion.category || '📋 질문'}
              </div>
              <span className="question-id">Q{currentQuestionIndex + 1}</span>
            </div>

            <h2 className="question-text">{currentQuestion.question}</h2>

            {answers[currentQuestion.id] !== undefined && (
              <div className="answered-badge">
                ✓ 답변: <strong>{String(answers[currentQuestion.id])}</strong>
              </div>
            )}

            <div className="answer-area">
              {currentQuestion.choices && currentQuestion.choices.length > 4 ? (
                // 선택지가 많으면 (결산월 등) 드롭다운 사용
                <div className="select-group">
                  <select
                    className="select-input"
                    value={userInput || answers[currentQuestion.id] as string || ''}
                    onChange={(e) => setUserInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && userInput) {
                        e.preventDefault()
                        e.stopPropagation()
                        handleAnswer(userInput)
                      }
                    }}
                    autoFocus
                  >
                    <option value="">선택해주세요</option>
                    {currentQuestion.choices.map((choice, i) => (
                      <option key={i} value={choice}>{choice}</option>
                    ))}
                  </select>
                  <button
                    className="submit-button"
                    onClick={() => {
                      if (userInput) {
                        handleAnswer(userInput)
                      }
                    }}
                    disabled={!userInput}
                  >
                    확인
                  </button>
                </div>
              ) : currentQuestion.choices ? (
                // 선택지가 적으면 버튼 사용
                <div className="choice-buttons">
                  {currentQuestion.choices.map((choice, i) => (
                    <button
                      key={i}
                      className={`choice-button ${answers[currentQuestion.id] === choice ? 'selected' : ''}`}
                      onClick={() => handleChoiceClick(choice)}
                    >
                      {choice}
                    </button>
                  ))}
                </div>
              ) : currentQuestion.type === 'date' ? (
                // 날짜 입력
                <div className="input-group">
                  <input
                    type="date"
                    className="date-input"
                    value={userInput || answers[currentQuestion.id] as string || ''}
                    onChange={(e) => setUserInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && userInput) {
                        e.preventDefault()
                        e.stopPropagation()
                        handleAnswer(userInput)
                      }
                    }}
                  />
                  <button
                    className="submit-button"
                    onClick={() => {
                      if (userInput) {
                        handleAnswer(userInput)
                      }
                    }}
                    disabled={!userInput}
                  >
                    확인
                  </button>
                </div>
              ) : currentQuestion.type === 'number' ? (
                <div className="input-group">
                  <input
                    type="number"
                    className={`text-input ${validationError ? 'has-error' : ''}`}
                    placeholder={`숫자 입력${currentQuestion.unit ? ` (${currentQuestion.unit})` : ''}`}
                    value={userInput}
                    onChange={(e) => {
                      setUserInput(e.target.value)
                      setValidationError(null)
                    }}
                    onKeyPress={handleKeyPress}
                    autoFocus
                  />
                  {currentQuestion.unit && <span className="unit-label">{currentQuestion.unit}</span>}
                  <button className="submit-button" onClick={handleInputSubmit} disabled={!userInput.trim()}>확인</button>
                </div>
              ) : (
                <div className="input-group">
                  <input
                    type="text"
                    className={`text-input ${validationError ? 'has-error' : ''}`}
                    placeholder="입력해주세요"
                    value={userInput}
                    onChange={(e) => {
                      setUserInput(e.target.value)
                      setValidationError(null)
                    }}
                    onKeyPress={handleKeyPress}
                    autoFocus
                  />
                  <button className="submit-button" onClick={handleInputSubmit} disabled={!userInput.trim()}>확인</button>
                </div>
              )}
              {validationError && (
                <div className="validation-error">
                  ⚠️ {validationError}
                </div>
              )}
            </div>

            <div className="navigation-buttons">
              <button
                className="nav-button"
                onClick={() => currentQuestionIndex > 0 && setCurrentQuestionIndex(currentQuestionIndex - 1)}
                disabled={currentQuestionIndex === 0}
              >
                ← 이전
              </button>
              <span className="nav-info">{currentQuestionIndex + 1} / {questions.length}</span>
              {isEditing && allAnswered ? (
                <button
                  className="nav-button done-button"
                  onClick={() => setIsEditing(false)}
                >
                  ✅ 수정 완료
                </button>
              ) : (
                <button
                  className="nav-button"
                  onClick={() => currentQuestionIndex < questions.length - 1 && setCurrentQuestionIndex(currentQuestionIndex + 1)}
                  disabled={currentQuestionIndex === questions.length - 1}
                >
                  다음 →
                </button>
              )}
            </div>
          </>
        ) : null}
      </div>
    </div>
  )
}
