import { useState } from 'react'
import UserManagement from '../components/admin/UserManagement'
import AuditLog from '../components/admin/AuditLog'
import TrainingDataManager from '../components/admin/TrainingDataManager'
import SystemSettings from '../components/admin/SystemSettings'
import './AdminPage.css'

type TabType = 'users' | 'audit' | 'training' | 'settings'

interface Tab {
  id: TabType
  label: string
  icon: string
}

const tabs: Tab[] = [
  { id: 'users', label: '사용자 관리', icon: '👥' },
  { id: 'audit', label: '검증 로그', icon: '📋' },
  { id: 'training', label: '학습 데이터', icon: '📊' },
  { id: 'settings', label: '시스템 설정', icon: '⚙️' },
]

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState<TabType>('users')

  const renderContent = () => {
    switch (activeTab) {
      case 'users':
        return <UserManagement />
      case 'audit':
        return <AuditLog />
      case 'training':
        return <TrainingDataManager />
      case 'settings':
        return <SystemSettings />
      default:
        return null
    }
  }

  return (
    <div className="admin-page">
      <div className="admin-header">
        <h1>관리</h1>
        <p className="admin-subtitle">시스템 관리 및 모니터링</p>
      </div>

      <div className="admin-tabs">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`admin-tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            <span className="tab-icon">{tab.icon}</span>
            <span className="tab-label">{tab.label}</span>
          </button>
        ))}
      </div>

      <div className="admin-content">
        {renderContent()}
      </div>
    </div>
  )
}
