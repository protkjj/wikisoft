import { useState, useEffect } from 'react'
import { adminApi, type UserInfo, type CreateUserRequest, type UpdateUserRequest } from '../../api/admin'

export default function UserManagement() {
  const [users, setUsers] = useState<UserInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingUser, setEditingUser] = useState<UserInfo | null>(null)

  useEffect(() => {
    loadUsers()
  }, [])

  const loadUsers = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await adminApi.getUsers()
      setUsers(data)
    } catch (err) {
      setError('사용자 목록을 불러오는데 실패했습니다')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateUser = async (data: CreateUserRequest) => {
    try {
      await adminApi.createUser(data)
      setShowCreateModal(false)
      loadUsers()
    } catch (err: any) {
      alert(err.response?.data?.detail || '사용자 생성에 실패했습니다')
    }
  }

  const handleUpdateUser = async (userId: string, data: UpdateUserRequest) => {
    try {
      await adminApi.updateUser(userId, data)
      setEditingUser(null)
      loadUsers()
    } catch (err: any) {
      alert(err.response?.data?.detail || '사용자 수정에 실패했습니다')
    }
  }

  const handleDeleteUser = async (userId: string) => {
    if (!confirm(`정말로 '${userId}' 사용자를 삭제하시겠습니까?`)) return

    try {
      await adminApi.deleteUser(userId)
      loadUsers()
    } catch (err: any) {
      alert(err.response?.data?.detail || '사용자 삭제에 실패했습니다')
    }
  }

  const handleToggleActive = async (user: UserInfo) => {
    await handleUpdateUser(user.id, { is_active: !user.is_active })
  }

  if (loading) {
    return <div className="loading-state">사용자 목록을 불러오는 중...</div>
  }

  if (error) {
    return (
      <div className="empty-state">
        <p>{error}</p>
        <button className="btn btn-primary" onClick={loadUsers}>다시 시도</button>
      </div>
    )
  }

  return (
    <div className="user-management">
      <div className="admin-panel-header">
        <h2 className="admin-panel-title">사용자 목록</h2>
        <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
          + 사용자 추가
        </button>
      </div>

      <div className="admin-table-container">
        <table className="admin-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>이름</th>
              <th>이메일</th>
              <th>역할</th>
              <th>상태</th>
              <th>작업</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id}>
                <td>{user.id}</td>
                <td>{user.name}</td>
                <td>{user.email}</td>
                <td>
                  <span className={`badge badge-${user.role === 'admin' ? 'info' : 'neutral'}`}>
                    {user.role === 'admin' ? '관리자' : '사용자'}
                  </span>
                </td>
                <td>
                  <span className={user.is_active ? 'status-active' : 'status-inactive'}>
                    {user.is_active ? '활성' : '비활성'}
                  </span>
                </td>
                <td>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => setEditingUser(user)}
                    >
                      수정
                    </button>
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => handleToggleActive(user)}
                    >
                      {user.is_active ? '비활성화' : '활성화'}
                    </button>
                    <button
                      className="btn btn-danger btn-sm"
                      onClick={() => handleDeleteUser(user.id)}
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

      {showCreateModal && (
        <UserModal
          title="사용자 추가"
          onClose={() => setShowCreateModal(false)}
          onSubmit={(data) => handleCreateUser(data as CreateUserRequest)}
        />
      )}

      {editingUser && (
        <UserModal
          title="사용자 수정"
          user={editingUser}
          onClose={() => setEditingUser(null)}
          onSubmit={(data) => handleUpdateUser(editingUser.id, data)}
        />
      )}
    </div>
  )
}

interface UserModalProps {
  title: string
  user?: UserInfo
  onClose: () => void
  onSubmit: (data: CreateUserRequest | UpdateUserRequest) => Promise<void> | void
}

function UserModal({ title, user, onClose, onSubmit }: UserModalProps) {
  const [formData, setFormData] = useState({
    username: user?.id || '',
    email: user?.email || '',
    name: user?.name || '',
    password: '',
    role: user?.role || 'user',
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (user) {
      // Update - only send changed fields
      const updates: UpdateUserRequest = {}
      if (formData.email !== user.email) updates.email = formData.email
      if (formData.name !== user.name) updates.name = formData.name
      if (formData.role !== user.role) updates.role = formData.role
      if (formData.password) updates.password = formData.password
      onSubmit(updates)
    } else {
      // Create
      onSubmit(formData as CreateUserRequest)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title">{title}</h3>
          <button className="modal-close" onClick={onClose}>&times;</button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            <div className="form-group">
              <label className="form-label">사용자명 (ID)</label>
              <input
                type="text"
                className="form-input"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                disabled={!!user}
                required={!user}
                minLength={2}
              />
            </div>
            <div className="form-group">
              <label className="form-label">이름</label>
              <input
                type="text"
                className="form-input"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label">이메일</label>
              <input
                type="email"
                className="form-input"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label">비밀번호 {user && '(변경시에만 입력)'}</label>
              <input
                type="password"
                className="form-input"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                required={!user}
                minLength={8}
                placeholder={user ? '변경하지 않으려면 비워두세요' : ''}
              />
            </div>
            <div className="form-group">
              <label className="form-label">역할</label>
              <select
                className="form-select"
                value={formData.role}
                onChange={(e) => setFormData({ ...formData, role: e.target.value })}
              >
                <option value="user">사용자</option>
                <option value="admin">관리자</option>
              </select>
            </div>
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              취소
            </button>
            <button type="submit" className="btn btn-primary">
              {user ? '수정' : '생성'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
