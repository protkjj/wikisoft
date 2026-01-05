import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import type { ValidationRun } from '../types'
import './DashboardPage.css'

interface Stats {
  totalValidations: number
  autoApproved: number
  needsReview: number
  rejected: number
  avgConfidence: number
}

export default function DashboardPage() {
  const [runs, setRuns] = useState<ValidationRun[]>([])
  const [stats, setStats] = useState<Stats>({
    totalValidations: 0,
    autoApproved: 0,
    needsReview: 0,
    rejected: 0,
    avgConfidence: 0
  })
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      const runsData = await api.getLatestRuns(20)
      setRuns(runsData)

      // Calculate stats from runs
      const total = runsData.length
      const autoApproved = runsData.filter(r => r.action === 'auto_approve').length
      const needsReview = runsData.filter(r => r.action === 'needs_review').length
      const rejected = runsData.filter(r => r.action === 'rejected').length
      const avgConf = runsData.reduce((sum, r) => sum + (r.confidence || 0), 0) / (total || 1)

      setStats({
        totalValidations: total,
        autoApproved,
        needsReview,
        rejected,
        avgConfidence: avgConf
      })
    } catch (err) {
      console.error('Failed to load dashboard data:', err)
    } finally {
      setLoading(false)
    }
  }

  const getStatusIcon = (action: string) => {
    switch (action) {
      case 'auto_approve': return '✅'
      case 'needs_review': return '⚠️'
      case 'rejected': return '❌'
      default: return '📄'
    }
  }

  const formatDate = (timestamp: string) => {
    if (!timestamp) return '-'
    const date = new Date(timestamp)
    return date.toLocaleDateString('ko-KR', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (loading) {
    return (
      <div className="dashboard-page">
        <div className="loading-state">데이터를 불러오는 중...</div>
      </div>
    )
  }

  return (
    <div className="dashboard-page">
      <div className="dashboard-header">
        <h1>대시보드</h1>
        <button onClick={() => navigate('/')} className="action-btn">
          + 새 검증
        </button>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">📊</div>
          <div className="stat-content">
            <div className="stat-value">{stats.totalValidations}</div>
            <div className="stat-label">총 검증 수</div>
          </div>
        </div>
        <div className="stat-card success">
          <div className="stat-icon">✅</div>
          <div className="stat-content">
            <div className="stat-value">{stats.autoApproved}</div>
            <div className="stat-label">자동 승인</div>
          </div>
        </div>
        <div className="stat-card warning">
          <div className="stat-icon">⚠️</div>
          <div className="stat-content">
            <div className="stat-value">{stats.needsReview}</div>
            <div className="stat-label">검토 필요</div>
          </div>
        </div>
        <div className="stat-card danger">
          <div className="stat-icon">❌</div>
          <div className="stat-content">
            <div className="stat-value">{stats.rejected}</div>
            <div className="stat-label">반려</div>
          </div>
        </div>
      </div>

      <div className="confidence-card">
        <h3>평균 신뢰도</h3>
        <div className="confidence-bar-container">
          <div
            className="confidence-bar"
            style={{ width: `${stats.avgConfidence * 100}%` }}
          />
        </div>
        <div className="confidence-value">{(stats.avgConfidence * 100).toFixed(1)}%</div>
      </div>

      <div className="recent-section">
        <h2>최근 검증 내역</h2>
        {runs.length === 0 ? (
          <div className="empty-state">
            <p>아직 검증 기록이 없습니다.</p>
            <button onClick={() => navigate('/')} className="action-btn">
              첫 검증 시작하기
            </button>
          </div>
        ) : (
          <div className="runs-list">
            {runs.slice(0, 10).map((run, index) => (
              <div key={index} className="run-item">
                <div className="run-icon">{getStatusIcon(run.action || '')}</div>
                <div className="run-info">
                  <div className="run-message">{run.message || '검증 완료'}</div>
                  <div className="run-meta">
                    <span className="run-date">{formatDate(run.timestamp)}</span>
                    {run.confidence && (
                      <span className="run-confidence">
                        신뢰도: {(run.confidence * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>
                </div>
                <div className={`run-status ${run.action}`}>
                  {run.action === 'auto_approve' && '자동 승인'}
                  {run.action === 'needs_review' && '검토 필요'}
                  {run.action === 'rejected' && '반려'}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
