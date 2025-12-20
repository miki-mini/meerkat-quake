import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone
from app.services.quake_service import QuakeService

@pytest.fixture
def quake_service():
    return QuakeService("http://mock-api")

def test_check_quake_recent_large(quake_service):
    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 200

    # JST now
    JST = timezone(timedelta(hours=9))
    now = datetime.now(JST)
    quake_time_str = now.strftime("%Y/%m/%d %H:%M:%S")

    mock_data = [{
        "earthquake": {
            "time": quake_time_str,
            "maxScale": 40, # Scale 4
            "hypocenter": {"name": "Test Place", "magnitude": 5.0},
            "domesticTsunami": "None"
        }
    }]
    mock_response.json.return_value = mock_data

    with patch('requests.get', return_value=mock_response):
        result = quake_service.check_quake()
        assert result['notify'] is True
        assert "震度4" in result['message']
        assert result['status'] == "Earthquake Detected"

def test_check_quake_old(quake_service):
    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 200

    # 10 mins ago
    JST = timezone(timedelta(hours=9))
    now = datetime.now(JST) - timedelta(minutes=10)
    quake_time_str = now.strftime("%Y/%m/%d %H:%M:%S")

    mock_data = [{
        "earthquake": {
            "time": quake_time_str,
            "maxScale": 40,
            "hypocenter": {"name": "Test Place", "magnitude": 5.0},
            "domesticTsunami": "None"
        }
    }]
    mock_response.json.return_value = mock_data

    with patch('requests.get', return_value=mock_response):
        result = quake_service.check_quake()
        assert result['notify'] is False
        assert result['status'] == "No recent earthquake"

def test_check_quake_small(quake_service):
    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 200

    # JST now
    JST = timezone(timedelta(hours=9))
    now = datetime.now(JST)
    quake_time_str = now.strftime("%Y/%m/%d %H:%M:%S")

    mock_data = [{
        "earthquake": {
            "time": quake_time_str,
            "maxScale": 20, # Scale 2
            "hypocenter": {"name": "Test Place", "magnitude": 3.0},
            "domesticTsunami": "None"
        }
    }]
    mock_response.json.return_value = mock_data

    with patch('requests.get', return_value=mock_response):
        result = quake_service.check_quake()
        assert result['notify'] is False
        assert result['status'] == "Small quake"
