import React, { useState, useCallback } from 'react'
import {
  Container,
  Paper,
  Typography,
  Box,
  Grid,
  Snackbar,
  Alert,
} from '@mui/material'

// Components
import ErrorBoundary from './components/ErrorBoundary'
import ApiControls from './components/ApiControls'
import ResponseDisplay from './components/ResponseDisplay'
import EmailDialog from './components/EmailDialog'
import EventDialog from './components/EventDialog'

// Hooks and utilities
import { useApi } from './hooks/useApi'
import { api } from './utils/api'

function App() {
  // State management
  const [emailDialog, setEmailDialog] = useState(false)
  const [eventDialog, setEventDialog] = useState(false)
  const [formatJson, setFormatJson] = useState(true)
  const [successMessage, setSuccessMessage] = useState('')
  const [showSuccess, setShowSuccess] = useState(false)

  // API hook
  const { loading, error, data, execute, clearError } = useApi()

  // API call handler
  const handleApiCall = useCallback(async (apiType) => {
    clearError()
    
    try {
      let result
      switch (apiType) {
        case 'health':
          result = await execute(api.healthCheck)
          break
        case 'account':
          result = await execute(api.getAccount)
          break
        case 'contacts':
          result = await execute(api.getContacts, 5, 0)
          break
        default:
          throw new Error('Unknown API operation')
      }
      return result
    } catch (err) {
      console.error('API call failed:', err)
    }
  }, [execute, clearError])

  // Dialog handlers
  const handleEmailDialog = useCallback(() => {
    setEmailDialog(true)
  }, [])

  const handleEventDialog = useCallback(() => {
    setEventDialog(true)
  }, [])

  const handleEmailSuccess = useCallback(() => {
    setSuccessMessage('Email sent successfully!')
    setShowSuccess(true)
  }, [])

  const handleEventSuccess = useCallback(() => {
    setSuccessMessage('Custom event sent successfully!')
    setShowSuccess(true)
  }, [])

  const handleFormatToggle = useCallback((checked) => {
    setFormatJson(checked)
  }, [])

  const handleCloseSuccess = useCallback(() => {
    setShowSuccess(false)
  }, [])

  return (
    <ErrorBoundary>
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Paper elevation={3} sx={{ p: 4 }}>
          <Box sx={{ mb: 4, textAlign: 'center' }}>
            <Typography variant="h3" component="h1" gutterBottom color="primary">
              Brevo API Integration
            </Typography>
            <Typography variant="h6" color="text.secondary">
              Enhanced single-page application for Brevo API testing
            </Typography>
          </Box>

          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <ApiControls
                onApiCall={handleApiCall}
                onEmailDialog={handleEmailDialog}
                onEventDialog={handleEventDialog}
                formatJson={formatJson}
                onFormatToggle={handleFormatToggle}
                loading={loading}
              />
            </Grid>

            <Grid item xs={12} md={8}>
              <ResponseDisplay
                response={data}
                error={error}
                loading={loading}
                formatJson={formatJson}
              />
            </Grid>
          </Grid>
        </Paper>

        <EmailDialog
          open={emailDialog}
          onClose={() => setEmailDialog(false)}
          onSuccess={handleEmailSuccess}
        />

        <EventDialog
          open={eventDialog}
          onClose={() => setEventDialog(false)}
          onSuccess={handleEventSuccess}
        />

        <Snackbar
          open={showSuccess}
          autoHideDuration={4000}
          onClose={handleCloseSuccess}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        >
          <Alert
            onClose={handleCloseSuccess}
            severity="success"
            variant="filled"
            sx={{ width: '100%' }}
          >
            {successMessage}
          </Alert>
        </Snackbar>
      </Container>
    </ErrorBoundary>
  )
}

export default App