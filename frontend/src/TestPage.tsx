/**
 * Simple Test Page to verify frontend is working
 */
import type { FC } from 'react';

const TestPage: FC = () => {
    return (
        <div style={{
            padding: '2rem',
            fontFamily: 'Arial, sans-serif',
            backgroundColor: '#f0f0f0',
            minHeight: '100vh'
        }}>
            <h1 style={{ color: '#333' }}>✅ Frontend đang chạy!</h1>
            <p>Nếu bạn thấy trang này, frontend đã hoạt động.</p>
            
            <div style={{
                marginTop: '2rem',
                padding: '1rem',
                backgroundColor: 'white',
                borderRadius: '8px',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
            }}>
                <h2>Thông tin:</h2>
                <ul>
                    <li>React: OK ✅</li>
                    <li>TypeScript: OK ✅</li>
                    <li>Vite: OK ✅</li>
                    <li>Routing: Đang test...</li>
                </ul>
            </div>

            <div style={{ marginTop: '2rem' }}>
                <button 
                    onClick={() => alert('Button hoạt động!')}
                    style={{
                        padding: '0.75rem 1.5rem',
                        backgroundColor: '#3b82f6',
                        color: 'white',
                        border: 'none',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontSize: '1rem'
                    }}
                >
                    Test Button
                </button>
            </div>
        </div>
    );
};

export default TestPage;

