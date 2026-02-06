import { useState, useEffect } from 'react'
import { adminApi, type AuditEntry, type AuditLogQuery } from '../../api/admin'

const actionLabels: Record<string, string> = {
  'auth.login': '로그인',
  'auth.logout': '로그아웃',
  'auth.login_failed': '로그인 실패',
  'auth.token_refresh': '토큰 갱신',
  'auth.password_change': '비밀번호 변경',
  'data.create': '데이터 생성',
  'data.read': '데이터 조회',
  'data.update': '데이터 수정',
  'data.delete': '데이터 삭제',
  'data.export': '데이터 내보내기',
  'data.import': '데이터 가져오기',
  'validate.start': '검증 시작',
  'validate.complete': '검증 완료',
  'validate.error': '검증 오류',
  'user.create': '사용자 생성',
  'user.update': '사용자 수정',
  'user.delete': '사용자 삭제',
  'user.role_change': '역할 변경',
  'workflow.trigger': '워크플로우 시작',
  'workflow.complete': '워크플로우 완료',
  'workflow.error': '워크플로우 오류',
  'security.permission_denied': '권한 거부',
  'security.rate_limit': '요청 제한',
  'security.suspicious': '의심 활동',
  'privacy.pii_detected': 'PII 감지',
  'privacy.data_masked': '데이터 마스킹',
  'privacy.data_anonymized': '데이터 익명화',
}

export default function AuditLog() {
  const [entries, setEntries] = useState<AuditEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filters, setFilters] = useState<AuditLogQuery>({
    limit: 100,
    offset: 0,
  })
  const [selectedEntry, setSelectedEntry] = useState<AuditEntry | null>(null)

  useEffect(() => {
    loadAuditLogs()
  }, [filters])

  const loadAuditLogs = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await adminApi.getAuditLogs(filters)
      setEntries(response.entries)
    } catch (err) {
      setError('감사 로그를 불러오는데 실패했습니다')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  }

  const getActionBadgeClass = (action: string) => {
    if (action.startsWith('auth.login_failed') || action.includes('error') || action.includes('denied')) {
      return 'badge-danger'
    }
    if (action.startsWith('auth') || action.includes('security')) {
      return 'badge-warning'
    }
    if (action.includes('delete')) {
      return 'badge-danger'
    }
    if (action.includes('create') || action.includes('complete')) {
      return 'badge-success'
    }
    return 'badge-info'
  }

  if (loading) {
    return <div className="loading-state">감사 로그를 불러오는 중...</div>
  }

  if (error) {
    return (
      <div className="empty-state">
        <p>{error}</p>
        <button className="btn btn-primary" onClick={loadAuditLogs}>다시 시도</button>
      </div>
    )
  }

  return (
    <div className="audit-log">
      <div className="admin-panel-header">
        <h2 className="admin-panel-title">감사 로그</h2>
        <button className="btn btn-secondary" onClick={loadAuditLogs}>
          새로고침
        </button>
      </div>

      <div className="filter-bar">
        <div className="filter-group">
          <input
            type="text"
            className="filter-input"
            placeholder="사용자 ID"
            value={filters.user_id || ''}
            onChange={(e) => setFilters({ ...filters, user_id: e.target.value || undefined })}
          />
          <select
            className="filter-input"
            value={filters.action || ''}
            onChange={(e) => setFilters({ ...filters, action: e.target.value || undefined })}
          >
            <option value="">모든 액션</option>
            {Object.entries(actionLabels).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
          <input
            type="date"
            className="filter-input"
            value={filters.start_date?.split('T')[0] || ''}
            onChange={(e) => setFilters({
              ...filters,
              start_date: e.target.value ? `${e.target.value}T00:00:00Z` : undefined
            })}
          />
          <input
            type="date"
            className="filter-input"
            value={filters.end_date?.split('T')[0] || ''}
            onChange={(e) => setFilters({
              ...filters,
              end_date: e.target.value ? `${e.target.value}T23:59:59Z` : undefined
            })}
          />
        </div>
      </div>

      {entries.length === 0 ? (
        <div className="empty-state">
          <p>감사 로그가 없습니다.</p>
        </div>
      ) : (
        <div className="admin-table-container">
          <table className="admin-table">
            <thead>
              <tr>
                <th>시간</th>
                <th>액션</th>
                <th>사용자</th>
                <th>리소스</th>
                <th>결과</th>
                <th>상세</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry) => (
                <tr key={entry.id}>
                  <td style={{ whiteSpace: 'nowrap', fontSize: '0.75rem' }}>
                    {formatDate(entry.timestamp)}
                  </td>
                  <td>
                    <span className={`badge ${getActionBadgeClass(entry.action)}`}>
                      {actionLabels[entry.action] || entry.action}
                    </span>
                  </td>
                  <td>
                    <div>{entry.user_id || '-'}</div>
                    {entry.user_email && (
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                        {entry.user_email}
                      </div>
                    )}
                  </td>
                  <td>
                    {entry.resource_type ? (
                      <span>
                        {entry.resource_type}
                        {entry.resource_id && `: ${entry.resource_id}`}
                      </span>
                    ) : (
                      '-'
                    )}
                  </td>
                  <td>
                    <span className={entry.success ? 'status-active' : 'status-inactive'}>
                      {entry.success ? '성공' : '실패'}
                    </span>
                  </td>
                  <td>
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => setSelectedEntry(entry)}
                    >
                      상세
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {selectedEntry && (
        <div className="modal-overlay" onClick={() => setSelectedEntry(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '600px' }}>
            <div className="modal-header">
              <h3 className="modal-title">로그 상세</h3>
              <button className="modal-close" onClick={() => setSelectedEntry(null)}>&times;</button>
            </div>
            <div className="modal-body">
              <div style={{ marginBottom: '16px' }}>
                <strong>ID:</strong> {selectedEntry.id}
              </div>
              <div style={{ marginBottom: '16px' }}>
                <strong>시간:</strong> {formatDate(selectedEntry.timestamp)}
              </div>
              <div style={{ marginBottom: '16px' }}>
                <strong>액션:</strong> {actionLabels[selectedEntry.action] || selectedEntry.action}
              </div>
              <div style={{ marginBottom: '16px' }}>
                <strong>사용자:</strong> {selectedEntry.user_id || '-'} ({selectedEntry.user_email || '-'})
              </div>
              <div style={{ marginBottom: '16px' }}>
                <strong>역할:</strong> {selectedEntry.user_role || '-'}
              </div>
              <div style={{ marginBottom: '16px' }}>
                <strong>IP:</strong> {selectedEntry.ip_address || '-'}
              </div>
              {selectedEntry.error_message && (
                <div style={{ marginBottom: '16px' }}>
                  <strong>오류:</strong> {selectedEntry.error_message}
                </div>
              )}
              {selectedEntry.details && Object.keys(selectedEntry.details).length > 0 && (
                <div>
                  <strong>상세 정보:</strong>
                  <div className="json-viewer">
                    <pre>{JSON.stringify(selectedEntry.details, null, 2)}</pre>
                  </div>
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setSelectedEntry(null)}>
                닫기
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
