/**
 * Loading Skeleton Components
 * Cải thiện UX với skeleton loading thay vì spinner
 */
import './LoadingSkeleton.css';

interface SkeletonProps {
    width?: string;
    height?: string;
    borderRadius?: string;
    className?: string;
}

// Base Skeleton component
export function Skeleton({ width, height, borderRadius = '4px', className = '' }: SkeletonProps) {
    return (
        <div
            className={`skeleton ${className}`}
            style={{
                width: width || '100%',
                height: height || '20px',
                borderRadius,
            }}
        />
    );
}

// Card skeleton
export function CardSkeleton() {
    return (
        <div className="card-skeleton">
            <div className="skeleton-header">
                <Skeleton width="40px" height="40px" borderRadius="8px" />
                <div style={{ flex: 1, marginLeft: '12px' }}>
                    <Skeleton width="60%" height="20px" />
                    <Skeleton width="40%" height="16px" className="mt-8" />
                </div>
            </div>
        </div>
    );
}

// Stats Card skeleton
export function StatsCardSkeleton() {
    return (
        <div className="stats-card-skeleton">
            <div className="skeleton-row">
                <Skeleton width="48px" height="48px" borderRadius="12px" />
                <div style={{ flex: 1 }}>
                    <Skeleton width="80%" height="16px" />
                    <Skeleton width="50%" height="28px" className="mt-8" />
                </div>
            </div>
            <Skeleton width="100%" height="4px" borderRadius="2px" className="mt-12" />
        </div>
    );
}

// Student List skeleton
export function StudentListSkeleton({ count = 5 }: { count?: number }) {
    return (
        <div className="student-list-skeleton">
            {Array.from({ length: count }).map((_, i) => (
                <div key={i} className="student-item-skeleton">
                    <Skeleton width="48px" height="48px" borderRadius="50%" />
                    <div className="student-info-skeleton">
                        <Skeleton width="70%" height="18px" />
                        <Skeleton width="50%" height="14px" className="mt-8" />
                    </div>
                    <div className="student-meta-skeleton">
                        <Skeleton width="80px" height="24px" borderRadius="12px" />
                        <Skeleton width="60px" height="16px" className="mt-8" />
                    </div>
                </div>
            ))}
        </div>
    );
}

// Table skeleton
export function TableSkeleton({ rows = 5, columns = 4 }: { rows?: number; columns?: number }) {
    return (
        <div className="table-skeleton">
            {/* Header */}
            <div className="table-header-skeleton">
                {Array.from({ length: columns }).map((_, i) => (
                    <Skeleton key={i} width="100%" height="20px" />
                ))}
            </div>
            {/* Rows */}
            {Array.from({ length: rows }).map((_, rowIndex) => (
                <div key={rowIndex} className="table-row-skeleton">
                    {Array.from({ length: columns }).map((_, colIndex) => (
                        <Skeleton key={colIndex} width="90%" height="16px" />
                    ))}
                </div>
            ))}
        </div>
    );
}

// Chart skeleton
export function ChartSkeleton() {
    return (
        <div className="chart-skeleton">
            <Skeleton width="40%" height="24px" className="mb-16" />
            <div className="chart-bars">
                {[80, 60, 100, 40, 90, 70].map((height, i) => (
                    <div key={i} className="chart-bar-wrapper">
                        <Skeleton width="100%" height={`${height}%`} borderRadius="4px 4px 0 0" />
                        <Skeleton width="60%" height="12px" className="mt-8" />
                    </div>
                ))}
            </div>
        </div>
    );
}

// Dashboard skeleton
export function DashboardSkeleton() {
    return (
        <div className="dashboard-skeleton">
            {/* Stats cards row */}
            <div className="skeleton-stats-row">
                <StatsCardSkeleton />
                <StatsCardSkeleton />
                <StatsCardSkeleton />
                <StatsCardSkeleton />
            </div>

            {/* Main content grid */}
            <div className="skeleton-grid">
                <div className="skeleton-left">
                    <CardSkeleton />
                    <CardSkeleton />
                </div>
                <div className="skeleton-right">
                    <ChartSkeleton />
                    <CardSkeleton />
                </div>
            </div>
        </div>
    );
}

// Student Detail skeleton
export function StudentDetailSkeleton() {
    return (
        <div className="student-detail-skeleton">
            {/* Header */}
            <div className="detail-header-skeleton">
                <Skeleton width="80px" height="80px" borderRadius="50%" />
                <div style={{ flex: 1, marginLeft: '20px' }}>
                    <Skeleton width="60%" height="32px" />
                    <Skeleton width="40%" height="20px" className="mt-12" />
                    <div style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
                        <Skeleton width="100px" height="32px" borderRadius="16px" />
                        <Skeleton width="80px" height="32px" borderRadius="16px" />
                    </div>
                </div>
            </div>

            {/* Stats grid */}
            <div className="detail-stats-skeleton">
                <StatsCardSkeleton />
                <StatsCardSkeleton />
                <StatsCardSkeleton />
            </div>

            {/* Content sections */}
            <div className="detail-sections-skeleton">
                <CardSkeleton />
                <CardSkeleton />
            </div>
        </div>
    );
}

// H5P Analytics skeleton
export function H5PAnalyticsSkeleton() {
    return (
        <div className="h5p-analytics-skeleton">
            <Skeleton width="300px" height="36px" className="mb-24" />
            <div className="h5p-grid-skeleton">
                {Array.from({ length: 6 }).map((_, i) => (
                    <div key={i} className="h5p-card-skeleton">
                        <Skeleton width="100%" height="120px" borderRadius="8px" />
                        <Skeleton width="80%" height="20px" className="mt-12" />
                        <Skeleton width="60%" height="16px" className="mt-8" />
                        <div style={{ display: 'flex', gap: '12px', marginTop: '12px' }}>
                            <Skeleton width="70px" height="24px" borderRadius="12px" />
                            <Skeleton width="70px" height="24px" borderRadius="12px" />
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default Skeleton;
