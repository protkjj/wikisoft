import { useState, useEffect, useMemo, useRef } from 'react'
import './DiagnosticWizard.css'
import ChatBot from './ChatBot'
import type { DiagnosticQuestion } from '../types'

// 검증 규칙 정의
interface ValidationRule {
  validate: (value: string | number | string[] | undefined, question: DiagnosticQuestion) => string | null
}

const VALIDATION_RULES: Record<string, ValidationRule> = {
  email: {
    validate: (value) => {
      if (!value || value === '') return null
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      return emailRegex.test(String(value)) ? null : '올바른 이메일 형식이 아닙니다 (예: example@email.com)'
    }
  },
  phone: {
    validate: (value) => {
      if (!value || value === '') return null
      const phoneRegex = /^[\d\-\s]+$/
      return phoneRegex.test(String(value)) ? null : '올바른 전화번호 형식이 아닙니다 (예: 02-1234-5678)'
    }
  },
  number: {
    validate: (value, question) => {
      if (value === undefined || value === '') return null
      const num = typeof value === 'number' ? value : parseFloat(String(value))
      if (isNaN(num)) return '숫자만 입력해주세요'
      if (num < 0) return '음수는 입력할 수 없습니다'
      // 나이/연령 관련 필드 (18~120)
      if (question.unit === '세' && (num < 18 || num > 120)) {
        return '18~120 범위의 값을 입력해주세요'
      }
      // 인원수 필드 (0~100000)
      if (question.unit === '명' && num > 100000) {
        return '인원수가 너무 큽니다'
      }
      // 퍼센트 필드 (0~100)
      if (question.unit === '%' && (num < 0 || num > 100)) {
        return '0~100 범위의 값을 입력해주세요'
      }
      return null
    }
  },
  date: {
    validate: (value) => {
      if (!value || value === '') return null
      const dateStr = String(value)
      // YYYY-MM-DD 형식 체크
      const dateRegex = /^\d{4}-\d{2}-\d{2}$/
      if (!dateRegex.test(dateStr)) return '올바른 날짜 형식이 아닙니다'
      const date = new Date(dateStr)
      if (isNaN(date.getTime())) return '유효하지 않은 날짜입니다'
      return null
    }
  }
}

// 질문 ID별 특수 검증 규칙 매핑
const QUESTION_VALIDATION_MAP: Record<string, string> = {
  '1-3': 'phone',   // 전화번호
  '1-4': 'email',   // 이메일
}

// 섹션 정의 (7페이지)
const SECTIONS = [
  { id: 1, title: '일반사항', icon: '📋', prefix: '1-' },
  { id: 2, title: '평가대상/퇴직급여', icon: '👥', prefix: '2-' },
  { id: 3, title: '사외적립자산', icon: '💰', prefix: '3-' },
  { id: 4, title: '제도 주요사항', icon: '⚙️', prefix: '4-' },
  { id: 5, title: '할인율', icon: '📊', prefix: '5-' },
  { id: 6, title: '적립비율', icon: '📈', prefix: '6-' },
  { id: 7, title: '특이사항', icon: '📝', prefix: '7-' },
]

interface DiagnosticWizardProps {
  questions: DiagnosticQuestion[]
  onComplete: (answers: Record<string, string | number | string[]>) => void
  onBack: () => void
  initialAnswers?: Record<string, string | number | string[]>
  mode?: 'roster' | 'full'
}

// 질문 검증 함수
function validateQuestion(question: DiagnosticQuestion, value: string | number | string[] | undefined): string | null {
  // 그룹 타입은 검증 제외
  if (question.type === 'group') return null

  // 특수 검증 규칙 (질문 ID 기반)
  const specialRule = QUESTION_VALIDATION_MAP[question.id]
  if (specialRule && VALIDATION_RULES[specialRule]) {
    const error = VALIDATION_RULES[specialRule].validate(value, question)
    if (error) return error
  }

  // 타입별 검증
  if (question.type === 'number' && VALIDATION_RULES.number) {
    const error = VALIDATION_RULES.number.validate(value, question)
    if (error) return error
  }

  if (question.type === 'date' && VALIDATION_RULES.date) {
    const error = VALIDATION_RULES.date.validate(value, question)
    if (error) return error
  }

  return null
}

export default function DiagnosticWizard({
  questions,
  onComplete,
  onBack,
  initialAnswers = {},
  mode = 'full'
}: DiagnosticWizardProps) {
  // 질문이 있는 섹션만 필터링
  const activeSections = useMemo(() => {
    return SECTIONS.filter(section =>
      questions.some(q => q.id.startsWith(section.prefix))
    )
  }, [questions])

  // 명부만 모드: 단일 페이지로 표시
  const isSinglePageMode = mode === 'roster'

  const [currentSection, setCurrentSection] = useState(() => activeSections[0]?.id || 1)
  const [answers, setAnswers] = useState<Record<string, string | number | string[]>>(initialAnswers)
  // 그룹 펼침/접기 상태 (기본: 모두 펼침)
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({})
  // 검증 에러 상태
  const [errors, setErrors] = useState<Record<string, string>>({})
  const questionsContainerRef = useRef<HTMLDivElement>(null)

  // 초기화: 모든 그룹을 펼침 상태로
  useEffect(() => {
    const groups = questions.filter(q => q.type === 'group')
    const initialExpanded: Record<string, boolean> = {}
    groups.forEach(g => {
      initialExpanded[g.id] = true // 기본 펼침
    })
    setExpandedGroups(initialExpanded)
  }, [questions])

  // 섹션별 질문 그룹화
  const questionsBySection = useMemo(() => {
    const grouped: Record<number, DiagnosticQuestion[]> = {}
    activeSections.forEach(section => {
      grouped[section.id] = questions.filter(q => q.id.startsWith(section.prefix))
    })
    return grouped
  }, [questions, activeSections])

  // 현재 섹션의 질문 (조건부 필터링 포함)
  const currentQuestions = useMemo(() => {
    const sectionQuestions = questionsBySection[currentSection] || []
    return sectionQuestions.filter(q => {
      if (!q.condition) return true
      const { question_id, answer: requiredAnswer } = q.condition
      const currentAnswer = answers[question_id]
      if (currentAnswer === undefined) return false
      return currentAnswer === requiredAnswer
    })
  }, [questionsBySection, currentSection, answers])

  // 그룹별로 질문 구조화 (중첩 그룹 지원)
  const groupedQuestions = useMemo(() => {
    // ID 기준 정렬 함수 (2-0 < 2-a < 2-b)
    const sortById = (a: DiagnosticQuestion, b: DiagnosticQuestion) => a.id.localeCompare(b.id)

    // 최상위 그룹만 추출 (parent가 없는 그룹) - ID순 정렬
    const topLevelGroups = currentQuestions
      .filter(q => q.type === 'group' && !q.parent)
      .sort(sortById)
    // 서브 그룹 (parent가 있는 그룹)
    const subGroups = currentQuestions.filter(q => q.type === 'group' && q.parent)
    // 일반 질문
    const normalQuestions = currentQuestions.filter(q => q.type !== 'group')

    const result: Array<{
      group: DiagnosticQuestion | null
      subGroups: Array<{ group: DiagnosticQuestion; children: DiagnosticQuestion[] }>
      children: DiagnosticQuestion[]
    }> = []

    // 그룹에 속하지 않는 독립 질문을 먼저 표시 (작성기준일 등) - ID순 정렬
    const orphanQuestions = normalQuestions
      .filter(q => !q.parent)
      .sort(sortById)
    orphanQuestions.forEach(q => {
      result.push({ group: null, subGroups: [], children: [q] })
    })

    // 최상위 그룹 처리
    topLevelGroups.forEach(topGroup => {
      const mySubGroups = subGroups
        .filter(sg => sg.parent === topGroup.id)
        .sort(sortById)
      const subGroupsWithChildren = mySubGroups.map(sg => ({
        group: sg,
        children: normalQuestions.filter(q => q.parent === sg.id).sort(sortById)
      }))
      // 직접 자식 (서브그룹이 아닌)
      const directChildren = normalQuestions
        .filter(q => q.parent === topGroup.id)
        .sort(sortById)

      result.push({
        group: topGroup,
        subGroups: subGroupsWithChildren,
        children: directChildren
      })
    })

    return result
  }, [currentQuestions])

  // 섹션별 완료 상태 (group 타입 제외하고 계산)
  const sectionStatus = useMemo(() => {
    return activeSections.map(section => {
      const sectionQuestions = questionsBySection[section.id] || []
      const visibleQuestions = sectionQuestions.filter(q => {
        // group 타입은 답변 대상에서 제외
        if (q.type === 'group') return false
        if (!q.condition) return true
        const { question_id, answer: requiredAnswer } = q.condition
        return answers[question_id] === requiredAnswer
      })
      const answeredCount = visibleQuestions.filter(q => answers[q.id] !== undefined).length
      const total = visibleQuestions.length
      return {
        ...section,
        total,
        answered: answeredCount,
        completed: total > 0 && answeredCount === total,
        progress: total > 0 ? (answeredCount / total) * 100 : 0
      }
    })
  }, [questionsBySection, answers, activeSections])

  // 전체 진행률
  const overallProgress = useMemo(() => {
    const totalAnswered = sectionStatus.reduce((sum, s) => sum + s.answered, 0)
    const totalQuestions = sectionStatus.reduce((sum, s) => sum + s.total, 0)
    return totalQuestions > 0 ? (totalAnswered / totalQuestions) * 100 : 0
  }, [sectionStatus])

  // 모든 섹션 완료 여부 (섹션 7 '특이사항'은 선택사항)
  const allCompleted = sectionStatus
    .filter(s => s.id !== 7) // 특이사항 제외
    .every(s => s.completed || s.total === 0)

  // 미완료 질문 목록 (섹션 7 제외)
  const unansweredQuestions = useMemo(() => {
    const unanswered: Array<{ sectionTitle: string; questionText: string; questionId: string }> = []

    activeSections
      .filter(s => s.id !== 7) // 특이사항 제외
      .forEach(section => {
        const sectionQuestions = questionsBySection[section.id] || []
        sectionQuestions.forEach(q => {
          // group 타입은 제외
          if (q.type === 'group') return
          // 조건부 질문 체크
          if (q.condition) {
            const { question_id, answer: requiredAnswer } = q.condition
            if (answers[question_id] !== requiredAnswer) return
          }
          // 미답변 질문
          if (answers[q.id] === undefined) {
            unanswered.push({
              sectionTitle: section.title,
              questionText: q.question.length > 30 ? q.question.slice(0, 30) + '...' : q.question,
              questionId: q.id
            })
          }
        })
      })

    return unanswered
  }, [activeSections, questionsBySection, answers])

  // 현재 섹션이 마지막 섹션인지
  const isLastSection = currentSection === activeSections[activeSections.length - 1]?.id

  // 답변 처리 (검증 포함)
  const handleAnswer = (questionId: string, value: string | number | string[]) => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: value
    }))

    // 해당 질문 찾아서 검증
    const question = questions.find(q => q.id === questionId)
    if (question) {
      const error = validateQuestion(question, value)
      setErrors(prev => {
        const newErrors = { ...prev }
        if (error) {
          newErrors[questionId] = error
        } else {
          delete newErrors[questionId]
        }
        return newErrors
      })
    }
  }

  // 그룹 펼침/접기 토글
  const toggleGroup = (groupId: string) => {
    setExpandedGroups(prev => ({
      ...prev,
      [groupId]: !prev[groupId]
    }))
  }

  // 그룹 합계 계산 (중첩 그룹 지원)
  const calculateGroupTotal = (groupId: string): number => {
    const children = currentQuestions.filter(q => q.parent === groupId)
    let total = 0
    children.forEach(child => {
      if (child.type === 'group') {
        // 중첩 그룹이면 재귀적으로 합계 계산
        total += calculateGroupTotal(child.id)
      } else {
        const val = answers[child.id]
        if (typeof val === 'number') {
          total += val
        } else if (typeof val === 'string' && !isNaN(parseFloat(val))) {
          total += parseFloat(val)
        }
      }
    })
    return total
  }

  // 질문 목록 맨 위로 스크롤
  const scrollToTop = () => {
    // 즉시 스크롤 (DOM 업데이트 전)
    if (questionsContainerRef.current) {
      questionsContainerRef.current.scrollTop = 0
    }
    // DOM 업데이트 후 다시 스크롤 (확실하게)
    setTimeout(() => {
      if (questionsContainerRef.current) {
        questionsContainerRef.current.scrollTop = 0
      }
      // 페이지 전체도 위로
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }, 100)
  }

  // 섹션 이동
  const goToSection = (sectionId: number) => {
    setCurrentSection(sectionId)
    scrollToTop()
  }

  // 현재 섹션의 검증 에러 체크
  const currentSectionErrors = useMemo(() => {
    return currentQuestions
      .filter(q => q.type !== 'group')
      .filter(q => errors[q.id])
      .map(q => ({ id: q.id, error: errors[q.id] }))
  }, [currentQuestions, errors])

  const goNext = () => {
    // 현재 섹션에 검증 에러가 있으면 이동 불가
    if (currentSectionErrors.length > 0) {
      // 첫 번째 에러 필드로 스크롤
      const firstErrorId = currentSectionErrors[0].id
      const errorElement = document.querySelector(`[data-question-id="${firstErrorId}"]`)
      if (errorElement) {
        errorElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }
      return
    }

    // 다음 섹션으로 이동 (activeSections 기반)
    const currentIndex = activeSections.findIndex(s => s.id === currentSection)
    if (currentIndex < activeSections.length - 1) {
      setCurrentSection(activeSections[currentIndex + 1].id)
      scrollToTop()
    }
  }

  const goPrev = () => {
    // 이전 섹션으로 이동 (activeSections 기반)
    const currentIndex = activeSections.findIndex(s => s.id === currentSection)
    if (currentIndex > 0) {
      setCurrentSection(activeSections[currentIndex - 1].id)
      scrollToTop()
    }
  }

  // 완료 처리
  const handleComplete = () => {
    onComplete(answers)
  }

  // 질문이 없으면 빈 화면
  if (!questions || questions.length === 0) {
    return (
      <div className="wizard-container">
        <div className="wizard-empty">
          <span className="empty-icon">⚠️</span>
          <h2>질문을 불러올 수 없습니다</h2>
          <button onClick={onBack}>← 돌아가기</button>
        </div>
      </div>
    )
  }

  const currentSectionInfo = sectionStatus.find(s => s.id === currentSection)
  const currentSectionData = activeSections.find(s => s.id === currentSection)
  const currentSectionIndex = activeSections.findIndex(s => s.id === currentSection)

  // 명부만 모드: ChatBot 컴포넌트 사용 (WIKISOFT3와 동일)
  if (isSinglePageMode) {
    return (
      <ChatBot
        questions={questions}
        onComplete={onComplete}
        onBack={onBack}
        initialAnswers={initialAnswers}
      />
    )
  }

  return (
    <div className="wizard-container">
      {/* 상단 스테퍼 */}
      <div className="wizard-stepper">
        {sectionStatus.map((section, idx) => (
          <div
            key={section.id}
            className={`stepper-item ${section.id === currentSection ? 'active' : ''} ${section.completed ? 'completed' : ''}`}
            onClick={() => goToSection(section.id)}
          >
            <div className="stepper-label">
              <span className="stepper-number">{idx + 1}</span>
              <span className="stepper-title">{section.title}</span>
              <span className="stepper-count">{section.answered}/{section.total}</span>
            </div>
            {idx < sectionStatus.length - 1 && (
              <div className={`stepper-line ${section.completed ? 'completed' : ''}`} />
            )}
          </div>
        ))}
      </div>

      {/* 전체 진행률 바 */}
      <div className="wizard-overall-progress">
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${overallProgress}%` }} />
        </div>
        <span className="progress-text">{Math.round(overallProgress)}% 완료</span>
      </div>

      {/* 섹션 헤더 */}
      <div className="wizard-section-header">
        <h2>
          <span className="section-icon">{currentSectionData?.icon}</span>
          {currentSectionIndex + 1}. {currentSectionData?.title}
        </h2>
        <p className="section-progress">
          {currentSectionInfo?.answered || 0} / {currentSectionInfo?.total || 0} 질문 완료
        </p>
      </div>

      {/* 질문 목록 */}
      <div className="wizard-questions" ref={questionsContainerRef}>
        {groupedQuestions.map(({ group, subGroups, children }, idx) => (
          <div key={group?.id || `standalone-${idx}`} className="question-group-container">
            {/* 최상위 그룹 헤더 */}
            {group && (
              <div
                className={`group-header ${expandedGroups[group.id] ? 'expanded' : 'collapsed'}`}
                onClick={() => toggleGroup(group.id)}
              >
                <div className="group-header-left">
                  <span className={`collapse-arrow ${expandedGroups[group.id] ? 'expanded' : ''}`}>
                    ▶
                  </span>
                  <span className="group-title">{group.question}</span>
                </div>
                <div className="group-header-right">
                  {group.calculated && (
                    <span className="group-total">
                      합계: {calculateGroupTotal(group.id).toLocaleString()}
                      {(children[0]?.unit || subGroups[0]?.children[0]?.unit) && ` ${children[0]?.unit || subGroups[0]?.children[0]?.unit}`}
                    </span>
                  )}
                </div>
              </div>
            )}

            {/* 그룹 내용 (펼침 상태일 때만) */}
            {(group ? expandedGroups[group.id] : true) && (
              <div className={`group-children ${group ? 'has-group' : ''}`}>
                {/* 서브 그룹이 있는 경우 */}
                {subGroups.map(({ group: subGroup, children: subChildren }) => (
                  <div key={subGroup.id} className="subgroup-container">
                    <div
                      className={`subgroup-header ${expandedGroups[subGroup.id] ? 'expanded' : 'collapsed'}`}
                      onClick={() => toggleGroup(subGroup.id)}
                    >
                      <div className="group-header-left">
                        <span className={`collapse-arrow ${expandedGroups[subGroup.id] ? 'expanded' : ''}`}>
                          ▶
                        </span>
                        <span className="subgroup-title">{subGroup.question}</span>
                      </div>
                      <div className="group-header-right">
                        {subGroup.calculated && (
                          <span className="group-total">
                            {calculateGroupTotal(subGroup.id).toLocaleString()}
                            {subChildren[0]?.unit && ` ${subChildren[0].unit}`}
                          </span>
                        )}
                        <span className="group-count">
                          {subChildren.filter(c => answers[c.id] !== undefined).length}/{subChildren.length}
                        </span>
                      </div>
                    </div>
                    {expandedGroups[subGroup.id] && (
                      <div className="subgroup-children">
                        {subChildren.map(question => (
                          <QuestionCard
                            key={question.id}
                            question={question}
                            value={answers[question.id]}
                            onChange={(value) => handleAnswer(question.id, value)}
                            isChild={true}
                            error={errors[question.id]}
                          />
                        ))}
                      </div>
                    )}
                  </div>
                ))}

                {/* 직접 자식 질문 (서브그룹이 없는 경우) */}
                {children.map(question => (
                  <QuestionCard
                    key={question.id}
                    question={question}
                    value={answers[question.id]}
                    onChange={(value) => handleAnswer(question.id, value)}
                    isChild={!!question.parent}
                    error={errors[question.id]}
                  />
                ))}
              </div>
            )}
          </div>
        ))}

        {currentQuestions.length === 0 && (
          <div className="no-questions">
            이 섹션에는 표시할 질문이 없습니다.
          </div>
        )}
      </div>

      {/* 하단 네비게이션 */}
      <div className="wizard-navigation">
        <button
          className="nav-btn prev"
          onClick={goPrev}
          disabled={currentSectionIndex === 0}
        >
          ← 이전
        </button>

        <div className="nav-info">
          <span>{currentSectionIndex + 1} / {activeSections.length}</span>
        </div>

        {isLastSection ? (
          <div className="complete-btn-wrapper">
            <button
              className="nav-btn complete"
              onClick={handleComplete}
              disabled={!allCompleted}
            >
              {allCompleted ? '✅ 완료 → 검증 시작' : `미완료 ${unansweredQuestions.length}개`}
            </button>
            {!allCompleted && unansweredQuestions.length > 0 && (
              <div className="unanswered-tooltip">
                <div className="tooltip-header">⚠️ 답변이 필요한 질문</div>
                <ul className="tooltip-list">
                  {unansweredQuestions.slice(0, 5).map((q, idx) => (
                    <li key={q.questionId}>
                      <span className="section-badge">{q.sectionTitle}</span>
                      {q.questionText}
                    </li>
                  ))}
                  {unansweredQuestions.length > 5 && (
                    <li className="more-count">...외 {unansweredQuestions.length - 5}개</li>
                  )}
                </ul>
              </div>
            )}
          </div>
        ) : (
          <button
            className="nav-btn next"
            onClick={goNext}
          >
            다음 →
          </button>
        )}
      </div>
    </div>
  )
}

// 개별 질문 카드 컴포넌트
interface QuestionCardProps {
  question: DiagnosticQuestion
  value: string | number | string[] | undefined
  onChange: (value: string | number | string[]) => void
  isChild?: boolean
  error?: string
}

function QuestionCard({ question, value, onChange, isChild = false, error }: QuestionCardProps) {
  const [inputValue, setInputValue] = useState('')
  const [isComposing, setIsComposing] = useState(false)  // 한글 IME 조합 상태
  const cardRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement | HTMLTextAreaElement>(null)

  useEffect(() => {
    // 숫자/텍스트 입력의 경우 기존 값 복원
    if (value !== undefined && (question.type === 'number' || question.type === 'text' || question.type === 'textarea')) {
      setInputValue(String(value))
    }
  }, [value, question.type])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setInputValue(e.target.value)
  }

  const handleInputBlur = () => {
    if (inputValue.trim()) {
      if (question.type === 'number') {
        onChange(parseFloat(inputValue) || 0)
      } else {
        onChange(inputValue)
      }
    }
  }

  // 한글 IME 조합 시작
  const handleCompositionStart = () => {
    setIsComposing(true)
  }

  // 한글 IME 조합 완료
  const handleCompositionEnd = (e: React.CompositionEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setIsComposing(false)
    setInputValue(e.currentTarget.value)
  }

  // 다음 입력 필드로 포커스 이동
  const focusNextInput = (currentElement: HTMLElement) => {
    const form = currentElement.closest('.wizard-questions')
    if (!form) return

    const inputs = Array.from(form.querySelectorAll<HTMLElement>(
      'input:not([type="checkbox"]):not([type="radio"]), textarea, select'
    ))
    const currentIndex = inputs.indexOf(currentElement)

    if (currentIndex >= 0 && currentIndex < inputs.length - 1) {
      inputs[currentIndex + 1].focus()
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    // 한글 조합 중이면 무시
    if (isComposing) return

    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      // Enter 키 누르면 값 저장
      if (inputValue.trim()) {
        if (question.type === 'number') {
          onChange(parseFloat(inputValue) || 0)
        } else {
          onChange(inputValue)
        }
      }
      // 포커스를 다음 필드로 이동
      focusNextInput(e.target as HTMLElement)
    }
  }

  // 포커스 시 해당 질문으로 부드럽게 스크롤
  const handleFocus = () => {
    if (cardRef.current) {
      cardRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }

  const handleChoiceClick = (choice: string) => {
    onChange(choice)
  }

  const handleMultiSelectToggle = (choice: string) => {
    const currentValues = Array.isArray(value) ? value : []
    if (currentValues.includes(choice)) {
      onChange(currentValues.filter(v => v !== choice))
    } else {
      onChange([...currentValues, choice])
    }
  }

  const isAnswered = value !== undefined && value !== '' &&
    (Array.isArray(value) ? value.length > 0 : true)

  // 단답형(text, textarea)은 세로 레이아웃
  const isVerticalLayout = question.type === 'text' || question.type === 'textarea'

  return (
    <div
      ref={cardRef}
      className={`question-card ${isChild ? 'child' : ''} ${isAnswered ? 'answered' : ''} ${isVerticalLayout ? 'vertical' : ''} ${error ? 'has-error' : ''}`}
      data-question-id={question.id}
    >
      <div className={isVerticalLayout ? 'question-column' : 'question-row'}>
        <div className={isVerticalLayout ? 'question-header-vertical' : 'question-left'}>
          <label className="question-label">
            {question.question}
          </label>
        </div>

        <div className={isVerticalLayout ? 'question-input-vertical' : 'question-right'}>
          {question.type === 'choice' && question.choices && (
            question.choices.length > 6 ? (
              // 선택지가 많으면 드롭다운
              <select
                className="choice-select"
                value={typeof value === 'string' ? value : ''}
                onChange={(e) => handleChoiceClick(e.target.value)}
                onFocus={handleFocus}
              >
                <option value="">선택하세요</option>
                {question.choices.map(choice => (
                  <option key={choice} value={choice}>{choice}</option>
                ))}
              </select>
            ) : (
              // 선택지가 적으면 버튼
              <div className="choice-group compact">
                {question.choices.map(choice => (
                  <button
                    key={choice}
                    className={`choice-btn ${value === choice ? 'selected' : ''}`}
                    onClick={() => handleChoiceClick(choice)}
                  >
                    {choice}
                  </button>
                ))}
              </div>
            )
          )}

          {question.type === 'multiselect' && question.choices && (
            <div className="multiselect-group">
              {question.choices.map(choice => (
                <label key={choice} className="multiselect-item">
                  <input
                    type="checkbox"
                    checked={Array.isArray(value) && value.includes(choice)}
                    onChange={() => handleMultiSelectToggle(choice)}
                  />
                  <span>{choice}</span>
                </label>
              ))}
            </div>
          )}

          {question.type === 'number' && (
            <div className="input-wrapper">
              <input
                type="number"
                value={inputValue}
                onChange={handleInputChange}
                onBlur={handleInputBlur}
                onKeyDown={handleKeyDown}
                onFocus={handleFocus}
                onCompositionStart={handleCompositionStart}
                onCompositionEnd={handleCompositionEnd}
                placeholder="0"
              />
              {question.unit && <span className="input-unit">{question.unit}</span>}
            </div>
          )}

          {question.type === 'text' && (
            <input
              type="text"
              value={inputValue}
              onChange={handleInputChange}
              onBlur={handleInputBlur}
              onKeyDown={handleKeyDown}
              onFocus={handleFocus}
              onCompositionStart={handleCompositionStart}
              onCompositionEnd={handleCompositionEnd}
              placeholder="입력"
            />
          )}

          {question.type === 'date' && (
            <input
              type="date"
              value={typeof value === 'string' ? value : ''}
              onChange={(e) => onChange(e.target.value)}
              onFocus={handleFocus}
            />
          )}

          {question.type === 'textarea' && (
            <textarea
              value={inputValue}
              onChange={handleInputChange}
              onBlur={handleInputBlur}
              onKeyDown={handleKeyDown}
              onFocus={handleFocus}
              onCompositionStart={handleCompositionStart}
              onCompositionEnd={handleCompositionEnd}
              placeholder="자유롭게 작성해주세요"
              rows={2}
            />
          )}
        </div>
      </div>

      {/* 검증 에러 메시지 */}
      {error && (
        <div className="question-error">
          <span className="error-icon">⚠</span>
          {error}
        </div>
      )}
    </div>
  )
}
