import os
import pickle
import pandas as pd
from pathlib import Path
from typing import Any, Union
from market_sim.storage.storage_interface import StorageInterface
from market_sim.config.config_manager import ConfigManager

class LocalStorage(StorageInterface):
    def __init__(self, config: ConfigManager):
        self.base_path = Path(config.local_storage_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save(self, filepath: str, data: Union[pd.DataFrame, Any]) -> str:
        """Save data to local storage.
        
        Args:
            filepath: Relative path where to save the data
            data: Data to save (DataFrame or other pickle-able object)
            
        Returns:
            str: Full path where data was saved
        """
        full_path = self.base_path / filepath
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Handle both DataFrames and other objects
        if isinstance(data, pd.DataFrame):
            data.to_pickle(full_path)
        else:
            with open(full_path, 'wb') as f:
                pickle.dump(data, f)
                
        return str(full_path)

    def load(self, filepath: str) -> Union[pd.DataFrame, Any]:
        """Load data from local storage.
        
        Args:
            filepath: Relative path to load data from
            
        Returns:
            Data loaded from storage (DataFrame or other object)
            
        Raises:
            KeyError: If file doesn't exist
        """
        full_path = self.base_path / filepath
        if not full_path.exists():
            raise KeyError(f"Key not found: {filepath}")
            
        try:
            # Try loading as DataFrame first
            return pd.read_pickle(full_path)
        except Exception:
            # If that fails, try regular pickle load
            with open(full_path, 'rb') as f:
                return pickle.load(f)

    def exists(self, filepath: str) -> bool:
        """Check if file exists in storage.
        
        Args:
            filepath: Relative path to check
            
        Returns:
            bool: True if file exists, False otherwise
        """
        return (self.base_path / filepath).exists()

    def list_files(self, directory: str = "") -> list[str]:
        """List files in directory.
        
        Args:
            directory: Relative directory path to list
            
        Returns:
            list[str]: List of file paths in directory
        """
        dir_path = self.base_path / directory
        if not dir_path.exists():
            return []
            
        files = []
        for p in dir_path.glob("**/*"):
            if p.is_file():
                files.append(str(p.relative_to(self.base_path)))
        return files
        
    def delete(self, filepath: str) -> bool:
        """Delete a file from storage.
        
        Args:
            filepath: Relative path to the file to delete
            
        Returns:
            bool: True if file was deleted, False otherwise
        """
        full_path = self.base_path / filepath
        if not full_path.exists():
            return False
        try:
            full_path.unlink()
            return True
        except Exception:
            return False
            
    def clear(self) -> bool:
        """Clear all files from storage.
        
        Returns:
            bool: True if all files were cleared, False otherwise
        """
        try:
            for file in self.base_path.glob("**/*"):
                if file.is_file():
                    file.unlink()
            return True
        except Exception:
            return False
            
    def list_keys(self) -> list[str]:
        """List all file keys in storage.
        
        Returns:
            list[str]: List of all file keys
        """
        return self.list_files()