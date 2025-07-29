import React, { useState } from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '../../contexts/ThemeContext';

interface ThemeSelectorProps {
  compact?: boolean;
}

const Container = styled(motion.div)<{ compact?: boolean }>`
  background: var(--surface-color);
  border-radius: ${props => props.compact ? '50px' : '12px'};
  border: 1px solid var(--border-color);
  padding: ${props => props.compact ? '0.5rem' : '1.5rem'};
  box-shadow: 0 4px 12px var(--shadow-color);
  position: relative;
`;

const CompactButton = styled(motion.button)`
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: none;
  background: var(--primary-color);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);

  &:hover {
    transform: scale(1.05);
  }
`;

const FullSelector = styled.div`
  min-width: 300px;
`;

const Title = styled.h3`
  color: var(--text-color);
  font-size: 1.2rem;
  font-weight: 600;
  margin: 0 0 1rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const ThemeGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
`;

const ThemeCard = styled(motion.button)<{ isActive?: boolean }>`
  background: var(--background-color);
  border: 2px solid ${props => props.isActive ? 'var(--primary-color)' : 'var(--border-color)'};
  border-radius: 8px;
  padding: 1rem;
  cursor: pointer;
  transition: all var(--transition-duration) ease;
  position: relative;
  overflow: hidden;

  &:hover {
    border-color: var(--primary-color);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(var(--primary-color), 0.2);
  }
`;

const ThemePreview = styled.div<{ colors: string[] }>`
  width: 100%;
  height: 40px;
  border-radius: 4px;
  margin-bottom: 0.5rem;
  display: grid;
  grid-template-columns: repeat(${props => props.colors.length}, 1fr);
  overflow: hidden;
`;

const ColorStripe = styled.div<{ color: string }>`
  background: ${props => props.color};
  height: 100%;
`;

const ThemeName = styled.div`
  color: var(--text-color);
  font-size: 0.8rem;
  font-weight: 500;
  text-align: center;
`;

const PreferencesSection = styled.div`
  border-top: 1px solid var(--border-color);
  padding-top: 1rem;
`;

const PreferenceGroup = styled.div`
  margin-bottom: 1rem;
`;

const PreferenceLabel = styled.label`
  color: var(--text-color);
  font-size: 0.9rem;
  font-weight: 500;
  display: block;
  margin-bottom: 0.5rem;
`;

const Select = styled.select`
  width: 100%;
  padding: 0.5rem;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--background-color);
  color: var(--text-color);
  font-size: 0.9rem;

  &:focus {
    outline: none;
    border-color: var(--primary-color);
    box-shadow: 0 0 0 2px rgba(var(--primary-color), 0.2);
  }
`;

const Checkbox = styled.input`
  margin-right: 0.5rem;
  accent-color: var(--primary-color);
`;

const CheckboxLabel = styled.label`
  color: var(--text-color);
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  cursor: pointer;
  margin-bottom: 0.5rem;

  &:hover {
    color: var(--primary-color);
  }
`;

const Dropdown = styled(motion.div)`
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 0.5rem;
  background: var(--surface-color);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 8px 24px var(--shadow-color);
  z-index: var(--z-dropdown);
  min-width: 320px;
`;

const ThemeSelector: React.FC<ThemeSelectorProps> = ({ compact = false }) => {
  const {
    currentTheme,
    availableThemes,
    switchTheme,
    preferences,
    updatePreferences,
    isLoading
  } = useTheme();

  const [isOpen, setIsOpen] = useState(false);

  const themeConfigs = {
    light: {
      name: 'Light',
      icon: '☀️',
      colors: ['#3498db', '#2ecc71', '#e74c3c', '#f8f9fa']
    },
    dark: {
      name: 'Dark',
      icon: '🌙',
      colors: ['#4A90E2', '#7ED321', '#F5A623', '#1a1a2e']
    },
    adhd: {
      name: 'ADHD Friendly',
      icon: '🧠',
      colors: ['#8E44AD', '#27AE60', '#F39C12', '#F7F1FF']
    },
    'high-contrast': {
      name: 'High Contrast',
      icon: '⚫',
      colors: ['#000000', '#000000', '#FF0000', '#FFFFFF']
    },
    neon: {
      name: 'Neon',
      icon: '💫',
      colors: ['#00FFFF', '#FF00FF', '#FFFF00', '#0A0A0A']
    },
    corporate: {
      name: 'Corporate',
      icon: '🏢',
      colors: ['#2E4A87', '#5B8A3A', '#C5282F', '#FAFAFA']
    }
  };

  const handleThemeChange = async (themeName: string) => {
    try {
      await switchTheme(themeName);
      if (compact) {
        setIsOpen(false);
      }
    } catch (error) {
      console.error('Failed to switch theme:', error);
    }
  };

  const handlePreferenceChange = async (key: string, value: any) => {
    try {
      await updatePreferences({ [key]: value });
    } catch (error) {
      console.error('Failed to update preferences:', error);
    }
  };

  if (compact) {
    return (
      <Container compact>
        <CompactButton
          onClick={() => setIsOpen(!isOpen)}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          🎨
        </CompactButton>

        <AnimatePresence>
          {isOpen && (
            <Dropdown
              initial={{ opacity: 0, scale: 0.95, y: -10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: -10 }}
              transition={{ duration: 0.2 }}
            >
              <Title>
                🎨 Theme Selector
              </Title>

              <ThemeGrid>
                {Object.entries(themeConfigs).map(([key, config]) => (
                  <ThemeCard
                    key={key}
                    isActive={currentTheme === key}
                    onClick={() => handleThemeChange(key)}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    disabled={isLoading}
                  >
                    <ThemePreview colors={config.colors}>
                      {config.colors.map((color, index) => (
                        <ColorStripe key={index} color={color} />
                      ))}
                    </ThemePreview>
                    <ThemeName>
                      {config.icon} {config.name}
                    </ThemeName>
                  </ThemeCard>
                ))}
              </ThemeGrid>

              <PreferencesSection>
                <PreferenceGroup>
                  <PreferenceLabel>Animation Speed</PreferenceLabel>
                  <Select
                    value={preferences.animation_speed}
                    onChange={(e) => handlePreferenceChange('animation_speed', e.target.value)}
                  >
                    <option value="slow">Slow</option>
                    <option value="normal">Normal</option>
                    <option value="fast">Fast</option>
                  </Select>
                </PreferenceGroup>

                <PreferenceGroup>
                  <PreferenceLabel>Contrast</PreferenceLabel>
                  <Select
                    value={preferences.contrast}
                    onChange={(e) => handlePreferenceChange('contrast', e.target.value)}
                  >
                    <option value="low">Low</option>
                    <option value="normal">Normal</option>
                    <option value="high">High</option>
                  </Select>
                </PreferenceGroup>

                <PreferenceGroup>
                  <PreferenceLabel>Font Size</PreferenceLabel>
                  <Select
                    value={preferences.font_size}
                    onChange={(e) => handlePreferenceChange('font_size', e.target.value)}
                  >
                    <option value="small">Small</option>
                    <option value="normal">Normal</option>
                    <option value="large">Large</option>
                  </Select>
                </PreferenceGroup>

                <CheckboxLabel>
                  <Checkbox
                    type="checkbox"
                    checked={preferences.compact_mode}
                    onChange={(e) => handlePreferenceChange('compact_mode', e.target.checked)}
                  />
                  Compact Mode
                </CheckboxLabel>

                <CheckboxLabel>
                  <Checkbox
                    type="checkbox"
                    checked={preferences.auto_theme}
                    onChange={(e) => handlePreferenceChange('auto_theme', e.target.checked)}
                  />
                  Auto Theme (Follow System)
                </CheckboxLabel>

                <CheckboxLabel>
                  <Checkbox
                    type="checkbox"
                    checked={preferences.notifications}
                    onChange={(e) => handlePreferenceChange('notifications', e.target.checked)}
                  />
                  Enable Notifications
                </CheckboxLabel>
              </PreferencesSection>
            </Dropdown>
          )}
        </AnimatePresence>
      </Container>
    );
  }

  return (
    <Container>
      <FullSelector>
        <Title>
          🎨 Theme Selector
        </Title>

        <ThemeGrid>
          {Object.entries(themeConfigs).map(([key, config]) => (
            <ThemeCard
              key={key}
              isActive={currentTheme === key}
              onClick={() => handleThemeChange(key)}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              disabled={isLoading}
            >
              <ThemePreview colors={config.colors}>
                {config.colors.map((color, index) => (
                  <ColorStripe key={index} color={color} />
                ))}
              </ThemePreview>
              <ThemeName>
                {config.icon} {config.name}
              </ThemeName>
            </ThemeCard>
          ))}
        </ThemeGrid>

        <PreferencesSection>
          <PreferenceGroup>
            <PreferenceLabel>Animation Speed</PreferenceLabel>
            <Select
              value={preferences.animation_speed}
              onChange={(e) => handlePreferenceChange('animation_speed', e.target.value)}
            >
              <option value="slow">Slow</option>
              <option value="normal">Normal</option>
              <option value="fast">Fast</option>
            </Select>
          </PreferenceGroup>

          <PreferenceGroup>
            <PreferenceLabel>Contrast</PreferenceLabel>
            <Select
              value={preferences.contrast}
              onChange={(e) => handlePreferenceChange('contrast', e.target.value)}
            >
              <option value="low">Low</option>
              <option value="normal">Normal</option>
              <option value="high">High</option>
            </Select>
          </PreferenceGroup>

          <PreferenceGroup>
            <PreferenceLabel>Font Size</PreferenceLabel>
            <Select
              value={preferences.font_size}
              onChange={(e) => handlePreferenceChange('font_size', e.target.value)}
            >
              <option value="small">Small</option>
              <option value="normal">Normal</option>
              <option value="large">Large</option>
            </Select>
          </PreferenceGroup>

          <CheckboxLabel>
            <Checkbox
              type="checkbox"
              checked={preferences.compact_mode}
              onChange={(e) => handlePreferenceChange('compact_mode', e.target.checked)}
            />
            Compact Mode
          </CheckboxLabel>

          <CheckboxLabel>
            <Checkbox
              type="checkbox"
              checked={preferences.auto_theme}
              onChange={(e) => handlePreferenceChange('auto_theme', e.target.checked)}
            />
            Auto Theme (Follow System)
          </CheckboxLabel>

          <CheckboxLabel>
            <Checkbox
              type="checkbox"
              checked={preferences.notifications}
              onChange={(e) => handlePreferenceChange('notifications', e.target.checked)}
            />
            Enable Notifications
          </CheckboxLabel>
        </PreferencesSection>
      </FullSelector>
    </Container>
  );
};

export default ThemeSelector;
