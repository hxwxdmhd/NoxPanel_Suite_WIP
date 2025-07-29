import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Avatar,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Chip,
  IconButton,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  LinearProgress,
  Alert,
  Tooltip,
  Divider
} from '@mui/material';
import {
  Business,
  People,
  Security,
  CloudQueue,
  Settings,
  Add,
  Edit,
  Delete,
  Visibility,
  TrendingUp,
  Storage,
  NetworkCheck,
  AdminPanelSettings
} from '@mui/icons-material';

interface Tenant {
  id: string;
  name: string;
  domain: string;
  status: 'active' | 'suspended' | 'pending';
  users: number;
  resources: {
    cpu: number;
    memory: number;
    storage: number;
  };
  subscription: {
    plan: string;
    expiresAt: string;
  };
  created: string;
  lastAccess: string;
}

interface TenantMetrics {
  totalTenants: number;
  activeTenants: number;
  resourceUsage: {
    cpu: number;
    memory: number;
    storage: number;
  };
  revenue: number;
}

const TenantDashboard: React.FC = () => {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [metrics, setMetrics] = useState<TenantMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedTenant, setSelectedTenant] = useState<Tenant | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [actionType, setActionType] = useState<'create' | 'edit' | 'view'>('view');

  useEffect(() => {
    fetchTenants();
    fetchMetrics();
  }, []);

  const fetchTenants = async () => {
    try {
      // Simulate API call
      const mockTenants: Tenant[] = [
        {
          id: '1',
          name: 'Acme Corporation',
          domain: 'acme.corp',
          status: 'active',
          users: 150,
          resources: { cpu: 75, memory: 68, storage: 45 },
          subscription: { plan: 'Enterprise', expiresAt: '2025-12-31' },
          created: '2024-01-15',
          lastAccess: '2025-07-18'
        },
        {
          id: '2',
          name: 'TechStart Inc',
          domain: 'techstart.io',
          status: 'active',
          users: 25,
          resources: { cpu: 35, memory: 42, storage: 28 },
          subscription: { plan: 'Professional', expiresAt: '2025-09-30' },
          created: '2024-03-22',
          lastAccess: '2025-07-17'
        },
        {
          id: '3',
          name: 'Global Solutions Ltd',
          domain: 'globalsol.com',
          status: 'pending',
          users: 0,
          resources: { cpu: 0, memory: 0, storage: 0 },
          subscription: { plan: 'Basic', expiresAt: '2025-08-15' },
          created: '2025-07-10',
          lastAccess: 'Never'
        }
      ];
      setTenants(mockTenants);
    } catch (error) {
      console.error('Error fetching tenants:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchMetrics = async () => {
    try {
      // Simulate API call
      const mockMetrics: TenantMetrics = {
        totalTenants: 3,
        activeTenants: 2,
        resourceUsage: { cpu: 55, memory: 55, storage: 36 },
        revenue: 25000
      };
      setMetrics(mockMetrics);
    } catch (error) {
      console.error('Error fetching metrics:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'success';
      case 'suspended': return 'error';
      case 'pending': return 'warning';
      default: return 'default';
    }
  };

  const handleTenantAction = (tenant: Tenant | null, action: 'create' | 'edit' | 'view') => {
    setSelectedTenant(tenant);
    setActionType(action);
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setSelectedTenant(null);
  };

  const ResourceUsageBar = ({ label, value, color }: { label: string; value: number; color: string }) => (
    <Box sx={{ mb: 2 }}>
      <Box display="flex" justifyContent="space-between" mb={1}>
        <Typography variant="body2" color="text.secondary">{label}</Typography>
        <Typography variant="body2" color="text.secondary">{value}%</Typography>
      </Box>
      <LinearProgress 
        variant="determinate" 
        value={value} 
        sx={{ 
          height: 8, 
          borderRadius: 4,
          backgroundColor: 'rgba(0,0,0,0.1)',
          '& .MuiLinearProgress-bar': {
            backgroundColor: color,
            borderRadius: 4
          }
        }}
      />
    </Box>
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
          🏢 Tenant Management Dashboard
        </Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => handleTenantAction(null, 'create')}
          sx={{ borderRadius: 2 }}
        >
          Create Tenant
        </Button>
      </Box>

      {/* Metrics Overview */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} md={3}>
          <Card sx={{ textAlign: 'center', p: 2 }}>
            <Avatar sx={{ mx: 'auto', mb: 2, bgcolor: 'primary.main' }}>
              <Business />
            </Avatar>
            <Typography variant="h4" color="primary">
              {metrics?.totalTenants || 0}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Total Tenants
            </Typography>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card sx={{ textAlign: 'center', p: 2 }}>
            <Avatar sx={{ mx: 'auto', mb: 2, bgcolor: 'success.main' }}>
              <TrendingUp />
            </Avatar>
            <Typography variant="h4" color="success.main">
              {metrics?.activeTenants || 0}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Active Tenants
            </Typography>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card sx={{ textAlign: 'center', p: 2 }}>
            <Avatar sx={{ mx: 'auto', mb: 2, bgcolor: 'info.main' }}>
              <People />
            </Avatar>
            <Typography variant="h4" color="info.main">
              {tenants.reduce((sum, tenant) => sum + tenant.users, 0)}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Total Users
            </Typography>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card sx={{ textAlign: 'center', p: 2 }}>
            <Avatar sx={{ mx: 'auto', mb: 2, bgcolor: 'warning.main' }}>
              <TrendingUp />
            </Avatar>
            <Typography variant="h4" color="warning.main">
              ${metrics?.revenue?.toLocaleString() || 0}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Monthly Revenue
            </Typography>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Resource Usage Overview */}
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <CloudQueue sx={{ mr: 1, verticalAlign: 'middle' }} />
                Resource Usage
              </Typography>
              <Divider sx={{ mb: 2 }} />
              {metrics && (
                <>
                  <ResourceUsageBar label="CPU" value={metrics.resourceUsage.cpu} color="#2196f3" />
                  <ResourceUsageBar label="Memory" value={metrics.resourceUsage.memory} color="#4caf50" />
                  <ResourceUsageBar label="Storage" value={metrics.resourceUsage.storage} color="#ff9800" />
                </>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Tenant List */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <AdminPanelSettings sx={{ mr: 1, verticalAlign: 'middle' }} />
                Active Tenants
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <List>
                {tenants.map((tenant) => (
                  <ListItem
                    key={tenant.id}
                    secondaryAction={
                      <Box>
                        <Tooltip title="View Details">
                          <IconButton
                            onClick={() => handleTenantAction(tenant, 'view')}
                            size="small"
                            sx={{ mr: 1 }}
                          >
                            <Visibility />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Edit">
                          <IconButton
                            onClick={() => handleTenantAction(tenant, 'edit')}
                            size="small"
                            sx={{ mr: 1 }}
                          >
                            <Edit />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Settings">
                          <IconButton size="small">
                            <Settings />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    }
                  >
                    <ListItemAvatar>
                      <Avatar sx={{ bgcolor: 'primary.main' }}>
                        {tenant.name.charAt(0)}
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={
                        <Box display="flex" alignItems="center" gap={2}>
                          <Typography variant="subtitle1">{tenant.name}</Typography>
                          <Chip
                            label={tenant.status}
                            color={getStatusColor(tenant.status) as any}
                            size="small"
                          />
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            {tenant.domain} • {tenant.users} users • {tenant.subscription.plan}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Last access: {tenant.lastAccess}
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

      {/* Tenant Details Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {actionType === 'create' ? 'Create New Tenant' : 
           actionType === 'edit' ? 'Edit Tenant' : 'Tenant Details'}
        </DialogTitle>
        <DialogContent>
          {selectedTenant && (
            <Box sx={{ pt: 2 }}>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Tenant Name"
                    value={selectedTenant.name}
                    disabled={actionType === 'view'}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Domain"
                    value={selectedTenant.domain}
                    disabled={actionType === 'view'}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth disabled={actionType === 'view'}>
                    <InputLabel>Status</InputLabel>
                    <Select value={selectedTenant.status}>
                      <MenuItem value="active">Active</MenuItem>
                      <MenuItem value="suspended">Suspended</MenuItem>
                      <MenuItem value="pending">Pending</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Users"
                    type="number"
                    value={selectedTenant.users}
                    disabled={actionType === 'view'}
                  />
                </Grid>
                <Grid item xs={12}>
                  <Alert severity="info">
                    <strong>Resource Usage:</strong> CPU {selectedTenant.resources.cpu}%, 
                    Memory {selectedTenant.resources.memory}%, 
                    Storage {selectedTenant.resources.storage}%
                  </Alert>
                </Grid>
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          {actionType !== 'view' && (
            <Button variant="contained" onClick={handleCloseDialog}>
              {actionType === 'create' ? 'Create' : 'Save'}
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TenantDashboard;
