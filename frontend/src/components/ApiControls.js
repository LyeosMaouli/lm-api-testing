/**
 * API Controls component with action buttons
 */

import React from 'react'
import {
  Card,
  CardContent,
  Typography,
  Button,
  Box,
  Divider,
  FormControlLabel,
  Switch,
} from '@mui/material'
import {
  AccountCircle,
  Email,
  Contacts,
  Refresh,
  Event,
} from '@mui/icons-material'

const ApiControls = ({ 
  onApiCall, 
  onEmailDialog, 
  onEventDialog, 
  formatJson, 
  onFormatToggle, 
  loading 
}) => {
  const apiButtons = [
    {
      label: 'Get Account Info',
      icon: <AccountCircle />,
      onClick: () => onApiCall('account'),
      color: 'primary',
    },
    {
      label: 'Get Contacts',
      icon: <Contacts />,
      onClick: () => onApiCall('contacts'),
      color: 'secondary',
    },
    {
      label: 'Send Test Email',
      icon: <Email />,
      onClick: onEmailDialog,
      color: 'success',
    },
    {
      label: 'Send Custom Event',
      icon: <Event />,
      onClick: onEventDialog,
      color: 'warning',
    },
    {
      label: 'Health Check',
      icon: <Refresh />,
      onClick: () => onApiCall('health'),
      color: 'info',
    },
  ]

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          API Operations
        </Typography>
        
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {apiButtons.map((button, index) => (
            <Button
              key={index}
              variant="contained"
              color={button.color}
              size="large"
              startIcon={button.icon}
              onClick={button.onClick}
              disabled={loading}
              fullWidth
              sx={{ py: 1.5 }}
            >
              {button.label}
            </Button>
          ))}
        </Box>

        <Divider sx={{ my: 2 }} />

        <FormControlLabel
          control={
            <Switch
              checked={formatJson}
              onChange={(e) => onFormatToggle(e.target.checked)}
            />
          }
          label="Format JSON Response"
        />
      </CardContent>
    </Card>
  )
}

export default ApiControls