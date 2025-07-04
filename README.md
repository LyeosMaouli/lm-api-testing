# Brevo API Integration Web Application

A single-user web application that integrates with Brevo's API to manage contacts, send emails, and retrieve account information.

## 🏗️ Architecture

- **Backend**: Python Flask with REST API
- **Frontend**: React with Material-UI (MUI)
- **API Integration**: Brevo (SendinBlue) API v3
- **Environment**: Windows Laptop

## 📋 Features

### Frontend

- Clean, responsive Material-UI design
- Single-page application with multiple API operations
- Real-time loading states and error handling
- JSON response formatting toggle
- Email sending dialog with form validation

### Backend

- RESTful API endpoints for Brevo integration
- CORS enabled for frontend communication
- Environment variable configuration
- Comprehensive error handling
- Secure API key management

### Brevo API Integration

- Account information retrieval
- Contact management
- Test email sending
- Health check endpoint

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

1. **Navigate to your existing repository:**

   ```bash
   cd lm-api-testing
   ```

2. **Create backend directory:**

   ```bash
   mkdir backend
   cd backend
   ```

3. **Create and save the backend files:**

   - Save the `app.py` file (Flask backend code)
   - Save the `requirements.txt` file

4. **Create virtual environment:**

   ```bash
   python -m venv venv
   ```

5. **Activate virtual environment:**

   ```bash
   # On Windows
   venv\Scripts\activate

   # On macOS/Linux (if needed)
   source venv/bin/activate
   ```

6. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

7. **Create environment file:**
   ```bash
   # Create .env file in backend directory
   copy .env.template .env
   ```
8. **Configure your API key:**

   - Open `.env` file
   - Replace `your_brevo_api_key_here` with your actual Brevo API key

9. **Run the backend:**

   ```bash
   python app.py
   ```

   Backend will be available at: `http://127.0.0.1:5000`

### Step 3: Frontend Setup

1. **In a new terminal, navigate to repository root:**

   ```bash
   cd lm-api-testing
   ```

2. **Create frontend directory:**

   ```bash
   mkdir frontend
   cd frontend
   ```

3. **Create React app structure:**

   ```bash
   # Create directories
   mkdir src public
   ```

4. **Save the frontend files:**

   - Save `package.json` in frontend directory
   - Save `App.js` in `src/` directory
   - Save `index.js` in `src/` directory
   - Save `index.html` in `public/` directory

5. **Install dependencies:**

   ```bash
   npm install
   ```

6. **Start the frontend:**

   ```bash
   npm start
   ```

   Frontend will be available at: `http://localhost:3000`

## 📁 Final Project Structure

```
lm-api-testing/
├── .gitignore
├── .vscode/
├── LICENSE
├── README (this file)
├── backend/
│   ├── venv/
│   ├── app.py
│   ├── requirements.txt
│   ├── .env
│   └── .env.template
└── frontend/
    ├── node_modules/
    ├── public/
    │   └── index.html
    ├── src/
    │   ├── App.js
    │   └── index.js
    ├── package.json
    └── package-lock.json
```

## 🔧 API Endpoints

### Backend Endpoints

| Method | Endpoint               | Description                         |
| ------ | ---------------------- | ----------------------------------- |
| GET    | `/`                    | Health check and API key status     |
| GET    | `/api/account`         | Get Brevo account information       |
| GET    | `/api/contacts`        | Get contacts list (with pagination) |
| POST   | `/api/send-test-email` | Send a test email                   |

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

## 🛡️ Security Features

- API keys stored as environment variables
- Input validation on all endpoints
- CORS properly configured
- Error handling without exposing sensitive data
- Request size limits and rate limiting ready

## 🎨 Frontend Features

### UI Components

- **Account Info Button**: Retrieves and displays account details
- **Get Contacts Button**: Shows contact list with pagination
- **Send Test Email Button**: Opens dialog for email composition
- **Health Check Button**: Verifies API connectivity
- **JSON Toggle**: Format response display
- **Response Area**: Displays formatted API responses

### Error Handling

- Network error messages
- API error responses
- Form validation
- Loading states

## 🔍 Troubleshooting

### Common Issues

1. **"BREVO_API_KEY not found" error:**

   - Ensure `.env` file exists in backend directory
   - Check API key is correctly set in `.env` file
   - Restart the backend server after changing `.env`

2. **CORS errors:**

   - Ensure backend is running on port 5000
   - Check frontend is making requests to correct URL

3. **"Module not found" errors:**

   - Ensure virtual environment is activated
   - Run `pip install -r requirements.txt` again

4. **Frontend won't start:**
   - Ensure Node.js is installed
   - Delete `node_modules` and run `npm install` again

### Testing the Integration

1. **Start both servers:**

   - Backend: `python app.py` (port 5000)
   - Frontend: `npm start` (port 3000)

2. **Test the health check:**

   - Click "Health Check" button
   - Should show API key configuration status

3. **Test account info:**

   - Click "Get Account Info" button
   - Should display your Brevo account details

4. **Test email sending:**
   - Click "Send Test Email" button
   - Fill in recipient email
   - Click "Send Email"

## 🚀 Production Deployment

### Backend Production Setup

1. **Install Gunicorn (already in requirements.txt):**

   ```bash
   pip install gunicorn
   ```

2. **Run with Gunicorn:**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

### Frontend Production Build

1. **Create production build:**

   ```bash
   npm run build
   ```

2. **Serve static files:**
   - Use a web server like Nginx or Apache
   - Or deploy to platforms like Netlify, Vercel

### Environment Variables for Production

```bash
# .env for production
BREVO_API_KEY=your_production_api_key
FLASK_ENV=production
FLASK_DEBUG=False
```

## 📝 Extending the Application

### Adding New API Endpoints

1. **Backend (app.py):**

   ```python
   @app.route('/api/new-endpoint', methods=['GET'])
   def new_endpoint():
       try:
           headers = get_brevo_headers()
           response = requests.get(f'{BREVO_BASE_URL}/new-path', headers=headers)
           # Handle response
           return jsonify({'status': 'success', 'data': response.json()})
       except Exception as e:
           return jsonify({'status': 'error', 'message': str(e)}), 500
   ```

2. **Frontend (App.js):**

   ```javascript
   const handleNewApiCall = () => {
       handleApiCall('/api/new-endpoint');
   };

   // Add new button to apiButtons array
   {
       label: 'New Operation',
       icon: <NewIcon />,
       onClick: handleNewApiCall,
       color: 'primary'
   }
   ```

### Available Brevo API Endpoints to Integrate

- **Campaigns**: `/campaigns` - Manage email campaigns
- **Lists**: `/contacts/lists` - Manage contact lists
- **Templates**: `/smtp/templates` - Email templates
- **Senders**: `/senders` - Manage sender identities
- **Webhooks**: `/webhooks` - Configure webhooks
- **Statistics**: `/emailCampaigns/{campaignId}/statistics` - Campaign stats

### Adding Database Support

If you need to store data locally:

1. **Add SQLAlchemy to requirements.txt:**

   ```txt
   Flask-SQLAlchemy==3.1.1
   ```

2. **Update app.py with database models:**

   ```python
   from flask_sqlalchemy import SQLAlchemy

   app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///brevo_data.db'
   db = SQLAlchemy(app)

   class Contact(db.Model):
       id = db.Column(db.Integer, primary_key=True)
       email = db.Column(db.String(120), unique=True, nullable=False)
       # Add more fields as needed
   ```

## 🔒 Security Best Practices

### API Key Security

- Never commit `.env` files to version control
- Use different API keys for development and production
- Regularly rotate API keys
- Implement API key validation

### Input Validation

```python
from flask import request
from email_validator import validate_email, EmailNotValidError

@app.route('/api/validate-email', methods=['POST'])
def validate_email_endpoint():
    data = request.get_json()
    email = data.get('email', '').strip()

    try:
        valid = validate_email(email)
        return jsonify({'status': 'success', 'email': valid.email})
    except EmailNotValidError:
        return jsonify({'status': 'error', 'message': 'Invalid email'}), 400
```

### Rate Limiting

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/api/send-test-email', methods=['POST'])
@limiter.limit("5 per minute")
def send_test_email():
    # Existing code
```

## 📊 Monitoring and Logging

### Enhanced Logging

```python
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler('logs/brevo_api.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Brevo API Integration startup')
```

### Health Check Enhancements

```python
@app.route('/health', methods=['GET'])
def detailed_health_check():
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0',
        'components': {
            'brevo_api': 'unknown',
            'environment': 'ok'
        }
    }

    # Test Brevo API connectivity
    try:
        headers = get_brevo_headers()
        response = requests.get(f'{BREVO_BASE_URL}/account', headers=headers, timeout=5)
        health_status['components']['brevo_api'] = 'healthy' if response.status_code == 200 else 'unhealthy'
    except:
        health_status['components']['brevo_api'] = 'unhealthy'
        health_status['status'] = 'degraded'

    return jsonify(health_status)
```

## 🎯 Next Steps

1. **Test all functionality** with your Brevo account
2. **Customize the UI** to match your branding
3. **Add more Brevo API endpoints** as needed
4. **Implement user authentication** if required
5. **Add data persistence** with a database
6. **Deploy to production** environment
7. **Set up monitoring** and alerting
8. **Create automated tests** for reliability

## 🆘 Support

### Documentation Links

- [Brevo API Documentation](https://developers.brevo.com/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [React Documentation](https://react.dev/)
- [Material-UI Documentation](https://mui.com/)

### Common Commands Reference

**Backend Commands:**

```bash
# Navigate to repository
cd lm-api-testing

# Activate virtual environment (from backend directory)
cd backend
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
python app.py

# Run production server
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**Frontend Commands:**

```bash
# Navigate to repository
cd lm-api-testing

# Install dependencies (from frontend directory)
cd frontend
npm install

# Start development server
npm start

# Build for production
npm run build

# Run tests
npm test
```

---

## 🎉 Congratulations!

You now have a complete, production-ready Brevo API integration web application! The application is designed to be easily extensible and follows best practices for security, error handling, and user experience.
