import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  LinearProgress,
  Alert,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  Memory as MemoryIcon,
  Storage as StorageIcon,
  NetworkCheck as NetworkIcon,
  Security as SecurityIcon,
  Speed as SpeedIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { Line, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
  ArcElement,
} from 'chart.js';
import { useQuery } from 'react-query';
import { useSocket } from '../contexts/SocketContext';
import { formatBytes, formatUptime, formatNumber } from '../utils/formatters';
import { apiClient } from '../services/api';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  ChartTooltip,
  Legend,
  ArcElement
);

const Dashboard = () => {
  const { socket, isConnected } = useSocket();
  const [metrics, setMetrics] = useState(null);
  const [metricsHistory, setMetricsHistory] = useState([]);
  const [alerts, setAlerts] = useState([]);

  const { data: systemStatus, refetch: refetchStatus } = useQuery(
    'systemStatus',
    () => apiClient.get('/api/v1/health'),
    {
      refetchInterval: 30000, // 30 seconds
    }
  );

  const { data: cacheStats } = useQuery(
    'cacheStats',
    () => apiClient.get('/api/v1/cache/stats'),
    {
      refetchInterval: 60000, // 1 minute
    }
  );

  useEffect(() => {
    if (socket) {
      socket.emit('subscribe_metrics');

      socket.on('metrics_update', (data) => {
        setMetrics(data);
        setMetricsHistory(prev => {
          const newHistory = [...prev, data];
          return newHistory.slice(-20); // Keep last 20 points
        });
      });

      socket.on('performance_alert', (data) => {
        setAlerts(prev => [...prev, ...data.alerts]);
      });

      return () => {
        socket.off('metrics_update');
        socket.off('performance_alert');
      };
    }
  }, [socket]);

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy':
      case 'online':
        return 'success';
      case 'warning':
        return 'warning';
      case 'error':
      case 'offline':
        return 'error';
      default:
        return 'info';
    }
  };

  const MetricCard = ({ title, value, unit, icon, color, progress }) => (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      transition={{ type: 'spring', stiffness: 300 }}
    >
      <Card sx={{ height: '100%' }}>
        <CardContent>
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Box>
              <Typography variant="h6" component="div" color="text.secondary">
                {title}
              </Typography>
              <Typography variant="h4" component="div" color={color}>
                {value}{unit}
              </Typography>
            </Box>
            <Box color={color}>
              {icon}
            </Box>
          </Box>
          {progress !== undefined && (
            <Box mt={2}>
              <LinearProgress
                variant="determinate"
                value={progress}
                sx={{
                  height: 8,
                  borderRadius: 4,
                  backgroundColor: 'rgba(0, 0, 0, 0.1)',
                  '& .MuiLinearProgress-bar': {
                    background: `linear-gradient(90deg, ${color}, ${color}aa)`,
                  },
                }}
              />
            </Box>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: false,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
      },
    },
    elements: {
      point: {
        radius: 0,
      },
    },
    interaction: {
      intersect: false,
    },
  };

  const lineChartData = {
    labels: metricsHistory.map((_, index) => `${index * 5}s`),
    datasets: [
      {
        label: 'CPU Usage (%)',
        data: metricsHistory.map(m => m.cpu_percent || 0),
        borderColor: '#667eea',
        backgroundColor: 'rgba(102, 126, 234, 0.1)',
        fill: true,
        tension: 0.4,
      },
      {
        label: 'Memory Usage (%)',
        data: metricsHistory.map(m => m.memory_percent || 0),
        borderColor: '#764ba2',
        backgroundColor: 'rgba(118, 75, 162, 0.1)',
        fill: true,
        tension: 0.4,
      },
    ],
  };

  const doughnutData = {
    labels: ['CPU', 'Memory', 'Disk', 'Available'],
    datasets: [
      {
        data: [
          metrics?.cpu_percent || 0,
          metrics?.memory_percent || 0,
          metrics?.disk_percent || 0,
          100 - ((metrics?.cpu_percent || 0) + (metrics?.memory_percent || 0) + (metrics?.disk_percent || 0)) / 3,
        ],
        backgroundColor: [
          '#667eea',
          '#764ba2',
          '#f093fb',
          '#e8f5e8',
        ],
        borderWidth: 2,
        borderColor: '#fff',
      },
    ],
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1" gutterBottom>
          System Dashboard
        </Typography>
        <Box display="flex" gap={1}>
          <Chip
            icon={<NetworkIcon />}
            label={isConnected ? 'Connected' : 'Disconnected'}
            color={isConnected ? 'success' : 'error'}
            variant="outlined"
          />
          <Tooltip title="Refresh Status">
            <IconButton onClick={refetchStatus} color="primary">
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Alerts */}
      {alerts.length > 0 && (
        <Box mb={3}>
          {alerts.slice(-3).map((alert, index) => (
            <Alert
              key={index}
              severity={alert.severity}
              sx={{ mb: 1 }}
              onClose={() => setAlerts(prev => prev.filter((_, i) => i !== index))}
            >
              {alert.message}
            </Alert>
          ))}
        </Box>
      )}

      {/* System Status Cards */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="CPU Usage"
            value={metrics?.cpu_percent?.toFixed(1) || '0.0'}
            unit="%"
            icon={<SpeedIcon fontSize="large" />}
            color="#667eea"
            progress={metrics?.cpu_percent || 0}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Memory Usage"
            value={metrics?.memory_percent?.toFixed(1) || '0.0'}
            unit="%"
            icon={<MemoryIcon fontSize="large" />}
            color="#764ba2"
            progress={metrics?.memory_percent || 0}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Disk Usage"
            value={metrics?.disk_percent?.toFixed(1) || '0.0'}
            unit="%"
            icon={<StorageIcon fontSize="large" />}
            color="#f093fb"
            progress={metrics?.disk_percent || 0}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Active Connections"
            value={metrics?.active_connections || 0}
            unit=""
            icon={<NetworkIcon fontSize="large" />}
            color="#4caf50"
          />
        </Grid>
      </Grid>

      {/* Network and System Info */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Network Traffic
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Sent: {formatBytes(metrics?.network_bytes_sent || 0)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Received: {formatBytes(metrics?.network_bytes_recv || 0)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Info
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Uptime: {formatUptime(metrics?.uptime || 0)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Version: v11.0
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Cache Status
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Backend: {cacheStats?.data?.backend || 'N/A'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Hit Rate: {cacheStats?.data?.hit_rate?.toFixed(1) || '0.0'}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Server Status
              </Typography>
              <Chip
                label={systemStatus?.data?.status || 'Unknown'}
                color={getStatusColor(systemStatus?.data?.status)}
                size="small"
              />
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                {systemStatus?.data?.version || 'N/A'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Performance Over Time
              </Typography>
              <Box sx={{ height: 300 }}>
                <Line data={lineChartData} options={chartOptions} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Resource Distribution
              </Typography>
              <Box sx={{ height: 300 }}>
                <Doughnut data={doughnutData} options={{ responsive: true, maintainAspectRatio: false }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
