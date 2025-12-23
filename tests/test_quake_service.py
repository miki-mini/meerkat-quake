import pytest
import json
from unittest.mock import MagicMock, patch, mock_open
from datetime import datetime, timedelta, timezone
from app.services.quake_service import QuakeService

@pytest.fixture
def quake_service():
    # Use a dummy file path for testing
    return QuakeService("http://mock-api", persistence_file="dummy_path.json")

def test_check_quake_new_notification(quake_service):
    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 200

    # JST now
    JST = timezone(timedelta(hours=9))
    now = datetime.now(JST)
    quake_time_str = now.strftime("%Y/%m/%d %H:%M:%S")

    # Mock Data with ID
    mock_data = [{
        "_id": "quake123", # API ID
        "earthquake": {
            "time": quake_time_str,
            "maxScale": 40, # Scale 4
            "hypocenter": {"name": "Test Place", "magnitude": 5.0},
            "domesticTsunami": "None"
        }
    }]
    mock_response.json.return_value = mock_data

    # Mock persistence: Last ID was different (or None)
    with patch('requests.get', return_value=mock_response), \
         patch.object(QuakeService, '_load_last_quake_id', return_value="old_id"), \
         patch.object(QuakeService, '_save_last_quake_id') as mock_save:

        result = quake_service.check_quake()

        assert result['notify'] is True
        assert "震度4" in result['message']
        assert result['status'] == "Earthquake Detected"

        # Verify save was called with new ID
        mock_save.assert_called_with("quake123")

def test_check_quake_already_notified(quake_service):
    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 200

    JST = timezone(timedelta(hours=9))
    now = datetime.now(JST)
    quake_time_str = now.strftime("%Y/%m/%d %H:%M:%S")

    mock_data = [{
        "_id": "quake123",
        "earthquake": {
            "time": quake_time_str,
            "maxScale": 40,
            "hypocenter": {"name": "Test Place", "magnitude": 5.0},
            "domesticTsunami": "None"
        }
    }]
    mock_response.json.return_value = mock_data

    # Mock persistence: Last ID is SAME
    with patch('requests.get', return_value=mock_response), \
         patch.object(QuakeService, '_load_last_quake_id', return_value="quake123"), \
         patch.object(QuakeService, '_save_last_quake_id') as mock_save:

        result = quake_service.check_quake()

        assert result['notify'] is False
        assert result['status'] == "Already notified"
        # Save should not be called (or doesn't matter, but logic says it returns early)
        mock_save.assert_not_called()

def test_check_quake_too_old(quake_service):
    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 200

    # 25 hours ago
    JST = timezone(timedelta(hours=9))
    now = datetime.now(JST) - timedelta(hours=25)
    quake_time_str = now.strftime("%Y/%m/%d %H:%M:%S")

    mock_data = [{
        "_id": "quake_old",
        "earthquake": {
            "time": quake_time_str,
            "maxScale": 40,
            "hypocenter": {"name": "Test Place", "magnitude": 5.0},
            "domesticTsunami": "None"
        }
    }]
    mock_response.json.return_value = mock_data

    with patch('requests.get', return_value=mock_response), \
         patch.object(QuakeService, '_load_last_quake_id', return_value="diff_id"):

        result = quake_service.check_quake()

        assert result['notify'] is False
        assert result['status'] == "Too old"

def test_persistence_methods(quake_service):
    # Test _save_last_quake_id
    with patch("builtins.open", mock_open()) as mock_file, \
         patch("os.makedirs") as mock_makedirs, \
         patch("app.services.quake_service.datetime") as mock_datetime:

        mock_datetime.now.return_value.isoformat.return_value = "2023-01-01T12:00:00"

        quake_service._save_last_quake_id("test_id")

        mock_makedirs.assert_called_with("", exist_ok=True) # dirname of "dummy_path" is ""? No, "dummy_path.json" dirname is empty string.
        # Actually os.path.dirname("dummy_path.json") is empty string.
        # os.makedirs("") might fail or do nothing?
        # Let's check logic: os.makedirs(os.path.dirname(...))
        # If dirname is empty, makedirs might raise error or do nothing.
        # But wait, local path "data/last_quake.json" has dirname "data".
        # In test fixture I used "dummy_path.json".
        # Using "data/dummy.json" is safer for test.

    # Let's refine the test to use a path with dir
    service = QuakeService("url", persistence_file="test_data/file.json")

    with patch("builtins.open", mock_open()) as mock_file, \
         patch("os.makedirs") as mock_makedirs:

        service._save_last_quake_id("test_id")
        mock_makedirs.assert_called_with("test_data", exist_ok=True)

        handle = mock_file()
        # Check written content
        # It's hard to check exact json dump string because of formatting, but we can check if write was called.
        assert handle.write.called

    # Test _load_last_quake_id
    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data='{"id": "saved_id"}')):

        loaded_id = service._load_last_quake_id()
        assert loaded_id == "saved_id"
