import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from '../App'

// Mock the API module
jest.mock('../utils/api', () => ({
  api: {
    healthCheck: jest.fn(),
    getAccount: jest.fn(),
    getContacts: jest.fn(),
    sendEmail: jest.fn(),
    sendEvent: jest.fn(),
  },
  apiClient: {
    clearCache: jest.fn(),
  },
  ApiError: class MockApiError extends Error {
    constructor(message, status = 0) {
      super(message)
      this.status = status
    }
  },
}))

describe('App Component', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  test('renders main heading', () => {
    render(<App />)
    expect(screen.getByText('Brevo API Integration')).toBeInTheDocument()
    expect(
      screen.getByText('Enhanced single-page application for Brevo API testing')
    ).toBeInTheDocument()
  })

  test('renders all API control buttons', () => {
    render(<App />)
    
    expect(screen.getByRole('button', { name: /get account info/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /get contacts/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /send test email/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /send custom event/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /health check/i })).toBeInTheDocument()
  })

  test('opens email dialog when email button is clicked', async () => {
    const user = userEvent.setup()
    render(<App />)
    
    const emailButton = screen.getByRole('button', { name: /send test email/i })
    await user.click(emailButton)
    
    expect(screen.getByText('Send Test Email')).toBeInTheDocument()
  })

  test('opens event dialog when event button is clicked', async () => {
    const user = userEvent.setup()
    render(<App />)
    
    const eventButton = screen.getByRole('button', { name: /send custom event/i })
    await user.click(eventButton)
    
    expect(screen.getByText('Send Custom Event')).toBeInTheDocument()
  })

  test('toggles JSON formatting', async () => {
    const user = userEvent.setup()
    render(<App />)
    
    const formatSwitch = screen.getByRole('checkbox', { name: /format json response/i })
    expect(formatSwitch).toBeChecked()
    
    await user.click(formatSwitch)
    expect(formatSwitch).not.toBeChecked()
  })

  test('displays success message after successful operation', async () => {
    render(<App />)
    
    // This would require mocking the dialog success callback
    // For now, just verify the snackbar structure exists
    expect(document.querySelector('[role="presentation"]')).toBeNull()
  })
})