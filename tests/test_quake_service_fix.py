
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone
from app.services.quake_service import QuakeService

@pytest.fixture
def quake_service():
    return QuakeService("http://mock-api", persistence_file="dummy_path.json")

def test_check_quake_small_scale_does_not_save_id(quake_service):
    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 200

    JST = timezone(timedelta(hours=9))
    now = datetime.now(JST)
    quake_time_str = now.strftime("%Y/%m/%d %H:%M:%S")

    # Mock Data with ID but Small Scale
    mock_data = [{
        "_id": "quake_small",
        "earthquake": {
            "time": quake_time_str,
            "maxScale": 10, # Scale 1 (< 30)
            "hypocenter": {"name": "Test Place", "magnitude": 3.0},
            "domesticTsunami": "None"
        }
    }]
    mock_response.json.return_value = mock_data

    # Mock persistence
    with patch('requests.get', return_value=mock_response), \
         patch.object(QuakeService, '_load_last_quake_id', return_value="diff_id"), \
         patch.object(QuakeService, '_save_last_quake_id') as mock_save:

        result = quake_service.check_quake()

        assert result['notify'] is False
        assert result['status'] == "Small quake"

        # KEY ASSERTION: Save should NOT be called
        mock_save.assert_not_called()
