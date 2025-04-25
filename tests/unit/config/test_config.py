import os
from unittest.mock import patch

import pytest

from market_sim.config.config_manager import ConfigManager


def test_load_config_from_env():
    with patch.dict(os.environ, {
        'STORAGE_TYPE': 'local',
        'LOCAL_STORAGE_PATH': './test_data',
        'DEFAULT_DRIFT': '0.05',
        'DEFAULT_VOLATILITY': '0.2'
    }):
        config = ConfigManager()
        assert config.storage_type == 'local'
        assert config.local_storage_path == './test_data'
        assert config.default_drift == 0.05
        assert config.default_volatility == 0.2

def test_missing_required_config():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError) as exc_info:
            ConfigManager()
        assert "Missing required configuration" in str(exc_info.value)

def test_invalid_storage_type():
    with patch.dict(os.environ, {'STORAGE_TYPE': 'invalid'}):
        with pytest.raises(ValueError) as exc_info:
            ConfigManager()
        assert "Invalid storage type" in str(exc_info.value)

def test_invalid_numeric_values():
    with patch.dict(os.environ, {
        'STORAGE_TYPE': 'local',
        'DEFAULT_DRIFT': 'not_a_number'
    }):
        with pytest.raises(ValueError) as exc_info:
            ConfigManager()
        assert "Invalid numeric value" in str(exc_info.value)