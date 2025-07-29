import React from 'react';
import { Box, Container, Typography, Paper, Button } from '@mui/material';

const Login: React.FC = () => {
  return (
    <Container maxWidth="sm" sx={{ py: 8 }}>
      <Paper 
        elevation={4} 
        sx={{ 
          p: 6, 
          textAlign: 'center',
          borderRadius: 2
        }}
      >
        <Typography variant="h3" component="h1" gutterBottom>
          NoxPanel Suite
        </Typography>
        <Typography variant="h6" color="text.secondary" gutterBottom>
          ADHD-Friendly Network Management
        </Typography>
        
        <Box mt={4}>
          <Typography variant="body1" gutterBottom>
            Login interface is being developed...
          </Typography>
          <Button 
            variant="contained" 
            size="large" 
            sx={{ mt: 2 }}
            disabled
          >
            Sign In
          </Button>
        </Box>
      </Paper>
    </Container>
  );
};

export default Login;