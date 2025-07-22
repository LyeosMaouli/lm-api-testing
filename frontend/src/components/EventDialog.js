/**
 * Event Dialog component for sending custom events
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
import { Event as EventIcon } from '@mui/icons-material'
import { useApiForm } from '../hooks/useApi'
import { api, validators } from '../utils/api'

const EventDialog = ({ open, onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    event_name: 'video_played',
    email_id: '',
    contact_properties: '',
    event_properties: '',
  })
  const [validationErrors, setValidationErrors] = useState({})

  const { isSubmitting, error, success, submit, clearMessages } = useApiForm(
    api.sendEvent,
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
      validators.required(formData.event_name, 'Event name')
      validators.maxLength(formData.event_name, 100, 'Event name')
    } catch (err) {
      errors.event_name = err.message
    }

    try {
      validators.email(formData.email_id)
    } catch (err) {
      errors.email_id = err.message
    }

    // Validate JSON fields if provided
    try {
      validators.json(formData.contact_properties, 'Contact properties')
    } catch (err) {
      errors.contact_properties = err.message
    }

    try {
      validators.json(formData.event_properties, 'Event properties')
    } catch (err) {
      errors.event_properties = err.message
    }

    setValidationErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleSubmit = async () => {
    if (!validateForm()) {
      return
    }

    try {
      const eventData = {
        event_name: formData.event_name.trim(),
        email_id: formData.email_id.trim(),
        event_date: new Date().toISOString(),
      }

      // Add JSON properties if provided
      if (formData.contact_properties.trim()) {
        eventData.contact_properties = formData.contact_properties.trim()
      }
      if (formData.event_properties.trim()) {
        eventData.event_properties = formData.event_properties.trim()
      }

      await submit(eventData)
    } catch (err) {
      // Error is handled by useApiForm hook
      console.error('Event submission error:', err)
    }
  }

  const handleReset = () => {
    setFormData({
      event_name: 'video_played',
      email_id: '',
      contact_properties: '',
      event_properties: '',
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

  const exampleContactProps = '{"AGE": 32, "GENDER": "FEMALE"}'
  const exampleEventProps = '{"video_title": "Brevo Tutorial", "duration": 142, "autoplayed": false}'

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: { minHeight: 500 }
      }}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <EventIcon />
          Send Custom Event
        </Box>
      </DialogTitle>
      
      <DialogContent>
        {success && (
          <Alert severity="success" sx={{ mb: 2 }}>
            Custom event sent successfully! 🎉
          </Alert>
        )}

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
          <TextField
            label="Event Name"
            value={formData.event_name}
            onChange={handleChange('event_name')}
            required
            fullWidth
            error={!!validationErrors.event_name}
            helperText={
              validationErrors.event_name || 
              'e.g., video_played, product_viewed, form_submitted'
            }
            disabled={isSubmitting}
          />
          
          <TextField
            label="Email ID"
            type="email"
            value={formData.email_id}
            onChange={handleChange('email_id')}
            required
            fullWidth
            error={!!validationErrors.email_id}
            helperText={
              validationErrors.email_id || 
              "Contact's email address"
            }
            disabled={isSubmitting}
          />
          
          <TextField
            label="Contact Properties (JSON)"
            multiline
            rows={3}
            value={formData.contact_properties}
            onChange={handleChange('contact_properties')}
            fullWidth
            placeholder={exampleContactProps}
            error={!!validationErrors.contact_properties}
            helperText={
              validationErrors.contact_properties || 
              'Optional: Contact attributes in JSON format'
            }
            disabled={isSubmitting}
          />
          
          <TextField
            label="Event Properties (JSON)"
            multiline
            rows={4}
            value={formData.event_properties}
            onChange={handleChange('event_properties')}
            fullWidth
            placeholder={exampleEventProps}
            error={!!validationErrors.event_properties}
            helperText={
              validationErrors.event_properties || 
              'Optional: Event-specific data in JSON format'
            }
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
          startIcon={isSubmitting ? <CircularProgress size={16} /> : <EventIcon />}
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Sending...' : 'Send Event'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default EventDialog