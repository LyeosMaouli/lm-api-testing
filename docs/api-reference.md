# 📡 API Reference Documentation

Complete API reference for the Brevo API Integration backend service.

## 🔗 Base URL

**Development:** `http://127.0.0.1:5000`  
**Production:** `https://your-api-domain.com`

## 📋 Table of Contents

- [Authentication](#authentication)
- [Rate Limiting](#rate-limiting)
- [Error Handling](#error-handling)
- [Endpoints](#endpoints)
  - [Health Check](#health-check)
  - [Account Information](#account-information)
  - [Contacts Management](#contacts-management)
  - [Email Operations](#email-operations)
  - [Custom Events](#custom-events)
- [Response Formats](#response-formats)
- [Status Codes](#status-codes)
- [Examples](#examples)

---

## 🔐 Authentication

The API uses Brevo API keys for authentication. The key must be configured in the backend's environment variables.

**Configuration:**
```bash
BREVO_API_KEY=your_brevo_api_key_here
```

**Headers:**
- The API automatically handles Brevo authentication
- No authentication headers required for API calls to this service
- Internal Brevo API calls use the configured API key

---

## ⚡ Rate Limiting

The API implements rate limiting to prevent abuse and ensure service stability.

| Endpoint | Rate Limit | Window |
|----------|------------|---------|
| Default | 200 requests | per day |
| Default | 50 requests | per hour |
| `/api/send-test-email` | 5 requests | per minute |
| `/api/send-custom-event` | 10 requests | per minute |
| `/` (Health Check) | No limit | - |

**Rate Limit Headers:**
- `X-RateLimit-Limit`: Request limit per time window
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Time when rate limit resets

---

## ❌ Error Handling

All API endpoints return consistent error response format.

**Error Response Structure:**
```json
{
  "status": "error",
  "message": "Human-readable error description",
  "details": "Technical details (optional)"
}
```

**Validation Error Example:**
```json
{
  "status": "error",
  "message": "Invalid email address: The email address is not valid. It must have exactly one @-sign."
}
```

---

## 🛣️ Endpoints

### Health Check

**GET** `/`

Check the health and configuration status of the API service.

**Rate Limit:** Exempt  
**Authentication:** Not required

**Response:**
```json
{
  "status": "success",
  "message": "Brevo API Integration Service is running",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "api_key_configured": true,
  "sender_email_configured": true,
  "configuration_errors": []
}
```

**cURL Example:**
```bash
curl -X GET http://127.0.0.1:5000/
```

---

### Account Information

**GET** `/api/account`

Retrieve Brevo account information including plan details and available credits.

**Rate Limit:** Default (50/hour, 200/day)  
**Caching:** 5 minutes TTL

**Response:**
```json
{
  "status": "success",
  "data": {
    "email": "user@example.com",
    "firstName": "John",
    "lastName": "Doe",
    "companyName": "Example Corp",
    "plan": "free",
    "emailCredits": 300
  }
}
```

**Error Response:**
```json
{
  "status": "error",
  "message": "BREVO_API_KEY not found in environment variables"
}
```

**cURL Example:**
```bash
curl -X GET \
  http://127.0.0.1:5000/api/account \
  -H "Content-Type: application/json"
```

---

### Contacts Management

**GET** `/api/contacts`

Retrieve a paginated list of contacts from Brevo.

**Rate Limit:** Default (50/hour, 200/day)  
**Caching:** No caching (real-time data)

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | integer | No | 10 | Number of contacts to retrieve (1-50) |
| `offset` | integer | No | 0 | Number of contacts to skip (≥0) |

**Response:**
```json
{
  "status": "success",
  "data": {
    "totalCount": 150,
    "contacts": [
      {
        "id": 1,
        "email": "contact@example.com",
        "attributes": {
          "FIRSTNAME": "Jane",
          "LASTNAME": "Smith"
        },
        "listIds": [2, 5],
        "createdAt": "2024-01-10T09:30:00.000Z",
        "modifiedAt": "2024-01-12T14:20:00.000Z"
      }
    ]
  }
}
```

**Validation Errors:**
```json
{
  "status": "error",
  "message": "Limit must be at least 1"
}
```

**cURL Example:**
```bash
curl -X GET \
  "http://127.0.0.1:5000/api/contacts?limit=5&offset=0" \
  -H "Content-Type: application/json"
```

---

### Email Operations

**POST** `/api/send-test-email`

Send a test email through Brevo with validation and sanitization.

**Rate Limit:** 5 requests per minute  
**Authentication:** Requires `BREVO_SENDER_EMAIL` configuration

**Request Body:**
```json
{
  "to": "recipient@example.com",
  "subject": "Test Email Subject",
  "content": "<p>HTML email content</p>"
}
```

**Request Body Parameters:**

| Parameter | Type | Required | Validation |
|-----------|------|----------|------------|
| `to` | string | Yes | Valid email address |
| `subject` | string | No | ≤ 255 characters |
| `content` | string | No | HTML (sanitized for XSS) |

**Successful Response:**
```json
{
  "status": "success",
  "message": "Test email sent successfully",
  "data": {
    "messageId": "abc123-def456-ghi789"
  }
}
```

**Validation Error Response:**
```json
{
  "status": "error",
  "message": "Invalid email address: Please enter a valid email address"
}
```

**Configuration Error Response:**
```json
{
  "status": "error",
  "message": "Sender email not configured. Please set BREVO_SENDER_EMAIL in environment variables."
}
```

**cURL Example:**
```bash
curl -X POST \
  http://127.0.0.1:5000/api/send-test-email \
  -H "Content-Type: application/json" \
  -d '{
    "to": "recipient@example.com",
    "subject": "Test Email",
    "content": "<p>This is a <strong>test email</strong> from the API.</p>"
  }'
```

---

### Custom Events

**POST** `/api/send-custom-event`

Send a custom event to Brevo for contact tracking and automation.

**Rate Limit:** 10 requests per minute

**Request Body:**
```json
{
  "event_name": "video_played",
  "email_id": "user@example.com",
  "contact_properties": "{\"age\": 30, \"city\": \"New York\"}",
  "event_properties": "{\"video_title\": \"Product Demo\", \"duration\": 120}"
}
```

**Request Body Parameters:**

| Parameter | Type | Required | Validation |
|-----------|------|----------|------------|
| `event_name` | string | Yes | ≤ 100 chars, alphanumeric + spaces, _, - |
| `email_id` | string | Yes | Valid email address |
| `contact_properties` | string | No | Valid JSON object |
| `event_properties` | string | No | Valid JSON object |
| `event_date` | string | No | ISO 8601 format (auto-generated if not provided) |

**Successful Response:**
```json
{
  "status": "success",
  "message": "Custom event sent successfully",
  "data": {
    "event_name": "video_played",
    "email_id": "user@example.com"
  }
}
```

**Validation Error Response:**
```json
{
  "status": "error",
  "message": "Invalid JSON in contact_properties: Expecting property name enclosed in double quotes"
}
```

**cURL Example:**
```bash
curl -X POST \
  http://127.0.0.1:5000/api/send-custom-event \
  -H "Content-Type: application/json" \
  -d '{
    "event_name": "product_viewed",
    "email_id": "customer@example.com",
    "contact_properties": "{\"segment\": \"premium\", \"age\": 35}",
    "event_properties": "{\"product_id\": \"ABC123\", \"category\": \"electronics\", \"price\": 299.99}"
  }'
```

---

## 📊 Response Formats

### Success Response Format
```json
{
  "status": "success",
  "message": "Operation completed successfully",
  "data": {
    // Response data specific to endpoint
  }
}
```

### Error Response Format
```json
{
  "status": "error",
  "message": "Human-readable error message",
  "details": "Optional technical details"
}
```

### Health Check Response Format
```json
{
  "status": "success" | "warning",
  "message": "Service status message",
  "timestamp": "ISO 8601 timestamp",
  "api_key_configured": boolean,
  "sender_email_configured": boolean,
  "configuration_errors": ["array", "of", "errors"]
}
```

---

## 🚦 Status Codes

| Code | Description | Usage |
|------|-------------|-------|
| 200 | OK | Successful GET requests |
| 201 | Created | Successful POST requests (email sent) |
| 400 | Bad Request | Validation errors, missing required fields |
| 401 | Unauthorized | Invalid or missing Brevo API key |
| 404 | Not Found | Invalid endpoint |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server errors |
| 502 | Bad Gateway | Brevo API unavailable |
| 504 | Gateway Timeout | Brevo API timeout |

---

## 📝 Examples

### Complete Email Workflow
```bash
# 1. Check service health
curl -X GET http://127.0.0.1:5000/

# 2. Get account information
curl -X GET http://127.0.0.1:5000/api/account

# 3. Send test email
curl -X POST http://127.0.0.1:5000/api/send-test-email \
  -H "Content-Type: application/json" \
  -d '{
    "to": "test@example.com",
    "subject": "Welcome Email",
    "content": "<h1>Welcome!</h1><p>Thank you for signing up.</p>"
  }'

# 4. Track custom event
curl -X POST http://127.0.0.1:5000/api/send-custom-event \
  -H "Content-Type: application/json" \
  -d '{
    "event_name": "email_opened",
    "email_id": "test@example.com",
    "event_properties": "{\"campaign\": \"welcome_series\", \"email_id\": \"123\"}"
  }'
```

### Error Handling Examples
```bash
# Invalid email address
curl -X POST http://127.0.0.1:5000/api/send-test-email \
  -H "Content-Type: application/json" \
  -d '{
    "to": "invalid-email",
    "subject": "Test"
  }'

# Response:
# {
#   "status": "error",
#   "message": "Invalid email address: Please enter a valid email address"
# }

# Rate limit exceeded
# Make 6 requests to /api/send-test-email within 1 minute

# Response:
# {
#   "status": "error",
#   "message": "Rate limit exceeded. Please try again later.",
#   "details": "5 per 1 minute"
# }
```

### Pagination Example
```bash
# Get first page of contacts
curl -X GET "http://127.0.0.1:5000/api/contacts?limit=10&offset=0"

# Get second page of contacts
curl -X GET "http://127.0.0.1:5000/api/contacts?limit=10&offset=10"

# Get all contacts (limited to 50 max per request)
curl -X GET "http://127.0.0.1:5000/api/contacts?limit=50&offset=0"
```

---

## 🔧 Development Testing

### Using HTTPie (Alternative to cURL)
```bash
# Install HTTPie
pip install httpie

# Health check
http GET :5000/

# Account info
http GET :5000/api/account

# Send email
http POST :5000/api/send-test-email \
  to=test@example.com \
  subject="Test via HTTPie" \
  content="<p>Hello from HTTPie!</p>"

# Custom event
http POST :5000/api/send-custom-event \
  event_name=test_event \
  email_id=user@example.com \
  contact_properties='{"source": "api"}' \
  event_properties='{"test": true}'
```

### Using JavaScript/Fetch
```javascript
// Health check
const healthCheck = async () => {
  const response = await fetch('http://127.0.0.1:5000/');
  const data = await response.json();
  console.log('Health:', data);
};

// Send email
const sendEmail = async () => {
  const response = await fetch('http://127.0.0.1:5000/api/send-test-email', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      to: 'test@example.com',
      subject: 'Test from JavaScript',
      content: '<p>Hello from JavaScript!</p>'
    })
  });
  const data = await response.json();
  console.log('Email result:', data);
};

// Send custom event
const sendEvent = async () => {
  const response = await fetch('http://127.0.0.1:5000/api/send-custom-event', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      event_name: 'page_view',
      email_id: 'user@example.com',
      event_properties: JSON.stringify({
        page: '/products',
        category: 'electronics'
      })
    })
  });
  const data = await response.json();
  console.log('Event result:', data);
};
```

---

## 🛡️ Security Considerations

1. **Input Validation**: All inputs are validated and sanitized
2. **XSS Protection**: HTML content is sanitized using bleach
3. **Rate Limiting**: Prevents API abuse
4. **CORS**: Configured for specific origins only
5. **Error Messages**: No sensitive information exposed
6. **API Keys**: Securely managed through environment variables

---

*This API reference provides complete documentation for integrating with the Brevo API Integration backend service. For frontend integration examples, see the React components in the `/frontend/src` directory.*