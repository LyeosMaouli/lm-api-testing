# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a production-ready Brevo API integration web application with:
- **Backend**: Python Flask REST API with comprehensive validation, rate limiting, and security (port 5000)
- **Frontend**: React with Material-UI, modular components, and error boundaries (port 3000)
- **Purpose**: Manage Brevo contacts, send emails, and track custom events
- **Architecture**: Full-stack with proper error handling, input validation, caching, and testing

## Development Commands

### Backend (Flask)
```bash
cd backend
# Activate virtual environment (Windows)
venv\Scripts\activate
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development tools
# Run development server
python app.py
# Run tests
pytest
pytest --cov  # With coverage
# Lint and format
black .
flake8 .
isort .
mypy .
# Run production server
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Frontend (React)
```bash
cd frontend
# Install dependencies
npm install
# Start development server
npm start
# Build for production
npm run build
# Run tests
npm test
npm run test:coverage  # With coverage
# Lint and format
npm run lint
npm run lint:fix
npm run format
npm run format:check
```

## Architecture

### Backend Structure (`backend/app.py`)
- Flask app with CORS enabled
- Environment variables via `.env` file
- API endpoints:
  - `GET /` - Health check
  - `GET /api/account` - Brevo account info
  - `GET /api/contacts` - List contacts (with pagination)
  - `POST /api/send-test-email` - Send email
  - `POST /api/send-custom-event` - Send custom events to Brevo

### Frontend Structure
- React 18 with Material-UI v5
- Single page application (`src/App.js`)
- Proxy configured to backend on port 5000
- Material-UI components for UI

### Environment Configuration
Backend requires `.env` file with:
- `BREVO_API_KEY` - Your Brevo API key (required)
- `BREVO_SENDER_EMAIL` - Email address for sending (required for email functionality)
- `BREVO_SENDER_NAME` - Display name for sender (optional, defaults to "API Integration")

## Key Implementation Details

### API Error Handling
All backend endpoints follow consistent error response format:
```json
{
  "status": "error|success",
  "message": "Human readable message",
  "data": {}, // success only
  "details": "Technical details" // error only
}
```

### Authentication
- Uses Brevo API key in headers: `{'api-key': 'your-key'}`
- No user authentication implemented - single-user application

### Frontend-Backend Communication
- Frontend uses fetch API to communicate with backend
- Proxy configuration in `frontend/package.json` routes `/api/*` to `http://127.0.0.1:5000`
- Loading states and error handling implemented in React

## Development Notes

### Running Both Services
1. Start backend first: `cd backend && python app.py`
2. Start frontend: `cd frontend && npm start`
3. Access application at `http://localhost:3000`

### Common Issues
- Ensure `.env` file exists in `backend/` directory with valid Brevo API key
- Virtual environment must be activated for backend development
- Frontend proxy depends on backend running on port 5000

### Adding New Brevo API Endpoints
1. Add new route in `backend/app.py` following existing error handling patterns
2. Use `get_brevo_headers()` function for authentication
3. Add corresponding frontend function in `App.js`
4. Follow existing loading/error state patterns in React

### Dependencies
- Backend: Flask, Flask-CORS, requests, python-dotenv, gunicorn
- Frontend: React, Material-UI, emotion (styling)

## Testing
- Backend: No test framework configured
- Frontend: Jest via react-scripts (`npm test`)