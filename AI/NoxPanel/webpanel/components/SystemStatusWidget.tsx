import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Grid,
  Chip,
  Alert,
  IconButton,
  Tooltip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider
} from '@mui/material';
import {
  Memory,
  Storage,
  Speed,
  Security,
  Warning,
  CheckCircle,
  Error,
  Refresh,
  Timeline,
  TrendingUp,
  TrendingDown,
  Settings
} from '@mui/icons-material';

interface SystemMetrics {
  cpu: {
    usage: number;
    temperature: number;
    cores: number;
    frequency: number;
  };
  memory: {
    used: number;
    total: number;
    percentage: number;
  };
  storage: {
    used: number;
    total: number;
    percentage: number;
  };
  network: {
    upload: number;
    download: number;
    latency: number;
  };
  rlvrScore: number;
  complianceScore: number;
  securityScore: number;
  systemHealth: number;
  uptime: string;
  lastUpdated: string;
}

interface SystemAlert {
  id: string;
  type: 'error' | 'warning' | 'info';
  message: string;
  timestamp: string;
  resolved: boolean;
}

interface SystemStatusWidgetProps {
  metrics: SystemMetrics;
  alerts: SystemAlert[];
  onRefresh: () => void;
  onConfigureAlerts: () => void;
  autoRefresh: boolean;
}

const SystemStatusWidget: React.FC<SystemStatusWidgetProps> = ({
  metrics,
  alerts,
  onRefresh,
  onConfigureAlerts,
  autoRefresh
}) => {
  const [lastRefresh, setLastRefresh] = useState(Date.now());
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        handleRefresh();
      }, 30000); // Refresh every 30 seconds

      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await onRefresh();
    setLastRefresh(Date.now());
    setIsRefreshing(false);
  };

  const getHealthColor = (value: number) => {
    if (value >= 90) return 'success';
    if (value >= 70) return 'warning';
    return 'error';
  };

  const getUsageColor = (percentage: number) => {
    if (percentage >= 90) return 'error';
    if (percentage >= 70) return 'warning';
    return 'success';
  };

  const getTrendIcon = (value: number, threshold: number) => {
    if (value > threshold) return <TrendingUp color="success" />;
    if (value < threshold) return <TrendingDown color="error" />;
    return <Timeline color="primary" />;
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatUptime = (uptime: string) => {
    // Assume uptime is in format "HH:MM:SS" or similar
    return uptime;
  };

  const activeAlerts = alerts.filter(alert => !alert.resolved);
  const criticalAlerts = activeAlerts.filter(alert => alert.type === 'error');
  const warningAlerts = activeAlerts.filter(alert => alert.type === 'warning');

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" component="h2">
          📊 System Status Monitor
        </Typography>
        <Box>
          <Tooltip title="Configure Alerts">
            <IconButton onClick={onConfigureAlerts}>
              <Settings />
            </IconButton>
          </Tooltip>
          <Tooltip title="Refresh Data">
            <IconButton onClick={handleRefresh} disabled={isRefreshing}>
              <Refresh sx={{ animation: isRefreshing ? 'spin 1s linear infinite' : 'none' }} />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Alert Summary */}
      {activeAlerts.length > 0 && (
        <Alert
          severity={criticalAlerts.length > 0 ? 'error' : 'warning'}
          sx={{ mb: 3 }}
        >
          <Typography variant="h6">System Alerts</Typography>
          {criticalAlerts.length > 0 && (
            <Typography>
              {criticalAlerts.length} critical alert(s) require immediate attention
            </Typography>
          )}
          {warningAlerts.length > 0 && (
            <Typography>
              {warningAlerts.length} warning(s) detected
            </Typography>
          )}
        </Alert>
      )}

      {/* Core Metrics */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Speed sx={{ mr: 1 }} />
                <Typography variant="h6">CPU Usage</Typography>
              </Box>
              <Typography variant="h4" color={getUsageColor(metrics.cpu.usage)}>
                {metrics.cpu.usage}%
              </Typography>
              <LinearProgress
                variant="determinate"
                value={metrics.cpu.usage}
                color={getUsageColor(metrics.cpu.usage)}
                sx={{ my: 1 }}
              />
              <Typography variant="body2" color="text.secondary">
                {metrics.cpu.cores} cores • {metrics.cpu.frequency} GHz
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Temp: {metrics.cpu.temperature}°C
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Memory sx={{ mr: 1 }} />
                <Typography variant="h6">Memory</Typography>
              </Box>
              <Typography variant="h4" color={getUsageColor(metrics.memory.percentage)}>
                {metrics.memory.percentage}%
              </Typography>
              <LinearProgress
                variant="determinate"
                value={metrics.memory.percentage}
                color={getUsageColor(metrics.memory.percentage)}
                sx={{ my: 1 }}
              />
              <Typography variant="body2" color="text.secondary">
                {formatBytes(metrics.memory.used)} / {formatBytes(metrics.memory.total)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Storage sx={{ mr: 1 }} />
                <Typography variant="h6">Storage</Typography>
              </Box>
              <Typography variant="h4" color={getUsageColor(metrics.storage.percentage)}>
                {metrics.storage.percentage}%
              </Typography>
              <LinearProgress
                variant="determinate"
                value={metrics.storage.percentage}
                color={getUsageColor(metrics.storage.percentage)}
                sx={{ my: 1 }}
              />
              <Typography variant="body2" color="text.secondary">
                {formatBytes(metrics.storage.used)} / {formatBytes(metrics.storage.total)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Security sx={{ mr: 1 }} />
                <Typography variant="h6">System Health</Typography>
              </Box>
              <Typography variant="h4" color={getHealthColor(metrics.systemHealth)}>
                {metrics.systemHealth}%
              </Typography>
              <LinearProgress
                variant="determinate"
                value={metrics.systemHealth}
                color={getHealthColor(metrics.systemHealth)}
                sx={{ my: 1 }}
              />
              <Typography variant="body2" color="text.secondary">
                Uptime: {formatUptime(metrics.uptime)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Compliance and Security Scores */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                🛡️ RLVR Compliance
              </Typography>
              <Typography variant="h3" color={getHealthColor(metrics.rlvrScore)}>
                {metrics.rlvrScore}%
              </Typography>
              <LinearProgress
                variant="determinate"
                value={metrics.rlvrScore}
                color={getHealthColor(metrics.rlvrScore)}
                sx={{ my: 1 }}
              />
              <Typography variant="body2" color="text.secondary">
                Target: ≥95% for Gate 6
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                🔒 Security Score
              </Typography>
              <Typography variant="h3" color={getHealthColor(metrics.securityScore)}>
                {metrics.securityScore}%
              </Typography>
              <LinearProgress
                variant="determinate"
                value={metrics.securityScore}
                color={getHealthColor(metrics.securityScore)}
                sx={{ my: 1 }}
              />
              <Typography variant="body2" color="text.secondary">
                Zero Trust Architecture
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                ✅ Compliance Score
              </Typography>
              <Typography variant="h3" color={getHealthColor(metrics.complianceScore)}>
                {metrics.complianceScore}%
              </Typography>
              <LinearProgress
                variant="determinate"
                value={metrics.complianceScore}
                color={getHealthColor(metrics.complianceScore)}
                sx={{ my: 1 }}
              />
              <Typography variant="body2" color="text.secondary">
                ISO 27001 / SOC 2
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Network Performance */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                🌐 Network Performance
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={4}>
                  <Typography variant="body2" color="text.secondary">Upload</Typography>
                  <Typography variant="h6">{formatBytes(metrics.network.upload)}/s</Typography>
                </Grid>
                <Grid item xs={4}>
                  <Typography variant="body2" color="text.secondary">Download</Typography>
                  <Typography variant="h6">{formatBytes(metrics.network.download)}/s</Typography>
                </Grid>
                <Grid item xs={4}>
                  <Typography variant="body2" color="text.secondary">Latency</Typography>
                  <Typography variant="h6">{metrics.network.latency}ms</Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                🚨 Recent Alerts
              </Typography>
              <List dense>
                {activeAlerts.slice(0, 3).map((alert) => (
                  <ListItem key={alert.id} sx={{ px: 0 }}>
                    <ListItemIcon>
                      {alert.type === 'error' && <Error color="error" />}
                      {alert.type === 'warning' && <Warning color="warning" />}
                      {alert.type === 'info' && <CheckCircle color="info" />}
                    </ListItemIcon>
                    <ListItemText
                      primary={alert.message}
                      secondary={new Date(alert.timestamp).toLocaleString()}
                    />
                  </ListItem>
                ))}
                {activeAlerts.length === 0 && (
                  <ListItem sx={{ px: 0 }}>
                    <ListItemIcon>
                      <CheckCircle color="success" />
                    </ListItemIcon>
                    <ListItemText
                      primary="No active alerts"
                      secondary="All systems operational"
                    />
                  </ListItem>
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* System Information */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            📋 System Information
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Typography variant="body2" color="text.secondary">Last Updated</Typography>
              <Typography variant="body1">{new Date(metrics.lastUpdated).toLocaleString()}</Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="body2" color="text.secondary">Auto Refresh</Typography>
              <Chip
                label={autoRefresh ? 'Enabled' : 'Disabled'}
                color={autoRefresh ? 'success' : 'default'}
                size="small"
              />
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    </Box>
  );
};

export default SystemStatusWidget;

// Add keyframes for refresh animation
const style = document.createElement('style');
style.textContent = `
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
`;
document.head.appendChild(style);