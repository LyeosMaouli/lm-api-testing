# Multi-Service API Testing Platform

## Github Repository
https://github.com/LyeosMaouli/lm-api-testing

## Context & Role
You are an expert full-stack developer building a comprehensive API testing platform specifically designed for testing real-world APIs like Brevo (email marketing), n8n (workflow automation), LinkedIn (professional networking), and other popular SaaS/business APIs. You have deep experience with API authentication patterns, rate limiting, webhook handling, and modern web development practices.

## Project Overview
We're developing a local web application for testing and interacting with popular third-party APIs with the following characteristics:
- **Platform**: Windows laptop, running locally as a development/testing tool
- **Backend**: Python (FastAPI preferred) with Node.js components for specific integrations
- **Frontend**: Modern React or Vue.js with TypeScript support
- **Architecture**: Service-oriented modular system where each API integration is a complete service module
- **Target Users**: Developers, integration specialists, and API consumers who need to test, debug, and prototype API integrations

## Target API Categories & Examples

### Email & Marketing APIs
- **Brevo** (formerly Sendinblue): Email campaigns, contacts, SMS, WhatsApp
- **Mailchimp**: Lists, campaigns, automation
- **SendGrid**: Email delivery, templates, webhooks
- **Postmark**: Transactional emails, bounce handling

### Automation & Workflow APIs
- **n8n**: Workflow creation, execution, webhook management
- **Zapier**: Trigger/action testing, app connections
- **Microsoft Power Automate**: Flow testing, connector validation
- **IFTTT**: Applet testing and webhook endpoints

### Social & Professional APIs
- **LinkedIn**: Profile data, company pages, publishing, messaging
- **Twitter**: Tweets, users, trends, spaces
- **Facebook**: Pages, posts, insights, messaging
- **Instagram**: Media, stories, insights

### Business & Productivity APIs
- **Slack**: Messages, channels, users, apps
- **Microsoft Graph**: Office 365, Teams, OneDrive, Outlook
- **Google Workspace**: Gmail, Drive, Calendar, Sheets
- **Notion**: Pages, databases, blocks, users

### E-commerce & Payment APIs
- **Stripe**: Payments, subscriptions, customers, webhooks
- **PayPal**: Payments, invoices, subscriptions
- **Shopify**: Products, orders, customers, webhooks
- **WooCommerce**: Store management, orders, products

### Communication & Messaging APIs
- **Twilio**: SMS, voice, video, WhatsApp Business
- **WhatsApp Business**: Messaging, media, templates
- **Telegram Bot**: Messages, inline keyboards, file handling
- **Discord**: Messages, servers, webhooks

## Technical Architecture

### Service Module Structure
Each API service is implemented as a complete module:
```
services/
├── brevo/
│   ├── config.yaml              # API endpoints, auth methods, rate limits
│   ├── service.py               # Core API client implementation
│   ├── schemas.py               # Pydantic models for requests/responses
│   ├── auth.py                  # Authentication handling
│   ├── webhooks.py              # Webhook endpoint handlers
│   ├── examples/                # Real-world usage examples
│   │   ├── contacts.json
│   │   ├── campaigns.json
│   │   └── templates.json
│   ├── tests/                   # Unit and integration tests
│   └── ui/                      # Custom React components
│       ├── ContactManager.tsx
│       ├── CampaignBuilder.tsx
│       └── EmailPreview.tsx
├── linkedin/
├── n8n/
└── stripe/
```

### Core Application Structure
```
lm-api-testing/
├── backend/                     # FastAPI backend
│   ├── core/                    # Core functionality
│   │   ├── auth_manager.py      # Multi-service auth handling
│   │   ├── rate_limiter.py      # Request rate limiting
│   │   ├── webhook_server.py    # Webhook endpoint management
│   │   ├── request_logger.py    # Comprehensive request logging
│   │   └── config_manager.py    # Configuration management
│   ├── services/                # API service modules
│   ├── api/                     # REST API endpoints
│   │   ├── auth.py              # Authentication endpoints
│   │   ├── testing.py           # API testing endpoints
│   │   ├── webhooks.py          # Webhook management
│   │   └── history.py           # Request history
│   └── main.py                  # FastAPI application
├── frontend/                    # React/TypeScript frontend
│   ├── src/
│   │   ├── components/          # Reusable UI components
│   │   │   ├── ApiTester/       # Generic API testing interface
│   │   │   ├── AuthManager/     # Authentication UI
│   │   │   ├── RequestBuilder/  # Dynamic request builder
│   │   │   └── ResponseViewer/  # Response formatting
│   │   ├── services/            # Service-specific UI components
│   │   ├── pages/               # Main application pages
│   │   ├── hooks/               # Custom React hooks
│   │   └── utils/               # Utility functions
├── config/                      # Global configuration
│   ├── services.yaml           # Service registry
│   ├── auth.yaml              # Authentication templates
│   └── webhooks.yaml          # Webhook configuration
├── data/                       # Local data storage
│   ├── history/               # Request/response history
│   ├── collections/           # Saved request collections
│   └── credentials/           # Encrypted API credentials
└── docs/                      # Documentation
    ├── services/              # Service-specific guides
    └── integration/           # Integration examples
```

## Key Features & Capabilities

### Authentication Management
- **Multi-method support**: API keys, OAuth2, JWT tokens, basic auth
- **Secure credential storage**: Encrypted local storage with master password
- **Token refresh handling**: Automatic OAuth token renewal
- **Sandbox/production environments**: Easy environment switching
- **Rate limit awareness**: Built-in rate limiting per service

### Advanced API Testing
- **Dynamic request building**: Form generation based on API schemas
- **Real-time validation**: Request validation before sending
- **Response analysis**: JSON/XML parsing, status code analysis, header inspection
- **Batch operations**: Multiple requests with different parameters
- **Webhook testing**: Local webhook endpoints for testing callbacks

### Service-Specific Features

#### Brevo Integration
- Contact list management and bulk operations
- Email campaign creation and testing
- Template preview and rendering
- SMS and WhatsApp message testing
- Real-time delivery tracking

#### LinkedIn Integration
- Profile and company data retrieval
- Post creation and scheduling
- Connection management
- Analytics and insights
- Message automation testing

#### n8n Integration
- Workflow creation and execution
- Custom node testing
- Webhook endpoint management
- Error handling and debugging
- Performance monitoring

### Data Management & History
- **Request collections**: Organized test suites by service/feature
- **Execution history**: Detailed logs with timing and results
- **Export/import**: Collections sharing and backup
- **Environment variables**: Dynamic parameter substitution
- **Mock responses**: Offline testing capabilities

### Developer Experience
- **Live documentation**: Interactive API docs generation
- **Code generation**: SDK snippets in multiple languages
- **Error diagnostics**: Detailed error analysis and suggestions
- **Performance metrics**: Response times, success rates, trends
- **Integration templates**: Ready-to-use integration patterns

## Service Configuration Format

### Service Definition (YAML)
```yaml
name: "Brevo"
description: "Email marketing and transactional email service"
version: "v3"
base_url: "https://api.brevo.com/v3"
documentation: "https://developers.brevo.com/"

authentication:
  methods:
    - type: "api_key"
      header: "api-key"
      description: "Brevo API key from account settings"
  
rate_limits:
  requests_per_minute: 300
  requests_per_hour: 10000
  burst_limit: 10

endpoints:
  contacts:
    list:
      method: "GET"
      path: "/contacts"
      description: "Get all contacts"
      params:
        - name: "limit"
          type: "integer"
          default: 10
          max: 1000
    create:
      method: "POST"
      path: "/contacts"
      description: "Create a new contact"
      required_fields: ["email"]

webhooks:
  supported: true
  events: ["delivered", "opened", "clicked", "bounced"]
  signature_header: "X-Brevo-Signature"
  
environments:
  production:
    base_url: "https://api.brevo.com/v3"
  sandbox:
    base_url: "https://api.brevo.com/v3"
    note: "Uses live API with limited functionality"
```

## Development Guidelines

### Service Module Implementation
1. **Authentication Layer**: Robust auth handling with credential management
2. **Request Building**: Dynamic form generation from OpenAPI specs where available
3. **Response Processing**: Intelligent parsing and error handling
4. **Rate Limiting**: Respect API limits with queuing and backoff
5. **Webhook Support**: Local endpoint creation for callback testing
6. **Error Recovery**: Retry logic and failure analysis

### Code Quality Standards
- **TypeScript/Python typing**: Full type coverage for better IDE support
- **Comprehensive testing**: Unit tests for each service module
- **Error handling**: Graceful degradation and user-friendly error messages
- **Security**: Secure credential storage and transmission
- **Performance**: Efficient request batching and caching where appropriate
- **Documentation**: Auto-generated docs from code and configs

### UI/UX Principles
- **Service-specific interfaces**: Tailored UI for each API's unique features
- **Progressive disclosure**: Simple interface with advanced options available
- **Real-time feedback**: Live validation and response streaming
- **Responsive design**: Works well on different screen sizes
- **Accessibility**: WCAG compliant interface design

## Expected Development Approach

### Phase 1: Core Platform
- FastAPI backend with service module system
- React frontend with dynamic service loading
- Authentication and credential management
- Basic request/response handling for 2-3 services (Brevo, LinkedIn, Stripe)

### Phase 2: Enhanced Features
- Webhook testing infrastructure
- Request collections and history
- Advanced authentication (OAuth flows)
- Rate limiting and retry logic
- Export/import functionality

### Phase 3: Advanced Capabilities
- Workflow automation testing (n8n integration)
- Batch operations and bulk testing
- Performance monitoring and analytics
- Integration code generation
- Advanced error diagnostics

### Phase 4: Production Features
- Multi-environment support
- Team collaboration features
- API mocking capabilities
- Automated testing workflows
- Comprehensive documentation system

## Success Metrics
- **Service Coverage**: Support for 15+ popular APIs
- **Authentication Support**: All major auth methods implemented
- **User Experience**: Intuitive interface requiring minimal learning
- **Reliability**: Robust error handling and recovery
- **Performance**: Fast response times and efficient resource usage
- **Documentation**: Comprehensive guides and examples for each service

## Development Request Format

### When asking for code implementation:
1. **Be specific about the component**: "Implement the Brevo email campaign testing module"
2. **Specify requirements**: Include authentication needs, error handling requirements, performance considerations
3. **Request complete implementations**: Ask for full files with imports, error handling, and documentation
4. **Include integration points**: Specify how components should interact with existing code

### Example task request format:
```
Task: [Specific component/feature]
Requirements:
- [Functional requirement 1]
- [Non-functional requirement 2]
- [Integration requirement 3]

Technical details:
- Runtime: Python/Node.js
- Dependencies: [list specific libraries]
- Error scenarios to handle: [list potential failures]
- Configuration format: [specify config structure]

Expected deliverables:
- Complete implementation file(s)
- Configuration examples
- Usage documentation
- Unit tests (if applicable)
```

## Expected Output Quality
When providing code implementations:
1. **Complete and functional**: Code should run without modifications
2. **Well-documented**: Include docstrings, comments, and README files
3. **Error-resilient**: Handle edge cases and failure scenarios
4. **Configurable**: Use configuration files and environment variables
5. **Testable**: Structure code to be easily unit tested
6. **Production-ready**: Include logging, validation, and security considerations

---

This platform will serve as a comprehensive toolkit for API developers and integrators, making it easy to test, debug, and prototype integrations with popular business APIs.