import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Alert,
  AlertTitle,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  LinearProgress,
  Avatar,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Tooltip,
  Divider,
  Paper,
  Badge
} from '@mui/material';
import {
  Security,
  Shield,
  Warning,
  CheckCircle,
  Error,
  Info,
  VpnKey,
  AdminPanelSettings,
  Visibility,
  VisibilityOff,
  Refresh,
  Settings,
  TrendingUp,
  TrendingDown,
  NetworkCheck,
  Lock,
  LockOpen,
  Fingerprint,
  VerifiedUser
} from '@mui/icons-material';

interface SecurityAlert {
  id: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  description: string;
  timestamp: string;
  status: 'active' | 'resolved' | 'investigating';
  affectedSystems: string[];
}

interface SecurityMetrics {
  overallScore: number;
  threatLevel: 'low' | 'medium' | 'high' | 'critical';
  activeThreats: number;
  blockedAttempts: number;
  systemsSecured: number;
  complianceScore: number;
  mfaEnabled: boolean;
  zeroTrustActive: boolean;
}

interface ComplianceStatus {
  framework: string;
  score: number;
  status: 'compliant' | 'partial' | 'non-compliant';
  lastAudit: string;
}

const SecurityMonitorPanel: React.FC = () => {
  const [securityAlerts, setSecurityAlerts] = useState<SecurityAlert[]>([]);
  const [metrics, setMetrics] = useState<SecurityMetrics | null>(null);
  const [compliance, setCompliance] = useState<ComplianceStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAlert, setSelectedAlert] = useState<SecurityAlert | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);

  useEffect(() => {
    fetchSecurityData();
    const interval = setInterval(fetchSecurityData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchSecurityData = async () => {
    try {
      // Simulate API calls
      const mockAlerts: SecurityAlert[] = [
        {
          id: '1',
          severity: 'high',
          title: 'Unusual Login Activity Detected',
          description: 'Multiple failed login attempts from IP 192.168.1.100',
          timestamp: new Date().toISOString(),
          status: 'active',
          affectedSystems: ['Authentication Server', 'User Portal']
        },
        {
          id: '2',
          severity: 'medium',
          title: 'SSL Certificate Expiring Soon',
          description: 'Certificate for api.noxpanel.com expires in 7 days',
          timestamp: new Date(Date.now() - 3600000).toISOString(),
          status: 'active',
          affectedSystems: ['API Gateway']
        },
        {
          id: '3',
          severity: 'low',
          title: 'Security Policy Updated',
          description: 'Password policy has been updated successfully',
          timestamp: new Date(Date.now() - 7200000).toISOString(),
          status: 'resolved',
          affectedSystems: ['User Management']
        }
      ];

      const mockMetrics: SecurityMetrics = {
        overallScore: 95,
        threatLevel: 'low',
        activeThreats: 2,
        blockedAttempts: 127,
        systemsSecured: 15,
        complianceScore: 98,
        mfaEnabled: true,
        zeroTrustActive: true
      };

      const mockCompliance: ComplianceStatus[] = [
        { framework: 'ISO 27001', score: 98, status: 'compliant', lastAudit: '2025-07-01' },
        { framework: 'NIST CSF', score: 96, status: 'compliant', lastAudit: '2025-06-15' },
        { framework: 'SOC 2', score: 94, status: 'compliant', lastAudit: '2025-06-01' },
        { framework: 'GDPR', score: 100, status: 'compliant', lastAudit: '2025-07-10' }
      ];

      setSecurityAlerts(mockAlerts);
      setMetrics(mockMetrics);
      setCompliance(mockCompliance);
    } catch (error) {
      console.error('Error fetching security data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'error';
      case 'high': return 'warning';
      case 'medium': return 'info';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical': return <Error />;
      case 'high': return <Warning />;
      case 'medium': return <Info />;
      case 'low': return <CheckCircle />;
      default: return <Info />;
    }
  };

  const getComplianceColor = (status: string) => {
    switch (status) {
      case 'compliant': return 'success';
      case 'partial': return 'warning';
      case 'non-compliant': return 'error';
      default: return 'default';
    }
  };

  const getThreatLevelColor = (level: string) => {
    switch (level) {
      case 'critical': return '#f44336';
      case 'high': return '#ff9800';
      case 'medium': return '#2196f3';
      case 'low': return '#4caf50';
      default: return '#9e9e9e';
    }
  };

  const handleAlertClick = (alert: SecurityAlert) => {
    setSelectedAlert(alert);
    setDetailsOpen(true);
  };

  const SecurityScoreCard = ({ title, score, icon, color }: { title: string; score: number; icon: React.ReactNode; color: string }) => (
    <Card sx={{ textAlign: 'center', p: 2, height: '100%' }}>
      <Avatar sx={{ mx: 'auto', mb: 2, bgcolor: color }}>
        {icon}
      </Avatar>
      <Typography variant="h4" sx={{ color, mb: 1 }}>
        {score}%
      </Typography>
      <Typography variant="body2" color="text.secondary">
        {title}
      </Typography>
      <LinearProgress
        variant="determinate"
        value={score}
        sx={{
          mt: 2,
          height: 8,
          borderRadius: 4,
          backgroundColor: 'rgba(0,0,0,0.1)',
          '& .MuiLinearProgress-bar': {
            backgroundColor: color,
            borderRadius: 4
          }
        }}
      />
    </Card>
  );

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <LinearProgress sx={{ width: '50%' }} />
      </Box>
    );
  }

  return (
    <Box p={3}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1" gutterBottom>
          🛡️ Security Monitor & Compliance
        </Typography>
        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={fetchSecurityData}
          sx={{ borderRadius: 2 }}
        >
          Refresh
        </Button>
      </Box>

      {/* Security Metrics Overview */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} md={3}>
          <SecurityScoreCard
            title="Security Score"
            score={metrics?.overallScore || 0}
            icon={<Shield />}
            color="#4caf50"
          />
        </Grid>
        <Grid item xs={12} md={3}>
          <SecurityScoreCard
            title="Compliance Score"
            score={metrics?.complianceScore || 0}
            icon={<VerifiedUser />}
            color="#2196f3"
          />
        </Grid>
        <Grid item xs={12} md={3}>
          <Card sx={{ textAlign: 'center', p: 2 }}>
            <Avatar sx={{ mx: 'auto', mb: 2, bgcolor: getThreatLevelColor(metrics?.threatLevel || 'low') }}>
              <Security />
            </Avatar>
            <Typography variant="h6" sx={{ color: getThreatLevelColor(metrics?.threatLevel || 'low'), mb: 1 }}>
              {metrics?.threatLevel?.toUpperCase() || 'LOW'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Threat Level
            </Typography>
            <Typography variant="caption" display="block" mt={1}>
              {metrics?.activeThreats || 0} Active Threats
            </Typography>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card sx={{ textAlign: 'center', p: 2 }}>
            <Avatar sx={{ mx: 'auto', mb: 2, bgcolor: 'error.main' }}>
              <Block />
            </Avatar>
            <Typography variant="h4" color="error.main">
              {metrics?.blockedAttempts || 0}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Blocked Attempts
            </Typography>
            <Typography variant="caption" display="block" mt={1}>
              Last 24 hours
            </Typography>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Security Alerts */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">
                  <Warning sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Security Alerts
                </Typography>
                <Badge badgeContent={securityAlerts.filter(a => a.status === 'active').length} color="error">
                  <Security />
                </Badge>
              </Box>
              <Divider sx={{ mb: 2 }} />
              <List>
                {securityAlerts.map((alert) => (
                  <ListItem
                    key={alert.id}
                    button
                    onClick={() => handleAlertClick(alert)}
                    sx={{
                      border: 1,
                      borderColor: 'divider',
                      borderRadius: 2,
                      mb: 1,
                      '&:hover': {
                        backgroundColor: 'action.hover'
                      }
                    }}
                  >
                    <ListItemIcon>
                      {getSeverityIcon(alert.severity)}
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box display="flex" alignItems="center" gap={2}>
                          <Typography variant="subtitle1">{alert.title}</Typography>
                          <Chip
                            label={alert.severity}
                            color={getSeverityColor(alert.severity) as any}
                            size="small"
                          />
                          <Chip
                            label={alert.status}
                            variant="outlined"
                            size="small"
                          />
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            {alert.description}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {new Date(alert.timestamp).toLocaleString()}
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Compliance Status */}
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <AdminPanelSettings sx={{ mr: 1, verticalAlign: 'middle' }} />
                Compliance Status
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <List>
                {compliance.map((framework) => (
                  <ListItem key={framework.framework} sx={{ px: 0 }}>
                    <ListItemText
                      primary={
                        <Box display="flex" justifyContent="space-between" alignItems="center">
                          <Typography variant="subtitle2">{framework.framework}</Typography>
                          <Chip
                            label={framework.status}
                            color={getComplianceColor(framework.status) as any}
                            size="small"
                          />
                        </Box>
                      }
                      secondary={
                        <Box>
                          <LinearProgress
                            variant="determinate"
                            value={framework.score}
                            sx={{
                              mt: 1,
                              mb: 1,
                              height: 6,
                              borderRadius: 3,
                              backgroundColor: 'rgba(0,0,0,0.1)',
                              '& .MuiLinearProgress-bar': {
                                backgroundColor: framework.score >= 95 ? '#4caf50' : framework.score >= 85 ? '#ff9800' : '#f44336',
                                borderRadius: 3
                              }
                            }}
                          />
                          <Typography variant="caption" color="text.secondary">
                            Score: {framework.score}% • Last audit: {framework.lastAudit}
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Security Features Status */}
      <Grid container spacing={3} mt={2}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <VpnKey sx={{ mr: 1, verticalAlign: 'middle' }} />
                Security Features Status
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Paper sx={{ p: 2, display: 'flex', alignItems: 'center' }}>
                    <Avatar sx={{ mr: 2, bgcolor: metrics?.mfaEnabled ? 'success.main' : 'error.main' }}>
                      {metrics?.mfaEnabled ? <Lock /> : <LockOpen />}
                    </Avatar>
                    <Box>
                      <Typography variant="subtitle1">Multi-Factor Authentication</Typography>
                      <Typography variant="body2" color="text.secondary">
                        {metrics?.mfaEnabled ? 'Enabled' : 'Disabled'}
                      </Typography>
                    </Box>
                  </Paper>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Paper sx={{ p: 2, display: 'flex', alignItems: 'center' }}>
                    <Avatar sx={{ mr: 2, bgcolor: metrics?.zeroTrustActive ? 'success.main' : 'error.main' }}>
                      <Fingerprint />
                    </Avatar>
                    <Box>
                      <Typography variant="subtitle1">Zero Trust Architecture</Typography>
                      <Typography variant="body2" color="text.secondary">
                        {metrics?.zeroTrustActive ? 'Active' : 'Inactive'}
                      </Typography>
                    </Box>
                  </Paper>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Alert Details Dialog */}
      <Dialog open={detailsOpen} onClose={() => setDetailsOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          Security Alert Details
        </DialogTitle>
        <DialogContent>
          {selectedAlert && (
            <Box sx={{ pt: 2 }}>
              <Alert severity={getSeverityColor(selectedAlert.severity) as any} sx={{ mb: 2 }}>
                <AlertTitle>{selectedAlert.title}</AlertTitle>
                {selectedAlert.description}
              </Alert>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom>Severity</Typography>
                  <Chip label={selectedAlert.severity} color={getSeverityColor(selectedAlert.severity) as any} />
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom>Status</Typography>
                  <Chip label={selectedAlert.status} variant="outlined" />
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="subtitle2" gutterBottom>Affected Systems</Typography>
                  <Box display="flex" gap={1} flexWrap="wrap">
                    {selectedAlert.affectedSystems.map((system) => (
                      <Chip key={system} label={system} variant="outlined" size="small" />
                    ))}
                  </Box>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="subtitle2" gutterBottom>Timestamp</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {new Date(selectedAlert.timestamp).toLocaleString()}
                  </Typography>
                </Grid>
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsOpen(false)}>Close</Button>
          <Button variant="contained" onClick={() => setDetailsOpen(false)}>
            Mark as Resolved
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default SecurityMonitorPanel;
