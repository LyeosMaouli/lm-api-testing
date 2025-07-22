"""
Tests for validation utilities
"""
import pytest
from validators import (
    ValidationError,
    validate_email_address,
    sanitize_html_content,
    validate_json_field,
    validate_event_name,
    validate_request_data,
    validate_pagination_params,
)


class TestValidateEmail:
    def test_valid_email(self):
        email = validate_email_address("test@example.com")
        assert email == "test@example.com"

    def test_invalid_email(self):
        with pytest.raises(ValidationError, match="Invalid email address"):
            validate_email_address("invalid-email")

    def test_empty_email(self):
        with pytest.raises(ValidationError):
            validate_email_address("")


class TestSanitizeHTML:
    def test_allowed_tags(self):
        content = "<p>Hello <strong>world</strong></p>"
        result = sanitize_html_content(content)
        assert result == "<p>Hello <strong>world</strong></p>"

    def test_dangerous_tags_removed(self):
        content = "<script>alert('xss')</script><p>Safe content</p>"
        result = sanitize_html_content(content)
        assert "<script>" not in result
        assert "<p>Safe content</p>" in result


class TestValidateJSON:
    def test_valid_json(self):
        result = validate_json_field('{"key": "value"}', "test_field")
        assert result == {"key": "value"}

    def test_invalid_json(self):
        with pytest.raises(ValidationError, match="Invalid JSON"):
            validate_json_field('{"invalid": json}', "test_field")

    def test_empty_string(self):
        result = validate_json_field("", "test_field")
        assert result is None

    def test_non_object_json(self):
        with pytest.raises(ValidationError, match="must be a JSON object"):
            validate_json_field('"string"', "test_field")


class TestValidateEventName:
    def test_valid_event_name(self):
        result = validate_event_name("video_played")
        assert result == "video_played"

    def test_event_name_with_spaces(self):
        result = validate_event_name("user signup")
        assert result == "user signup"

    def test_empty_event_name(self):
        with pytest.raises(ValidationError, match="Event name is required"):
            validate_event_name("")

    def test_long_event_name(self):
        long_name = "a" * 101
        with pytest.raises(ValidationError, match="100 characters or less"):
            validate_event_name(long_name)


class TestValidateRequestData:
    def test_all_required_fields_present(self):
        data = {"field1": "value1", "field2": "value2"}
        validate_request_data(data, ["field1", "field2"])  # Should not raise

    def test_missing_required_fields(self):
        data = {"field1": "value1"}
        with pytest.raises(ValidationError, match="Missing required fields"):
            validate_request_data(data, ["field1", "field2"])


class TestValidatePagination:
    def test_valid_pagination(self):
        limit, offset = validate_pagination_params(10, 20)
        assert limit == 10
        assert offset == 20

    def test_invalid_limit_too_low(self):
        with pytest.raises(ValidationError, match="Limit must be at least 1"):
            validate_pagination_params(0, 0)

    def test_invalid_limit_too_high(self):
        with pytest.raises(ValidationError, match="Limit cannot exceed 50"):
            validate_pagination_params(100, 0)

    def test_invalid_offset_negative(self):
        with pytest.raises(ValidationError, match="Offset cannot be negative"):
            validate_pagination_params(10, -1)