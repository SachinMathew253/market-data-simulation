import os
from pathlib import Path
import pickle
import pytest
import numpy as np

from market_sim.storage.storage_interface import StorageInterface
from market_sim.storage.local_storage import LocalStorage
from market_sim.config.config_manager import ConfigManager

@pytest.fixture
def test_data_path(tmp_path):
    return str(tmp_path / "test_data")

@pytest.fixture
def local_storage(test_data_path):
    os.environ['STORAGE_TYPE'] = 'local'
    os.environ['LOCAL_STORAGE_PATH'] = test_data_path
    os.environ['DEFAULT_DRIFT'] = '0.05'
    os.environ['DEFAULT_VOLATILITY'] = '0.2'
    config = ConfigManager()
    return LocalStorage(config)

def test_local_storage_save_load(local_storage):
    # Test data
    data = {
        'prices': np.array([100.0, 101.0, 102.0]),
        'timestamps': np.array(['2025-01-01', '2025-01-02', '2025-01-03'])
    }
    
    # Save data
    key = 'test_simulation'
    local_storage.save(key, data)
    
    # Load data
    loaded_data = local_storage.load(key)
    
    # Verify data
    assert isinstance(loaded_data, dict)
    np.testing.assert_array_equal(loaded_data['prices'], data['prices'])
    np.testing.assert_array_equal(loaded_data['timestamps'], data['timestamps'])

def test_local_storage_nonexistent_key(local_storage):
    with pytest.raises(KeyError):
        local_storage.load('nonexistent_key')

def test_local_storage_list_keys(local_storage):
    # Save multiple datasets
    data = {'test': np.array([1.0, 2.0])}
    local_storage.save('test1', data)
    local_storage.save('test2', data)
    
    # List keys
    keys = local_storage.list_keys()
    assert isinstance(keys, list)
    assert 'test1' in keys
    assert 'test2' in keys

def test_local_storage_delete(local_storage):
    # Save and then delete data
    data = {'test': np.array([1.0, 2.0])}
    key = 'test_delete'
    local_storage.save(key, data)
    assert key in local_storage.list_keys()
    
    local_storage.delete(key)
    assert key not in local_storage.list_keys()

def test_local_storage_clear(local_storage):
    # Save multiple datasets
    data = {'test': np.array([1.0, 2.0])}
    local_storage.save('test1', data)
    local_storage.save('test2', data)
    
    # Clear all data
    local_storage.clear()
    assert len(local_storage.list_keys()) == 0