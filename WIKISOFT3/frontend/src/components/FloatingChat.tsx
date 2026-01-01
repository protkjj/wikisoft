import React, { useState, useImperativeHandle, forwardRef } from 'react'
import './FloatingChat.css'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export interface FloatingChatHandle {
  open: () => void
  setQuestion: (question: string) => void
  askQuestion: (question: string) => void
}

interface FloatingChatProps {
  validationContext?: any  // 검증 결과 컨텍스트
}

const FloatingChat = forwardRef<FloatingChatHandle, FloatingChatProps>(({ validationContext }, ref) => {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  // 외부에서 호출 가능한 메서드 노출
  useImperativeHandle(ref, () => ({
    open: () => setIsOpen(true),
    setQuestion: (question: string) => {
      setIsOpen(true)
      setInput(question)
    },
    askQuestion: (question: string) => {
      setIsOpen(true)
      setInput(question)
      // 약간의 딜레이 후 자동 전송
      setTimeout(() => {
        sendMessage(question)
      }, 100)
    }
  }))

  const sendMessage = async (messageText: string) => {
    if (!messageText.trim() || loading) return

    const userMessage: Message = { role: 'user', content: messageText.trim() }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const res = await fetch('/api/agent/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message: userMessage.content,
          context: validationContext ? {
            validation_results: validationContext,
            has_file: true
          } : undefined
        }),
      })

      if (!res.ok) throw new Error('Agent error')

      const data = await res.json()
      const assistantMessage: Message = {
        role: 'assistant',
        content: data.answer || '응답을 받지 못했습니다.',
      }
      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Agent error:', error)
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: '⚠️ 오류가 발생했습니다. 잠시 후 다시 시도해주세요.' },
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleSend = async () => {
    await sendMessage(input)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <>
      {/* Floating Button */}
      <button
        className="floating-chat-button"
        onClick={() => setIsOpen(!isOpen)}
        aria-label="AI 도움받기"
      >
        💬
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div className="floating-chat-window">
          <div className="chat-header">
            <h3>🤖 AI 도우미</h3>
            <button onClick={() => setIsOpen(false)} className="chat-close-btn">
              ✕
            </button>
          </div>

          <div className="chat-messages">
            {messages.length === 0 && (
              <div className="chat-welcome">
                안녕하세요! 검증 시스템에 대해 궁금한 점을 물어보세요.
              </div>
            )}
            {messages.map((msg, idx) => (
              <div key={idx} className={`chat-message ${msg.role}`}>
                <div className="message-content">{msg.content}</div>
              </div>
            ))}
            {loading && (
              <div className="chat-message assistant">
                <div className="message-content typing">응답 중...</div>
              </div>
            )}
          </div>

          <div className="chat-input-area">
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="질문을 입력하세요..."
              disabled={loading}
              className="chat-input"
            />
            <button onClick={handleSend} disabled={loading || !input.trim()} className="chat-send-btn">
              전송
            </button>
          </div>
        </div>
      )}
    </>
  )
})

export default FloatingChat
