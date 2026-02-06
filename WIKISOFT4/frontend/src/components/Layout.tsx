import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import ThemeToggle from './ThemeToggle'
import './Layout.css'

export default function Layout() {
  const { user, isAuthenticated, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const handleLogoClick = (e: React.MouseEvent) => {
    e.preventDefault()
    // 온보딩으로 리셋하라는 플래그 설정
    sessionStorage.setItem('resetToOnboarding', 'true')
    sessionStorage.removeItem('currentStep')
    navigate('/')
    // 같은 페이지에서 리로드 트리거
    window.location.reload()
  }

  return (
    <div className="layout">
      <header className="layout-header">
        <div className="header-left">
          <a href="/" className="logo" onClick={handleLogoClick}>
            OneCheck
          </a>
          {isAuthenticated && (
            <nav className="nav-links">
              {user?.role !== 'admin' && user?.role !== 'superadmin' && (
                <NavLink to="/" className={({ isActive }) => isActive ? 'active' : ''}>
                  검증
                </NavLink>
              )}
              <NavLink to="/dashboard" className={({ isActive }) => isActive ? 'active' : ''}>
                대시보드
              </NavLink>
              {(user?.role === 'admin' || user?.role === 'superadmin') && (
                <NavLink to="/admin" className={({ isActive }) => isActive ? 'active' : ''}>
                  관리
                </NavLink>
              )}
              <NavLink to="/history" className={({ isActive }) => isActive ? 'active' : ''}>
                이력
              </NavLink>
            </nav>
          )}
        </div>
        <div className="header-right">
          <span className="version-tag">v4</span>
          <ThemeToggle />
          {isAuthenticated ? (
            <div className="user-menu">
              <span className="username">{user?.username}</span>
              <button onClick={handleLogout} className="logout-btn">
                로그아웃
              </button>
            </div>
          ) : (
            <NavLink to="/login" className="login-link">
              로그인
            </NavLink>
          )}
        </div>
      </header>
      <main className="layout-main">
        <Outlet />
      </main>
      <footer className="layout-footer">
        <p>OneCheck — Zero Touch Retirement Validation Platform</p>
      </footer>
    </div>
  )
}
