import React from 'react';
import { Box, Container, Typography, Paper } from '@mui/material';

const Analytics: React.FC = () => {
  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box mb={4}>
        <Typography variant="h3" component="h1" gutterBottom>
          Analytics & Reports
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Data visualization and reporting dashboard
        </Typography>
      </Box>
      
      <Paper 
        elevation={2} 
        sx={{ 
          p: 4, 
          textAlign: 'center',
          borderRadius: 2
        }}
      >
        <Typography variant="h5" gutterBottom>
          Analytics Dashboard
        </Typography>
        <Typography variant="body1">
          Analytics and reporting interface is being developed...
        </Typography>
      </Paper>
    </Container>
  );
};

export default Analytics;