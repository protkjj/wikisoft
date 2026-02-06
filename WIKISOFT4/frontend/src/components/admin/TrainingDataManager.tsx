import { useState, useEffect } from 'react'
import { adminApi, type TrainingFile, type TrainingDataStats } from '../../api/admin'

const fileTypeLabels: Record<string, string> = {
  validation: '검증 데이터',
  layer1_error: 'L1 오류',
  layer2_error: 'L2 오류',
  case: '케이스',
  correction: '수정 데이터',
  other: '기타',
}

export default function TrainingDataManager() {
  const [files, setFiles] = useState<TrainingFile[]>([])
  const [stats, setStats] = useState<TrainingDataStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filterType, setFilterType] = useState<string>('')
  const [selectedFile, setSelectedFile] = useState<TrainingFile | null>(null)
  const [fileContent, setFileContent] = useState<any>(null)
  const [loadingContent, setLoadingContent] = useState(false)

  useEffect(() => {
    loadTrainingData()
  }, [filterType])

  const loadTrainingData = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await adminApi.getTrainingData(filterType || undefined)
      setFiles(response.files)
      setStats(response.stats)
    } catch (err) {
      setError('학습 데이터를 불러오는데 실패했습니다')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleViewFile = async (file: TrainingFile) => {
    try {
      setSelectedFile(file)
      setLoadingContent(true)
      const detail = await adminApi.getTrainingDataFile(file.filename)
      setFileContent(detail.content)
    } catch (err) {
      console.error(err)
      setFileContent({ error: '파일 내용을 불러오는데 실패했습니다' })
    } finally {
      setLoadingContent(false)
    }
  }

  const handleDeleteFile = async (filename: string) => {
    if (!confirm(`정말로 '${filename}' 파일을 삭제하시겠습니까?`)) return

    try {
      await adminApi.deleteTrainingData(filename)
      loadTrainingData()
      if (selectedFile?.filename === filename) {
        setSelectedFile(null)
        setFileContent(null)
      }
    } catch (err: any) {
      alert(err.response?.data?.detail || '파일 삭제에 실패했습니다')
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
    })
  }

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  if (loading) {
    return <div className="loading-state">학습 데이터를 불러오는 중...</div>
  }

  if (error) {
    return (
      <div className="empty-state">
        <p>{error}</p>
        <button className="btn btn-primary" onClick={loadTrainingData}>다시 시도</button>
      </div>
    )
  }

  return (
    <div className="training-data-manager">
      <div className="admin-panel-header">
        <h2 className="admin-panel-title">학습 데이터</h2>
        <button className="btn btn-secondary" onClick={loadTrainingData}>
          새로고침
        </button>
      </div>

      {stats && (
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-label">총 파일 수</div>
            <div className="stat-value">{stats.total_files}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">총 크기</div>
            <div className="stat-value">{formatBytes(stats.total_size_bytes)}</div>
          </div>
          {Object.entries(stats.type_counts).map(([type, count]) => (
            <div className="stat-card" key={type}>
              <div className="stat-label">{fileTypeLabels[type] || type}</div>
              <div className="stat-value">{count}</div>
            </div>
          ))}
        </div>
      )}

      <div className="filter-bar">
        <div className="filter-group">
          <select
            className="filter-input"
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
          >
            <option value="">모든 타입</option>
            {Object.entries(fileTypeLabels).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
        </div>
      </div>

      {files.length === 0 ? (
        <div className="empty-state">
          <p>학습 데이터 파일이 없습니다.</p>
        </div>
      ) : (
        <div className="admin-table-container">
          <table className="admin-table">
            <thead>
              <tr>
                <th>파일명</th>
                <th>타입</th>
                <th>크기</th>
                <th>수정일</th>
                <th>작업</th>
              </tr>
            </thead>
            <tbody>
              {files.map((file) => (
                <tr key={file.filename}>
                  <td style={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                    {file.filename}
                  </td>
                  <td>
                    <span className="badge badge-neutral">
                      {fileTypeLabels[file.file_type] || file.file_type}
                    </span>
                  </td>
                  <td>{formatBytes(file.size_bytes)}</td>
                  <td style={{ whiteSpace: 'nowrap', fontSize: '0.75rem' }}>
                    {formatDate(file.modified_at)}
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => handleViewFile(file)}
                      >
                        보기
                      </button>
                      <button
                        className="btn btn-danger btn-sm"
                        onClick={() => handleDeleteFile(file.filename)}
                      >
                        삭제
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {selectedFile && (
        <div className="modal-overlay" onClick={() => { setSelectedFile(null); setFileContent(null) }}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '800px' }}>
            <div className="modal-header">
              <h3 className="modal-title">{selectedFile.filename}</h3>
              <button className="modal-close" onClick={() => { setSelectedFile(null); setFileContent(null) }}>
                &times;
              </button>
            </div>
            <div className="modal-body">
              <div style={{ marginBottom: '16px' }}>
                <span className="badge badge-neutral" style={{ marginRight: '8px' }}>
                  {fileTypeLabels[selectedFile.file_type] || selectedFile.file_type}
                </span>
                <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                  {formatBytes(selectedFile.size_bytes)} | {formatDate(selectedFile.modified_at)}
                </span>
              </div>
              {loadingContent ? (
                <div className="loading-state">파일 내용을 불러오는 중...</div>
              ) : (
                <div className="json-viewer">
                  <pre>{JSON.stringify(fileContent, null, 2)}</pre>
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button
                className="btn btn-danger"
                onClick={() => handleDeleteFile(selectedFile.filename)}
              >
                삭제
              </button>
              <button
                className="btn btn-secondary"
                onClick={() => { setSelectedFile(null); setFileContent(null) }}
              >
                닫기
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
