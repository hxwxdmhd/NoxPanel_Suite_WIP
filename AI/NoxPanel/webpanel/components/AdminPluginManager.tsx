import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Switch,
  Chip,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Tooltip,
  Grid,
  LinearProgress
} from '@mui/material';
import {
  Security,
  Warning,
  CheckCircle,
  Block,
  Refresh,
  Settings,
  Info,
  Delete,
  CloudDownload
} from '@mui/icons-material';

interface Plugin {
  id: string;
  name: string;
  version: string;
  status: 'active' | 'inactive' | 'quarantined' | 'updating';
  securityScore: number;
  lastUpdated: string;
  description: string;
  dependencies: string[];
  author: string;
  category: string;
  riskLevel: 'low' | 'medium' | 'high';
}

interface AdminPluginManagerProps {
  plugins: Plugin[];
  onPluginToggle: (pluginId: string, enabled: boolean) => void;
  onPluginQuarantine: (pluginId: string) => void;
  onPluginUpdate: (pluginId: string) => void;
  onPluginDelete: (pluginId: string) => void;
  systemHealth: number;
  rlvrCompliance: number;
}

const AdminPluginManager: React.FC<AdminPluginManagerProps> = ({
  plugins,
  onPluginToggle,
  onPluginQuarantine,
  onPluginUpdate,
  onPluginDelete,
  systemHealth,
  rlvrCompliance
}) => {
  const [selectedPlugin, setSelectedPlugin] = useState<Plugin | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');

  const filteredPlugins = plugins.filter(plugin => {
    const matchesFilter = filterStatus === 'all' || plugin.status === filterStatus;
    const matchesSearch = plugin.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         plugin.description.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'success';
      case 'inactive': return 'default';
      case 'quarantined': return 'error';
      case 'updating': return 'warning';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <CheckCircle color="success" />;
      case 'inactive': return <Block color="disabled" />;
      case 'quarantined': return <Warning color="error" />;
      case 'updating': return <Refresh color="warning" />;
      default: return <Info />;
    }
  };

  const getRiskLevelColor = (riskLevel: string) => {
    switch (riskLevel) {
      case 'low': return 'success';
      case 'medium': return 'warning';
      case 'high': return 'error';
      default: return 'default';
    }
  };

  const handlePluginClick = (plugin: Plugin) => {
    setSelectedPlugin(plugin);
    setDialogOpen(true);
  };

  const handleTogglePlugin = (pluginId: string, enabled: boolean) => {
    onPluginToggle(pluginId, enabled);
  };

  const quarantinedCount = plugins.filter(p => p.status === 'quarantined').length;
  const activeCount = plugins.filter(p => p.status === 'active').length;
  const totalCount = plugins.length;

  return (
    <Box sx={{ p: 3 }}>
      {/* Header Section */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          🔧 Plugin Management Center
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Ultimate Suite v11.0 - Enterprise Plugin Control
        </Typography>
      </Box>

      {/* System Health Overview */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Health
              </Typography>
              <LinearProgress
                variant="determinate"
                value={systemHealth}
                color={systemHealth > 90 ? 'success' : systemHealth > 70 ? 'warning' : 'error'}
                sx={{ mb: 1 }}
              />
              <Typography variant="body2" color="text.secondary">
                {systemHealth}% Operational
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                RLVR Compliance
              </Typography>
              <LinearProgress
                variant="determinate"
                value={rlvrCompliance}
                color={rlvrCompliance > 95 ? 'success' : rlvrCompliance > 85 ? 'warning' : 'error'}
                sx={{ mb: 1 }}
              />
              <Typography variant="body2" color="text.secondary">
                {rlvrCompliance}% Compliant
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Active Plugins
              </Typography>
              <Typography variant="h4" color="success.main">
                {activeCount}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                of {totalCount} total
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quarantined
              </Typography>
              <Typography variant="h4" color="error.main">
                {quarantinedCount}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Security Issues
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Security Alerts */}
      {quarantinedCount > 0 && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Typography variant="h6">Security Alert</Typography>
          {quarantinedCount} plugin(s) have been quarantined due to security concerns.
          Review and take appropriate action.
        </Alert>
      )}

      {/* Filter Controls */}
      <Box sx={{ mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <input
              type="text"
              placeholder="Search plugins..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                width: '100%',
                padding: '12px',
                borderRadius: '4px',
                border: '1px solid #ddd',
                fontSize: '14px'
              }}
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              style={{
                width: '100%',
                padding: '12px',
                borderRadius: '4px',
                border: '1px solid #ddd',
                fontSize: '14px'
              }}
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="quarantined">Quarantined</option>
              <option value="updating">Updating</option>
            </select>
          </Grid>
        </Grid>
      </Box>

      {/* Plugin Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Plugin</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Security Score</TableCell>
              <TableCell>Risk Level</TableCell>
              <TableCell>Last Updated</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredPlugins.map((plugin) => (
              <TableRow key={plugin.id} hover>
                <TableCell>
                  <Box sx={{ cursor: 'pointer' }} onClick={() => handlePluginClick(plugin)}>
                    <Typography variant="subtitle1" fontWeight="bold">
                      {plugin.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      v{plugin.version} • {plugin.category}
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  <Chip
                    icon={getStatusIcon(plugin.status)}
                    label={plugin.status.toUpperCase()}
                    color={getStatusColor(plugin.status)}
                    variant="outlined"
                  />
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <LinearProgress
                      variant="determinate"
                      value={plugin.securityScore}
                      color={plugin.securityScore > 80 ? 'success' : plugin.securityScore > 60 ? 'warning' : 'error'}
                      sx={{ width: 60, mr: 1 }}
                    />
                    <Typography variant="body2">
                      {plugin.securityScore}%
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  <Chip
                    label={plugin.riskLevel.toUpperCase()}
                    color={getRiskLevelColor(plugin.riskLevel)}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {new Date(plugin.lastUpdated).toLocaleDateString()}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Switch
                      checked={plugin.status === 'active'}
                      onChange={(e) => handleTogglePlugin(plugin.id, e.target.checked)}
                      disabled={plugin.status === 'quarantined'}
                    />
                    <Tooltip title="Update Plugin">
                      <IconButton
                        size="small"
                        onClick={() => onPluginUpdate(plugin.id)}
                        disabled={plugin.status === 'updating'}
                      >
                        <CloudDownload />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Quarantine Plugin">
                      <IconButton
                        size="small"
                        onClick={() => onPluginQuarantine(plugin.id)}
                        disabled={plugin.status === 'quarantined'}
                      >
                        <Security />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete Plugin">
                      <IconButton
                        size="small"
                        onClick={() => onPluginDelete(plugin.id)}
                        color="error"
                      >
                        <Delete />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Plugin Details Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {selectedPlugin?.name} - Plugin Details
        </DialogTitle>
        <DialogContent>
          {selectedPlugin && (
            <Box sx={{ mt: 2 }}>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="h6" gutterBottom>Basic Information</Typography>
                  <Typography><strong>Version:</strong> {selectedPlugin.version}</Typography>
                  <Typography><strong>Author:</strong> {selectedPlugin.author}</Typography>
                  <Typography><strong>Category:</strong> {selectedPlugin.category}</Typography>
                  <Typography><strong>Status:</strong> {selectedPlugin.status}</Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="h6" gutterBottom>Security Information</Typography>
                  <Typography><strong>Security Score:</strong> {selectedPlugin.securityScore}%</Typography>
                  <Typography><strong>Risk Level:</strong> {selectedPlugin.riskLevel}</Typography>
                  <Typography><strong>Last Updated:</strong> {new Date(selectedPlugin.lastUpdated).toLocaleString()}</Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="h6" gutterBottom>Description</Typography>
                  <Typography>{selectedPlugin.description}</Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="h6" gutterBottom>Dependencies</Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {selectedPlugin.dependencies.map((dep, index) => (
                      <Chip key={index} label={dep} size="small" />
                    ))}
                  </Box>
                </Grid>
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AdminPluginManager;