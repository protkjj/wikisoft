import { useState, useEffect } from 'react'
import { adminApi, type SystemSettingsData } from '../../api/admin'

export default function SystemSettings() {
  const [settings, setSettings] = useState<SystemSettingsData | null>(null)
  const [formData, setFormData] = useState<Partial<SystemSettingsData>>({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [hasChanges, setHasChanges] = useState(false)

  useEffect(() => {
    loadSettings()
  }, [])

  useEffect(() => {
    if (settings) {
      const changed = Object.keys(formData).some(
        (key) => formData[key as keyof SystemSettingsData] !== settings[key as keyof SystemSettingsData]
      )
      setHasChanges(changed)
    }
  }, [formData, settings])

  const loadSettings = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await adminApi.getSettings()
      setSettings(data)
      setFormData(data)
    } catch (err) {
      setError('시스템 설정을 불러오는데 실패했습니다')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    if (!settings) return

    // Build updates with only changed fields
    const updates: Partial<SystemSettingsData> = {}
    Object.keys(formData).forEach((key) => {
      const k = key as keyof SystemSettingsData
      if (formData[k] !== settings[k]) {
        (updates as any)[k] = formData[k]
      }
    })

    if (Object.keys(updates).length === 0) {
      return
    }

    try {
      setSaving(true)
      const newSettings = await adminApi.updateSettings(updates)
      setSettings(newSettings)
      setFormData(newSettings)
      alert('설정이 저장되었습니다')
    } catch (err: any) {
      alert(err.response?.data?.detail || '설정 저장에 실패했습니다')
    } finally {
      setSaving(false)
    }
  }

  const handleReset = () => {
    if (settings) {
      setFormData(settings)
    }
  }

  const handleExtensionChange = (value: string) => {
    const extensions = value.split(',').map((ext) => ext.trim()).filter(Boolean)
    setFormData({ ...formData, allowed_extensions: extensions })
  }

  if (loading) {
    return <div className="loading-state">시스템 설정을 불러오는 중...</div>
  }

  if (error) {
    return (
      <div className="empty-state">
        <p>{error}</p>
        <button className="btn btn-primary" onClick={loadSettings}>다시 시도</button>
      </div>
    )
  }

  return (
    <div className="system-settings">
      <div className="admin-panel-header">
        <h2 className="admin-panel-title">시스템 설정</h2>
        <div className="admin-panel-actions">
          <button
            className="btn btn-secondary"
            onClick={handleReset}
            disabled={!hasChanges}
          >
            초기화
          </button>
          <button
            className="btn btn-primary"
            onClick={handleSave}
            disabled={!hasChanges || saving}
          >
            {saving ? '저장 중...' : '저장'}
          </button>
        </div>
      </div>

      <div className="settings-form">
        <div className="settings-section">
          <h3 className="settings-section-title">급여 설정</h3>
          <div className="form-group">
            <label className="form-label">최저임금 (월)</label>
            <input
              type="number"
              className="form-input"
              value={formData.minimum_wage || 0}
              onChange={(e) => setFormData({ ...formData, minimum_wage: parseInt(e.target.value) || 0 })}
              min={0}
            />
            <p className="form-hint">검증 시 급여가 최저임금 이상인지 확인합니다.</p>
          </div>
          <div className="form-group">
            <label className="form-label">정년 나이</label>
            <input
              type="number"
              className="form-input"
              value={formData.retirement_age || 60}
              onChange={(e) => setFormData({ ...formData, retirement_age: parseInt(e.target.value) || 60 })}
              min={0}
              max={100}
            />
            <p className="form-hint">퇴직연금 계산 시 사용되는 정년 나이입니다.</p>
          </div>
        </div>

        <div className="settings-section">
          <h3 className="settings-section-title">검증 설정</h3>
          <div className="form-group">
            <label className="form-label">검증 신뢰도 임계값</label>
            <input
              type="number"
              className="form-input"
              value={formData.validation_confidence_threshold || 0.8}
              onChange={(e) => setFormData({
                ...formData,
                validation_confidence_threshold: parseFloat(e.target.value) || 0.8
              })}
              min={0}
              max={1}
              step={0.1}
            />
            <p className="form-hint">이 값 이상이면 자동 승인, 미만이면 검토 필요로 분류됩니다. (0.0 ~ 1.0)</p>
          </div>
        </div>

        <div className="settings-section">
          <h3 className="settings-section-title">파일 설정</h3>
          <div className="form-group">
            <label className="form-label">최대 파일 크기 (MB)</label>
            <input
              type="number"
              className="form-input"
              value={formData.max_file_size_mb || 50}
              onChange={(e) => setFormData({ ...formData, max_file_size_mb: parseInt(e.target.value) || 50 })}
              min={1}
              max={500}
            />
            <p className="form-hint">업로드 가능한 최대 파일 크기입니다.</p>
          </div>
          <div className="form-group">
            <label className="form-label">허용 확장자</label>
            <input
              type="text"
              className="form-input"
              value={formData.allowed_extensions?.join(', ') || '.xls, .xlsx'}
              onChange={(e) => handleExtensionChange(e.target.value)}
            />
            <p className="form-hint">쉼표로 구분하여 입력하세요. (예: .xls, .xlsx)</p>
          </div>
        </div>
      </div>

      <style>{`
        .settings-form {
          max-width: 600px;
        }
        .settings-section {
          margin-bottom: 32px;
          padding-bottom: 24px;
          border-bottom: 1px solid var(--border-color, #e5e7eb);
        }
        .settings-section:last-child {
          border-bottom: none;
        }
        .settings-section-title {
          font-size: 1rem;
          font-weight: 600;
          color: var(--text-primary, #111827);
          margin: 0 0 16px 0;
        }
      `}</style>
    </div>
  )
}
