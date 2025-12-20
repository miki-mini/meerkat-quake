import pytest
from unittest.mock import MagicMock, patch
from app.services.health_service import HealthService

def test_health_check_ok():
    service = HealthService()
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch('requests.get', return_value=mock_response):
        errors = service.check_health({"TestSite": "http://example.com"})
        assert len(errors) == 0

def test_health_check_fail():
    service = HealthService()
    mock_response = MagicMock()
    mock_response.status_code = 500

    with patch('requests.get', return_value=mock_response):
        errors = service.check_health({"TestSite": "http://example.com"})
        assert len(errors) == 1
        assert "Abnormal response" in errors[0]

def test_health_check_exception():
    service = HealthService()

    with patch('requests.get', side_effect=Exception("Connection Error")):
        errors = service.check_health({"TestSite": "http://example.com"})
        assert len(errors) == 1
        assert "Access failed" in errors[0]
