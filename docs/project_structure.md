# Project Structure

This document outlines the folder structure of the Market Data Simulation project and explains the purpose of each component.

## Root Directory
- `README.md`: Main project documentation
- `requirements.txt`: Python dependencies required for the project

## Directories

### `/docs`
Contains all project documentation:
- `project_structure.md`: This file
- `test_strategy.md`: Test strategy and test cases
- `index_data_tasks.md`: Tasks for index data generation
- `option_chain_plan.md`: Plan for option chain integration
- `design_patterns.md`: Design patterns used in the project
- `data_storage.md`: Data storage strategy
- `project_roadmap.md`: Implementation roadmap

### `/src`
Contains all source code for the project:

#### `/src/models`
Contains mathematical models for market simulation:
- `base_model.py`: Abstract base class for all models
- `gbm.py`: Geometric Brownian Motion implementation
- `jump_diffusion.py`: Jump-Diffusion model implementation
- `regime_switching.py`: Regime-switching model
- `black_scholes.py`: Black-Scholes model for options pricing
- `monte_carlo.py`: Monte Carlo methods for options simulation

#### `/src/data_generation`
Contains data generation logic:
- `index_generator.py`: Generator for index price data
- `option_chain_generator.py`: Generator for option chain data

#### `/src/storage`
Contains storage-related functionality:
- `storage_factory.py`: Factory pattern implementation for storage backends
- `local_storage.py`: Local file system storage implementation
- `cloud_storage.py`: Google Cloud Storage implementation

#### `/src/utils`
Contains utility functions:
- `config_loader.py`: Configuration loading utilities

### `/tests`
Contains all test files:

#### `/tests/unit`
Unit tests for individual components:
- `test_models.py`: Tests for mathematical models
- `test_data_generation.py`: Tests for data generation components
- `test_storage.py`: Tests for storage components

#### `/tests/integration`
Integration tests for combined functionality:
- `test_index_simulation.py`: Tests for full index simulation
- `test_option_chain.py`: Tests for option chain generation

### `/config`
Contains configuration files:
- `default_params.json`: Default simulation parameters
- `env_config.json`: Environment-specific configuration (local/cloud)

## Key Design Principles
1. **Modularity**: Each component has a single responsibility
2. **Extensibility**: New models can be easily added by extending base classes
3. **Configurability**: All parameters can be configured externally
4. **Testability**: Components are designed for easy testing
5. **Interoperability**: Components work together through well-defined interfaces
