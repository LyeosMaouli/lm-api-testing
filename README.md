# 🚀 Multi-Service API Testing Platform

A comprehensive local development tool for testing and debugging real-world business API integrations including Stripe, Brevo, LinkedIn, n8n, and other popular SaaS services.

## ✨ Features

- **🔌 Service-Oriented Architecture**: Plug-and-play service modules with automatic discovery
- **🔐 Secure Credential Management**: AES-256 encrypted credential storage with master password
- **⚡ Advanced Rate Limiting**: Intelligent rate limiting with multiple strategies (token bucket, sliding window)
- **📊 Request History & Analytics**: Comprehensive logging and analysis of all API interactions
- **🎯 Dynamic Request Building**: Form generation from service configurations and OpenAPI specs
- **🪝 Webhook Testing**: Local webhook endpoints with signature verification
- **🔄 Multi-Environment Support**: Production, sandbox, and custom environment configurations
- **📝 Real-time Validation**: Request validation before sending with detailed error messages

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React Frontend │    │   FastAPI Backend │    │  Service Modules │
│                 │    │                  │    │                 │
│ • Service UI    │◄──►│ • Rate Limiting  │◄──►│ • Stripe        │
│ • Request Forms │    │ • Authentication │    │ • Brevo         │
│ • Response View │    │ • Request Logging│    │ • LinkedIn      │
│ • Collections   │    │ • Config Manager │    │ • Custom APIs   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────►│ Encrypted Storage│◄─────────────┘
                        │                 │
                        │ • Credentials   │
                        │ • Request History│
                        │ • Collections   │
                        └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend development)
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/LyeosMaouli/lm-api-testing.git
cd lm-api-testing
```

### 2. Backend Setup

```bash
# Install Python dependencies
cd backend
pip install -r requirements.txt

# Setup environment variables (interactive)
python ../scripts/setup_env.py --interactive

# Or copy and edit manually
cp ../.env.example .env
# Edit .env file with your settings

# Run setup script
python ../scripts/dev_server.py --setup-only
```

### 3. Start the Backend Server

```bash
# Development server with auto-reload
python ../scripts/dev_server.py

# Or manually with uvicorn
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 4. Access the API

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **System Info**: http://localhost:8000/system/info

## ⚙️ Environment Configuration

### Using Environment Variables in Service Configs

Service configurations support environment variable substitution using the syntax:

- `${VAR_NAME}` - Required environment variable
- `${VAR_NAME:default_value}` - Environment variable with fallback

Example in `backend/app/services/brevo/config.yaml`:

```yaml
settings:
  default_sender_email: "${BREVO_DEFAULT_SENDER_EMAIL:noreply@example.com}"
  default_sender_name: "${BREVO_DEFAULT_SENDER_NAME:API Testing Platform}"
```

### Environment Setup Utility

Use the interactive setup utility to configure your environment:

```bash
# Interactive setup
python scripts/setup_env.py --interactive

# Validate current configuration
python scripts/setup_env.py --validate
```

### Key Environment Variables

```bash
# Brevo Service Configuration
BREVO_DEFAULT_SENDER_EMAIL=your-email@yourdomain.com
BREVO_DEFAULT_SENDER_NAME=Your Company Name
BREVO_API_KEY=xkeysib-your-api-key-here

# Application Settings
API_TESTING_SECRET_KEY=your-secret-key
API_TESTING_DEBUG=true
API_TESTING_HOST=127.0.0.1
API_TESTING_PORT=8000
```

### Core Endpoints

- `GET /` - API information and status
- `GET /health` - Health check with component status
- `GET /system/info` - Detailed system information

### Service Management

- `GET /api/v1/services/` - List all available services
- `GET /api/v1/services/{service_name}` - Get service details
- `POST /api/v1/services/{service_name}/reload` - Reload service module
- `GET /api/v1/services/{service_name}/validation` - Validate service

### API Testing

- `POST /api/v1/testing/execute` - Execute single API test
- `POST /api/v1/testing/batch` - Execute batch API tests
- `POST /api/v1/testing/method` - Call specific service method
- `GET /api/v1/testing/{service_name}/methods` - List service methods

### Credential Management

- `GET /api/v1/services/{service_name}/credentials` - Get credential info
- `PUT /api/v1/services/{service_name}/credentials` - Update credentials
- `DELETE /api/v1/services/{service_name}/credentials` - Delete credentials

## 🔧 Service Configuration

### Adding a New Service

1. **Create Service Directory**

```bash
mkdir -p backend/app/services/myservice
touch backend/app/services/myservice/__init__.py
```

2. **Create Configuration File**

```yaml
# backend/app/services/myservice/config.yaml
name: "myservice"
display_name: "My Service"
description: "Custom API integration"
version: "v1"
base_url: "https://api.myservice.com/v1"

authentication:
  api_key:
    type: "api_key"
    header: "Authorization"
    required_fields: ["api_key"]

rate_limits:
  requests_per_minute: 100
  burst_limit: 10

endpoints:
  list_items:
    method: "GET"
    path: "/items"
    description: "List all items"
```

3. **Implement Service Client**

```python
# backend/app/services/myservice/client.py
from ...services.base import BaseService

class MyService(BaseService):
    async def test_connection(self):
        response = await self.make_request("GET", "/health")
        return {"success": response.status_code == 200}

    def get_supported_endpoints(self):
        return ["list_items", "create_item"]

    async def list_items(self, limit=10):
        response = await self.make_request("GET", "/items", params={"limit": limit})
        return response.json()
```

### Brevo Service Example

The platform includes a complete Brevo integration for email marketing:

```python
# Test Brevo connection
curl -X POST http://localhost:8000/api/v1/services/brevo/test-connection \
  -H "Content-Type: application/json" \
  -d '{
    "environment": "production",
    "credentials": {
      "api_key": "xkeysib-your_brevo_api_key_here"
    }
  }'

# Create a contact
curl -X POST http://localhost:8000/api/v1/testing/method \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "brevo",
    "method_name": "create_contact",
    "arguments": {
      "email": "test@example.com",
      "attributes": {
        "FIRSTNAME": "John",
        "LASTNAME": "Doe"
      }
    },
    "credentials": {
      "api_key": "xkeysib-your_brevo_api_key_here"
    }
  }'

# Send a transactional email
curl -X POST http://localhost:8000/api/v1/testing/method \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "brevo",
    "method_name": "send_transactional_email",
    "arguments": {
      "to": [{"email": "recipient@example.com", "name": "Recipient"}],
      "subject": "Test Email",
      "html_content": "<h1>Hello!</h1><p>This is a test email.</p>"
    },
    "credentials": {
      "api_key": "xkeysib-your_brevo_api_key_here"
    }
  }'
```

## 🔐 Security Features

### Credential Encryption

- AES-256-GCM authenticated encryption
- PBKDF2 key derivation with 100,000 iterations
- Salt-based protection against rainbow table attacks
- Master password protection

### Rate Limiting

- Service-specific rate limiting configuration
- Multiple strategies: token bucket, sliding window, fixed window
- Intelligent queuing and exponential backoff
- Per-endpoint and global rate limiting

### Request Security

- Input validation with Pydantic models
- SQL injection prevention
- Secure HTTP client configuration
- Certificate validation for HTTPS

## 📊 Monitoring & Logging

### Request Tracking

- Comprehensive request/response logging
- Performance metrics and timing analysis
- Error categorization and analysis
- Rate limit usage monitoring

### System Monitoring

- Service health checks
- Resource usage tracking
- Rate limit status monitoring
- Error rate analysis

## 🧪 Testing

### Running Tests

```bash
cd backend
pytest tests/ -v --cov=app --cov-report=html
```

### Test Categories

- **Unit Tests**: Core functionality and service modules
- **Integration Tests**: API endpoint testing
- **Service Tests**: External API integration testing
- **Security Tests**: Encryption and authentication testing

## 🚧 Development

### Project Structure

```
lm-api-testing/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── core/              # Core functionality
│   │   ├── services/          # Service integrations
│   │   ├── api/               # REST API endpoints
│   │   └── main.py            # Application entry point
│   └── requirements.txt# Multi-Service API Testing Platform - Project Structure

## Complete Directory Structure
```

lm-api-testing/
├── backend/ # FastAPI Backend
│ ├── app/
│ │ ├── **init**.py
│ │ ├── main.py # FastAPI application entry point
│ │ ├── core/ # Core functionality
│ │ │ ├── **init**.py
│ │ │ ├── auth_manager.py # Multi-service authentication
│ │ │ ├── config_manager.py # Configuration management
│ │ │ ├── service_discovery.py # Service module discovery
│ │ │ ├── rate_limiter.py # Request rate limiting
│ │ │ ├── request_logger.py # Request/response logging
│ │ │ ├── webhook_server.py # Webhook endpoint management
│ │ │ ├── encryption.py # Credential encryption
│ │ │ └── exceptions.py # Custom exceptions
│ │ ├── api/ # REST API endpoints
│ │ │ ├── **init**.py
│ │ │ ├── auth.py # Authentication endpoints
│ │ │ ├── services.py # Service management endpoints
│ │ │ ├── testing.py # API testing endpoints
│ │ │ ├── webhooks.py # Webhook management
│ │ │ ├── history.py # Request history
│ │ │ └── collections.py # Request collections
│ │ ├── services/ # Service modules
│ │ │ ├── **init**.py
│ │ │ ├── base.py # Base service class
│ │ │ └── stripe/ # Example service
│ │ │ ├── **init**.py
│ │ │ ├── config.yaml
│ │ │ ├── client.py
│ │ │ ├── auth.py
│ │ │ └── models.py
│ │ └── models/ # Pydantic models
│ │ ├── **init**.py
│ │ ├── auth.py
│ │ ├── service.py
│ │ ├── request.py
│ │ └── response.py
│ ├── requirements.txt # Python dependencies
│ ├── requirements-dev.txt # Development dependencies
│ └── pytest.ini # Test configuration
├── frontend/ # React Frontend
│ ├── public/
│ ├── src/
│ │ ├── components/
│ │ ├── pages/
│ │ ├── hooks/
│ │ ├── services/
│ │ └── utils/
│ ├── package.json
│ ├── tsconfig.json
│ ├── tailwind.config.js
│ └── vite.config.ts
├── config/ # Global configuration
│ ├── services.yaml # Service registry
│ ├── auth_templates.yaml # Authentication templates
│ └── app_config.yaml # Application configuration
├── data/ # Local data storage
│ ├── credentials/ # Encrypted credentials
│ ├── history/ # Request history
│ ├── collections/ # Saved collections
│ └── logs/ # Application logs
├── docker/ # Docker configuration
│ ├── Dockerfile.backend
│ ├── Dockerfile.frontend
│ └── docker-compose.yml
├── scripts/ # Utility scripts
│ ├── setup.py # Project setup
│ ├── dev_server.py # Development server
│ └── migrate.py # Data migration
├── tests/ # Test suite
│ ├── backend/
│ ├── frontend/
│ └── integration/
├── docs/ # Documentation
│ ├── services/
│ ├── api/
│ └── setup/
├── .env.example # Environment variables template
├── .gitignore # Git ignore rules
├── README.md # Project documentation
├── LICENSE # MIT License
└── pyproject.toml # Python project configuration

```

## Key Architecture Decisions

### 1. **Modular Service System**
Each API service is completely self-contained with its own configuration, authentication, and UI components.

### 2. **Secure by Default**
All credentials are encrypted at rest, with secure token handling and rotation.

### 3. **Configuration-Driven**
Services are defined through YAML configuration files, making it easy to add new services without code changes.

### 4. **Comprehensive Logging**
Every request/response is logged with correlation IDs for debugging and analysis.

### 5. **Rate Limiting Built-in**
Each service respects its rate limits with intelligent queuing and backoff strategies.

## Next Steps
1. Backend core implementation
2. FastAPI application setup
3. Service discovery system
4. Authentication framework
5. First service integration (Stripe)

Let's start building! 🚀
```
