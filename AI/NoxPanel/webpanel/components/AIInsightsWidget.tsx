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
  ListItemIcon,
  ListItemText,
  Chip,
  LinearProgress,
  Paper,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Divider,
  Alert,
  AlertTitle,
  Badge,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@mui/material';
import {
  Psychology,
  TrendingUp,
  TrendingDown,
  Insights,
  Analytics,
  Timeline,
  PieChart,
  BarChart,
  ShowChart,
  Speed,
  Memory,
  Storage,
  NetworkCheck,
  Cloud,
  Security,
  People,
  Devices,
  Refresh,
  Download,
  Share,
  Settings,
  Notifications,
  Warning,
  CheckCircle,
  Info,
  BugReport,
  Lightbulb,
  AutoFixHigh,
  SmartToy
} from '@mui/icons-material';

interface AIInsight {
  id: string;
  type: 'performance' | 'security' | 'optimization' | 'prediction' | 'anomaly';
  title: string;
  description: string;
  confidence: number;
  impact: 'high' | 'medium' | 'low';
  recommendation: string;
  timestamp: string;
  status: 'new' | 'acknowledged' | 'implementing' | 'resolved';
}

interface SystemMetrics {
  cpu: { current: number; average: number; trend: 'up' | 'down' | 'stable' };
  memory: { current: number; average: number; trend: 'up' | 'down' | 'stable' };
  storage: { current: number; average: number; trend: 'up' | 'down' | 'stable' };
  network: { current: number; average: number; trend: 'up' | 'down' | 'stable' };
  responseTime: { current: number; average: number; trend: 'up' | 'down' | 'stable' };
  uptime: number;
}

interface PredictiveAnalysis {
  resourcePrediction: {
    cpu: { nextHour: number; nextDay: number; nextWeek: number };
    memory: { nextHour: number; nextDay: number; nextWeek: number };
    storage: { nextHour: number; nextDay: number; nextWeek: number };
  };
  scalingRecommendations: string[];
  costOptimization: string[];
  maintenanceSchedule: string[];
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel = ({ children, value, index }: TabPanelProps) => (
  <div role="tabpanel" hidden={value !== index}>
    {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
  </div>
);

const AIInsightsWidget: React.FC = () => {
  const [aiInsights, setAiInsights] = useState<AIInsight[]>([]);
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [predictions, setPredictions] = useState<PredictiveAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedInsight, setSelectedInsight] = useState<AIInsight | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [tabValue, setTabValue] = useState(0);

  useEffect(() => {
    fetchAIInsights();
    const interval = setInterval(fetchAIInsights, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  const fetchAIInsights = async () => {
    try {
      // Simulate AI-powered insights
      const mockInsights: AIInsight[] = [
        {
          id: '1',
          type: 'performance',
          title: 'CPU Usage Pattern Anomaly Detected',
          description: 'Unusual CPU spikes detected during off-peak hours, suggesting potential background processes or security issues.',
          confidence: 92,
          impact: 'high',
          recommendation: 'Review scheduled tasks and investigate unauthorized processes. Consider implementing CPU throttling.',
          timestamp: new Date().toISOString(),
          status: 'new'
        },
        {
          id: '2',
          type: 'optimization',
          title: 'Memory Usage Optimization Opportunity',
          description: 'AI analysis suggests 23% memory usage reduction possible through cache optimization and garbage collection tuning.',
          confidence: 87,
          impact: 'medium',
          recommendation: 'Implement memory pooling for frequently accessed objects and optimize cache retention policies.',
          timestamp: new Date(Date.now() - 1800000).toISOString(),
          status: 'acknowledged'
        },
        {
          id: '3',
          type: 'prediction',
          title: 'Storage Capacity Warning',
          description: 'Based on current growth patterns, storage capacity will reach 85% within 2 weeks.',
          confidence: 95,
          impact: 'high',
          recommendation: 'Plan for storage expansion or implement data archival policies. Consider cloud storage integration.',
          timestamp: new Date(Date.now() - 3600000).toISOString(),
          status: 'implementing'
        },
        {
          id: '4',
          type: 'security',
          title: 'Network Traffic Anomaly',
          description: 'Unusual network traffic patterns detected from internal subnet, potentially indicating lateral movement.',
          confidence: 78,
          impact: 'high',
          recommendation: 'Review network segmentation and implement additional monitoring for suspicious lateral movement.',
          timestamp: new Date(Date.now() - 7200000).toISOString(),
          status: 'new'
        }
      ];

      const mockMetrics: SystemMetrics = {
        cpu: { current: 68, average: 45, trend: 'up' },
        memory: { current: 72, average: 58, trend: 'up' },
        storage: { current: 84, average: 76, trend: 'up' },
        network: { current: 45, average: 32, trend: 'up' },
        responseTime: { current: 125, average: 98, trend: 'up' },
        uptime: 99.8
      };

      const mockPredictions: PredictiveAnalysis = {
        resourcePrediction: {
          cpu: { nextHour: 72, nextDay: 68, nextWeek: 75 },
          memory: { nextHour: 75, nextDay: 73, nextWeek: 78 },
          storage: { nextHour: 84, nextDay: 85, nextWeek: 87 }
        },
        scalingRecommendations: [
          'Consider adding 2 additional CPU cores for peak load handling',
          'Memory upgrade to 32GB recommended within 1 month',
          'Network bandwidth increase needed for growing user base'
        ],
        costOptimization: [
          'Migrate 15% of workload to cheaper storage tiers',
          'Implement auto-scaling to reduce idle resource costs',
          'Consider reserved instances for 20% cost savings'
        ],
        maintenanceSchedule: [
          'Database optimization recommended in 3 days',
          'Cache cleanup scheduled for low-traffic window',
          'Security patch deployment planned for weekend'
        ]
      };

      setAiInsights(mockInsights);
      setMetrics(mockMetrics);
      setPredictions(mockPredictions);
    } catch (error) {
      console.error('Error fetching AI insights:', error);
    } finally {
      setLoading(false);
    }
  };

  const getInsightIcon = (type: string) => {
    switch (type) {
      case 'performance': return <Speed />;
      case 'security': return <Security />;
      case 'optimization': return <AutoFixHigh />;
      case 'prediction': return <Timeline />;
      case 'anomaly': return <BugReport />;
      default: return <Insights />;
    }
  };

  const getInsightColor = (type: string) => {
    switch (type) {
      case 'performance': return '#2196f3';
      case 'security': return '#f44336';
      case 'optimization': return '#4caf50';
      case 'prediction': return '#ff9800';
      case 'anomaly': return '#9c27b0';
      default: return '#607d8b';
    }
  };

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return <TrendingUp color="error" />;
      case 'down': return <TrendingDown color="success" />;
      case 'stable': return <ShowChart color="info" />;
      default: return <ShowChart />;
    }
  };

  const handleInsightClick = (insight: AIInsight) => {
    setSelectedInsight(insight);
    setDetailsOpen(true);
  };

  const MetricCard = ({ title, metric, icon, color }: { title: string; metric: any; icon: React.ReactNode; color: string }) => (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Avatar sx={{ bgcolor: color }}>
            {icon}
          </Avatar>
          {getTrendIcon(metric.trend)}
        </Box>
        <Typography variant="h4" color={color} gutterBottom>
          {metric.current}%
        </Typography>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          {title}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          Avg: {metric.average}% | Trend: {metric.trend}
        </Typography>
      </CardContent>
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
          🤖 AI Insights & Analytics
        </Typography>
        <Box>
          <IconButton onClick={fetchAIInsights} sx={{ mr: 1 }}>
            <Refresh />
          </IconButton>
          <IconButton sx={{ mr: 1 }}>
            <Download />
          </IconButton>
          <IconButton>
            <Settings />
          </IconButton>
        </Box>
      </Box>

      <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)} sx={{ mb: 3 }}>
        <Tab label="Insights" icon={<Psychology />} />
        <Tab label="Metrics" icon={<Analytics />} />
        <Tab label="Predictions" icon={<Timeline />} />
      </Tabs>

      <TabPanel value={tabValue} index={0}>
        {/* AI Insights */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h6">
                    <SmartToy sx={{ mr: 1, verticalAlign: 'middle' }} />
                    AI-Generated Insights
                  </Typography>
                  <Badge badgeContent={aiInsights.filter(i => i.status === 'new').length} color="error">
                    <Notifications />
                  </Badge>
                </Box>
                <Divider sx={{ mb: 2 }} />
                <List>
                  {aiInsights.map((insight) => (
                    <ListItem
                      key={insight.id}
                      button
                      onClick={() => handleInsightClick(insight)}
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
                        <Avatar sx={{ bgcolor: getInsightColor(insight.type) }}>
                          {getInsightIcon(insight.type)}
                        </Avatar>
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Box display="flex" alignItems="center" gap={2}>
                            <Typography variant="subtitle1">{insight.title}</Typography>
                            <Chip
                              label={insight.impact}
                              color={getImpactColor(insight.impact) as any}
                              size="small"
                            />
                            <Chip
                              label={`${insight.confidence}%`}
                              variant="outlined"
                              size="small"
                            />
                          </Box>
                        }
                        secondary={
                          <Box>
                            <Typography variant="body2" color="text.secondary">
                              {insight.description}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {new Date(insight.timestamp).toLocaleString()}
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

          <Grid item xs={12} md={4}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <Lightbulb sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Quick Actions
                </Typography>
                <Divider sx={{ mb: 2 }} />
                <List>
                  <ListItem>
                    <Button variant="outlined" fullWidth startIcon={<AutoFixHigh />}>
                      Auto-Optimize Performance
                    </Button>
                  </ListItem>
                  <ListItem>
                    <Button variant="outlined" fullWidth startIcon={<Security />}>
                      Security Scan
                    </Button>
                  </ListItem>
                  <ListItem>
                    <Button variant="outlined" fullWidth startIcon={<Storage />}>
                      Storage Cleanup
                    </Button>
                  </ListItem>
                  <ListItem>
                    <Button variant="outlined" fullWidth startIcon={<Timeline />}>
                      Capacity Planning
                    </Button>
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        {/* System Metrics */}
        <Grid container spacing={3} mb={3}>
          <Grid item xs={12} md={2.4}>
            <MetricCard title="CPU Usage" metric={metrics?.cpu} icon={<Speed />} color="#2196f3" />
          </Grid>
          <Grid item xs={12} md={2.4}>
            <MetricCard title="Memory" metric={metrics?.memory} icon={<Memory />} color="#4caf50" />
          </Grid>
          <Grid item xs={12} md={2.4}>
            <MetricCard title="Storage" metric={metrics?.storage} icon={<Storage />} color="#ff9800" />
          </Grid>
          <Grid item xs={12} md={2.4}>
            <MetricCard title="Network" metric={metrics?.network} icon={<NetworkCheck />} color="#9c27b0" />
          </Grid>
          <Grid item xs={12} md={2.4}>
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Avatar sx={{ bgcolor: '#607d8b' }}>
                    <CheckCircle />
                  </Avatar>
                  <TrendingUp color="success" />
                </Box>
                <Typography variant="h4" color="#607d8b" gutterBottom>
                  {metrics?.uptime}%
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Uptime
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Response: {metrics?.responseTime.current}ms
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        {/* Predictive Analysis */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <Timeline sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Resource Predictions
                </Typography>
                <Divider sx={{ mb: 2 }} />
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Resource</TableCell>
                        <TableCell>Next Hour</TableCell>
                        <TableCell>Next Day</TableCell>
                        <TableCell>Next Week</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      <TableRow>
                        <TableCell>CPU</TableCell>
                        <TableCell>{predictions?.resourcePrediction.cpu.nextHour}%</TableCell>
                        <TableCell>{predictions?.resourcePrediction.cpu.nextDay}%</TableCell>
                        <TableCell>{predictions?.resourcePrediction.cpu.nextWeek}%</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Memory</TableCell>
                        <TableCell>{predictions?.resourcePrediction.memory.nextHour}%</TableCell>
                        <TableCell>{predictions?.resourcePrediction.memory.nextDay}%</TableCell>
                        <TableCell>{predictions?.resourcePrediction.memory.nextWeek}%</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Storage</TableCell>
                        <TableCell>{predictions?.resourcePrediction.storage.nextHour}%</TableCell>
                        <TableCell>{predictions?.resourcePrediction.storage.nextDay}%</TableCell>
                        <TableCell>{predictions?.resourcePrediction.storage.nextWeek}%</TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <TrendingUp sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Scaling Recommendations
                </Typography>
                <Divider sx={{ mb: 2 }} />
                <List>
                  {predictions?.scalingRecommendations.map((rec, index) => (
                    <ListItem key={index}>
                      <ListItemIcon>
                        <CheckCircle color="success" />
                      </ListItemIcon>
                      <ListItemText primary={rec} />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      {/* Insight Details Dialog */}
      <Dialog open={detailsOpen} onClose={() => setDetailsOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          AI Insight Details
        </DialogTitle>
        <DialogContent>
          {selectedInsight && (
            <Box sx={{ pt: 2 }}>
              <Alert severity={getImpactColor(selectedInsight.impact) as any} sx={{ mb: 2 }}>
                <AlertTitle>{selectedInsight.title}</AlertTitle>
                {selectedInsight.description}
              </Alert>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom>Type</Typography>
                  <Chip label={selectedInsight.type} sx={{ bgcolor: getInsightColor(selectedInsight.type), color: 'white' }} />
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom>Confidence</Typography>
                  <Box display="flex" alignItems="center">
                    <LinearProgress 
                      variant="determinate" 
                      value={selectedInsight.confidence} 
                      sx={{ flexGrow: 1, mr: 1 }}
                    />
                    <Typography variant="body2">{selectedInsight.confidence}%</Typography>
                  </Box>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="subtitle2" gutterBottom>Recommendation</Typography>
                  <Paper sx={{ p: 2, backgroundColor: 'background.default' }}>
                    <Typography variant="body2">{selectedInsight.recommendation}</Typography>
                  </Paper>
                </Grid>
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsOpen(false)}>Close</Button>
          <Button variant="outlined" onClick={() => setDetailsOpen(false)}>
            Acknowledge
          </Button>
          <Button variant="contained" onClick={() => setDetailsOpen(false)}>
            Implement
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AIInsightsWidget;
