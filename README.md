# Brevo API Integration Web Application

A production-ready, single-user web application that integrates with Brevo's API to manage contacts, send emails, and track custom events with comprehensive security, validation, and testing.

## 🏗️ Architecture

- **Backend**: Python Flask with REST API, rate limiting, and comprehensive validation (port 5000)
- **Frontend**: React with Material-UI, modular components, and error boundaries (port 3000)
- **API Integration**: Brevo (SendinBlue) API v3 with full error handling
- **Security**: Input validation, XSS protection, rate limiting, and CORS configuration

## 📋 Enhanced Features

### Frontend
- Clean, responsive Material-UI design with modular components
- Real-time loading states and comprehensive error handling
- JSON response formatting with copy-to-clipboard functionality
- Validated email and event forms with debouncing
- Error boundaries to prevent application crashes
- Success notifications and user feedback
- Environment-based configuration

### Backend
- RESTful API endpoints with comprehensive validation
- Rate limiting: 5/min for emails, 10/min for events
- Input sanitization and XSS prevention
- CORS configured for specific origins
- Request timeout handling (10-second default)
- Centralized configuration management
- Comprehensive test coverage

### Brevo API Integration
- Account information retrieval with caching
- Contact management with validated pagination
- Test email sending with HTML sanitization
- Custom event tracking with property validation
- Enhanced health check with configuration status

## 🚀 Quick Start

### Prerequisites

- Python 3.8+ installed
- Node.js 16+ and npm installed
- Brevo account with API key

### Step 1: Get Your Brevo API Key

1. Go to [Brevo Dashboard](https://app.brevo.com/settings/keys/api)
2. Create a new API key
3. Copy the key for configuration

### Step 2: Backend Setup

1. **Navigate to your repository:**
   ```bash
   cd lm-api-testing
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment:**
   ```bash
   # On Windows
   venv\Scripts\activate

   # On macOS/Linux
   source venv/bin/activate
   ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # For development
   ```

5. **Configure environment:**
   ```bash
   # Copy template and configure
   copy backend\.env.template backend\.env
   ```
   
   Edit `.env` file with your Brevo API key:
   ```bash
   BREVO_API_KEY=your_actual_brevo_api_key_here
   BREVO_SENDER_EMAIL=your_verified_sender@example.com
   BREVO_SENDER_NAME=Your Name
   ```

6. **Run the backend:**
   ```bash
   python app.py
   ```
   
   Backend will be available at: `http://127.0.0.1:5000`

### Step 3: Frontend Setup

1. **In a new terminal, navigate to frontend:**
   ```bash
   cd lm-api-testing/frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the frontend:**
   ```bash
   npm start
   ```
   
   Frontend will be available at: `http://localhost:3000`

## 📁 Project Structure

```
lm-api-testing/
├── .gitignore
├── LICENSE
├── README.md
├── CLAUDE.md                    # Development guidance
├── backend/
│   ├── venv/
│   ├── app.py                   # Main Flask application
│   ├── config.py                # Configuration management
│   ├── validators.py            # Input validation utilities
│   ├── requirements.txt         # Core dependencies
│   ├── requirements-dev.txt     # Development dependencies
│   ├── pyproject.toml          # Tool configurations
│   ├── .env                    # Environment variables
│   ├── .env.template           # Environment template
│   └── tests/
│       ├── __init__.py
│       ├── test_app.py         # Application tests
│       └── test_validators.py   # Validation tests
└── frontend/
    ├── node_modules/
    ├── public/
    │   └── index.html
    ├── src/
    │   ├── App.js               # Main application component
    │   ├── index.js
    │   ├── components/          # Reusable UI components
    │   │   ├── ErrorBoundary.js
    │   │   ├── ApiControls.js
    │   │   ├── ResponseDisplay.js
    │   │   ├── EmailDialog.js
    │   │   └── EventDialog.js
    │   ├── hooks/               # Custom React hooks
    │   │   └── useApi.js
    │   ├── utils/               # Utility functions
    │   │   └── api.js
    │   └── tests/
    │       └── App.test.js
    ├── package.json
    ├── package-lock.json
    ├── .env                     # Frontend environment
    ├── .env.template
    ├── .eslintrc.js
    └── .prettierrc
```

## 🔧 API Endpoints

### Backend Endpoints

| Method | Endpoint               | Rate Limit | Description                                    |
| ------ | ---------------------- | ---------- | ---------------------------------------------- |
| GET    | `/`                    | Exempt     | Enhanced health check with config status      |
| GET    | `/api/account`         | Default    | Get Brevo account information (cached)        |
| GET    | `/api/contacts`        | Default    | Get contacts list (validated pagination)      |
| POST   | `/api/send-test-email` | 5/min      | Send a validated and sanitized test email     |
| POST   | `/api/send-custom-event` | 10/min   | Send custom event with property validation    |

### Example API Calls

**Get Account Info:**
```bash
curl http://127.0.0.1:5000/api/account
```

**Send Test Email:**
```bash
curl -X POST http://127.0.0.1:5000/api/send-test-email \
  -H "Content-Type: application/json" \
  -d '{
    "to": "test@example.com",
    "subject": "Test Email",
    "content": "<p>Hello from Brevo!</p>"
  }'
```

**Send Custom Event:**
```bash
curl -X POST http://127.0.0.1:5000/api/send-custom-event \
  -H "Content-Type: application/json" \
  -d '{
    "event_name": "video_played",
    "email_id": "user@example.com",
    "contact_properties": "{\"age\": 30}",
    "event_properties": "{\"duration\": 120}"
  }'
```

## 🛡️ Security Features

- **Input Validation**: Email validation, JSON validation, event name validation
- **XSS Protection**: HTML content sanitization using bleach
- **Rate Limiting**: Configurable rate limits per endpoint
- **CORS Security**: Configured for specific origins only
- **API Key Management**: Secure environment variable storage
- **Request Timeouts**: Protection against hanging requests
- **Error Handling**: No sensitive data exposure in error messages

## 🎨 Frontend Features

### UI Components
- **API Controls**: Operation buttons with loading states
- **Response Display**: Formatted JSON with copy functionality
- **Email Dialog**: Validated email composition with real-time feedback
- **Event Dialog**: Custom event creation with JSON validation
- **Error Boundary**: Global error handling and recovery
- **Success Notifications**: User feedback for successful operations

### Performance Optimizations
- **Response Caching**: 5-minute TTL for API responses
- **Form Debouncing**: 500ms debouncing for form submissions
- **Request Optimization**: Cancellable requests and timeout handling
- **Error Recovery**: Graceful error handling without app crashes

## 🧪 Development & Testing

### Backend Development

```bash
cd backend
# Activate virtual environment
venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run development server
python app.py

# Run tests with coverage
pytest --cov

# Code quality checks
black .                 # Format code
flake8 .               # Lint code
isort .                # Sort imports
mypy .                 # Type checking
```

### Frontend Development

```bash
cd frontend
# Install dependencies
npm install

# Start development server
npm start

# Run tests with coverage
npm test
npm run test:coverage

# Code quality
npm run lint           # Check linting
npm run lint:fix       # Fix linting issues
npm run format         # Format code
npm run format:check   # Check formatting
```

## 🔍 Troubleshooting

### Common Issues

1. **"BREVO_API_KEY not found" error:**
   - Ensure `.env` file exists in backend directory
   - Verify API key is correctly set in `.env` file
   - Restart the backend server after changing `.env`
   - Check configuration with health check endpoint

2. **"Sender email not configured" error:**
   - Add `BREVO_SENDER_EMAIL` to `.env` file
   - Ensure the sender email is verified in Brevo
   - Restart backend after configuration changes

3. **CORS errors:**
   - Ensure backend is running on port 5000
   - Check frontend is making requests to correct URL
   - Verify CORS origins in backend configuration

4. **Rate limiting errors:**
   - Check rate limit status in API responses
   - Wait for rate limit reset period
   - Adjust rate limits in configuration if needed

5. **Frontend won't start:**
   - Ensure Node.js 16+ is installed
   - Delete `node_modules` and run `npm install` again
   - Check for port conflicts

### Testing the Integration

1. **Start both servers:**
   - Backend: `python app.py` (port 5000)
   - Frontend: `npm start` (port 3000)

2. **Test the health check:**
   - Click "Health Check" button
   - Should show configuration status and API connectivity

3. **Test account info:**
   - Click "Get Account Info" button
   - Should display your Brevo account details

4. **Test email sending:**
   - Click "Send Test Email" button
   - Fill in recipient email with proper validation
   - Observe success notification

5. **Test custom events:**
   - Click "Send Custom Event" button
   - Fill in event details with JSON validation
   - Observe real-time validation feedback

## 🚀 Production Deployment

### Backend Production Setup

1. **Environment Configuration:**
   ```bash
   # Production .env
   BREVO_API_KEY=your_production_api_key
   BREVO_SENDER_EMAIL=verified_sender@yourdomain.com
   FLASK_ENV=production
   FLASK_DEBUG=false
   FLASK_HOST=0.0.0.0
   FLASK_PORT=5000
   ```

2. **Run with Gunicorn:**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

### Frontend Production Build

1. **Environment Configuration:**
   ```bash
   # Production .env
   REACT_APP_API_BASE_URL=https://your-api-domain.com
   REACT_APP_API_TIMEOUT=10000
   REACT_APP_ENABLE_DEBUG_MODE=false
   ```

2. **Create production build:**
   ```bash
   npm run build
   ```

3. **Deploy static files:**
   - Use a web server like Nginx or Apache
   - Deploy to platforms like Netlify, Vercel, or AWS S3

### Production Deployment Checklist

- [ ] Set `FLASK_ENV=production` and `FLASK_DEBUG=false`
- [ ] Use strong, unique Brevo API keys
- [ ] Configure proper CORS origins for production domains
- [ ] Set up proper logging and monitoring
- [ ] Use `gunicorn` or similar WSGI server for backend
- [ ] Build frontend with `npm run build`
- [ ] Serve frontend static files with proper caching headers
- [ ] Set up SSL/TLS certificates
- [ ] Configure firewall and security groups
- [ ] Set up backup and monitoring systems

## 📝 Extending the Application

### Adding New Brevo API Endpoints

1. **Backend Implementation:**
   ```python
   @app.route('/api/new-endpoint', methods=['GET'])
   @limiter.limit("10 per minute")  # Add rate limiting
   def new_endpoint():
       try:
           # Validate inputs
           # Use make_brevo_request() helper
           response = make_brevo_request('GET', '/new-brevo-path')
           return jsonify({'status': 'success', 'data': response.json()})
       except ValidationError as e:
           return jsonify({'status': 'error', 'message': str(e)}), 400
   ```

2. **Frontend Integration:**
   ```javascript
   // Add to utils/api.js
   export const api = {
     // ... existing methods
     newOperation: (params) => apiClient.get(`/api/new-endpoint?${params}`),
   }
   
   // Use in components with hooks
   const { execute } = useApi()
   const handleNewOperation = () => execute(api.newOperation, params)
   ```

### Available Brevo API Endpoints to Integrate

- **Campaigns**: `/campaigns` - Manage email campaigns
- **Lists**: `/contacts/lists` - Manage contact lists
- **Templates**: `/smtp/templates` - Email templates
- **Senders**: `/senders` - Manage sender identities
- **Webhooks**: `/webhooks` - Configure webhooks
- **Statistics**: `/emailCampaigns/{campaignId}/statistics` - Campaign stats

## 📊 Dependencies

### Backend Core Dependencies
- **Flask**: Web framework with CORS support
- **Flask-Limiter**: Rate limiting functionality
- **requests**: HTTP client for Brevo API
- **python-dotenv**: Environment variable management
- **email-validator**: Email validation
- **bleach**: HTML sanitization
- **validators**: General input validation
- **gunicorn**: Production WSGI server

### Backend Development Dependencies
- **pytest**: Testing framework
- **pytest-flask**: Flask testing utilities
- **pytest-cov**: Coverage reporting
- **black**: Code formatting
- **flake8**: Code linting
- **isort**: Import sorting
- **mypy**: Type checking

### Frontend Core Dependencies
- **React 18**: UI framework
- **Material-UI v5**: Component library
- **@emotion/react**: Styling library
- **@emotion/styled**: Styled components

### Frontend Development Dependencies
- **@testing-library/react**: React testing utilities
- **@testing-library/jest-dom**: DOM testing matchers
- **@testing-library/user-event**: User interaction testing
- **eslint**: Code linting
- **prettier**: Code formatting
- **eslint-config-prettier**: ESLint-Prettier integration

## 🆘 Support

### Documentation Links

- [Brevo API Documentation](https://developers.brevo.com/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [React Documentation](https://react.dev/)
- [Material-UI Documentation](https://mui.com/)
- [pytest Documentation](https://docs.pytest.org/)
- [Jest Documentation](https://jestjs.io/)

### Common Commands Reference

**Backend Commands:**
```bash
# Development
cd backend
venv\Scripts\activate
python app.py

# Testing
pytest
pytest --cov
pytest tests/test_validators.py

# Code Quality
black .
flake8 .
isort .
mypy .

# Production
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**Frontend Commands:**
```bash
# Development
cd frontend
npm start

# Testing
npm test
npm run test:coverage

# Code Quality
npm run lint
npm run format
npm run format:check

# Production
npm run build
```

---

## 🎉 Congratulations!

You now have a complete, production-ready, enterprise-grade Brevo API integration web application! The application features:

✅ **Security**: Input validation, XSS protection, rate limiting  
✅ **Performance**: Caching, debouncing, request optimization  
✅ **Reliability**: Error boundaries, comprehensive testing, graceful error handling  
✅ **Developer Experience**: Code formatting, linting, type checking, comprehensive documentation  
✅ **Production Ready**: Environment configuration, monitoring, deployment guides  

The application is designed to be easily extensible and follows industry best practices for security, performance, and maintainability.