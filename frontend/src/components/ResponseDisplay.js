/**
 * Response Display component for API responses
 */

import React from 'react'
import {
  Card,
  CardContent,
  Typography,
  TextField,
  Alert,
  CircularProgress,
  Box,
  IconButton,
  Snackbar,
} from '@mui/material'
import { ContentCopy as CopyIcon, Close as CloseIcon } from '@mui/icons-material'

const ResponseDisplay = ({ 
  response, 
  error, 
  loading, 
  formatJson 
}) => {
  const [copySuccess, setCopySuccess] = React.useState(false)

  const formatResponse = (data) => {
    if (!data) return ''
    
    if (formatJson) {
      try {
        return JSON.stringify(data, null, 2)
      } catch (e) {
        return String(data)
      }
    }
    return String(data)
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(formatResponse(response))
      setCopySuccess(true)
    } catch (err) {
      console.error('Failed to copy to clipboard:', err)
    }
  }

  const handleCloseCopySnackbar = () => {
    setCopySuccess(false)
  }

  return (
    <>
      <Card sx={{ height: '100%' }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" sx={{ flexGrow: 1 }}>
              API Response
            </Typography>
            {response && (
              <IconButton
                onClick={handleCopy}
                size="small"
                title="Copy response to clipboard"
              >
                <CopyIcon />
              </IconButton>
            )}
          </Box>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          {loading && (
            <Box
              sx={{ 
                display: 'flex', 
                justifyContent: 'center', 
                alignItems: 'center',
                py: 4 
              }}
            >
              <CircularProgress />
              <Typography variant="body2" sx={{ ml: 2 }}>
                Processing request...
              </Typography>
            </Box>
          )}

          <TextField
            multiline
            rows={20}
            fullWidth
            value={formatResponse(response)}
            placeholder="API responses will appear here..."
            variant="outlined"
            InputProps={{
              readOnly: true,
              sx: {
                fontFamily: 'monospace',
                fontSize: '0.875rem',
                backgroundColor: '#f5f5f5',
              },
            }}
            helperText={
              response 
                ? `Response received at ${new Date().toLocaleTimeString()}`
                : 'Click any API operation button to see the response'
            }
          />
        </CardContent>
      </Card>

      <Snackbar
        open={copySuccess}
        autoHideDuration={2000}
        onClose={handleCloseCopySnackbar}
        message="Response copied to clipboard"
        action={
          <IconButton
            size="small"
            color="inherit"
            onClick={handleCloseCopySnackbar}
          >
            <CloseIcon fontSize="small" />
          </IconButton>
        }
      />
    </>
  )
}

export default ResponseDisplay