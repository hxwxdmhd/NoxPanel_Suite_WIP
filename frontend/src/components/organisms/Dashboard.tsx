import React from 'react';
import { Box, Container, Typography, Paper } from '@mui/material';

const Dashboard: React.FC = () => {
  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box mb={4}>
        <Typography variant="h3" component="h1" gutterBottom>
          NoxPanel Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Real-time network security monitoring and management
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
          Welcome to NoxPanel Suite
        </Typography>
        <Typography variant="body1">
          Your ADHD-friendly network management dashboard is loading...
        </Typography>
      </Paper>
    </Container>
  );
};

export default Dashboard;