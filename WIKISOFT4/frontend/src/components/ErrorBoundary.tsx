import { Component, ErrorInfo, ReactNode } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null
    }
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo)
    this.setState({ errorInfo })
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    })
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div style={{
          padding: '2rem',
          textAlign: 'center',
          maxWidth: '600px',
          margin: '4rem auto',
          border: '1px solid #ef4444',
          borderRadius: '12px',
          background: 'rgba(239, 68, 68, 0.1)'
        }}>
          <h1 style={{ color: '#ef4444', fontSize: '1.5rem', marginBottom: '1rem' }}>
            ⚠️ 오류가 발생했습니다
          </h1>
          <p style={{ color: '#666', marginBottom: '1.5rem' }}>
            일시적인 문제가 발생했습니다. 페이지를 새로고침하거나 아래 버튼을 클릭해주세요.
          </p>
          {this.state.error && (
            <details style={{
              marginBottom: '1.5rem',
              textAlign: 'left',
              padding: '1rem',
              background: '#fff',
              borderRadius: '8px'
            }}>
              <summary style={{ cursor: 'pointer', fontWeight: 600 }}>
                오류 상세 정보
              </summary>
              <pre style={{
                marginTop: '1rem',
                fontSize: '0.875rem',
                overflow: 'auto',
                color: '#ef4444'
              }}>
                {this.state.error.message}
              </pre>
            </details>
          )}
          <button
            onClick={this.handleReset}
            style={{
              padding: '0.75rem 1.5rem',
              background: '#3b82f6',
              color: '#fff',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '1rem',
              fontWeight: 600
            }}
          >
            다시 시도
          </button>
        </div>
      )
    }

    return this.props.children
  }
}
