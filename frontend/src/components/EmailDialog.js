/**
 * Email Dialog component for sending test emails
 */

import React, { useState } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  Alert,
  CircularProgress,
} from '@mui/material'
import { Send as SendIcon } from '@mui/icons-material'
import { useApiForm } from '../hooks/useApi'
import { api, validators } from '../utils/api'

const EmailDialog = ({ open, onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    to: '',
    subject: 'Test Email from Brevo API',
    content: '<p>This is a test email sent via Brevo API integration.</p>',
  })
  const [validationErrors, setValidationErrors] = useState({})

  const { isSubmitting, error, success, submit, clearMessages } = useApiForm(
    api.sendEmail,
    500 // 500ms debounce
  )

  React.useEffect(() => {
    if (success) {
      const timer = setTimeout(() => {
        onClose()
        onSuccess?.()
        handleReset()
      }, 1500)
      return () => clearTimeout(timer)
    }
  }, [success, onClose, onSuccess])

  const handleChange = (field) => (event) => {
    const value = event.target.value
    setFormData(prev => ({ ...prev, [field]: value }))
    
    // Clear validation error when user starts typing
    if (validationErrors[field]) {
      setValidationErrors(prev => ({ ...prev, [field]: null }))
    }
  }

  const validateForm = () => {
    const errors = {}

    try {
      validators.email(formData.to)
    } catch (err) {
      errors.to = err.message
    }

    try {
      validators.required(formData.subject, 'Subject')
      validators.maxLength(formData.subject, 255, 'Subject')
    } catch (err) {
      errors.subject = err.message
    }

    try {
      validators.required(formData.content, 'Content')
    } catch (err) {
      errors.content = err.message
    }

    setValidationErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleSubmit = async () => {
    if (!validateForm()) {
      return
    }

    try {
      await submit(formData)
    } catch (err) {
      // Error is handled by useApiForm hook
      console.error('Email submission error:', err)
    }
  }

  const handleReset = () => {
    setFormData({
      to: '',
      subject: 'Test Email from Brevo API',
      content: '<p>This is a test email sent via Brevo API integration.</p>',
    })
    setValidationErrors({})
    clearMessages()
  }

  const handleClose = () => {
    if (!isSubmitting) {
      onClose()
      setTimeout(handleReset, 300) // Reset after dialog closes
    }
  }

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: { minHeight: 400 }
      }}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <SendIcon />
          Send Test Email
        </Box>
      </DialogTitle>
      
      <DialogContent>
        {success && (
          <Alert severity="success" sx={{ mb: 2 }}>
            Email sent successfully! 📧
          </Alert>
        )}

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
          <TextField
            label="Recipient Email"
            type="email"
            value={formData.to}
            onChange={handleChange('to')}
            required
            fullWidth
            error={!!validationErrors.to}
            helperText={
              validationErrors.to || 
              'Email will be sent from the configured sender in backend'
            }
            disabled={isSubmitting}
          />
          
          <TextField
            label="Subject"
            value={formData.subject}
            onChange={handleChange('subject')}
            required
            fullWidth
            error={!!validationErrors.subject}
            helperText={validationErrors.subject}
            disabled={isSubmitting}
          />
          
          <TextField
            label="HTML Content"
            multiline
            rows={4}
            value={formData.content}
            onChange={handleChange('content')}
            required
            fullWidth
            error={!!validationErrors.content}
            helperText={validationErrors.content}
            disabled={isSubmitting}
          />
        </Box>
      </DialogContent>
      
      <DialogActions>
        <Button onClick={handleClose} disabled={isSubmitting}>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          startIcon={isSubmitting ? <CircularProgress size={16} /> : <SendIcon />}
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Sending...' : 'Send Email'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default EmailDialog