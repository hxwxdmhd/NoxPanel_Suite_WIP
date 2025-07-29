import React from 'react';
import { Box, Container, Typography, Paper } from '@mui/material';

const Security: React.FC = () => {
  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box mb={4}>
        <Typography variant="h3" component="h1" gutterBottom>
          Security Monitoring
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Real-time security alerts and threat monitoring
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
          Security Dashboard
        </Typography>
        <Typography variant="body1">
          Security monitoring interface is being developed...
        </Typography>
      </Paper>
    </Container>
  );
};

export default Security;