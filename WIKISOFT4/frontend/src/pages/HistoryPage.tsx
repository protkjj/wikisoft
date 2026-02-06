import { useState, useEffect } from 'react'
import { api } from '../api'
import { useAuth } from '../contexts/AuthContext'
import type { ValidationRun } from '../types'
import './HistoryPage.css'

type FilterType = 'all' | 'auto_approve' | 'needs_review' | 'rejected'

export default function HistoryPage() {
  const [runs, setRuns] = useState<ValidationRun[]>([])
  const [filteredRuns, setFilteredRuns] = useState<ValidationRun[]>([])
  const [filter, setFilter] = useState<FilterType>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [userFilter, setUserFilter] = useState<string>('')
  const [uniqueUsers, setUniqueUsers] = useState<string[]>([])
  const { user } = useAuth()

  const isAdmin = user?.role === 'admin' || user?.role === 'superadmin'

  useEffect(() => {
    loadHistory()
  }, [userFilter])

  useEffect(() => {
    applyFilters()
  }, [runs, filter, searchQuery])

  const loadHistory = async () => {
    try {
      setLoading(true)
      const data = await api.getLatestRuns(100, userFilter || undefined)
      setRuns(data)

      // 관리자용: 고유 사용자 목록 추출
      if (isAdmin && !userFilter) {
        const users = [...new Set(data.map((r: any) => r.user_id).filter(Boolean))]
        setUniqueUsers(users as string[])
      }
    } catch (err) {
      console.error('Failed to load history:', err)
    } finally {
      setLoading(false)
    }
  }

  const applyFilters = () => {
    let result = [...runs]

    // Apply status filter
    if (filter !== 'all') {
      result = result.filter(r => r.action === filter)
    }

    // Apply search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      result = result.filter(r =>
        r.message?.toLowerCase().includes(query) ||
        r.file_url?.toLowerCase().includes(query) ||
        r.run_id?.toLowerCase().includes(query) ||
        r.company_name?.toLowerCase().includes(query)
      )
    }

    setFilteredRuns(result)
  }

  const getStatusBadge = (action: string) => {
    switch (action) {
      case 'auto_approve':
        return <span className="badge success">자동 승인</span>
      case 'needs_review':
        return <span className="badge warning">검토 필요</span>
      case 'rejected':
        return <span className="badge danger">반려</span>
      default:
        return <span className="badge">{action}</span>
    }
  }

  const formatDate = (timestamp: string) => {
    if (!timestamp) return '-'
    const date = new Date(timestamp)
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getConfidenceClass = (confidence: number) => {
    if (confidence >= 0.9) return 'high'
    if (confidence >= 0.7) return 'medium'
    return 'low'
  }

  if (loading) {
    return (
      <div className="history-page">
        <div className="loading-state">검증 이력을 불러오는 중...</div>
      </div>
    )
  }

  return (
    <div className="history-page">
      <div className="history-header">
        <h1>검증 이력</h1>
        <div className="history-stats">
          총 {runs.length}건
        </div>
      </div>

      <div className="filter-bar">
        <div className="filter-buttons">
          <button
            className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
          >
            전체
          </button>
          <button
            className={`filter-btn success ${filter === 'auto_approve' ? 'active' : ''}`}
            onClick={() => setFilter('auto_approve')}
          >
            자동 승인
          </button>
          <button
            className={`filter-btn warning ${filter === 'needs_review' ? 'active' : ''}`}
            onClick={() => setFilter('needs_review')}
          >
            검토 필요
          </button>
          <button
            className={`filter-btn danger ${filter === 'rejected' ? 'active' : ''}`}
            onClick={() => setFilter('rejected')}
          >
            반려
          </button>
        </div>
        <div className="filter-right">
          {isAdmin && uniqueUsers.length > 0 && (
            <select
              className="user-filter"
              value={userFilter}
              onChange={(e) => setUserFilter(e.target.value)}
            >
              <option value="">전체 사용자</option>
              {uniqueUsers.map((u) => (
                <option key={u} value={u}>{u}</option>
              ))}
            </select>
          )}
          <input
            type="text"
            className="search-input"
            placeholder="검색..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      {filteredRuns.length === 0 ? (
        <div className="empty-state">
          <p>검색 결과가 없습니다.</p>
        </div>
      ) : (
        <div className="history-table-container">
          <table className="history-table">
            <thead>
              <tr>
                <th>일시</th>
                <th>회사명</th>
                <th>상태</th>
                <th>신뢰도</th>
                <th>메시지</th>
                <th>실행 ID</th>
              </tr>
            </thead>
            <tbody>
              {filteredRuns.map((run, index) => (
                <tr key={index}>
                  <td className="date-cell">{formatDate(run.timestamp)}</td>
                  <td className="company-cell">{run.company_name || '-'}</td>
                  <td>{getStatusBadge(run.action || '')}</td>
                  <td>
                    {run.confidence != null && (
                      <span className={`confidence ${getConfidenceClass(run.confidence)}`}>
                        {(run.confidence * 100).toFixed(0)}%
                      </span>
                    )}
                  </td>
                  <td className="message-cell">{run.message || '-'}</td>
                  <td className="id-cell">{run.run_id?.slice(0, 8) || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
