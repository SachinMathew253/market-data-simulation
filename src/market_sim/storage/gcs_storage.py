from typing import Any, Dict, Union
import pandas as pd
from google.cloud import storage
from .storage_interface import StorageInterface


class GCSStorage(StorageInterface):
    """Google Cloud Storage implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize GCS storage with config"""
        super().__init__(config)
        self.client = storage.Client()
        self.base_path = "MASTER/NIFTY50/simulated"
        self.bucket_name = self._config.get("gcs_bucket", "quant_research_data_test")

    def save(self, filepath: str, data: Union[pd.DataFrame, Any]) -> str:
        """Save data to GCS bucket"""
        bucket = self.client.bucket(self.bucket_name)
        
        # Construct full path
        full_path = f"{self.base_path}/{filepath}"
        
        # Create a blob and upload the file
        blob = bucket.blob(full_path)
        if isinstance(data, pd.DataFrame):
            blob.upload_from_string(data.to_pickle(index=True))
        else:
            blob.upload_from_string(str(data))
        
        return full_path

    def load(self, filepath: str) -> Union[pd.DataFrame, Any]:
        """Load data from GCS bucket"""
        bucket = self.client.bucket(self.bucket_name)
        
        # Construct full path
        full_path = f"{self.base_path}/{filepath}"
        
        # Get the blob and download
        blob = bucket.blob(full_path)
        content = blob.download_as_string()
        
        if filepath.endswith('.csv'):
            return pd.read_csv(content)
        return content

    def exists(self, filepath: str) -> bool:
        """Check if file exists in storage"""
        bucket = self.client.bucket(self.bucket_name)
        full_path = f"{self.base_path}/{filepath}"
        blob = bucket.blob(full_path)
        return blob.exists()

    def list_files(self, directory: str = "") -> list[str]:
        """List files in directory"""
        bucket = self.client.bucket(self.bucket_name)
        prefix = f"{self.base_path}/{directory}".rstrip("/") + "/"
        blobs = bucket.list_blobs(prefix=prefix)
        return [blob.name.replace(prefix, "") for blob in blobs]

    def delete(self, filepath: str) -> bool:
        """Delete a file from storage"""
        bucket = self.client.bucket(self.bucket_name)
        full_path = f"{self.base_path}/{filepath}"
        blob = bucket.blob(full_path)
        if blob.exists():
            blob.delete()
            return True
        return False

    def clear(self) -> bool:
        """Clear all files from storage"""
        bucket = self.client.bucket(self.bucket_name)
        blobs = bucket.list_blobs(prefix=self.base_path)
        for blob in blobs:
            blob.delete()
        return True

    def list_keys(self) -> list[str]:
        """List all file keys in storage"""
        bucket = self.client.bucket(self.bucket_name)
        blobs = bucket.list_blobs(prefix=self.base_path)
        return [blob.name.replace(f"{self.base_path}/", "") for blob in blobs]