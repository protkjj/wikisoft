import { useState, FormEvent } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import './LoginPage.css'

type ValidationMode = 'roster' | 'full'

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [validationMode, setValidationMode] = useState<ValidationMode>('full')

  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const from = (location.state as any)?.from?.pathname || '/'

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    try {
      const loggedInUser = await login(username, password)
      localStorage.setItem('validationMode', validationMode)
      sessionStorage.setItem('newLogin', 'true')
      sessionStorage.removeItem('currentStep')

      // 관리자는 대시보드로, 일반 사용자는 검증 페이지로
      const isAdmin = loggedInUser.role === 'admin' || loggedInUser.role === 'superadmin'
      const destination = isAdmin ? '/dashboard' : (from === '/' ? '/' : from)
      navigate(destination, { replace: true })
    } catch (err: any) {
      if (err.response?.status === 401) {
        setError('아이디 또는 비밀번호가 올바르지 않습니다.')
      } else {
        setError('로그인 중 오류가 발생했습니다. 다시 시도해주세요.')
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="login-page">
      {/* Left Panel - Brand */}
      <div className="login-brand-panel">
        <div className="brand-content">
          <h1 className="brand-logo">OneCheck</h1>
          <p className="brand-tagline">퇴직연금 검증 자동화 플랫폼</p>
        </div>
      </div>

      {/* Right Panel - Form */}
      <div className="login-form-panel">
        <div className="form-wrapper">
          <div className="form-header">
            <h2 className="form-title">로그인</h2>
          </div>

          <form onSubmit={handleSubmit} className="login-form">
            {error && <div className="error-message">{error}</div>}

            <div className="form-group">
              <label htmlFor="username">사용자 ID</label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoFocus
                autoComplete="username"
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">비밀번호</label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
            </div>

            {/* Mode Selector - Segmented Control */}
            <div className="mode-selector">
              <div className="segmented-control">
                <button
                  type="button"
                  className={`segment ${validationMode === 'roster' ? 'selected' : ''}`}
                  onClick={() => setValidationMode('roster')}
                >
                  Basic
                </button>
                <button
                  type="button"
                  className={`segment ${validationMode === 'full' ? 'selected' : ''}`}
                  onClick={() => setValidationMode('full')}
                >
                  Complete
                </button>
              </div>
            </div>

            <button type="submit" className="login-button" disabled={isLoading}>
              {isLoading ? (
                <span className="loading-text">
                  <span className="spinner"></span>
                  로그인 중...
                </span>
              ) : (
                '로그인'
              )}
            </button>

            <button type="button" className="signup-button">회원가입</button>
          </form>

          <div className="login-footer">
            <p>관리자: admin / admin1234!</p>
            <p>사용자: user / user1234!</p>
          </div>
        </div>
      </div>
    </div>
  )
}
