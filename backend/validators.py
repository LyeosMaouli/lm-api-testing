"""
Input validation utilities for Brevo API integration
"""
from email_validator import validate_email, EmailNotValidError
import bleach
import json
import validators
from typing import Dict, Any, Tuple, Optional

class ValidationError(Exception):
    """Custom validation error"""
    pass

def validate_email_address(email: str) -> str:
    """
    Validate and normalize email address
    
    Args:
        email: Email address to validate
        
    Returns:
        Normalized email address
        
    Raises:
        ValidationError: If email is invalid
    """
    try:
        validated_email = validate_email(email)
        return validated_email.email
    except EmailNotValidError as e:
        raise ValidationError(f"Invalid email address: {str(e)}")

def sanitize_html_content(content: str) -> str:
    """
    Sanitize HTML content to prevent XSS
    
    Args:
        content: Raw HTML content
        
    Returns:
        Sanitized HTML content
    """
    allowed_tags = [
        'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li', 'a', 'img', 'div', 'span', 'table', 'tr', 'td', 'th'
    ]
    allowed_attributes = {
        'a': ['href', 'title'],
        'img': ['src', 'alt', 'width', 'height'],
        '*': ['class', 'style']
    }
    
    return bleach.clean(content, tags=allowed_tags, attributes=allowed_attributes)

def validate_json_field(json_str: str, field_name: str) -> Optional[Dict[str, Any]]:
    """
    Validate JSON string field
    
    Args:
        json_str: JSON string to validate
        field_name: Name of the field (for error messages)
        
    Returns:
        Parsed JSON object or None if empty
        
    Raises:
        ValidationError: If JSON is invalid
    """
    if not json_str or not json_str.strip():
        return None
        
    try:
        parsed_json = json.loads(json_str)
        if not isinstance(parsed_json, dict):
            raise ValidationError(f"{field_name} must be a JSON object")
        return parsed_json
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON in {field_name}: {str(e)}")

def validate_event_name(event_name: str) -> str:
    """
    Validate event name
    
    Args:
        event_name: Event name to validate
        
    Returns:
        Validated event name
        
    Raises:
        ValidationError: If event name is invalid
    """
    if not event_name or not event_name.strip():
        raise ValidationError("Event name is required")
    
    event_name = event_name.strip()
    
    # Check length
    if len(event_name) > 100:
        raise ValidationError("Event name must be 100 characters or less")
    
    # Check for valid characters (alphanumeric, underscore, hyphen)
    if not event_name.replace('_', '').replace('-', '').replace(' ', '').isalnum():
        raise ValidationError("Event name can only contain letters, numbers, spaces, underscores, and hyphens")
    
    return event_name

def validate_request_data(data: Dict[str, Any], required_fields: list[str]) -> None:
    """
    Validate that required fields are present in request data
    
    Args:
        data: Request data dictionary
        required_fields: List of required field names
        
    Raises:
        ValidationError: If required fields are missing
    """
    missing_fields = []
    for field in required_fields:
        if field not in data or not data[field]:
            missing_fields.append(field)
    
    if missing_fields:
        raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")

def validate_pagination_params(limit: int, offset: int) -> Tuple[int, int]:
    """
    Validate pagination parameters
    
    Args:
        limit: Number of items to return
        offset: Number of items to skip
        
    Returns:
        Tuple of (validated_limit, validated_offset)
        
    Raises:
        ValidationError: If parameters are invalid
    """
    # Validate limit
    if limit < 1:
        raise ValidationError("Limit must be at least 1")
    if limit > 50:
        raise ValidationError("Limit cannot exceed 50")
    
    # Validate offset
    if offset < 0:
        raise ValidationError("Offset cannot be negative")
    
    return limit, offset