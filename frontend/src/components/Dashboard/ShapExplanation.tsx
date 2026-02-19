import { useEffect, useState } from 'react';
import api from '../../services/api';
import type { ShapExplanation, ShapFactor } from '../../types';
import './ShapExplanation.css';

interface ShapExplanationChartProps {
  userId: number;
  courseId: string;
}

function formatFeatureValue(value: number | string | null): string {
  if (value === null || value === undefined) return 'N/A';
  if (typeof value === 'string') return value;
  if (Number.isInteger(value)) return value.toString();
  return value.toFixed(2);
}

function FactorBar({ factor, type, maxShap }: { factor: ShapFactor; type: 'risk' | 'protective'; maxShap: number }) {
  const absShap = Math.abs(factor.shap_value);
  const widthPct = maxShap > 0 ? (absShap / maxShap) * 100 : 0;
  const shapDisplay = type === 'risk'
    ? `+${absShap.toFixed(2)}`
    : `-${absShap.toFixed(2)}`;

  return (
    <div className="shap-factor-row">
      <div className="shap-factor-left">
        <span className="shap-factor-label" title={factor.feature}>
          {factor.label_vi}
        </span>
        <span className="shap-factor-feat-val">
          = {formatFeatureValue(factor.feature_value)}
        </span>
      </div>
      <div className="shap-factor-right">
        <div className="shap-factor-bar-container">
          <div
            className={`shap-factor-bar ${type}`}
            style={{ width: `${Math.max(widthPct, 2)}%` }}
          />
        </div>
        <span className={`shap-factor-shap ${type}`}>
          {shapDisplay}
        </span>
      </div>
    </div>
  );
}

export function ShapExplanationChart({ userId, courseId }: ShapExplanationChartProps) {
  const [data, setData] = useState<ShapExplanation | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const fetchExplanation = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const result = await api.getStudentExplanation(userId, courseId);
        if (!cancelled) setData(result);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Không thể tải phân tích');
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    };

    fetchExplanation();
    return () => { cancelled = true; };
  }, [userId, courseId]);

  if (isLoading) {
    return (
      <div className="shap-explanation">
        <div className="shap-loading">
          <div className="loading-spinner" />
          <p>Đang phân tích SHAP...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="shap-explanation">
        <div className="shap-error">
          <span className="error-icon">&#9888;&#65039;</span>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const allShapValues = [
    ...data.risk_factors.map(f => Math.abs(f.shap_value)),
    ...data.protective_factors.map(f => Math.abs(f.shap_value)),
  ];
  const maxShap = Math.max(...allShapValues, 0.001);

  return (
    <div className="shap-explanation">
      <div className="shap-base-info">
        <div className="shap-base-item">
          <span className="label">Nguy cơ trung bình (lớp)</span>
          <span className="value">{(data.base_value * 100).toFixed(1)}%</span>
        </div>
        <div className="shap-base-divider" />
        <div className="shap-base-item">
          <span className="label">Nguy cơ sinh viên này</span>
          <span className="value highlight">{data.fail_risk_score.toFixed(1)}%</span>
        </div>
      </div>

      <p className="shap-description">
        Các yếu tố dưới đây cho thấy lý do AI dự đoán mức nguy cơ của sinh viên.
        Giá trị <strong>SHAP</strong> (bên phải) thể hiện mức độ ảnh hưởng của từng yếu tố.
      </p>

      {data.risk_factors.length > 0 && (
        <div className="shap-section">
          <div className="shap-section-header risk">
            <span className="shap-section-icon">&#9650;</span>
            Yếu tố tăng nguy cơ
          </div>
          <div className="shap-factors">
            {data.risk_factors.map(f => (
              <FactorBar key={f.feature} factor={f} type="risk" maxShap={maxShap} />
            ))}
          </div>
        </div>
      )}

      {data.protective_factors.length > 0 && (
        <div className="shap-section">
          <div className="shap-section-header protective">
            <span className="shap-section-icon">&#9660;</span>
            Yếu tố bảo vệ
          </div>
          <div className="shap-factors">
            {data.protective_factors.map(f => (
              <FactorBar key={f.feature} factor={f} type="protective" maxShap={maxShap} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default ShapExplanationChart;
