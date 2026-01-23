/**
 * Sidebar Navigation Component
 */
import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Users, Settings, BarChart3 } from 'lucide-react';
import './Sidebar.css';

const Sidebar: React.FC = () => {
    const location = useLocation();

    const navItems = [
        { path: '/', icon: LayoutDashboard, label: 'Tổng quan' },
        { path: '/students', icon: Users, label: 'Học viên' },
        { path: '/analytics', icon: BarChart3, label: 'Phân tích' },
        { path: '/settings', icon: Settings, label: 'Cài đặt' },
    ];

    return (
        <aside className="sidebar">
            <div className="sidebar-header">
                <div className="sidebar-logo">
                    <LayoutDashboard className="sidebar-logo-icon" />
                    <h1 className="sidebar-title">Teacher Dashboard</h1>
                </div>
            </div>

            <nav className="sidebar-nav">
                {navItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = location.pathname === item.path;

                    return (
                        <Link
                            key={item.path}
                            to={item.path}
                            className={`sidebar-nav-item ${isActive ? 'active' : ''}`}
                        >
                            <Icon className="sidebar-nav-icon" />
                            <span className="sidebar-nav-label">{item.label}</span>
                        </Link>
                    );
                })}
            </nav>

            <div className="sidebar-footer">
                <p className="sidebar-footer-text">
                    © 2025 Open edX Analytics
                </p>
            </div>
        </aside>
    );
};

export default Sidebar;
