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

  return (
    <div className="layout">
      <header className="layout-header">
        <div className="header-left">
          <NavLink to="/" className="logo">
            WIKISOFT <span className="version">4.1</span>
          </NavLink>
          {isAuthenticated && (
            <nav className="nav-links">
              <NavLink to="/" className={({ isActive }) => isActive ? 'active' : ''}>
                검증
              </NavLink>
              <NavLink to="/dashboard" className={({ isActive }) => isActive ? 'active' : ''}>
                대시보드
              </NavLink>
              <NavLink to="/history" className={({ isActive }) => isActive ? 'active' : ''}>
                이력
              </NavLink>
            </nav>
          )}
        </div>
        <div className="header-right">
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
        <p>WIKISOFT 4.1.0 - Security-first HR/Finance Validation Platform</p>
      </footer>
    </div>
  )
}
