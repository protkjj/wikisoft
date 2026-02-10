import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import './index.css'
import { ErrorBoundary } from './components/ErrorBoundary'
import { SessionProvider } from './contexts/SessionContext'
import { AuthProvider } from './contexts/AuthContext'

// Layout and Pages
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import AdminRoute from './components/admin/AdminRoute'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import HistoryPage from './pages/HistoryPage'
import AdminPage from './pages/AdminPage'
import App from './App' // Main validation page
import PortfolioPage from './pages/PortfolioPage'
import PortfolioOneCheck from './pages/PortfolioOneCheck'
import PortfolioDrobot from './pages/PortfolioDrobot'
import PortfolioCraip from './pages/PortfolioCraip'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <BrowserRouter>
        <AuthProvider>
          <SessionProvider>
            <Routes>
              {/* Public route */}
              <Route path="/login" element={<LoginPage />} />
              <Route path="/portfolio" element={<PortfolioPage />} />
              <Route path="/portfolio/onecheck" element={<PortfolioOneCheck />} />
              <Route path="/portfolio/drobot" element={<PortfolioDrobot />} />
              <Route path="/portfolio/craip" element={<PortfolioCraip />} />

              {/* Protected routes with layout */}
              <Route element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }>
                <Route path="/" element={<App />} />
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/history" element={<HistoryPage />} />
                <Route path="/admin" element={
                  <AdminRoute>
                    <AdminPage />
                  </AdminRoute>
                } />
              </Route>
            </Routes>
          </SessionProvider>
        </AuthProvider>
      </BrowserRouter>
    </ErrorBoundary>
  </React.StrictMode>,
)
