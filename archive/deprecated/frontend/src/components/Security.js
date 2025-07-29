import React from 'react';
import { Box, Typography, Card, CardContent } from '@mui/material';

const Security = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Security Center
      </Typography>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Security Dashboard
          </Typography>
          <Typography variant="body1">
            Advanced security features coming soon...
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
};

export default Security;
