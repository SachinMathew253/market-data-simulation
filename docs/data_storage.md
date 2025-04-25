# Data Storage Strategy

This document outlines the strategy for storing and retrieving generated market data in the Market Data Simulation project.

## Overview

The project requires a flexible storage mechanism that can:
1. Save generated data in pickle (.pkl) format
2. Support both local filesystem storage and Google Cloud Storage
3. Be configurable via environment variables or configuration files
4. Maintain data integrity and versioning

## Data Formats

### Index Data Structure

Index data will be stored as pandas DataFrames with the following structure:

```
DataFrame with columns:
- Open: Opening price for the period
- High: Highest price during the period
- Low: Lowest price during the period
- Close: Closing price for the period
- Volume: (Optional) Trading volume
- Metadata: Additional simulation parameters
```

### Option Chain Data Structure

Option chain data will be stored as a pandas DataFrame with the following structure:

```
DataFrame with columns:
- Strike: Strike price
- ExpiryDate: Option expiration date
- CallPrice: Price of call option
- PutPrice: Price of put option
- CallIV: Implied volatility for call
- PutIV: Implied volatility for put
- CallDelta, CallGamma, etc.: Option Greeks
- PutDelta, PutGamma, etc.: Option Greeks
- Metadata: Additional simulation parameters
```

## Storage Implementation

### 1. Storage Factory

We'll implement a factory pattern to abstract storage backend selection.

```python
class StorageFactory:
    @staticmethod
    def get_storage(storage_type, **kwargs):
        if storage_type.lower() == "local":
            return LocalStorage(**kwargs)
        elif storage_type.lower() == "gcs":
            return GoogleCloudStorage(**kwargs)
        else:
            raise ValueError(f"Unsupported storage type: {storage_type}")
```

### 2. Storage Interface

A common interface will be defined for all storage implementations.

```python
class BaseStorage(ABC):
    @abstractmethod
    def save(self, data, filepath):
        """Save data to the specified location"""
        pass
        
    @abstractmethod
    def load(self, filepath):
        """Load data from the specified location"""
        pass
        
    @abstractmethod
    def exists(self, filepath):
        """Check if file exists at the specified location"""
        pass
        
    @abstractmethod
    def list_files(self, directory, pattern=None):
        """List files in the directory matching the pattern"""
        pass
```

### 3. Local Storage Implementation

Implementation for storing data on the local filesystem.

```python
class LocalStorage(BaseStorage):
    def __init__(self, base_path=None):
        self.base_path = base_path or os.getenv('LOCAL_STORAGE_PATH', './data')
        os.makedirs(self.base_path, exist_ok=True)
        
    def save(self, data, filepath):
        full_path = os.path.join(self.base_path, filepath)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, 'wb') as f:
            pickle.dump(data, f)
            
        return full_path
        
    def load(self, filepath):
        full_path = os.path.join(self.base_path, filepath)
        
        with open(full_path, 'rb') as f:
            data = pickle.load(f)
            
        return data
        
    def exists(self, filepath):
        full_path = os.path.join(self.base_path, filepath)
        return os.path.exists(full_path)
        
    def list_files(self, directory='', pattern=None):
        full_dir = os.path.join(self.base_path, directory)
        
        if not os.path.exists(full_dir):
            return []
            
        files = os.listdir(full_dir)
        
        if pattern:
            import re
            pattern_compiled = re.compile(pattern)
            files = [f for f in files if pattern_compiled.match(f)]
            
        return files
```

### 4. Google Cloud Storage Implementation

Implementation for storing data in Google Cloud Storage.

```python
class GoogleCloudStorage(BaseStorage):
    def __init__(self, bucket_name=None):
        from google.cloud import storage
        
        self.bucket_name = bucket_name or os.getenv('GCS_BUCKET_NAME')
        if not self.bucket_name:
            raise ValueError("Google Cloud Storage bucket name must be provided")
            
        self.client = storage.Client()
        self.bucket = self.client.bucket(self.bucket_name)
        
    def save(self, data, filepath):
        blob = self.bucket.blob(filepath)
        
        with tempfile.NamedTemporaryFile() as temp:
            pickle.dump(data, temp)
            temp.flush()
            temp.seek(0)
            blob.upload_from_file(temp)
            
        return f"gs://{self.bucket_name}/{filepath}"
        
    def load(self, filepath):
        blob = self.bucket.blob(filepath)
        
        with tempfile.NamedTemporaryFile() as temp:
            blob.download_to_file(temp)
            temp.flush()
            temp.seek(0)
            data = pickle.load(temp)
            
        return data
        
    def exists(self, filepath):
        blob = self.bucket.blob(filepath)
        return blob.exists()
        
    def list_files(self, directory='', pattern=None):
        prefix = directory
        if prefix and not prefix.endswith('/'):
            prefix += '/'
            
        blobs = self.client.list_blobs(self.bucket_name, prefix=prefix)
        files = [blob.name.replace(prefix, '') for blob in blobs 
                 if blob.name != prefix]
                 
        if pattern:
            import re
            pattern_compiled = re.compile(pattern)
            files = [f for f in files if pattern_compiled.match(f)]
            
        return files
```

## Configuration

Storage configuration will be managed through environment variables and/or configuration files.

### Environment Variables

```
# Local Storage
LOCAL_STORAGE_PATH=/path/to/local/storage

# Google Cloud Storage
GCS_BUCKET_NAME=my-simulation-bucket
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

### Configuration File

```json
{
  "storage": {
    "type": "gcs",
    "local": {
      "base_path": "/path/to/local/storage"
    },
    "gcs": {
      "bucket_name": "my-simulation-bucket"
    }
  }
}
```

## File Naming Convention

To maintain organization and enable easy searching, we'll use the following naming convention:

```
{data_type}/{market_type}/{model_type}/{timestamp}_{additional_params}.pkl
```

Examples:
- `index/nifty/gbm/20230901_123045_bullish_high_vol.pkl`
- `option_chain/nifty/black_scholes/20230901_123045_weekly_expiry.pkl`

## Data Versioning

To support versioning:

1. Include metadata in each saved data file
   ```python
   data.attrs['version'] = '1.0'
   data.attrs['created_at'] = datetime.now().isoformat()
   data.attrs['model_params'] = json.dumps(model_params)
   ```

2. Use version-specific directories if major changes to data structure occur
   ```
   v1/index/nifty/...
   v2/index/nifty/...
   ```

## Error Handling

The storage implementations will include comprehensive error handling:

```python
def save(self, data, filepath):
    try:
        # Save implementation
        pass
    except Exception as e:
        logger.error(f"Failed to save data to {filepath}: {str(e)}")
        raise StorageError(f"Save operation failed: {str(e)}")
```

## Usage Examples

### Saving Data

```python
# Initialize storage based on configuration
config = ConfigManager().get_config()
storage_type = config['storage']['type']
storage = StorageFactory.get_storage(storage_type)

# Generate data
generator = IndexDataGenerator(...)
index_data = generator.generate_data(...)

# Save data with appropriate naming
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
filepath = f"index/nifty/gbm/{timestamp}_bullish.pkl"
storage.save(index_data, filepath)
```

### Loading Data

```python
# Initialize storage based on configuration
storage = StorageFactory.get_storage(config['storage']['type'])

# Load specific file
filepath = "index/nifty/gbm/20230901_123045_bullish.pkl"
index_data = storage.load(filepath)

# Or find the most recent file matching a pattern
files = storage.list_files("index/nifty/gbm/", pattern=r".*bullish\.pkl$")
if files:
    latest_file = sorted(files)[-1]
    index_data = storage.load(f"index/nifty/gbm/{latest_file}")
```
