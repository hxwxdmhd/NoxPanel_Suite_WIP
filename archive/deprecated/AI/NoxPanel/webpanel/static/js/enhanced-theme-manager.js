/**
 * NoxPanel Enhanced Theme Manager v4.3
 * Comprehensive theme system with ADHD-friendly design and purple variants
 */

class EnhancedThemeManager {
    constructor() {
        this.themes = {
            'light': {
                name: 'Light',
                description: 'Clean, bright theme for daytime use',
                icon: '☀️',
                category: 'standard'
            },
            'dark': {
                name: 'Dark',
                description: 'Easy on the eyes for low-light environments',
                icon: '🌙',
                category: 'standard'
            },
            'purple': {
                name: 'Purple Light',
                description: 'Calming purple theme with good contrast',
                icon: '🟣',
                category: 'purple'
            },
            'purple-dark': {
                name: 'Purple Dark',
                description: 'Deep purple theme for focus and concentration',
                icon: '🟪',
                category: 'purple'
            },
            'purple-high-contrast': {
                name: 'Purple High Contrast',
                description: 'Maximum readability with enhanced accessibility',
                icon: '⚫',
                category: 'accessibility'
            }
        };

        this.currentTheme = this.getStoredTheme() || this.detectSystemPreference();
        this.isADHDMode = this.getStoredADHDMode() || false;
        this.reducedMotion = this.detectReducedMotion();

        this.init();
    }

    init() {
        this.applyTheme(this.currentTheme);
        this.applyADHDMode(this.isADHDMode);
        this.createThemeSelector();
        this.setupEventListeners();
        this.setupAccessibilityFeatures();
        this.announceThemeChange();
    }

    // ===== THEME DETECTION AND STORAGE =====

    getStoredTheme() {
        return localStorage.getItem('noxpanel-theme');
    }

    setStoredTheme(theme) {
        localStorage.setItem('noxpanel-theme', theme);
    }

    getStoredADHDMode() {
        return localStorage.getItem('noxpanel-adhd-mode') === 'true';
    }

    setStoredADHDMode(enabled) {
        localStorage.setItem('noxpanel-adhd-mode', enabled.toString());
    }

    detectSystemPreference() {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        return 'light';
    }

    detectReducedMotion() {
        return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }

    // ===== THEME APPLICATION =====

    applyTheme(theme) {
        if (!this.themes[theme]) {
            console.warn(`Theme '${theme}' not found, falling back to light`);
            theme = 'light';
        }

        // Remove all theme attributes
        Object.keys(this.themes).forEach(themeName => {
            document.documentElement.removeAttribute(`data-theme-${themeName}`);
        });

        // Apply new theme
        document.documentElement.setAttribute('data-theme', theme);
        this.currentTheme = theme;
        this.setStoredTheme(theme);
        this.updateThemeSelector();
        this.updateMetaThemeColor();
        this.dispatchThemeChange();

        // Announce to screen readers
        this.announceToScreenReader(`Theme changed to ${this.themes[theme].name}`);
    }

    applyADHDMode(enabled) {
        this.isADHDMode = enabled;
        this.setStoredADHDMode(enabled);

        if (enabled) {
            document.documentElement.setAttribute('data-adhd-mode', 'true');
            document.body.classList.add('adhd-friendly');
        } else {
            document.documentElement.removeAttribute('data-adhd-mode');
            document.body.classList.remove('adhd-friendly');
        }

        this.updateADHDToggle();
        this.announceToScreenReader(`ADHD-friendly mode ${enabled ? 'enabled' : 'disabled'}`);
    }

    // ===== THEME SELECTOR UI =====

    createThemeSelector() {
        // Check if selector already exists
        if (document.getElementById('theme-selector-container')) {
            return;
        }

        const container = document.createElement('div');
        container.id = 'theme-selector-container';
        container.className = 'theme-selector';
        container.setAttribute('role', 'region');
        container.setAttribute('aria-label', 'Theme selector');

        container.innerHTML = `
            <div class="theme-selector-header">
                <h4>🎨 Theme Selection</h4>
                <p class="text-muted">Choose your preferred visual theme</p>
            </div>

            <div class="theme-categories">
                <div class="theme-category" data-category="standard">
                    <h5>Standard Themes</h5>
                    <div class="theme-options" id="standard-themes"></div>
                </div>

                <div class="theme-category" data-category="purple">
                    <h5>Purple Themes</h5>
                    <div class="theme-options" id="purple-themes"></div>
                </div>

                <div class="theme-category" data-category="accessibility">
                    <h5>Accessibility Themes</h5>
                    <div class="theme-options" id="accessibility-themes"></div>
                </div>
            </div>

            <div class="adhd-controls">
                <label class="adhd-toggle">
                    <input type="checkbox" id="adhd-mode-toggle" ${this.isADHDMode ? 'checked' : ''}>
                    <span class="adhd-label">🧠 ADHD-Friendly Mode</span>
                    <small class="adhd-description">Enhanced visual chunking and focus indicators</small>
                </label>
            </div>

            <div class="accessibility-info">
                <small>
                    <strong>Keyboard shortcuts:</strong><br>
                    • Ctrl+Shift+T: Toggle theme<br>
                    • Ctrl+Shift+A: Toggle ADHD mode
                </small>
            </div>
        `;

        // Add to page (try multiple locations)
        const targets = [
            document.querySelector('.sidebar'),
            document.querySelector('nav'),
            document.querySelector('header'),
            document.body
        ];

        for (const target of targets) {
            if (target) {
                target.appendChild(container);
                break;
            }
        }

        this.populateThemeOptions();
    }

    populateThemeOptions() {
        Object.entries(this.themes).forEach(([themeKey, themeData]) => {
            const container = document.getElementById(`${themeData.category}-themes`);
            if (!container) return;

            const option = document.createElement('button');
            option.className = `theme-option ${this.currentTheme === themeKey ? 'active' : ''}`;
            option.setAttribute('data-theme', themeKey);
            option.setAttribute('aria-pressed', this.currentTheme === themeKey);
            option.title = themeData.description;

            option.innerHTML = `
                <span class="theme-icon">${themeData.icon}</span>
                <span class="theme-name">${themeData.name}</span>
            `;

            container.appendChild(option);
        });
    }

    updateThemeSelector() {
        const options = document.querySelectorAll('.theme-option');
        options.forEach(option => {
            const isActive = option.getAttribute('data-theme') === this.currentTheme;
            option.classList.toggle('active', isActive);
            option.setAttribute('aria-pressed', isActive);
        });
    }

    updateADHDToggle() {
        const toggle = document.getElementById('adhd-mode-toggle');
        if (toggle) {
            toggle.checked = this.isADHDMode;
        }
    }

    // ===== EVENT HANDLING =====

    setupEventListeners() {
        // Theme option clicks
        document.addEventListener('click', (e) => {
            if (e.target.closest('.theme-option')) {
                const theme = e.target.closest('.theme-option').getAttribute('data-theme');
                this.applyTheme(theme);
            }
        });

        // ADHD mode toggle
        document.addEventListener('change', (e) => {
            if (e.target.id === 'adhd-mode-toggle') {
                this.applyADHDMode(e.target.checked);
            }
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + Shift + T: Toggle theme
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'T') {
                e.preventDefault();
                this.toggleTheme();
            }

            // Ctrl/Cmd + Shift + A: Toggle ADHD mode
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'A') {
                e.preventDefault();
                this.toggleADHDMode();
            }

            // Escape: Close theme selector if open
            if (e.key === 'Escape' && document.querySelector('.theme-selector:focus-within')) {
                document.activeElement.blur();
            }
        });

        // System theme preference changes
        if (window.matchMedia) {
            const darkMediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            darkMediaQuery.addEventListener('change', () => {
                if (!this.getStoredTheme()) {
                    this.applyTheme(this.detectSystemPreference());
                }
            });

            const motionMediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
            motionMediaQuery.addEventListener('change', () => {
                this.reducedMotion = motionMediaQuery.matches;
                this.updateAnimationPreferences();
            });
        }
    }

    // ===== THEME CYCLING =====

    toggleTheme() {
        const themeKeys = Object.keys(this.themes);
        const currentIndex = themeKeys.indexOf(this.currentTheme);
        const nextIndex = (currentIndex + 1) % themeKeys.length;
        this.applyTheme(themeKeys[nextIndex]);
    }

    toggleADHDMode() {
        this.applyADHDMode(!this.isADHDMode);
    }

    // ===== ACCESSIBILITY FEATURES =====

    setupAccessibilityFeatures() {
        // Update meta theme color for mobile browsers
        this.updateMetaThemeColor();

        // Set up focus management
        this.setupFocusManagement();

        // Handle reduced motion preferences
        this.updateAnimationPreferences();

        // Add skip links if they don't exist
        this.ensureSkipLinks();
    }

    updateMetaThemeColor() {
        let themeColor = '#ffffff'; // Default light

        if (this.currentTheme.includes('dark')) {
            themeColor = '#121212';
        } else if (this.currentTheme.includes('purple')) {
            themeColor = '#8b5cf6';
        }

        let metaTheme = document.querySelector('meta[name="theme-color"]');
        if (!metaTheme) {
            metaTheme = document.createElement('meta');
            metaTheme.name = 'theme-color';
            document.head.appendChild(metaTheme);
        }
        metaTheme.content = themeColor;
    }

    setupFocusManagement() {
        // Enhanced focus indicators for ADHD mode
        document.addEventListener('focusin', (e) => {
            if (this.isADHDMode) {
                e.target.classList.add('enhanced-focus');
            }
        });

        document.addEventListener('focusout', (e) => {
            e.target.classList.remove('enhanced-focus');
        });
    }

    updateAnimationPreferences() {
        if (this.reducedMotion) {
            document.documentElement.style.setProperty('--animation-speed', '0.01ms');
            document.documentElement.style.setProperty('--theme-transition', 'none');
        } else {
            document.documentElement.style.removeProperty('--animation-speed');
            document.documentElement.style.removeProperty('--theme-transition');
        }
    }

    ensureSkipLinks() {
        if (!document.querySelector('.skip-link')) {
            const skipLink = document.createElement('a');
            skipLink.className = 'skip-link';
            skipLink.href = '#main-content';
            skipLink.textContent = 'Skip to main content';
            document.body.insertBefore(skipLink, document.body.firstChild);
        }
    }

    // ===== SCREEN READER SUPPORT =====

    announceToScreenReader(message) {
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'sr-only';
        announcement.textContent = message;

        document.body.appendChild(announcement);

        // Remove after announcement
        setTimeout(() => {
            document.body.removeChild(announcement);
        }, 1000);
    }

    announceThemeChange() {
        if (this.currentTheme && this.themes[this.currentTheme]) {
            const message = `Using ${this.themes[this.currentTheme].name} theme. ${this.themes[this.currentTheme].description}`;
            this.announceToScreenReader(message);
        }
    }

    // ===== EVENTS AND INTEGRATION =====

    dispatchThemeChange() {
        const event = new CustomEvent('themeChanged', {
            detail: {
                theme: this.currentTheme,
                themeData: this.themes[this.currentTheme],
                adhdMode: this.isADHDMode,
                reducedMotion: this.reducedMotion
            }
        });
        document.dispatchEvent(event);
    }

    // ===== PUBLIC API =====

    getCurrentTheme() {
        return this.currentTheme;
    }

    getAvailableThemes() {
        return { ...this.themes };
    }

    isADHDModeEnabled() {
        return this.isADHDMode;
    }

    setTheme(theme) {
        this.applyTheme(theme);
    }

    enableADHDMode() {
        this.applyADHDMode(true);
    }

    disableADHDMode() {
        this.applyADHDMode(false);
    }

    // ===== UTILITY METHODS =====

    exportSettings() {
        return {
            theme: this.currentTheme,
            adhdMode: this.isADHDMode,
            timestamp: new Date().toISOString()
        };
    }

    importSettings(settings) {
        if (settings.theme && this.themes[settings.theme]) {
            this.applyTheme(settings.theme);
        }
        if (typeof settings.adhdMode === 'boolean') {
            this.applyADHDMode(settings.adhdMode);
        }
    }

    resetToDefaults() {
        const defaultTheme = this.detectSystemPreference();
        this.applyTheme(defaultTheme);
        this.applyADHDMode(false);

        // Clear stored preferences
        localStorage.removeItem('noxpanel-theme');
        localStorage.removeItem('noxpanel-adhd-mode');

        this.announceToScreenReader('Theme settings reset to defaults');
    }
}

// ===== GLOBAL INTEGRATION =====

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.noxThemeManager = new EnhancedThemeManager();
    });
} else {
    window.noxThemeManager = new EnhancedThemeManager();
}

// Backwards compatibility
window.ThemeManager = EnhancedThemeManager;

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EnhancedThemeManager;
}
