import { useState } from 'react'
import './ChatBot.css'
import type { DiagnosticQuestion } from './types'

interface ChatBotProps {
  questions: DiagnosticQuestion[]
  onComplete: (answers: Record<string, string | number>) => void
  onBack: () => void
}

export default function ChatBot({ questions, onComplete, onBack }: ChatBotProps) {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [answers, setAnswers] = useState<Record<string, string | number>>({})
  const [userInput, setUserInput] = useState('')

  const currentQuestion = questions[currentQuestionIndex]
  const progress = ((Object.keys(answers).length) / questions.length) * 100
  const allAnswered = Object.keys(answers).length === questions.length

  const handleAnswer = (value: string | number) => {
    if (!currentQuestion) return

    const newAnswers = {
      ...answers,
      [currentQuestion.id]: value
    }
    setAnswers(newAnswers)
    setUserInput('')

    // 다음 질문으로 자동 이동
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1)
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

        {allAnswered && (
          <button className="complete-button" onClick={handleComplete}>
            ✅ 완료 → 파일 업로드
          </button>
        )}
      </div>

      {/* 오른쪽 메인: 현재 질문 */}
      <div className="question-main">
        <div className="main-header">
          <div className={`category-badge ${currentQuestion.category}`}>
            {categoryLabels[currentQuestion.category] || currentQuestion.category}
          </div>
          <span className="question-id">{currentQuestion.id.toUpperCase()}</span>
        </div>

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
            onClick={() => currentQuestionIndex > 0 && setCurrentQuestionIndex(currentQuestionIndex - 1)}
            disabled={currentQuestionIndex === 0}
          >
            ← 이전
          </button>
          <span className="nav-info">{currentQuestionIndex + 1} / {questions.length}</span>
          <button 
            className="nav-button"
            onClick={() => currentQuestionIndex < questions.length - 1 && setCurrentQuestionIndex(currentQuestionIndex + 1)}
            disabled={currentQuestionIndex === questions.length - 1}
          >
            다음 →
          </button>
        </div>
      </div>
    </div>
  )
}
