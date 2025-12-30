import { useState } from 'react'
import './App.css'

function App() {
  const [file, setFile] = useState<File | null>(null)
  const [sessionId, setSessionId] = useState<string>('')
  const [loading, setLoading] = useState(false)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
    }
  }

  const handleUpload = async () => {
    if (!file) {
      alert('파일을 선택해주세요')
      return
    }

    setLoading(true)
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch('http://localhost:8000/validate', {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()
      setSessionId(data.session_id)
      alert('업로드 성공!')
    } catch (error) {
      console.error('Upload failed:', error)
      alert('업로드 실패')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="App">
      <h1>🏢 WIKISOFT 명부검증</h1>
      
      <div className="upload-section">
        <input
          type="file"
          accept=".csv,.xlsx,.xls"
          onChange={handleFileChange}
        />
        <button onClick={handleUpload} disabled={loading || !file}>
          {loading ? '업로드 중...' : '파일 업로드'}
        </button>
      </div>

      {sessionId && (
        <div className="session-info">
          <p>✅ 세션 ID: {sessionId}</p>
          <p>TODO: 그리드 & 챗봇 UI 구현</p>
        </div>
      )}

      <div className="guide">
        <h2>📚 다음 단계</h2>
        <ol>
          <li>internal/ai/ 구현 (AI 통합)</li>
          <li>SpreadsheetView 컴포넌트 (AG Grid)</li>
          <li>ChatBot 컴포넌트</li>
        </ol>
      </div>
    </div>
  )
}

export default App
