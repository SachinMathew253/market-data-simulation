from abc import ABC, abstractmethod
from typing import Any, Union
import pandas as pd

class StorageInterface(ABC):
    @abstractmethod
    def save(self, filepath: str, data: Union[pd.DataFrame, Any]) -> str:
        """Save data to storage."""
        pass

    @abstractmethod
    def load(self, filepath: str) -> Union[pd.DataFrame, Any]:
        """Load data from storage."""
        pass

    @abstractmethod
    def exists(self, filepath: str) -> bool:
        """Check if file exists in storage."""
        pass

    @abstractmethod
    def list_files(self, directory: str = "") -> list[str]:
        """List files in directory."""
        pass
        
    @abstractmethod
    def delete(self, filepath: str) -> bool:
        """Delete a file from storage."""
        pass
        
    @abstractmethod
    def clear(self) -> bool:
        """Clear all files from storage."""
        pass
        
    @abstractmethod
    def list_keys(self) -> list[str]:
        """List all file keys in storage."""
        pass