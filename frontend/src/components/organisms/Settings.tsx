import React from 'react';
import { Box, Container, Typography, Paper } from '@mui/material';

const Settings: React.FC = () => {
  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box mb={4}>
        <Typography variant="h3" component="h1" gutterBottom>
          Settings
        </Typography>
        <Typography variant="body1" color="text.secondary">
          System preferences and accessibility options
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
          Settings Panel
        </Typography>
        <Typography variant="body1">
          Settings and preferences interface is being developed...
        </Typography>
      </Paper>
    </Container>
  );
};

export default Settings;