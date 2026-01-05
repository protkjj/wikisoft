import { useState, useEffect, useRef, useMemo } from 'react'
import './ChatBot.css'
import type { DiagnosticQuestion } from './types'

interface ChatBotProps {
  questions: DiagnosticQuestion[]
  onComplete: (answers: Record<string, string | number>) => void
  onBack: () => void
  initialAnswers?: Record<string, string | number>  // 기존 답변 유지용
}

export default function ChatBot({ questions, onComplete, onBack, initialAnswers = {} }: ChatBotProps) {
  const [answers, setAnswers] = useState<Record<string, string | number>>(initialAnswers)
  const [userInput, setUserInput] = useState('')
  const [isEditing, setIsEditing] = useState(false)  // 답변 수정 모드
  const questionRefs = useRef<(HTMLLIElement | null)[]>([])

  // 조건부 질문 필터링 - 조건을 만족하는 질문만 표시
  const visibleQuestions = useMemo(() => {
    return questions.filter(q => {
      // condition이 없으면 항상 표시
      if (!q.condition) return true

      // condition이 있으면 해당 조건 확인
      const { question_id, answer: requiredAnswer } = q.condition
      const currentAnswer = answers[question_id]

      // 조건 질문에 답변이 없으면 숨김
      if (currentAnswer === undefined) return false

      // 답변이 조건과 일치하면 표시
      return currentAnswer === requiredAnswer
    })
  }, [questions, answers])

  // 첫 번째 미응답 질문 인덱스로 시작 (기존 답변이 있으면)
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(() => {
    // visibleQuestions 계산 (초기화 시점)
    const visible = questions.filter(q => {
      if (!q.condition) return true
      const currentAnswer = initialAnswers[q.condition.question_id]
      if (currentAnswer === undefined) return false
      return currentAnswer === q.condition.answer
    })
    // 미응답 질문 찾기
    const firstUnanswered = visible.findIndex(q => initialAnswers[q.id] === undefined)
    return firstUnanswered === -1 ? 0 : firstUnanswered
  })

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

  // 현재 질문 (visibleQuestions 기준)
  const safeIndex = Math.min(currentQuestionIndex, visibleQuestions.length - 1)
  const currentQuestion = visibleQuestions[safeIndex]

  // 보이는 질문 중 답변된 개수
  const answeredCount = visibleQuestions.filter(q => answers[q.id] !== undefined).length
  const progress = (answeredCount / visibleQuestions.length) * 100
  const allAnswered = answeredCount === visibleQuestions.length

  // 현재 질문이 변경되면 해당 항목으로 스크롤 (사이드바만)
  useEffect(() => {
    const currentRef = questionRefs.current[safeIndex]
    if (currentRef) {
      // scrollIntoView를 사이드바 컨테이너 기준으로 제한
      currentRef.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  }, [safeIndex])

  // 다음 미응답 질문 인덱스 찾기
  const findNextUnanswered = (fromIndex: number, currentAnswers: Record<string, string | number>) => {
    for (let i = fromIndex + 1; i < visibleQuestions.length; i++) {
      if (currentAnswers[visibleQuestions[i].id] === undefined) {
        return i
      }
    }
    return -1  // 모두 응답됨
  }

  const handleAnswer = (value: string | number) => {
    if (!currentQuestion) return

    const newAnswers = {
      ...answers,
      [currentQuestion.id]: value
    }
    setAnswers(newAnswers)
    setUserInput('')

    // 다음 미응답 질문으로 이동 (없으면 현재 화면 유지)
    const nextUnanswered = findNextUnanswered(safeIndex, newAnswers)
    if (nextUnanswered !== -1) {
      setCurrentQuestionIndex(nextUnanswered)
    }
    // 모든 질문 완료 시 현재 화면 유지 (완료 버튼 표시)
  }

  const handleChoiceClick = (choice: string) => {
    handleAnswer(choice)
  }

  const handleInputSubmit = () => {
    if (!userInput.trim()) return
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

  // 새로운 카테고리 레이블
  const categoryLabels: Record<string, string> = {
    // 기존
    'data_quality': '📊 데이터 품질',
    'financial_assumptions': '💰 재무 가정',
    'retirement_settings': '🏖️ 퇴직 설정',
    'headcount_aggregates': '👥 인원 집계',
    'amount_aggregates': '💵 금액 집계',
    // 새로운 카테고리
    'basic_retirement': '📋 기초자료_퇴직급여',
    'employee_roster': '👤 재직자명부',
    'retiree_roster': '🚪 퇴직자명부',
    'employee_headcount': '👥 평가대상 인원',
    'retiree_headcount': '📊 퇴직자 인원',
    'retirement_estimate': '💰 퇴직금 추계액',
  }

  const getQuestionStatus = (index: number): 'answered' | 'current' | 'pending' | 'conditional' => {
    const q = visibleQuestions[index]
    if (!q) return 'pending'
    if (answers[q.id] !== undefined) return 'answered'
    if (index === safeIndex) return 'current'
    // 조건부 질문 표시
    if (q.condition) return 'conditional'
    return 'pending'
  }

  return (
    <div className="chatbot-layout">
      {/* 왼쪽 사이드바: 질문 목록 */}
      <div className="question-sidebar">
        <div className="sidebar-header">
          <h3>📋 질문 목록</h3>
          <p>{answeredCount} / {visibleQuestions.length} 완료</p>
        </div>

        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${progress}%` }}></div>
        </div>

        <ul className="question-list">
          {visibleQuestions.map((q, index) => {
            const status = getQuestionStatus(index)
            // '-' 이전 내용만 추출 (없으면 앞 15자)
            const preview = q.question.includes(' - ')
              ? q.question.split(' - ')[0]
              : q.question.substring(0, 15)
            const isConditional = !!q.condition
            return (
              <li
                key={q.id}
                ref={(el) => { questionRefs.current[index] = el }}
                className={`question-item ${status} ${isConditional ? 'conditional' : ''}`}
                onClick={() => handleQuestionClick(index)}
              >
                <span className="question-number">
                  {isConditional ? '↳' : index + 1}
                </span>
                <span className="question-preview">{preview}</span>
                {status === 'answered' && <span className="check-mark">✓</span>}
              </li>
            )
          })}
        </ul>

        {allAnswered && (
          <button className="complete-button" onClick={handleComplete}>
            ✅ 완료 → 파일 업로드
          </button>
        )}
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
            <p className="completion-subtitle">{visibleQuestions.length}개 질문에 모두 답변하셨습니다.</p>

            <div className="completion-summary">
              <p>이제 검증할 Excel 명부 파일을 업로드해주세요.</p>
            </div>

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
                📁 파일 업로드로 이동 →
              </button>
            </div>
          </div>
        ) : currentQuestion ? (
          // 질문 진행 중
          <>
            <div className="main-header">
              <div className={`category-badge ${currentQuestion.category}`}>
                {categoryLabels[currentQuestion.category] || currentQuestion.category}
              </div>
              <span className="question-id">{currentQuestion.id.toUpperCase()}</span>
            </div>

            {/* 조건부 질문 안내 */}
            {currentQuestion.condition && (
              <div className="conditional-notice">
                ↳ 이전 질문 답변에 따른 추가 질문입니다
              </div>
            )}

            <h2 className="question-text">{currentQuestion.question}</h2>

            {answers[currentQuestion.id] !== undefined && (
              <div className="answered-badge">
                ✓ 답변: <strong>{answers[currentQuestion.id]}</strong>
              </div>
            )}

            <div className="answer-area">
              {currentQuestion.choices ? (
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
              ) : currentQuestion.type === 'number' ? (
                <div className="input-group">
                  <input
                    type="number"
                    className="text-input"
                    placeholder={`숫자 입력${currentQuestion.unit ? ` (${currentQuestion.unit})` : ''}`}
                    value={userInput}
                    onChange={(e) => setUserInput(e.target.value)}
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
                    className="text-input"
                    placeholder="입력해주세요"
                    value={userInput}
                    onChange={(e) => setUserInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    autoFocus
                  />
                  <button className="submit-button" onClick={handleInputSubmit} disabled={!userInput.trim()}>확인</button>
                </div>
              )}
            </div>

            <div className="navigation-buttons">
              <button
                className="nav-button"
                onClick={() => safeIndex > 0 && setCurrentQuestionIndex(safeIndex - 1)}
                disabled={safeIndex === 0}
              >
                ← 이전
              </button>
              <span className="nav-info">{safeIndex + 1} / {visibleQuestions.length}</span>
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
                  onClick={() => safeIndex < visibleQuestions.length - 1 && setCurrentQuestionIndex(safeIndex + 1)}
                  disabled={safeIndex === visibleQuestions.length - 1}
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
