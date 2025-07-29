import React from 'react';
import { Box, Container, Typography, Paper } from '@mui/material';

const PluginManager: React.FC = () => {
  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box mb={4}>
        <Typography variant="h3" component="h1" gutterBottom>
          Plugin Manager
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Manage and configure NoxPanel plugins
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
          Plugin Management System
        </Typography>
        <Typography variant="body1">
          Plugin management interface is being developed...
        </Typography>
      </Paper>
    </Container>
  );
};

export default PluginManager;