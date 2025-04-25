# Market Data Simulation API

A FastAPI-based service for simulating market data including index prices and option chains using various mathematical models.

## Features

- Index price simulation using:
  - Geometric Brownian Motion (GBM)
  - Jump Diffusion Model
- Market scenarios:
  - Bullish
  - Bearish
  - Volatile
  - Range-bound
- Option chain generation using Black-Scholes model
- Local or Google Cloud Storage support
- Asynchronous processing with status tracking

## Prerequisites

- Python 3.8+
- pip
- virtualenv (recommended)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd market-data-simulation
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e .
```

4. Create a `.env` file in the project root using `.env.example` as a template.

## Running the Application

1. Start the FastAPI server:
```bash
python run.py
```

The API will be available at http://localhost:8000

2. Access the API documentation:
- OpenAPI UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Usage

### Generate Market Data

```bash
curl -X POST "http://localhost:8000/api/v1/simulate" \
  -H "Content-Type: application/json" \
  -d '{
    "initial_value": 18000,
    "market_type": "BULLISH",
    "volatility": 0.2,
    "time_period_days": 252,
    "include_options": false,
    "storage_type": "LOCAL",
    "output_path": "simulation_result.pkl"
}'
```

### Check Simulation Status

```bash
curl "http://localhost:8000/api/v1/simulate/{simulation_id}/status"
```

## API Reference

### Endpoints

#### Generate Market Simulation
```http
POST /api/v1/simulate
```
Generates market data based on specified parameters.

**Request Body:**
```json
{
    "initial_value": 18000,          // Initial index value
    "market_type": "BULLISH",        // BULLISH, BEARISH, VOLATILE, or RANGE_BOUND
    "volatility": 0.2,               // Volatility parameter (0 to 1)
    "time_period_days": 252,         // Number of trading days to simulate
    "include_options": false,        // Whether to generate option chain data
    "storage_type": "LOCAL",         // LOCAL or GCS
    "output_path": "result.pkl",     // Output file path
    "options_config": {              // Optional, required if include_options is true
        "strike_range_percent": 10,   // Strike price range around current price
        "num_strikes": 10,           // Number of strike prices
        "time_to_expiry_days": 30    // Option expiry period
    }
}
```

**Response:**
```json
{
    "simulation_id": "uuid-string",   // Unique simulation identifier
    "status": "success",             // Status of the simulation
    "storage_path": "result.pkl"     // Path where data is stored
}
```

#### Check Simulation Status
```http
GET /api/v1/simulate/{simulation_id}/status
```
Returns the current status of a simulation.

**Response:**
```json
{
    "simulation_id": "uuid-string",
    "status": "completed",           // running, completed, failed
    "progress": 100.0,              // Progress percentage
    "error_message": null           // Error message if failed
}
```

#### Health Check
```http
GET /health
```
Check API health status.

**Response:**
```json
{
    "status": "healthy"
}
```

## Configuration

Environment variables (in `.env`):

```env
# Storage Configuration
STORAGE_TYPE=LOCAL               # local or gcs
LOCAL_STORAGE_PATH=./data       # Path for local storage

# Model Configuration
DEFAULT_DRIFT=0.05              # Default drift parameter
DEFAULT_VOLATILITY=0.2          # Default volatility
DEFAULT_JUMP_INTENSITY=1.0      # Jump frequency for jump diffusion
DEFAULT_JUMP_MEAN=0.0          # Mean jump size
DEFAULT_JUMP_VOLATILITY=0.2    # Jump size volatility

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

## Testing

Run tests with:
```bash
python -m pytest tests/
```

## Project Structure

```
market-data-simulation/
├── src/market_sim/           # Main package
│   ├── api/                 # FastAPI endpoints
│   ├── models/             # Mathematical models
│   ├── storage/            # Storage implementations
│   └── config/             # Configuration management
├── tests/                   # Test suites
│   ├── integration/        # Integration tests
│   └── unit/              # Unit tests
└── docs/                   # Documentation
```