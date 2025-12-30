import { useState, useEffect, useRef } from 'react'
import './ChatBot.css'
import type { DiagnosticQuestion } from './types'

interface Message {
  type: 'bot' | 'user'
  content: string
  timestamp: Date
  question?: DiagnosticQuestion
}

interface ChatBotProps {
  questions: DiagnosticQuestion[]
  onComplete: (answers: Record<string, string | number>) => void
  onBack: () => void
}

export default function ChatBot({ questions, onComplete, onBack }: ChatBotProps) {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [answers, setAnswers] = useState<Record<string, string | number>>({})
  const [userInput, setUserInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const currentQuestion = questions[currentQuestionIndex]
  const progress = ((currentQuestionIndex) / questions.length) * 100

  // 초기 로드
  useEffect(() => {
    // 첫 질문 자동 표시
    // 특별한 초기화 작업 없음
  }, [])

  // 자동 스크롤 (필요 없음)
  useEffect(() => {
    // 자동 스크롤 제거
  }, [])

  const handleAnswer = (value: string | number) => {
    if (!currentQuestion) return

    // 답변 저장
    const newAnswers = {
      ...answers,
      [currentQuestion.id]: value
    }
    setAnswers(newAnswers)
    setUserInput('')

    // 다음 질문으로
    const nextIndex = currentQuestionIndex + 1
    setCurrentQuestionIndex(nextIndex)

    if (nextIndex >= questions.length) {
      // 완료
      setTimeout(() => {
        onComplete(newAnswers)
      }, 500)
    }
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

  const handleBack = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1)
    } else {
      onBack()
    }
  }

  const categoryLabels: Record<string, string> = {
    'data_quality': '📊 데이터 품질',
    'financial_assumptions': '💰 재무 가정',
    'retirement_settings': '🏖️ 퇴직 설정',
    'headcount_aggregates': '👥 인원 집계',
    'amount_aggregates': '💵 금액 집계'
  }

  return (
    <div className="content-section">
      <div className="chat-container">
        {/* 헤더 */}
        <div className="chat-header">
          <h3>📋 진단 질문</h3>
          <p>질문 {currentQuestionIndex + 1} / {questions.length}개</p>
        </div>

        {/* 진행률 */}
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${progress}%` }}></div>
        </div>

        {/* 질문 표시 */}
        {currentQuestionIndex < questions.length ? (
          <div className="question-form">
            {/* 카테고리 배지 */}
            <div className={`category-badge ${currentQuestion.category}`}>
              {categoryLabels[currentQuestion.category] || currentQuestion.category}
            </div>
            
            {/* 질문 ID */}
            <div className="question-id">{currentQuestion.id.toUpperCase()}</div>
            
            {/* 질문 텍스트 */}
            <h2 className="question-text">{currentQuestion.question}</h2>
            
            {/* 선택지 또는 입력 */}
            <div className="answer-area">
              {currentQuestion.choices ? (
                <div className="choice-buttons">
                  {currentQuestion.choices.map((choice, i) => (
                    <button
                      key={i}
                      className="choice-button"
                      onClick={() => handleChoiceClick(choice)}
                    >
                      {choice}
                    </button>
                  ))}
                </div>
              ) : currentQuestion.type === 'number' ? (
                <div className="number-input-group">
                  <input
                    type="number"
                    className="number-input"
                    placeholder={`숫자 입력${currentQuestion.unit ? ` (${currentQuestion.unit})` : ''}`}
                    value={userInput}
                    onChange={(e) => setUserInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    autoFocus
                  />
                  {currentQuestion.unit && (
                    <span className="unit-label">{currentQuestion.unit}</span>
                  )}
                  <button
                    className="submit-button"
                    onClick={handleInputSubmit}
                    disabled={!userInput.trim()}
                  >
                    다음 →
                  </button>
                </div>
              ) : (
                <div className="text-input-group">
                  <input
                    type="text"
                    className="text-input"
                    placeholder="입력해주세요"
                    value={userInput}
                    onChange={(e) => setUserInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    autoFocus
                  />
                  <button
                    className="submit-button"
                    onClick={handleInputSubmit}
                    disabled={!userInput.trim()}
                  >
                    다음 →
                  </button>
                </div>
              )}
            </div>

            {/* 진행 정보 */}
            <div className="progress-info">
              <div className="question-counter">
                질문 <strong>{currentQuestionIndex + 1}</strong> / {questions.length}
              </div>
            </div>
          </div>
        ) : (
          <div className="completion-message">
            <div className="icon">🎉</div>
            <h3>진단 완료!</h3>
            <p>모든 질문에 답변하셨습니다.</p>
            <p style={{ marginTop: '1rem', color: '#888', fontSize: '0.9rem' }}>
              다음 단계로 자동으로 이동합니다...
            </p>
          </div>
        )}
      </div>

      {/* 하단 액션 */}
      <div className="actions" style={{ marginTop: '2rem', display: 'flex', gap: '1rem' }}>
        <button className="btn-secondary" onClick={handleBack}>
          ← {currentQuestionIndex > 0 ? '이전' : '처음으로'}
        </button>
      </div>
    </div>
  )
}
