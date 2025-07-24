/**
 * NoxPanel Theme Manager v3.1
 * Handles theme switching and persistence
 */

class ThemeManager {
    constructor() {
        this.currentTheme = this.getStoredTheme() || 'light';
        this.init();
    }

    init() {
        this.applyTheme(this.currentTheme);
        this.createThemeToggle();
        this.setupEventListeners();
    }

    getStoredTheme() {
        return localStorage.getItem('noxpanel-theme');
    }

    setStoredTheme(theme) {
        localStorage.setItem('noxpanel-theme', theme);
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        this.currentTheme = theme;
        this.setStoredTheme(theme);
        this.updateThemeToggle();
        this.dispatchThemeChange();
    }

    toggleTheme() {
        const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.applyTheme(newTheme);
    }

    createThemeToggle() {
        // Check if toggle already exists
        if (document.getElementById('theme-toggle')) {
            return;
        }

        const toggle = document.createElement('button');
        toggle.id = 'theme-toggle';
        toggle.className = 'theme-toggle';
        toggle.setAttribute('aria-label', 'Toggle theme');
        toggle.title = 'Toggle dark/light theme';

        document.body.appendChild(toggle);
    }

    updateThemeToggle() {
        const toggle = document.getElementById('theme-toggle');
        if (toggle) {
            toggle.innerHTML = this.currentTheme === 'light' ? '🌙' : '☀️';
            toggle.setAttribute('aria-label', `Switch to ${this.currentTheme === 'light' ? 'dark' : 'light'} theme`);
        }
    }

    setupEventListeners() {
        // Theme toggle click
        document.addEventListener('click', (e) => {
            if (e.target.id === 'theme-toggle') {
                this.toggleTheme();
            }
        });

        // Keyboard shortcut (Ctrl/Cmd + Shift + T)
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'T') {
                e.preventDefault();
                this.toggleTheme();
            }
        });

        // System theme preference change
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            mediaQuery.addListener((e) => {
                if (!this.getStoredTheme()) {
                    this.applyTheme(e.matches ? 'dark' : 'light');
                }
            });
        }
    }

    dispatchThemeChange() {
        // Dispatch custom event for other components to listen to
        const event = new CustomEvent('themeChanged', {
            detail: { theme: this.currentTheme }
        });
        document.dispatchEvent(event);
    }

    // Public methods for other components
    getCurrentTheme() {
        return this.currentTheme;
    }

    isDarkTheme() {
        return this.currentTheme === 'dark';
    }

    setTheme(theme) {
        if (theme === 'light' || theme === 'dark') {
            this.applyTheme(theme);
        }
    }
}

// Initialize theme manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.themeManager = new ThemeManager();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemeManager;
}

/**
 * Theme-aware component utilities
 */
class ThemeAwareComponent {
    constructor(element) {
        this.element = element;
        this.setupThemeListener();
    }

    setupThemeListener() {
        document.addEventListener('themeChanged', (e) => {
            this.onThemeChange(e.detail.theme);
        });
    }

    onThemeChange(theme) {
        // Override in subclasses
        console.log(`Theme changed to: ${theme}`);
    }

    getCurrentTheme() {
        return window.themeManager ? window.themeManager.getCurrentTheme() : 'light';
    }

    isDarkTheme() {
        return this.getCurrentTheme() === 'dark';
    }
}

/**
 * Chart/Visualization theme utilities
 */
class ChartThemeHelper {
    static getThemeColors(theme = null) {
        const currentTheme = theme || (window.themeManager ? window.themeManager.getCurrentTheme() : 'light');

        if (currentTheme === 'dark') {
            return {
                background: '#1a1a1a',
                surface: '#2d2d2d',
                primary: '#0d6efd',
                secondary: '#6c757d',
                text: '#ffffff',
                textSecondary: '#adb5bd',
                grid: '#404040',
                border: '#404040'
            };
        } else {
            return {
                background: '#ffffff',
                surface: '#f8f9fa',
                primary: '#007bff',
                secondary: '#6c757d',
                text: '#212529',
                textSecondary: '#6c757d',
                grid: '#e9ecef',
                border: '#dee2e6'
            };
        }
    }

    static getChartOptions(theme = null) {
        const colors = this.getThemeColors(theme);

        return {
            backgroundColor: colors.background,
            textStyle: {
                color: colors.text
            },
            grid: {
                borderColor: colors.grid
            },
            axis: {
                textStyle: {
                    color: colors.textSecondary
                },
                lineStyle: {
                    color: colors.border
                }
            }
        };
    }
}

/**
 * Toast/Notification theme utilities
 */
class NotificationThemeHelper {
    static getToastClass(type, theme = null) {
        const currentTheme = theme || (window.themeManager ? window.themeManager.getCurrentTheme() : 'light');
        const baseClass = `toast-${type}`;
        const themeClass = currentTheme === 'dark' ? 'toast-dark' : 'toast-light';

        return `${baseClass} ${themeClass}`;
    }

    static createThemedToast(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `toast ${this.getToastClass(type)} fade-in`;
        toast.textContent = message;

        // Auto-remove after duration
        setTimeout(() => {
            toast.classList.add('fade-out');
            setTimeout(() => toast.remove(), 300);
        }, duration);

        // Add to toast container or body
        const container = document.querySelector('.toast-container') || document.body;
        container.appendChild(toast);

        return toast;
    }
}

// Export utilities
window.ThemeAwareComponent = ThemeAwareComponent;
window.ChartThemeHelper = ChartThemeHelper;
window.NotificationThemeHelper = NotificationThemeHelper;
