# tests/test_config_manager.py
"""
Test the configuration management system.
"""

import pytest
import tempfile
import os
from pathlib import Path
from backend.app.core.config_manager import ConfigManager, ServiceConfig

@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

def test_config_manager_initialization(temp_config_dir):
    """Test ConfigManager initialization."""
    config_manager = ConfigManager(temp_config_dir)
    assert config_manager.config_dir == Path(temp_config_dir)

def test_create_service_config_template(temp_config_dir):
    """Test creating a service configuration template."""
    config_manager = ConfigManager(temp_config_dir)
    
    template_file = config_manager.create_service_config_template("test_service")
    
    assert os.path.exists(template_file)
    
    # Verify the template contains expected content
    with open(template_file, 'r') as f:
        content = f.read()
        assert 'name: "test_service"' in content
        assert 'display_name: "Test_service"' in content

def test_list_available_services_empty(temp_config_dir):
    """Test listing services when none exist."""
    config_manager = ConfigManager(temp_config_dir)
    services = config_manager.list_available_services()
    assert services == []