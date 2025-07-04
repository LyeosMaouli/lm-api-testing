from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Brevo API configuration
BREVO_API_KEY = os.getenv('BREVO_API_KEY')
BREVO_SENDER_EMAIL = os.getenv('BREVO_SENDER_EMAIL')
BREVO_SENDER_NAME = os.getenv('BREVO_SENDER_NAME', 'API Integration')
BREVO_BASE_URL = 'https://api.brevo.com/v3'

def get_brevo_headers():
    """Get headers for Brevo API requests"""
    if not BREVO_API_KEY:
        raise ValueError("BREVO_API_KEY not found in environment variables")
    
    return {
        'api-key': BREVO_API_KEY,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'success',
        'message': 'Brevo API Integration Service is running',
        'api_key_configured': bool(BREVO_API_KEY)
    })

@app.route('/api/account', methods=['GET'])
def get_account_info():
    """Get Brevo account information"""
    try:
        headers = get_brevo_headers()
        response = requests.get(f'{BREVO_BASE_URL}/account', headers=headers)
        
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
            return jsonify({
                'status': 'error',
                'message': f'Brevo API error: {response.status_code}',
                'details': response.text
            }), response.status_code
            
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to connect to Brevo API',
            'details': str(e)
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'details': str(e)
        }), 500

@app.route('/api/send-custom-event', methods=['POST'])
def send_custom_event():
    """Send a custom event to Brevo"""
    try:
        headers = get_brevo_headers()
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'Request body is required'
            }), 400
        
        # Validate required fields
        event_name = data.get('event_name')
        email_id = data.get('email_id')
        
        if not event_name:
            return jsonify({
                'status': 'error',
                'message': 'Event name is required'
            }), 400
            
        if not email_id:
            return jsonify({
                'status': 'error',
                'message': 'Email ID is required'
            }), 400
        
        # Prepare event payload
        event_payload = {
            'event_name': event_name,
            'event_date': data.get('event_date'),  # ISO format or current time if not provided
            'identifiers': {
                'email_id': email_id
            }
        }
        
        # Add optional contact properties
        contact_properties = data.get('contact_properties', {})
        if contact_properties:
            event_payload['contact_properties'] = contact_properties
        
        # Add optional event properties
        event_properties = data.get('event_properties', {})
        if event_properties:
            event_payload['event_properties'] = event_properties
        
        # Add other identifiers if provided
        identifiers = event_payload['identifiers']
        if data.get('phone_id'):
            identifiers['phone_id'] = data.get('phone_id')
        if data.get('ext_id'):
            identifiers['ext_id'] = data.get('ext_id')
        
        response = requests.post(f'{BREVO_BASE_URL}/events', headers=headers, json=event_payload)
        
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
            
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to connect to Brevo API',
            'details': str(e)
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'details': str(e)
        }), 500

@app.route('/api/contacts', methods=['GET'])
def get_contacts():
    """Get contacts from Brevo"""
    try:
        headers = get_brevo_headers()
        
        # Get query parameters
        limit = request.args.get('limit', 10, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        params = {
            'limit': min(limit, 50),  # Cap at 50 for safety
            'offset': max(offset, 0)
        }
        
        response = requests.get(f'{BREVO_BASE_URL}/contacts', headers=headers, params=params)
        
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
            return jsonify({
                'status': 'error',
                'message': f'Brevo API error: {response.status_code}',
                'details': response.text
            }), response.status_code
            
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to connect to Brevo API',
            'details': str(e)
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'details': str(e)
        }), 500

@app.route('/api/send-test-email', methods=['POST'])
def send_test_email():
    """Send a test email via Brevo"""
    try:
        headers = get_brevo_headers()
        
        # Check if sender email is configured
        if not BREVO_SENDER_EMAIL:
            return jsonify({
                'status': 'error',
                'message': 'Sender email not configured. Please set BREVO_SENDER_EMAIL in environment variables.'
            }), 400
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'Request body is required'
            }), 400
        
        # Validate required fields
        to_email = data.get('to')
        if not to_email:
            return jsonify({
                'status': 'error',
                'message': 'Recipient email (to) is required'
            }), 400
        
        # Prepare email payload with mandatory sender from env
        email_payload = {
            'sender': {
                'name': BREVO_SENDER_NAME,
                'email': BREVO_SENDER_EMAIL
            },
            'to': [{'email': to_email}],
            'subject': data.get('subject', 'Test Email from Brevo API'),
            'htmlContent': data.get('content', '<p>This is a test email sent via Brevo API integration.</p>')
        }
        
        response = requests.post(f'{BREVO_BASE_URL}/smtp/email', headers=headers, json=email_payload)
        
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
            
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to connect to Brevo API',
            'details': str(e)
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'details': str(e)
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

if __name__ == '__main__':
    # Check if API key is configured
    if not BREVO_API_KEY:
        logger.warning("BREVO_API_KEY not found in environment variables!")
        print("⚠️  Warning: BREVO_API_KEY not configured. Please check your .env file.")
    else:
        logger.info("Brevo API key configured successfully")
    
    # Check if sender email is configured
    if not BREVO_SENDER_EMAIL:
        logger.warning("BREVO_SENDER_EMAIL not found in environment variables!")
        print("⚠️  Warning: BREVO_SENDER_EMAIL not configured. Please check your .env file.")
    else:
        logger.info(f"Brevo sender email configured: {BREVO_SENDER_EMAIL}")
    
    # Run the app
    app.run(debug=True, host='127.0.0.1', port=5000)