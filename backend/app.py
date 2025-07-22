from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import requests
import logging
from datetime import datetime

from config import config
from validators import (
    ValidationError, validate_email_address, sanitize_html_content,
    validate_json_field, validate_event_name, validate_request_data,
    validate_pagination_params
)

# Initialize Flask app
app = Flask(__name__)
CORS(app, origins=['http://localhost:3000', 'http://127.0.0.1:3000'])
app.config['MAX_CONTENT_LENGTH'] = config.max_content_length

# Initialize rate limiter
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=[config.rate_limit_default],
    storage_uri="memory://"
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
)
logger = logging.getLogger(__name__)

def get_brevo_headers():
    """Get headers for Brevo API requests"""
    if not config.brevo_api_key:
        raise ValidationError("BREVO_API_KEY not found in environment variables")
    
    return {
        'api-key': config.brevo_api_key,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

def make_brevo_request(method: str, endpoint: str, **kwargs):
    """Make a request to Brevo API with proper error handling and timeout"""
    headers = get_brevo_headers()
    url = f'{config.brevo_base_url}{endpoint}'
    
    # Set timeout if not provided
    if 'timeout' not in kwargs:
        kwargs['timeout'] = config.request_timeout
    
    try:
        response = requests.request(method, url, headers=headers, **kwargs)
        return response
    except requests.exceptions.Timeout:
        raise ValidationError("Request to Brevo API timed out")
    except requests.exceptions.ConnectionError:
        raise ValidationError("Failed to connect to Brevo API")
    except requests.exceptions.RequestException as e:
        raise ValidationError(f"Request failed: {str(e)}")

@app.route('/', methods=['GET'])
@limiter.exempt
def health_check():
    """Health check endpoint"""
    config_errors = config.validate()
    
    return jsonify({
        'status': 'success' if not config_errors else 'warning',
        'message': 'Brevo API Integration Service is running',
        'timestamp': datetime.utcnow().isoformat(),
        'api_key_configured': bool(config.brevo_api_key),
        'sender_email_configured': bool(config.brevo_sender_email),
        'configuration_errors': config_errors
    })

@app.route('/api/account', methods=['GET'])
def get_account_info():
    """Get Brevo account information"""
    try:
        response = make_brevo_request('GET', '/account')
        
        if response.status_code == 200:
            data = response.json()
            return jsonify({
                'status': 'success',
                'data': {
                    'email': data.get('email', 'N/A'),
                    'firstName': data.get('firstName', 'N/A'),
                    'lastName': data.get('lastName', 'N/A'),
                    'companyName': data.get('companyName', 'N/A'),
                    'plan': data.get('plan', [{}])[0].get('type', 'N/A') if data.get('plan') else 'N/A',
                    'emailCredits': data.get('plan', [{}])[0].get('creditsLeft', 'N/A') if data.get('plan') else 'N/A'
                }
            })
        else:
            logger.error(f"Brevo API error: {response.status_code} - {response.text}")
            return jsonify({
                'status': 'error',
                'message': f'Brevo API error: {response.status_code}',
                'details': response.text
            }), response.status_code
            
    except ValidationError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred'
        }), 500

@app.route('/api/send-custom-event', methods=['POST'])
@limiter.limit(config.rate_limit_events)
def send_custom_event():
    """Send a custom event to Brevo"""
    try:
        # Get and validate request data
        data = request.get_json()
        if not data:
            raise ValidationError('Request body is required')
        
        validate_request_data(data, ['event_name', 'email_id'])
        
        # Validate and clean inputs
        event_name = validate_event_name(data['event_name'])
        email_id = validate_email_address(data['email_id'])
        
        # Validate optional JSON fields
        contact_properties = validate_json_field(
            data.get('contact_properties', ''), 'contact_properties'
        )
        event_properties = validate_json_field(
            data.get('event_properties', ''), 'event_properties'
        )
        
        # Prepare event payload
        event_payload = {
            'event_name': event_name,
            'event_date': data.get('event_date', datetime.utcnow().isoformat()),
            'identifiers': {'email_id': email_id}
        }
        
        # Add optional properties
        if contact_properties:
            event_payload['contact_properties'] = contact_properties
        if event_properties:
            event_payload['event_properties'] = event_properties
        
        # Add other identifiers if provided
        if data.get('phone_id'):
            event_payload['identifiers']['phone_id'] = data.get('phone_id')
        if data.get('ext_id'):
            event_payload['identifiers']['ext_id'] = data.get('ext_id')
        
        response = make_brevo_request('POST', '/events', json=event_payload)
        
        if response.status_code == 204:  # Brevo returns 204 for successful event creation
            return jsonify({
                'status': 'success',
                'message': 'Custom event sent successfully',
                'data': {
                    'event_name': event_name,
                    'email_id': email_id
                }
            })
        else:
            logger.error(f"Brevo API error: {response.status_code} - {response.text}")
            return jsonify({
                'status': 'error',
                'message': f'Failed to send event: {response.status_code}',
                'details': response.text
            }), response.status_code
            
    except ValidationError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred'
        }), 500

@app.route('/api/contacts', methods=['GET'])
def get_contacts():
    """Get contacts from Brevo"""
    try:
        # Get and validate query parameters
        limit = request.args.get('limit', 10, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        limit, offset = validate_pagination_params(limit, offset)
        
        params = {'limit': limit, 'offset': offset}
        
        response = make_brevo_request('GET', '/contacts', params=params)
        
        if response.status_code == 200:
            data = response.json()
            return jsonify({
                'status': 'success',
                'data': {
                    'totalCount': data.get('count', 0),
                    'contacts': [{
                        'id': contact.get('id'),
                        'email': contact.get('email'),
                        'attributes': contact.get('attributes', {}),
                        'listIds': contact.get('listIds', []),
                        'createdAt': contact.get('createdAt'),
                        'modifiedAt': contact.get('modifiedAt')
                    } for contact in data.get('contacts', [])]
                }
            })
        else:
            logger.error(f"Brevo API error: {response.status_code} - {response.text}")
            return jsonify({
                'status': 'error',
                'message': f'Brevo API error: {response.status_code}',
                'details': response.text
            }), response.status_code
            
    except ValidationError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred'
        }), 500

@app.route('/api/send-test-email', methods=['POST'])
@limiter.limit(config.rate_limit_email)
def send_test_email():
    """Send a test email via Brevo"""
    try:
        # Check if sender email is configured
        if not config.brevo_sender_email:
            raise ValidationError('Sender email not configured. Please set BREVO_SENDER_EMAIL in environment variables.')
        
        # Get and validate request data
        data = request.get_json()
        if not data:
            raise ValidationError('Request body is required')
        
        validate_request_data(data, ['to'])
        
        # Validate and clean inputs
        to_email = validate_email_address(data['to'])
        subject = data.get('subject', 'Test Email from Brevo API').strip()
        content = sanitize_html_content(data.get('content', '<p>This is a test email sent via Brevo API integration.</p>'))
        
        # Validate subject length
        if len(subject) > 255:
            raise ValidationError('Subject must be 255 characters or less')
        
        # Prepare email payload
        email_payload = {
            'sender': {
                'name': config.brevo_sender_name,
                'email': config.brevo_sender_email
            },
            'to': [{'email': to_email}],
            'subject': subject,
            'htmlContent': content
        }
        
        response = make_brevo_request('POST', '/smtp/email', json=email_payload)
        
        if response.status_code == 201:
            return jsonify({
                'status': 'success',
                'message': 'Test email sent successfully',
                'data': response.json()
            })
        else:
            logger.error(f"Brevo API error: {response.status_code} - {response.text}")
            return jsonify({
                'status': 'error',
                'message': f'Failed to send email: {response.status_code}',
                'details': response.text
            }), response.status_code
            
    except ValidationError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred'
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'status': 'error',
        'message': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), 500

@app.errorhandler(ValidationError)
def handle_validation_error(e):
    return jsonify({
        'status': 'error',
        'message': str(e)
    }), 400

@app.errorhandler(429)
def handle_rate_limit(e):
    return jsonify({
        'status': 'error',
        'message': 'Rate limit exceeded. Please try again later.',
        'details': str(e)
    }), 429

if __name__ == '__main__':
    # Validate configuration
    config_errors = config.validate()
    if config_errors:
        logger.warning(f"Configuration issues: {', '.join(config_errors)}")
        for error in config_errors:
            print(f"⚠️  Warning: {error}")
    else:
        logger.info("Configuration validated successfully")
        logger.info(f"Brevo sender email: {config.brevo_sender_email}")
    
    # Run the app
    app.run(
        debug=config.flask_debug,
        host=config.flask_host,
        port=config.flask_port
    )