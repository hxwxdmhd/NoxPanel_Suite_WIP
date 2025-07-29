import React from 'react';
import { Box, Typography, Card, CardContent } from '@mui/material';

const Analytics = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Analytics
      </Typography>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Analytics Dashboard
          </Typography>
          <Typography variant="body1">
            Advanced analytics features coming soon...
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
};

export default Analytics;
