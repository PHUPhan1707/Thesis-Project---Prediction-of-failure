import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDashboard } from '../../context/DashboardContext';
import { api } from '../../services/api';
import type { QuickStats } from '../../types';
import './QuickActions.css';

interface QuickActionsProps {
    stats: QuickStats | null;
    onRefresh?: () => void;
    isLoading?: boolean;
}

type EmailTarget = 'HIGH' | 'HIGH_MEDIUM' | 'ALL';

export function QuickActions({ stats, onRefresh, isLoading }: QuickActionsProps) {
    const navigate = useNavigate();
    const { selectedCourse } = useDashboard();

    // Modal state
    const [showModal, setShowModal] = useState(false);
    const [target, setTarget] = useState<EmailTarget>('HIGH');
    const [subject, setSubject] = useState('Nhắc nhở học tập - Hãy tiếp tục cố gắng!');
    const [message, setMessage] = useState(
        'Kính gửi các bạn sinh viên,\n\n' +
        'Chúng tôi nhận thấy bạn chưa hoạt động gần đây trên khóa học. ' +
        'Hãy đăng nhập và tiếp tục học để không bỏ lỡ nội dung quan trọng nhé!\n\n' +
        'Nếu bạn gặp khó khăn, vui lòng liên hệ giảng viên để được hỗ trợ.\n\n' +
        'Trân trọng,\nGiảng viên'
    );
    const [preview, setPreview] = useState<{ total: number; has_email: number } | null>(null);
    const [previewError, setPreviewError] = useState(false);
    const [isOpening, setIsOpening] = useState(false);

    // Load preview count when target changes
    useEffect(() => {
        if (!showModal || !selectedCourse) return;
        setPreview(null);
        setPreviewError(false);
        api.previewEmailRecipients(selectedCourse.course_id, target)
            .then(data => { setPreview(data); setPreviewError(false); })
            .catch(() => { setPreviewError(true); setPreview({ total: 0, has_email: 0 }); });
    }, [target, showModal, selectedCourse]);

    const handleOpenModal = () => {
        setShowModal(true);
    };

    const handleOpenMailClient = async () => {
        if (!selectedCourse) return;
        setIsOpening(true);
        try {
            const res = await api.getEmailRecipients(selectedCourse.course_id, target);
            if (!res.emails.length) {
                alert('Không tìm thấy sinh viên có email.');
                return;
            }

            const encodedSubject = encodeURIComponent(subject);
            const encodedBody = encodeURIComponent(message);

            // Trường "to" PHẢI được điền (dù chỉ 1 email) thì OS/trình duyệt mới
            // hiện hộp thoại chọn ứng dụng email (Outlook / Gmail / …) — giống như
            // luồng gửi cho từng cá nhân. Nếu để "to" trống và chỉ có "bcc" thì
            // nhiều handler sẽ bị bỏ qua và không bật dialog chọn.
            const buildMailto = (emails: string[]) => {
                const to = encodeURIComponent(emails[0]);
                const rest = emails.slice(1);
                const bccPart = rest.length
                    ? `bcc=${encodeURIComponent(rest.join(','))}&`
                    : '';
                return `mailto:${to}?${bccPart}subject=${encodedSubject}&body=${encodedBody}`;
            };

            const mailto = buildMailto(res.emails);

            // Nếu URL quá dài, tách nhỏ và cảnh báo
            if (mailto.length > 8000) {
                const chunks: string[][] = [];
                const chunkSize = 50;
                for (let i = 0; i < res.emails.length; i += chunkSize) {
                    chunks.push(res.emails.slice(i, i + chunkSize));
                }
                alert(
                    `Có ${res.emails.length} sinh viên — quá nhiều cho 1 email.\n` +
                    `Hệ thống sẽ mở ${chunks.length} cửa sổ email (mỗi cửa sổ ~${chunkSize} người).\n\n` +
                    `Vui lòng cho phép popup nếu bị chặn.`
                );
                for (const chunk of chunks) {
                    window.open(buildMailto(chunk));
                    await new Promise(r => setTimeout(r, 300));
                }
            } else {
                window.location.href = mailto;
            }

            setShowModal(false);
        } catch (err: any) {
            alert(err?.message || 'Không thể lấy danh sách email.');
        } finally {
            setIsOpening(false);
        }
    };

    const targetLabels: Record<EmailTarget, string> = {
        HIGH: 'Chỉ sinh viên nguy cơ CAO',
        HIGH_MEDIUM: 'Sinh viên nguy cơ CAO + TRUNG BÌNH',
        ALL: 'Tất cả sinh viên chưa hoàn thành',
    };

    return (
        <div className="quick-actions">
            <div className="actions-header">
                <span className="header-icon">⚡</span>
                <h3>Hành Động Nhanh</h3>
            </div>

            {stats && (
                <div className="quick-stats-grid">
                    <div className="quick-stat stat-red">
                        <span className="stat-icon">🚨</span>
                        <div className="stat-info">
                            <span className="stat-value">{stats.new_high_risk_count}</span>
                            <span className="stat-label">Nguy cơ cao</span>
                        </div>
                    </div>
                    <div className="quick-stat stat-orange">
                        <span className="stat-icon">😴</span>
                        <div className="stat-info">
                            <span className="stat-value">{stats.inactive_students_count}</span>
                            <span className="stat-label">Không hoạt động</span>
                        </div>
                    </div>
                    <div className="quick-stat stat-blue">
                        <span className="stat-icon">📋</span>
                        <div className="stat-info">
                            <span className="stat-value">{stats.intervention_pending}</span>
                            <span className="stat-label">Cần can thiệp</span>
                        </div>
                    </div>
                </div>
            )}

            <div className="action-buttons">
                <button className="action-btn btn-primary" onClick={handleOpenModal} disabled={isLoading || !selectedCourse}>
                    <span className="btn-icon">📧</span>
                    <span className="btn-text">Gửi Email Nhắc Nhở</span>
                </button>

                <button className="action-btn btn-secondary" onClick={onRefresh} disabled={isLoading}>
                    <span className="btn-icon">{isLoading ? '⏳' : '🔄'}</span>
                    <span className="btn-text">{isLoading ? 'Đang tải...' : 'Làm Mới Dữ Liệu'}</span>
                </button>

                <button className="action-btn btn-outline" onClick={() => navigate('/report')} disabled={isLoading}>
                    <span className="btn-icon">📊</span>
                    <span className="btn-text">Xem Báo Cáo</span>
                </button>

                <button className="action-btn btn-outline" onClick={() => navigate('/pipeline')} disabled={isLoading}>
                    <span className="btn-icon">🤖</span>
                    <span className="btn-text">Chạy Dự Đoán AI</span>
                </button>
            </div>

            {/* Email Modal */}
            {showModal && (
                <div className="email-modal-overlay" onClick={() => !isOpening && setShowModal(false)}>
                    <div className="email-modal" onClick={e => e.stopPropagation()}>
                        <div className="email-modal-header">
                            <h3>📧 Gửi Email Nhắc Nhở Hàng Loạt</h3>
                            <button className="modal-close-btn" onClick={() => setShowModal(false)} disabled={isOpening}>✕</button>
                        </div>

                        <div className="email-modal-body">
                            {/* Target selection */}
                            <div className="form-group">
                                <label>Đối tượng gửi</label>
                                <div className="target-options">
                                    {(['HIGH', 'HIGH_MEDIUM', 'ALL'] as EmailTarget[]).map(t => (
                                        <label key={t} className={`target-option ${target === t ? 'selected' : ''}`}>
                                            <input
                                                type="radio"
                                                name="target"
                                                value={t}
                                                checked={target === t}
                                                onChange={() => setTarget(t)}
                                            />
                                            <span>{targetLabels[t]}</span>
                                        </label>
                                    ))}
                                </div>
                                {preview
                                    ? previewError
                                        ? <p className="preview-count" style={{color:'#ef4444'}}>
                                            Không thể kết nối backend. Hãy kiểm tra server đã chạy chưa.
                                          </p>
                                        : <p className="preview-count">
                                            Tìm thấy <strong>{preview.has_email}</strong> sinh viên có email
                                            (tổng <strong>{preview.total}</strong> phù hợp)
                                          </p>
                                    : <p className="preview-count loading">Đang kiểm tra...</p>
                                }
                            </div>

                            {/* Subject */}
                            <div className="form-group">
                                <label>Tiêu đề email</label>
                                <input
                                    type="text"
                                    className="form-input"
                                    value={subject}
                                    onChange={e => setSubject(e.target.value)}
                                    placeholder="Nhập tiêu đề..."
                                />
                            </div>

                            {/* Message */}
                            <div className="form-group">
                                <label>Nội dung email</label>
                                <textarea
                                    className="form-textarea"
                                    rows={5}
                                    value={message}
                                    onChange={e => setMessage(e.target.value)}
                                    placeholder="Nhập nội dung..."
                                />
                            </div>

                            <p className="mailto-note">
                                Hệ thống sẽ hỏi bạn chọn ứng dụng email (Outlook, Gmail…) rồi mở sẵn email với
                                tiêu đề và nội dung đã nhập. Sinh viên đầu tiên ở trường <strong>To</strong>,
                                các sinh viên còn lại ở trường <strong>BCC</strong> để bảo mật.
                            </p>

                            <div className="email-modal-footer">
                                <button className="action-btn btn-outline" onClick={() => setShowModal(false)} disabled={isOpening}>
                                    Hủy
                                </button>
                                <button
                                    className="action-btn btn-primary"
                                    onClick={handleOpenMailClient}
                                    disabled={isOpening || !preview?.has_email || !subject.trim()}
                                >
                                    <span className="btn-icon">{isOpening ? '⏳' : '📧'}</span>
                                    <span className="btn-text">
                                        {isOpening ? 'Đang mở...' : `Mở email cho ${preview?.has_email ?? '...'} sinh viên`}
                                    </span>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default QuickActions;
