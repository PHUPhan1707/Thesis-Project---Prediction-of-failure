/**
 * Error Boundary Component
 * Catches React errors and displays a fallback UI
 */
import { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({
      error,
      errorInfo,
    });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          padding: '2rem',
          textAlign: 'center',
          color: '#ef4444',
          backgroundColor: '#fef2f2',
          border: '1px solid #fecaca',
          borderRadius: '8px',
          margin: '2rem',
        }}>
          <h2 style={{ marginBottom: '1rem' }}>⚠️ Đã xảy ra lỗi</h2>
          <p style={{ marginBottom: '1rem' }}>
            {this.state.error?.message || 'Có lỗi không xác định xảy ra'}
          </p>
          {import.meta.env.DEV && this.state.errorInfo && (
            <details style={{
              marginTop: '1rem',
              padding: '1rem',
              backgroundColor: '#fff',
              borderRadius: '4px',
              textAlign: 'left',
              fontSize: '0.875rem',
            }}>
              <summary style={{ cursor: 'pointer', marginBottom: '0.5rem' }}>
                Chi tiết lỗi (Development)
              </summary>
              <pre style={{
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
                color: '#666',
              }}>
                {this.state.error?.stack}
                {'\n\n'}
                {this.state.errorInfo.componentStack}
              </pre>
            </details>
          )}
          <button
            onClick={() => window.location.reload()}
            style={{
              marginTop: '1rem',
              padding: '0.5rem 1rem',
              backgroundColor: '#ef4444',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
            }}
          >
            Tải lại trang
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;

