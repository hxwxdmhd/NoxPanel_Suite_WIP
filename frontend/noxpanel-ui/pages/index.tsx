import { useState, useEffect } from 'react';
import Head from 'next/head';
import dynamic from 'next/dynamic';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import toast from 'react-hot-toast';

// Components
import Layout from '../components/Layout';
import DashboardCard from '../components/DashboardCard';
import SystemStatus from '../components/SystemStatus';
import QuickActions from '../components/QuickActions';
import AIAssistant from '../components/AI/AIAssistant';
import ThemeToggle from '../components/ThemeToggle';
import ModuleGrid from '../components/ModuleGrid';

// Hooks
import { useSystemStatus } from '../hooks/useSystemStatus';
import { useWebSocket } from '../hooks/useWebSocket';
import { useLocalStorage } from '../hooks/useLocalStorage';

// Types
import type { SystemStatusData, DashboardModule } from '../types';

// Dynamic imports for performance
const NetworkMonitor = dynamic(() => import('../components/Network/NetworkMonitor'), {
  loading: () => <div className="animate-pulse bg-gray-200 h-64 rounded-lg" />
});

const AIModelStatus = dynamic(() => import('../components/AI/AIModelStatus'), {
  loading: () => <div className="animate-pulse bg-gray-200 h-32 rounded-lg" />
});

const DEFAULT_MODULES: DashboardModule[] = [
  {
    id: 'system-status',
    title: 'System Overview',
    type: 'status',
    position: { x: 0, y: 0, w: 6, h: 4 },
    enabled: true
  },
  {
    id: 'network-monitor',
    title: 'Network Monitor',
    type: 'network',
    position: { x: 6, y: 0, w: 6, h: 4 },
    enabled: true
  },
  {
    id: 'ai-models',
    title: 'AI Models',
    type: 'ai',
    position: { x: 0, y: 4, w: 4, h: 3 },
    enabled: true
  },
  {
    id: 'quick-actions',
    title: 'Quick Actions',
    type: 'actions',
    position: { x: 4, y: 4, w: 4, h: 3 },
    enabled: true
  },
  {
    id: 'security-alerts',
    title: 'Security Alerts',
    type: 'security',
    position: { x: 8, y: 4, w: 4, h: 3 },
    enabled: true
  }
];

export default function Dashboard() {
  // State management
  const [theme, setTheme] = useLocalStorage('nox-theme', 'steady');
  const [modules, setModules] = useLocalStorage('dashboard-modules', DEFAULT_MODULES);
  const [isEditMode, setIsEditMode] = useState(false);
  const [showAIAssistant, setShowAIAssistant] = useState(false);

  // Data fetching
  const { data: systemStatus, isLoading, error } = useSystemStatus();
  const { isConnected, messages } = useWebSocket('/ws/dashboard');

  // Handle real-time updates
  useEffect(() => {
    if (messages.length > 0) {
      const latestMessage = messages[messages.length - 1];
      
      switch (latestMessage.type) {
        case 'alert':
          toast.error(latestMessage.message);
          break;
        case 'success':
          toast.success(latestMessage.message);
          break;
        case 'info':
          toast(latestMessage.message);
          break;
      }
    }
  }, [messages]);

  // Theme toggle
  const toggleTheme = () => {
    const newTheme = theme === 'spicy' ? 'steady' : 'spicy';
    setTheme(newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
  };

  // Handle module updates
  const updateModules = (newModules: DashboardModule[]) => {
    setModules(newModules);
  };

  if (error) {
    return (
      <Layout>
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-red-600 mb-4">
              🚨 System Error
            </h1>
            <p className="text-gray-600 mb-4">
              Failed to connect to NoxSuite backend
            </p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-nox-primary text-white rounded-lg hover:bg-nox-secondary"
            >
              Retry Connection
            </button>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <>
      <Head>
        <title>NoxSuite - AI-Powered Infrastructure Management</title>
        <meta name="description" content="ADHD-friendly network management with AI automation" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
        <link rel="manifest" href="/manifest.json" />
        <meta name="theme-color" content="#6366f1" />
      </Head>

      <Layout>
        <div className={`min-h-screen transition-colors duration-300 ${
          theme === 'spicy' 
            ? 'bg-spicy-bg text-spicy-text' 
            : 'bg-steady-bg text-steady-text'
        }`}>
          
          {/* Header */}
          <header className="sticky top-0 z-50 border-b border-gray-200 dark:border-gray-700 bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between items-center h-16">
                
                {/* Logo & Title */}
                <div className="flex items-center space-x-4">
                  <motion.div
                    initial={{ rotate: 0 }}
                    animate={{ rotate: 360 }}
                    transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                    className="text-3xl"
                  >
                    🧠
                  </motion.div>
                  <div>
                    <h1 className="text-2xl font-bold text-nox-primary">
                      NoxSuite
                    </h1>
                    <p className="text-sm text-gray-500">
                      AI-Powered Infrastructure
                    </p>
                  </div>
                </div>

                {/* Status Indicator */}
                <div className="flex items-center space-x-2">
                  <div className={`w-3 h-3 rounded-full ${
                    isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'
                  }`} />
                  <span className="text-sm text-gray-600">
                    {isConnected ? 'Connected' : 'Disconnected'}
                  </span>
                </div>

                {/* Controls */}
                <div className="flex items-center space-x-4">
                  
                  {/* Theme Toggle */}
                  <ThemeToggle theme={theme} onToggle={toggleTheme} />

                  {/* Edit Mode Toggle */}
                  <button
                    onClick={() => setIsEditMode(!isEditMode)}
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      isEditMode
                        ? 'bg-nox-accent text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {isEditMode ? '✅ Done' : '⚙️ Edit'}
                  </button>

                  {/* AI Assistant Toggle */}
                  <button
                    onClick={() => setShowAIAssistant(!showAIAssistant)}
                    className="p-2 rounded-lg bg-nox-primary text-white hover:bg-nox-secondary transition-colors"
                    title="AI Assistant"
                  >
                    🤖
                  </button>
                </div>
              </div>
            </div>
          </header>

          {/* Main Content */}
          <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
            
            {/* Loading State */}
            {isLoading && (
              <div className="flex items-center justify-center py-12">
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  className="text-4xl"
                >
                  🔄
                </motion.div>
                <span className="ml-4 text-lg">Loading NoxSuite Dashboard...</span>
              </div>
            )}

            {/* Dashboard Grid */}
            {!isLoading && systemStatus && (
              <AnimatePresence mode="wait">
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.5 }}
                >
                  <ModuleGrid
                    modules={modules}
                    isEditMode={isEditMode}
                    onModulesChange={updateModules}
                    systemData={systemStatus}
                  />
                </motion.div>
              </AnimatePresence>
            )}

            {/* Welcome Message for New Users */}
            {!isLoading && systemStatus && modules.length === 0 && (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="text-center py-12"
              >
                <div className="text-6xl mb-4">🎉</div>
                <h2 className="text-3xl font-bold mb-4">
                  Welcome to NoxSuite!
                </h2>
                <p className="text-xl text-gray-600 mb-6">
                  Your AI-powered infrastructure is ready.
                </p>
                <button
                  onClick={() => setModules(DEFAULT_MODULES)}
                  className="px-6 py-3 bg-nox-primary text-white rounded-lg text-lg font-medium hover:bg-nox-secondary transition-colors"
                >
                  🚀 Set Up Dashboard
                </button>
              </motion.div>
            )}

            {/* Quick Stats Bar */}
            {systemStatus && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-4"
              >
                <DashboardCard
                  title="System Health"
                  value={`${Math.round(systemStatus.health_score || 0)}%`}
                  icon="🏥"
                  color={systemStatus.health_score > 90 ? 'green' : systemStatus.health_score > 70 ? 'yellow' : 'red'}
                />
                <DashboardCard
                  title="Active Services"
                  value={`${systemStatus.active_services || 0}/${systemStatus.total_services || 0}`}
                  icon="⚙️"
                  color="blue"
                />
                <DashboardCard
                  title="AI Models"
                  value={systemStatus.ai_models?.length || 0}
                  icon="🤖"
                  color="purple"
                />
                <DashboardCard
                  title="Alerts"
                  value={systemStatus.alerts?.length || 0}
                  icon="🚨"
                  color={systemStatus.alerts?.length > 0 ? 'red' : 'green'}
                />
              </motion.div>
            )}
          </main>

          {/* AI Assistant Sidebar */}
          <AnimatePresence>
            {showAIAssistant && (
              <AIAssistant
                isOpen={showAIAssistant}
                onClose={() => setShowAIAssistant(false)}
                systemData={systemStatus}
              />
            )}
          </AnimatePresence>

          {/* Footer */}
          <footer className="border-t border-gray-200 dark:border-gray-700 mt-12">
            <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between items-center">
                <div className="text-sm text-gray-500">
                  NoxSuite v2.0.0 - Built with ♥️ for ADHD-friendly operations
                </div>
                <div className="flex space-x-4 text-sm">
                  <a href="/api/docs" target="_blank" className="text-nox-primary hover:text-nox-secondary">
                    API Docs
                  </a>
                  <a href="http://localhost:3001" target="_blank" className="text-nox-primary hover:text-nox-secondary">
                    Grafana
                  </a>
                  <a href="http://localhost:7860" target="_blank" className="text-nox-primary hover:text-nox-secondary">
                    Langflow
                  </a>
                </div>
              </div>
            </div>
          </footer>
        </div>
      </Layout>
    </>
  );
}
