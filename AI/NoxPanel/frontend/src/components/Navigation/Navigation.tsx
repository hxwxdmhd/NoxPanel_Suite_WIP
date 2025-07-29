import React, { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '../../contexts/ThemeContext';

const NavContainer = styled(motion.nav)`
  position: fixed;
  left: 0;
  top: 0;
  width: 250px;
  height: 100vh;
  background: var(--surface-color);
  border-right: 1px solid var(--border-color);
  padding: 1.5rem 0;
  z-index: var(--z-fixed);
  overflow-y: auto;
  transition: all var(--transition-duration) ease;

  @media (max-width: 768px) {
    transform: translateX(-100%);
    &.mobile-open {
      transform: translateX(0);
    }
  }
`;

const Logo = styled.div`
  padding: 0 1.5rem 2rem;
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 2rem;
`;

const LogoTitle = styled.h1`
  color: var(--primary-color);
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const LogoSubtitle = styled.p`
  color: var(--text-muted);
  font-size: 0.8rem;
  margin: 0.25rem 0 0;
  opacity: 0.8;
`;

const NavSection = styled.div`
  margin-bottom: 2rem;
`;

const SectionTitle = styled.h3`
  color: var(--text-muted);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 0 1.5rem;
  margin-bottom: 1rem;
`;

const NavItem = styled(NavLink)`
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 1.5rem;
  color: var(--text-color);
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all var(--transition-duration) ease;
  position: relative;
  border-left: 3px solid transparent;

  &:hover {
    background: rgba(var(--primary-color), 0.1);
    color: var(--primary-color);
    border-left-color: var(--primary-color);
  }

  &.active {
    background: rgba(var(--primary-color), 0.15);
    color: var(--primary-color);
    border-left-color: var(--primary-color);
    font-weight: 600;
  }
`;

const NavIcon = styled.span`
  font-size: 1.2rem;
  width: 24px;
  text-align: center;
  flex-shrink: 0;
`;

const Badge = styled.span`
  background: var(--accent-color);
  color: white;
  font-size: 0.7rem;
  padding: 0.2rem 0.5rem;
  border-radius: 12px;
  margin-left: auto;
  font-weight: 600;
`;

const StatusIndicator = styled.div<{ status: 'online' | 'offline' | 'warning' }>`
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-left: auto;
  background: ${props => {
    switch (props.status) {
      case 'online': return '#28a745';
      case 'warning': return '#ffc107';
      case 'offline': return '#dc3545';
      default: return 'var(--text-muted)';
    }
  }};
  box-shadow: 0 0 0 2px rgba(${props => {
    switch (props.status) {
      case 'online': return '40, 167, 69';
      case 'warning': return '255, 193, 7';
      case 'offline': return '220, 53, 69';
      default: return '128, 128, 128';
    }
  }}, 0.3);
`;

const CollapseButton = styled(motion.button)`
  position: absolute;
  top: 1rem;
  right: -12px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--surface-color);
  border: 1px solid var(--border-color);
  color: var(--text-color);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  z-index: 1;

  &:hover {
    background: var(--primary-color);
    color: white;
  }
`;

const MobileToggle = styled.button`
  position: fixed;
  top: 1rem;
  left: 1rem;
  z-index: var(--z-modal);
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.5rem;
  font-size: 1.2rem;
  cursor: pointer;
  display: none;

  @media (max-width: 768px) {
    display: block;
  }
`;

const Overlay = styled(motion.div)`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: var(--z-modal-backdrop);
  display: none;

  @media (max-width: 768px) {
    display: block;
  }
`;

const UserProfile = styled.div`
  position: absolute;
  bottom: 1rem;
  left: 1rem;
  right: 1rem;
  padding: 1rem;
  background: var(--background-color);
  border-radius: var(--border-radius);
  border: 1px solid var(--border-color);
`;

const UserInfo = styled.div`
  display: flex;
  align-items: center;
  gap: 0.75rem;
`;

const UserAvatar = styled.div`
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--primary-color);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 0.9rem;
`;

const UserDetails = styled.div`
  flex: 1;
`;

const UserName = styled.div`
  color: var(--text-color);
  font-size: 0.9rem;
  font-weight: 600;
`;

const UserRole = styled.div`
  color: var(--text-muted);
  font-size: 0.75rem;
`;

const Navigation: React.FC = () => {
  const { currentTheme } = useTheme();
  const location = useLocation();
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  const navigationItems = [
    {
      section: 'Main',
      items: [
        { path: '/dashboard', icon: '📊', label: 'Dashboard', status: 'online' },
        { path: '/scripts', icon: '🚀', label: 'Script Manager', badge: '12' },
        { path: '/monitoring', icon: '👁️', label: 'Monitoring', status: 'online' },
        { path: '/network', icon: '🌐', label: 'Network', status: 'warning' },
      ]
    },
    {
      section: 'Configuration',
      items: [
        { path: '/themes', icon: '🎨', label: 'Themes' },
        { path: '/settings', icon: '⚙️', label: 'Settings' },
        { path: '/users', icon: '👥', label: 'Users' },
        { path: '/security', icon: '🔒', label: 'Security', badge: '3' },
      ]
    },
    {
      section: 'Tools',
      items: [
        { path: '/logs', icon: '📋', label: 'System Logs' },
        { path: '/diagnostics', icon: '🔧', label: 'Diagnostics' },
        { path: '/backup', icon: '💾', label: 'Backup' },
        { path: '/analytics', icon: '📈', label: 'Analytics' },
      ]
    }
  ];

  const toggleMobile = () => {
    setIsMobileOpen(!isMobileOpen);
  };

  const closeMobile = () => {
    setIsMobileOpen(false);
  };

  return (
    <>
      <MobileToggle onClick={toggleMobile}>
        ☰
      </MobileToggle>

      <AnimatePresence>
        {isMobileOpen && (
          <Overlay
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={closeMobile}
          />
        )}
      </AnimatePresence>

      <NavContainer
        className={isMobileOpen ? 'mobile-open' : ''}
        initial={{ x: -250 }}
        animate={{ x: 0 }}
        transition={{ duration: 0.3, ease: 'easeOut' }}
      >
        <CollapseButton
          onClick={() => setIsCollapsed(!isCollapsed)}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
        >
          {isCollapsed ? '→' : '←'}
        </CollapseButton>

        <Logo>
          <LogoTitle>
            ⚡ NoxPanel
          </LogoTitle>
          <LogoSubtitle>System Management Console</LogoSubtitle>
        </Logo>

        {navigationItems.map((section) => (
          <NavSection key={section.section}>
            <SectionTitle>{section.section}</SectionTitle>
            {section.items.map((item) => (
              <NavItem
                key={item.path}
                to={item.path}
                className={({ isActive }) => isActive ? 'active' : ''}
                onClick={closeMobile}
              >
                <NavIcon>{item.icon}</NavIcon>
                <AnimatePresence>
                  {!isCollapsed && (
                    <motion.span
                      initial={{ opacity: 0, width: 0 }}
                      animate={{ opacity: 1, width: 'auto' }}
                      exit={{ opacity: 0, width: 0 }}
                      transition={{ duration: 0.2 }}
                    >
                      {item.label}
                    </motion.span>
                  )}
                </AnimatePresence>

                {!isCollapsed && item.badge && (
                  <Badge>{item.badge}</Badge>
                )}

                {!isCollapsed && item.status && (
                  <StatusIndicator status={item.status as any} />
                )}
              </NavItem>
            ))}
          </NavSection>
        ))}

        <AnimatePresence>
          {!isCollapsed && (
            <UserProfile>
              <UserInfo>
                <UserAvatar>A</UserAvatar>
                <UserDetails>
                  <UserName>Admin User</UserName>
                  <UserRole>System Administrator</UserRole>
                </UserDetails>
              </UserInfo>
            </UserProfile>
          )}
        </AnimatePresence>
      </NavContainer>
    </>
  );
};

export default Navigation;
