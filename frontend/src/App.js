import React, { useState } from "react"
import {
  Container,
  Paper,
  Typography,
  Button,
  TextField,
  Box,
  Alert,
  CircularProgress,
  Divider,
  Card,
  CardContent,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControlLabel,
  Switch
} from "@mui/material"
import {
  AccountCircle,
  Email,
  Contacts,
  Send,
  Refresh
} from "@mui/icons-material"

const API_BASE_URL = "http://127.0.0.1:5000"

function App() {
  const [response, setResponse] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [emailDialog, setEmailDialog] = useState(false)
  const [emailForm, setEmailForm] = useState({
    to: "",
    subject: "Test Email from Brevo API",
    content: "<p>This is a test email sent via Brevo API integration.</p>",
    senderName: "Test Sender",
    senderEmail: ""
  })
  const [formatJson, setFormatJson] = useState(true)

  const formatResponse = (data) => {
    if (formatJson) {
      try {
        return JSON.stringify(data, null, 2)
      } catch (e) {
        return String(data)
      }
    }
    return String(data)
  }

  const handleApiCall = async (endpoint, method = "GET", body = null) => {
    setLoading(true)
    setError("")

    try {
      const config = {
        method,
        headers: {
          "Content-Type": "application/json"
        }
      }

      if (body) {
        config.body = JSON.stringify(body)
      }

      const response = await fetch(`${API_BASE_URL}${endpoint}`, config)
      const data = await response.json()

      if (!response.ok) {
        throw new Error(
          data.message || `HTTP error! status: ${response.status}`
        )
      }

      setResponse(formatResponse(data))
    } catch (err) {
      setError(err.message)
      setResponse("")
    } finally {
      setLoading(false)
    }
  }

  const handleEmailSubmit = () => {
    if (!emailForm.to) {
      setError("Recipient email is required")
      return
    }

    handleApiCall("/api/send-test-email", "POST", emailForm)
    setEmailDialog(false)
  }

  const apiButtons = [
    {
      label: "Get Account Info",
      icon: <AccountCircle />,
      onClick: () => handleApiCall("/api/account"),
      color: "primary"
    },
    {
      label: "Get Contacts",
      icon: <Contacts />,
      onClick: () => handleApiCall("/api/contacts?limit=5"),
      color: "secondary"
    },
    {
      label: "Send Test Email",
      icon: <Email />,
      onClick: () => setEmailDialog(true),
      color: "success"
    },
    {
      label: "Health Check",
      icon: <Refresh />,
      onClick: () => handleApiCall("/"),
      color: "info"
    }
  ]

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Box sx={{ mb: 4, textAlign: "center" }}>
          <Typography variant="h3" component="h1" gutterBottom color="primary">
            Brevo API Integration
          </Typography>
          <Typography variant="h6" color="text.secondary">
            Single-page web application for Brevo API testing
          </Typography>
        </Box>

        <Grid container spacing={3}>
          {/* API Buttons Section */}
          <Grid item xs={12} md={4}>
            <Card sx={{ height: "100%" }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  API Operations
                </Typography>
                <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
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
                      onChange={(e) => setFormatJson(e.target.checked)}
                    />
                  }
                  label="Format JSON Response"
                />
              </CardContent>
            </Card>
          </Grid>

          {/* Response Section */}
          <Grid item xs={12} md={8}>
            <Card sx={{ height: "100%" }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  API Response
                </Typography>

                {error && (
                  <Alert severity="error" sx={{ mb: 2 }}>
                    {error}
                  </Alert>
                )}

                {loading && (
                  <Box
                    sx={{ display: "flex", justifyContent: "center", py: 4 }}
                  >
                    <CircularProgress />
                  </Box>
                )}

                <TextField
                  multiline
                  rows={20}
                  fullWidth
                  value={response}
                  placeholder="API responses will appear here..."
                  variant="outlined"
                  InputProps={{
                    readOnly: true,
                    sx: {
                      fontFamily: "monospace",
                      fontSize: "0.875rem",
                      backgroundColor: "#f5f5f5"
                    }
                  }}
                />
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>

      {/* Email Dialog */}
      <Dialog
        open={emailDialog}
        onClose={() => setEmailDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <Send />
            Send Test Email
          </Box>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2, pt: 1 }}>
            <TextField
              label="Recipient Email"
              type="email"
              value={emailForm.to}
              onChange={(e) =>
                setEmailForm({ ...emailForm, to: e.target.value })
              }
              required
              fullWidth
            />
            <TextField
              label="Sender Name"
              value={emailForm.senderName}
              onChange={(e) =>
                setEmailForm({ ...emailForm, senderName: e.target.value })
              }
              fullWidth
            />
            <TextField
              label="Sender Email (Optional)"
              type="email"
              value={emailForm.senderEmail}
              onChange={(e) =>
                setEmailForm({ ...emailForm, senderEmail: e.target.value })
              }
              fullWidth
              helperText="Leave empty to use recipient email as sender"
            />
            <TextField
              label="Subject"
              value={emailForm.subject}
              onChange={(e) =>
                setEmailForm({ ...emailForm, subject: e.target.value })
              }
              fullWidth
            />
            <TextField
              label="HTML Content"
              multiline
              rows={4}
              value={emailForm.content}
              onChange={(e) =>
                setEmailForm({ ...emailForm, content: e.target.value })
              }
              fullWidth
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEmailDialog(false)}>Cancel</Button>
          <Button
            onClick={handleEmailSubmit}
            variant="contained"
            startIcon={<Send />}
          >
            Send Email
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  )
}

export default App
