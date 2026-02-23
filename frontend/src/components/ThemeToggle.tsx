/**
 * Theme Toggle Button
 * Nút chuyển đổi giữa light/dark mode
 */
import { useTheme } from '../context/ThemeContext';
import { Moon, Sun } from 'lucide-react';
import './ThemeToggle.css';

export default function ThemeToggle() {
    const { theme, toggleTheme } = useTheme();

    return (
        <button
            className="theme-toggle"
            onClick={toggleTheme}
            aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
            title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
        >
            <div className="theme-toggle-inner">
                {theme === 'light' ? (
                    <Moon className="theme-icon" size={20} />
                ) : (
                    <Sun className="theme-icon" size={20} />
                )}
            </div>
        </button>
    );
}
