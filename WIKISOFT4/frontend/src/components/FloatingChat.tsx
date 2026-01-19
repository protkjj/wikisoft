import React, { useState, useImperativeHandle, forwardRef, useRef, useEffect, useCallback } from 'react'
import './FloatingChat.css'

// 메시지 데이터 구조
export interface Message {
  id: string
  text: string
  sender: 'user' | 'bot'
  timestamp: Date
}

export interface FloatingChatHandle {
  open: () => void
  setQuestion: (question: string) => void
  askQuestion: (question: string) => void
}

interface FloatingChatProps {
  validationContext?: any
}

const FloatingChat = forwardRef<FloatingChatHandle, FloatingChatProps>(({ validationContext }, ref) => {
  // 상태 관리
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [panelWidth, setPanelWidth] = useState(420)
  const [isResizing, setIsResizing] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const panelRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isTyping])

  // 패널 열릴 때 입력창 포커스
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 300)
    }
  }, [isOpen])

  // Resize handlers
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    setIsResizing(true)
  }, [])

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return
      const newWidth = window.innerWidth - e.clientX
      setPanelWidth(Math.min(Math.max(320, newWidth), 800))
    }

    const handleMouseUp = () => {
      setIsResizing(false)
    }

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
      document.body.style.cursor = 'ew-resize'
      document.body.style.userSelect = 'none'
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
  }, [isResizing])

  useImperativeHandle(ref, () => ({
    open: () => setIsOpen(true),
    setQuestion: (question: string) => {
      setIsOpen(true)
      setInputValue(question)
    },
    askQuestion: (question: string) => {
      setIsOpen(true)
      setInputValue(question)
      setTimeout(() => {
        handleSend(question)
      }, 100)
    }
  }))

  // 메시지 전송 로직
  const handleSend = async (messageText?: string) => {
    const text = messageText || inputValue
    if (!text.trim() || isTyping) return

    // 1. 사용자 메시지 생성 및 추가
    const userMessage: Message = {
      id: Date.now().toString(),
      text: text.trim(),
      sender: 'user',
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, userMessage])
    setInputValue('')
    setIsTyping(true)

    // 2. API 호출
    try {
      const res = await fetch('/api/agent/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage.text,
          context: validationContext ? {
            validation_results: validationContext,
            has_file: true
          } : undefined
        }),
      })

      if (!res.ok) throw new Error('Agent error')

      const data = await res.json()
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: data.response || data.answer || '응답을 받지 못했습니다.',
        sender: 'bot',
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, botMessage])
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: '오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
        sender: 'bot',
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsTyping(false)
      // 메시지 전송 후 입력창에 포커스
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }

  // Enter 키 전송
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('ko-KR', {
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <>
      {/* Floating Button */}
      {!isOpen && (
        <button
          className="chat-fab"
          onClick={() => setIsOpen(true)}
          aria-label="AI 도움받기"
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
        </button>
      )}

      {/* Overlay */}
      {isOpen && (
        <div
          className="chat-overlay"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Side Panel */}
      <div
        ref={panelRef}
        className={`chat-panel ${isOpen ? 'open' : ''}`}
        style={{ width: isOpen ? panelWidth : undefined }}
      >
        {/* Resize Handle */}
        <div
          className="chat-resize-handle"
          onMouseDown={handleMouseDown}
        />
        {/* Header */}
        <div className="chat-header">
          <div className="chat-header-title">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
            <span>AI 도우미</span>
          </div>
          <button
            className="chat-close-btn"
            onClick={() => setIsOpen(false)}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        {/* Messages */}
        <div className="chat-messages">
          {messages.length === 0 && (
            <div className="chat-empty">
              <p>검증 시스템에 대해 궁금한 점을 물어보세요.</p>
            </div>
          )}

          {messages.map((msg) => (
            <div key={msg.id} className={`chat-message ${msg.sender === 'user' ? 'user' : 'assistant'}`}>
              <div className="message-avatar">
                {msg.sender === 'user' ? '나' : 'AI'}
              </div>
              <div className="message-bubble-wrapper">
                <div className="message-bubble">
                  <p>{msg.text}</p>
                </div>
                <span className="message-time">{formatTime(msg.timestamp)}</span>
              </div>
            </div>
          ))}

          {isTyping && (
            <div className="chat-message assistant">
              <div className="message-avatar">AI</div>
              <div className="message-bubble-wrapper">
                <div className="message-bubble">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="chat-input-area">
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={e => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="질문을 입력하세요..."
            disabled={isTyping}
            className="chat-input"
          />
          <button
            onClick={() => handleSend()}
            disabled={isTyping || !inputValue.trim()}
            className="chat-send-btn"
          >
            전송
          </button>
        </div>
      </div>
    </>
  )
})

export default FloatingChat
