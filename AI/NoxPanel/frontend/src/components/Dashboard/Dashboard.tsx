import React, { useState, useEffect } from 'react';
import { useQuery } from 'react-query';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { useTheme } from '../../contexts/ThemeContext';
import { api } from '../../services/api';

const DashboardContainer = styled(motion.div)`
  padding: 1.5rem;
  max-width: 1400px;
  margin: 0 auto;
`;

const WelcomeSection = styled(motion.div)`
  background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
  border-radius: 16px;
  padding: 2rem;
  margin-bottom: 2rem;
  color: white;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    right: 0;
    width: 200px;
    height: 200px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 50%;
    transform: translate(50%, -50%);
  }
`;

const WelcomeTitle = styled.h1`
  font-size: 2.5rem;
  font-weight: 700;
  margin: 0 0 0.5rem 0;
  position: relative;
  z-index: 1;
`;

const WelcomeSubtitle = styled.p`
  font-size: 1.2rem;
  opacity: 0.9;
  margin: 0;
  position: relative;
  z-index: 1;
`;

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
`;

const StatCard = styled(motion.div)<{ color?: string }>`
  background: var(--surface-color);
  border-radius: 12px;
  padding: 1.5rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 4px;
    height: 100%;
    background: ${props => props.color || 'var(--primary-color)'};
  }
`;

const StatIcon = styled.div`
  font-size: 2rem;
  margin-bottom: 1rem;
`;

const StatValue = styled.div`
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-color);
  margin-bottom: 0.5rem;
`;

const StatLabel = styled.div`
  font-size: 0.9rem;
  color: rgba(var(--text-color), 0.7);
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const ContentGrid = styled.div`
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 2rem;
  margin-bottom: 2rem;

  @media (max-width: 1024px) {
    grid-template-columns: 1fr;
  }
`;

const Section = styled(motion.div)`
  background: var(--surface-color);
  border-radius: 12px;
  padding: 1.5rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
`;

const SectionTitle = styled.h3`
  color: var(--text-color);
  font-size: 1.3rem;
  font-weight: 600;
  margin: 0 0 1rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const ActivityList = styled.div`
  max-height: 300px;
  overflow-y: auto;
`;

const ActivityItem = styled(motion.div)`
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem;
  border-radius: 8px;
  margin-bottom: 0.5rem;
  background: var(--background-color);
  border: 1px solid rgba(255, 255, 255, 0.05);

  &:hover {
    background: rgba(var(--primary-color), 0.1);
    border-color: var(--primary-color);
  }
`;

const ActivityIcon = styled.div<{ type: 'success' | 'warning' | 'error' | 'info' }>`
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  background: ${props => {
    switch (props.type) {
      case 'success': return '#28a745';
      case 'warning': return '#ffc107';
      case 'error': return '#dc3545';
      default: return 'var(--primary-color)';
    }
  }};
`;

const ActivityContent = styled.div`
  flex: 1;
`;

const ActivityText = styled.div`
  color: var(--text-color);
  font-size: 0.9rem;
  line-height: 1.4;
`;

const ActivityTime = styled.div`
  color: rgba(var(--text-color), 0.6);
  font-size: 0.8rem;
  margin-top: 0.25rem;
`;

const QuickActions = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
`;

const ActionButton = styled(motion.button)`
  background: var(--background-color);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 1rem;
  color: var(--text-color);
  cursor: pointer;
  transition: all var(--transition-duration) ease;

  &:hover {
    background: var(--primary-color);
    color: white;
    transform: translateY(-2px);
  }
`;

const SystemHealth = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1rem;
`;

const HealthItem = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: var(--background-color);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.05);
`;

const HealthLabel = styled.span`
  color: var(--text-color);
  font-size: 0.9rem;
`;

const HealthStatus = styled.span<{ status: 'good' | 'warning' | 'critical' }>`
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 500;
  background: ${props => {
    switch (props.status) {
      case 'good': return '#28a745';
      case 'warning': return '#ffc107';
      case 'critical': return '#dc3545';
      default: return 'var(--primary-color)';
    }
  }};
  color: white;
`;

const LoadingSpinner = styled(motion.div)`
  width: 40px;
  height: 40px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-top: 3px solid var(--primary-color);
  border-radius: 50%;
  margin: 2rem auto;
`;

const Dashboard: React.FC = () => {
  const { currentTheme } = useTheme();

  // Fetch dashboard data
  const { data: dashboardData, isLoading, error } = useQuery(
    'dashboard',
    api.getDashboard,
    {
      refetchInterval: 5000, // Refresh every 5 seconds
    }
  );

  // Fetch system status
  const { data: statusData } = useQuery(
    'status',
    api.getStatus,
    {
      refetchInterval: 10000, // Refresh every 10 seconds
    }
  );

  if (isLoading) {
    return (
      <DashboardContainer>
        <LoadingSpinner
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
        />
      </DashboardContainer>
    );
  }

  if (error) {
    return (
      <DashboardContainer>
        <Section>
          <div style={{ textAlign: 'center', padding: '2rem', color: '#dc3545' }}>
            ❌ Failed to load dashboard data. Please refresh the page.
          </div>
        </Section>
      </DashboardContainer>
    );
  }

  const stats = dashboardData?.data?.stats || {};
  const recentActivity = dashboardData?.data?.recent_activity || [];
  const systemHealth = statusData?.data?.health || {};

  return (
    <DashboardContainer
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <WelcomeSection
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6, delay: 0.1 }}
      >
        <WelcomeTitle>Welcome to NoxPanel</WelcomeTitle>
        <WelcomeSubtitle>
          Monitor, manage, and optimize your system with ease
        </WelcomeSubtitle>
      </WelcomeSection>

      <StatsGrid>
        <StatCard
          color="#28a745"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          whileHover={{ y: -5, transition: { duration: 0.2 } }}
        >
          <StatIcon>🔋</StatIcon>
          <StatValue>{stats.cpu_usage || '0'}%</StatValue>
          <StatLabel>CPU Usage</StatLabel>
        </StatCard>

        <StatCard
          color="#007bff"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          whileHover={{ y: -5, transition: { duration: 0.2 } }}
        >
          <StatIcon>💾</StatIcon>
          <StatValue>{stats.memory_usage || '0'}%</StatValue>
          <StatLabel>Memory Usage</StatLabel>
        </StatCard>

        <StatCard
          color="#ffc107"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          whileHover={{ y: -5, transition: { duration: 0.2 } }}
        >
          <StatIcon>🌐</StatIcon>
          <StatValue>{stats.active_connections || '0'}</StatValue>
          <StatLabel>Active Connections</StatLabel>
        </StatCard>

        <StatCard
          color="#17a2b8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.5 }}
          whileHover={{ y: -5, transition: { duration: 0.2 } }}
        >
          <StatIcon>⚡</StatIcon>
          <StatValue>{stats.scripts_executed || '0'}</StatValue>
          <StatLabel>Scripts Executed</StatLabel>
        </StatCard>
      </StatsGrid>

      <ContentGrid>
        <Section
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.6 }}
        >
          <SectionTitle>
            📈 Recent Activity
          </SectionTitle>
          <ActivityList>
            {recentActivity.length > 0 ? (
              recentActivity.map((activity: any, index: number) => (
                <ActivityItem
                  key={index}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.1 }}
                >
                  <ActivityIcon type={activity.type || 'info'} />
                  <ActivityContent>
                    <ActivityText>{activity.message}</ActivityText>
                    <ActivityTime>
                      {new Date(activity.timestamp).toLocaleString()}
                    </ActivityTime>
                  </ActivityContent>
                </ActivityItem>
              ))
            ) : (
              <ActivityItem
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                <ActivityContent>
                  <ActivityText>No recent activity</ActivityText>
                </ActivityContent>
              </ActivityItem>
            )}
          </ActivityList>
        </Section>

        <div>
          <Section
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.7 }}
          >
            <SectionTitle>
              🏥 System Health
            </SectionTitle>
            <SystemHealth>
              <HealthItem>
                <HealthLabel>Database</HealthLabel>
                <HealthStatus status={systemHealth.database || 'good'}>
                  {systemHealth.database || 'Good'}
                </HealthStatus>
              </HealthItem>
              <HealthItem>
                <HealthLabel>Network</HealthLabel>
                <HealthStatus status={systemHealth.network || 'good'}>
                  {systemHealth.network || 'Good'}
                </HealthStatus>
              </HealthItem>
              <HealthItem>
                <HealthLabel>Storage</HealthLabel>
                <HealthStatus status={systemHealth.storage || 'good'}>
                  {systemHealth.storage || 'Good'}
                </HealthStatus>
              </HealthItem>
              <HealthItem>
                <HealthLabel>Services</HealthLabel>
                <HealthStatus status={systemHealth.services || 'good'}>
                  {systemHealth.services || 'Good'}
                </HealthStatus>
              </HealthItem>
            </SystemHealth>
          </Section>

          <Section
            style={{ marginTop: '1.5rem' }}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.8 }}
          >
            <SectionTitle>
              ⚡ Quick Actions
            </SectionTitle>
            <QuickActions>
              <ActionButton
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => {
                  // TODO: Implement script execution
                  console.log('Execute script');
                }}
              >
                🚀 Run Script
              </ActionButton>
              <ActionButton
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => {
                  // TODO: Implement system scan
                  console.log('Scan system');
                }}
              >
                🔍 Scan System
              </ActionButton>
              <ActionButton
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => {
                  // TODO: Implement backup
                  console.log('Create backup');
                }}
              >
                💾 Backup
              </ActionButton>
              <ActionButton
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => {
                  // TODO: Implement settings
                  console.log('Open settings');
                }}
              >
                ⚙️ Settings
              </ActionButton>
            </QuickActions>
          </Section>
        </div>
      </ContentGrid>
    </DashboardContainer>
  );
};

export default Dashboard;
