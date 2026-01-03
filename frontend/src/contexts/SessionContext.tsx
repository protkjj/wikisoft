import { createContext, useContext, useState, useEffect, ReactNode } from 'react'

interface Session {
  sessionId: string | null
  createdAt: number | null
  expiresAt: number | null
}

interface SessionContextType {
  session: Session
  setSession: (sessionId: string) => void
  clearSession: () => void
  isSessionValid: () => boolean
}

const SessionContext = createContext<SessionContextType | undefined>(undefined)

// 세션 타임아웃: 2시간 (밀리초)
const SESSION_TIMEOUT_MS = 2 * 60 * 60 * 1000

export function SessionProvider({ children }: { children: ReactNode }) {
  const [session, setSessionState] = useState<Session>(() => {
    // localStorage에서 세션 복원
    const stored = localStorage.getItem('wikisoft3_session')
    if (stored) {
      try {
        const parsed: Session = JSON.parse(stored)
        // 만료 체크
        if (parsed.expiresAt && parsed.expiresAt > Date.now()) {
          return parsed
        }
      } catch (e) {
        // Session parsing failed - will use default session
      }
    }
    return { sessionId: null, createdAt: null, expiresAt: null }
  })

  // 세션이 변경될 때마다 localStorage 동기화
  useEffect(() => {
    if (session.sessionId) {
      localStorage.setItem('wikisoft3_session', JSON.stringify(session))
    } else {
      localStorage.removeItem('wikisoft3_session')
    }
  }, [session])

  const setSession = (sessionId: string) => {
    const now = Date.now()
    setSessionState({
      sessionId,
      createdAt: now,
      expiresAt: now + SESSION_TIMEOUT_MS
    })
  }

  const clearSession = () => {
    setSessionState({ sessionId: null, createdAt: null, expiresAt: null })
  }

  const isSessionValid = () => {
    if (!session.sessionId || !session.expiresAt) return false
    return session.expiresAt > Date.now()
  }

  return (
    <SessionContext.Provider value={{ session, setSession, clearSession, isSessionValid }}>
      {children}
    </SessionContext.Provider>
  )
}

export function useSession() {
  const context = useContext(SessionContext)
  if (!context) {
    throw new Error('useSession must be used within SessionProvider')
  }
  return context
}
