/**
 * Stats Card Component
 * Displays a statistic with icon, title, value, and optional trend
 */
import React from 'react';
import type { LucideIcon } from 'lucide-react';
import './StatsCard.css';

interface StatsCardProps {
    icon: LucideIcon;
    title: string;
    value: string | number;
    description?: string;
    trend?: {
        value: number;
        positive: boolean;
    };
    color?: 'primary' | 'success' | 'warning' | 'danger';
}

const StatsCard: React.FC<StatsCardProps> = ({
    icon: Icon,
    title,
    value,
    description,
    trend,
    color = 'primary',
}) => {
    return (
        <div className={`stats-card stats-card-${color}`}>
            <div className="stats-card-icon-wrapper">
                <Icon className="stats-card-icon" />
            </div>

            <div className="stats-card-content">
                <h3 className="stats-card-title">{title}</h3>
                <div className="stats-card-value">{value}</div>

                {description && (
                    <p className="stats-card-description">{description}</p>
                )}

                {trend && (
                    <div className={`stats-card-trend ${trend.positive ? 'positive' : 'negative'}`}>
                        <span>{trend.positive ? '↑' : '↓'}</span>
                        <span>{Math.abs(trend.value)}%</span>
                    </div>
                )}
            </div>
        </div>
    );
};

export default StatsCard;
