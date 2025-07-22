/**
 * Error Boundary component to catch JavaScript errors anywhere in the component tree
 */

import React from 'react'
import {
  Alert,
  AlertTitle,
  Button,
  Box,
  Typography,
  Paper,
} from '@mui/material'
import { Refresh as RefreshIcon } from '@mui/icons-material'

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    }
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true }
  }

  componentDidCatch(error, errorInfo) {
    // Log error details
    console.error('Error Boundary caught an error:', error, errorInfo)
    
    this.setState({
      error,
      errorInfo,
    })

    // In production, you might want to log this to an error reporting service
    if (process.env.NODE_ENV === 'production') {
      // Example: logErrorToService(error, errorInfo)
    }
  }

  handleReload = () => {
    window.location.reload()
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    })
  }

  render() {
    if (this.state.hasError) {
      const isDevelopment = process.env.NODE_ENV === 'development'

      return (
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: '50vh',
            p: 2,
          }}
        >
          <Paper
            elevation={3}
            sx={{
              p: 4,
              maxWidth: 600,
              width: '100%',
              textAlign: 'center',
            }}
          >
            <Alert severity="error" sx={{ mb: 3, textAlign: 'left' }}>
              <AlertTitle>Application Error</AlertTitle>
              Something went wrong. The application encountered an unexpected error.
            </Alert>

            <Typography variant="h6" gutterBottom>
              What can you do?
            </Typography>

            <Box sx={{ mb: 3, textAlign: 'left' }}>
              <Typography variant="body2" paragraph>
                • Try refreshing the page
              </Typography>
              <Typography variant="body2" paragraph>
                • Check your internet connection
              </Typography>
              <Typography variant="body2" paragraph>
                • If the problem persists, please contact support
              </Typography>
            </Box>

            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
              <Button
                variant="contained"
                startIcon={<RefreshIcon />}
                onClick={this.handleReload}
                color="primary"
              >
                Reload Page
              </Button>
              <Button
                variant="outlined"
                onClick={this.handleReset}
                color="secondary"
              >
                Try Again
              </Button>
            </Box>

            {isDevelopment && this.state.error && (
              <Box
                sx={{
                  mt: 4,
                  p: 2,
                  backgroundColor: '#f5f5f5',
                  borderRadius: 1,
                  textAlign: 'left',
                }}
              >
                <Typography variant="h6" color="error" gutterBottom>
                  Development Error Details:
                </Typography>
                <Typography
                  variant="body2"
                  component="pre"
                  sx={{
                    fontFamily: 'monospace',
                    fontSize: '0.75rem',
                    overflow: 'auto',
                    maxHeight: 200,
                    whiteSpace: 'pre-wrap',
                  }}
                >
                  {this.state.error.toString()}
                  {this.state.errorInfo.componentStack}
                </Typography>
              </Box>
            )}
          </Paper>
        </Box>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary