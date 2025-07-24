import React from 'react';
import { Box, Typography, Card, CardContent } from '@mui/material';

const Settings = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Settings
      </Typography>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            System Settings
          </Typography>
          <Typography variant="body1">
            Advanced settings panel coming soon...
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
};

export default Settings;
