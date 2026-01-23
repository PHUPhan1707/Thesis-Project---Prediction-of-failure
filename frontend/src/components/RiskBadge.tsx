/**
 * Risk Badge Component
 * Displays risk level with appropriate color and icon
 */
import React from 'react';
import { AlertCircle, AlertTriangle, CheckCircle } from 'lucide-react';
import type { RiskLevel } from '../types';
import './RiskBadge.css';

interface RiskBadgeProps {
    level: RiskLevel;
    score?: number;
    size?: 'small' | 'medium' | 'large';
    showScore?: boolean;
}

const RiskBadge: React.FC<RiskBadgeProps> = ({
    level,
    score,
    size = 'medium',
    showScore = false
}) => {
    const getIcon = () => {
        switch (level) {
            case 'HIGH':
                return <AlertCircle className="risk-badge-icon" />;
            case 'MEDIUM':
                return <AlertTriangle className="risk-badge-icon" />;
            case 'LOW':
                return <CheckCircle className="risk-badge-icon" />;
        }
    };

    const getLabel = () => {
        switch (level) {
            case 'HIGH':
                return 'Nguy cơ cao';
            case 'MEDIUM':
                return 'Nguy cơ trung bình';
            case 'LOW':
                return 'Nguy cơ thấp';
        }
    };

    return (
        <div className={`risk-badge risk-badge-${level.toLowerCase()} risk-badge-${size}`}>
            {getIcon()}
            <span className="risk-badge-label">{getLabel()}</span>
            {showScore && score !== undefined && (
                <span className="risk-badge-score">({score.toFixed(1)}%)</span>
            )}
        </div>
    );
};

export default RiskBadge;
