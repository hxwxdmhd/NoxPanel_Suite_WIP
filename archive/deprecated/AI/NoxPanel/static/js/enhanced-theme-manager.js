/**
 * Enhanced Theme Manager v7.0
 * Advanced theme management for Heimnetz/NoxPanel/NoxGuard Suite
 * Combines with Ultimate Dashboard theme system
 */

class EnhancedThemeManager {
    constructor() {
        this.themes = {
            light: {
                name: 'Light Theme',
                colors: {
                    primary: '#6f42c1',
                    secondary: '#6c757d',
                    accent: '#8e44ad',
                    background: '#ffffff',
                    surface: '#f8f9fa',
                    text: '#212529',
                    textMuted: '#6c757d',
                    border: '#dee2e6',
                    hover: '#e9ecef',
                    focus: '#6f42c1'
                }
            },
            dark: {
                name: 'Dark Theme',
                colors: {
                    primary: '#8e44ad',
                    secondary: '#495057',
                    accent: '#9b7fd6',
                    background: '#212529',
                    surface: '#343a40',
                    text: '#ffffff',
                    textMuted: '#adb5bd',
                    border: '#495057',
                    hover: '#495057',
                    focus: '#8e44ad'
                }
            },
            purple: {
                name: 'Purple Theme',
                colors: {
                    primary: '#6f42c1',
                    secondary: '#8e44ad',
                    accent: '#9b7fd6',
                    background: '#1a1625',
                    surface: '#2d1b3d',
                    text: '#e9ecef',
                    textMuted: '#adb5bd',
                    border: '#4a2c7a',
                    hover: '#3a2159',
                    focus: '#8e44ad'
                }
            },
            'purple-dark': {
                name: 'Purple Dark',
                colors: {
                    primary: '#4a2c7a',
                    secondary: '#6b4094',
                    accent: '#8e44ad',
                    background: '#0f0a1a',
                    surface: '#1a1625',
                    text: '#ffffff',
                    textMuted: '#b19cd9',
                    border: '#2d1b3d',
                    hover: '#2d1b3d',
                    focus: '#6b4094'
                }
            },
            'purple-light': {
                name: 'Purple Light',
                colors: {
                    primary: '#9b7fd6',
                    secondary: '#b19cd9',
                    accent: '#6f42c1',
                    background: '#f8f6ff',
                    surface: '#ffffff',
                    text: '#2d1b3d',
                    textMuted: '#4a2c7a',
                    border: '#e5d9f2',
                    hover: '#f0e8ff',
                    focus: '#6f42c1'
                }
            }
        };
        
        this.currentTheme = this.getStoredTheme() || 'purple';
        this.adhd_mode = this.getADHDMode();
        this.init();
    }

    init() {
        this.applyTheme(this.currentTheme);
        this.setupThemeSelector();
        this.setupADHDToggle();
        this.setupSystemThemeDetection();
        this.setupMotionPreferences();
        console.log('🎨 Enhanced Theme Manager v7.0 initialized');
    }

    applyTheme(themeName) {
        const theme = this.themes[themeName];
        if (!theme) {
            console.warn(`Theme "${themeName}" not found, falling back to purple`);
            themeName = 'purple';
        }

        const root = document.documentElement;
        const colors = this.themes[themeName].colors;

        // Apply CSS variables
        Object.entries(colors).forEach(([key, value]) => {
            const cssVar = `--theme-${key.replace(/([A-Z])/g, '-$1').toLowerCase()}`;
            root.style.setProperty(cssVar, value);
            
            // Also set RGB values for transparency effects
            const rgb = this.hexToRgb(value);
            if (rgb) {
                root.style.setProperty(`${cssVar}-rgb`, `${rgb.r}, ${rgb.g}, ${rgb.b}`);
            }
        });

        // Update body class
        document.body.className = document.body.className.replace(/theme-\w+/g, '');
        document.body.classList.add(`theme-${themeName}`);

        // Update meta theme-color for mobile browsers
        let metaTheme = document.querySelector('meta[name="theme-color"]');
        if (!metaTheme) {
            metaTheme = document.createElement('meta');
            metaTheme.name = 'theme-color';
            document.head.appendChild(metaTheme);
        }
        metaTheme.content = colors.primary;

        // Store preference
        this.currentTheme = themeName;
        localStorage.setItem('preferred-theme', themeName);
        
        // Dispatch theme change event
        document.dispatchEvent(new CustomEvent('themeChanged', {
            detail: { theme: themeName, colors }
        }));

        console.log(`🎨 Applied theme: ${this.themes[themeName].name}`);
    }

    setupThemeSelector() {
        const selector = document.querySelector('.theme-selector');
        if (!selector) return;

        // Clear existing options
        selector.innerHTML = '';

        // Create theme options
        Object.entries(this.themes).forEach(([key, theme]) => {
            const option = document.createElement('div');
            option.className = 'theme-option';
            option.dataset.theme = key;
            option.title = theme.name;
            option.style.background = `linear-gradient(135deg, ${theme.colors.primary}, ${theme.colors.secondary})`;
            
            if (key === this.currentTheme) {
                option.classList.add('active');
            }
            
            option.addEventListener('click', () => this.selectTheme(key));
            selector.appendChild(option);
        });
    }

    selectTheme(themeName) {
        this.applyTheme(themeName);
        
        // Update selector UI
        document.querySelectorAll('.theme-option').forEach(option => {
            option.classList.toggle('active', option.dataset.theme === themeName);
        });
    }

    setupADHDToggle() {
        const toggle = document.querySelector('#adhd-mode-toggle');
        if (toggle) {
            toggle.checked = this.adhd_mode;
            toggle.addEventListener('change', (e) => {
                this.toggleADHDMode(e.target.checked);
            });
        }
        
        this.applyADHDMode();
    }

    toggleADHDMode(enabled) {
        this.adhd_mode = enabled;
        localStorage.setItem('adhd-mode', enabled.toString());
        this.applyADHDMode();
    }

    applyADHDMode() {
        document.body.classList.toggle('adhd-mode', this.adhd_mode);
        
        if (this.adhd_mode) {
            console.log('🧠 ADHD-friendly mode enabled');
        }
    }

    setupSystemThemeDetection() {
        if (window.matchMedia) {
            const darkMode = window.matchMedia('(prefers-color-scheme: dark)');
            const lightMode = window.matchMedia('(prefers-color-scheme: light)');
            
            const handleSystemTheme = () => {
                if (!this.getStoredTheme()) {
                    if (darkMode.matches) {
                        this.applyTheme('dark');
                    } else if (lightMode.matches) {
                        this.applyTheme('light');
                    }
                }
            };
            
            darkMode.addEventListener('change', handleSystemTheme);
            lightMode.addEventListener('change', handleSystemTheme);
        }
    }

    setupMotionPreferences() {
        if (window.matchMedia) {
            const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
            
            const handleMotionPreference = () => {
                document.body.classList.toggle('reduce-motion', reducedMotion.matches);
            };
            
            reducedMotion.addEventListener('change', handleMotionPreference);
            handleMotionPreference(); // Apply initial state
        }
    }

    getStoredTheme() {
        return localStorage.getItem('preferred-theme');
    }

    getADHDMode() {
        return localStorage.getItem('adhd-mode') === 'true';
    }

    hexToRgb(hex) {
        if (!hex) return null;
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
        } : null;
    }

    // Advanced features
    createCustomTheme(name, colors) {
        this.themes[name] = {
            name: name,
            colors: colors
        };
        this.setupThemeSelector();
    }

    exportTheme() {
        return {
            current: this.currentTheme,
            themes: this.themes,
            adhdMode: this.adhd_mode
        };
    }

    importTheme(themeData) {
        if (themeData.themes) {
            this.themes = { ...this.themes, ...themeData.themes };
        }
        if (themeData.current) {
            this.applyTheme(themeData.current);
        }
        if (typeof themeData.adhdMode === 'boolean') {
            this.toggleADHDMode(themeData.adhdMode);
        }
        this.setupThemeSelector();
    }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.themeManager = new EnhancedThemeManager();
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EnhancedThemeManager;
}
