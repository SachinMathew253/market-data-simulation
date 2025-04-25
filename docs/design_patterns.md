# Design Patterns

This document outlines the key design patterns used in the Market Data Simulation project to ensure extensibility, maintainability, and clean architecture.

## Strategy Pattern

The Strategy pattern is used to define a family of algorithms, encapsulate each one, and make them interchangeable. This pattern is particularly useful for our simulation models.

### Implementation:

```python
# Abstract strategy
class BaseModel(ABC):
    @abstractmethod
    def simulate(self, initial_price, dt, periods, **kwargs):
        pass
        
# Concrete strategies
class GBM(BaseModel):
    def simulate(self, initial_price, dt, periods, **kwargs):
        # GBM-specific implementation
        pass
        
class JumpDiffusion(BaseModel):
    def simulate(self, initial_price, dt, periods, **kwargs):
        # Jump Diffusion-specific implementation
        pass
        
# Context
class IndexDataGenerator:
    def __init__(self, model: BaseModel):
        self._model = model
        
    def set_model(self, model: BaseModel):
        self._model = model
        
    def generate_data(self, timeframe, periods):
        # Use the model's simulate method
        return self._model.simulate(...)
```

**Benefits:**
- Models can be switched at runtime
- New models can be added without changing existing code
- Decouples the data generation logic from specific model implementations

## Factory Pattern

The Factory pattern is used to create objects without exposing the instantiation logic to the client. This pattern is used for creating model instances and storage handlers.

### Implementation:

```python
class ModelFactory:
    @staticmethod
    def get_model(model_type, **params):
        if model_type == 'gbm':
            return GBM(params['mu'], params['sigma'])
        elif model_type == 'jump_diffusion':
            return JumpDiffusion(params['mu'], params['sigma'], params['lambda'], params['jump_mean'], params['jump_std'])
        elif model_type == 'regime_switching':
            return RegimeSwitching(params['regimes'], params['transition_matrix'])
        else:
            raise ValueError(f"Unknown model type: {model_type}")
```

**Benefits:**
- Centralizes object creation
- Makes it easy to switch implementations
- Simplifies adding new model types

## Decorator Pattern

The Decorator pattern is used to dynamically add behaviors to objects without changing their interface. This is useful for adding features like logging, caching, or additional functionality to models.

### Implementation:

```python
class ModelDecorator(BaseModel):
    def __init__(self, model: BaseModel):
        self._model = model
        
    def simulate(self, initial_price, dt, periods, **kwargs):
        return self._model.simulate(initial_price, dt, periods, **kwargs)
        
class JumpComponentDecorator(ModelDecorator):
    def __init__(self, model: BaseModel, lambda_jump, mu_jump, sigma_jump):
        super().__init__(model)
        self.lambda_jump = lambda_jump
        self.mu_jump = mu_jump
        self.sigma_jump = sigma_jump
        
    def simulate(self, initial_price, dt, periods, **kwargs):
        # Get base simulation
        prices = super().simulate(initial_price, dt, periods, **kwargs)
        
        # Add jumps
        for t in range(1, periods + 1):
            if np.random.uniform() < self.lambda_jump * dt:
                jump_multiplier = np.exp(np.random.normal(self.mu_jump, self.sigma_jump))
                prices[t] *= jump_multiplier
                
        return prices
```

**Benefits:**
- Allows adding functionality to models dynamically
- Supports the open/closed principle
- Creates a flexible composition of behaviors

## Template Method Pattern

The Template Method pattern defines the skeleton of an algorithm, deferring some steps to subclasses. This is useful for defining the general structure of simulation algorithms while allowing specific implementations to vary.

### Implementation:

```python
class BaseOptionModel(ABC):
    def price_option(self, S, K, T, sigma, option_type='call'):
        """Template method for option pricing"""
        # Common pre-processing
        if T <= 0:
            return self._calculate_intrinsic_value(S, K, option_type)
            
        # Delegate to specific pricing logic
        if option_type == 'call':
            price = self._price_call(S, K, T, sigma)
        elif option_type == 'put':
            price = self._price_put(S, K, T, sigma)
        else:
            raise ValueError(f"Unknown option type: {option_type}")
            
        # Common post-processing
        return max(0, price)  # Options can't have negative values
        
    @abstractmethod
    def _price_call(self, S, K, T, sigma):
        """Calculate call option price"""
        pass
        
    @abstractmethod
    def _price_put(self, S, K, T, sigma):
        """Calculate put option price"""
        pass
        
    def _calculate_intrinsic_value(self, S, K, option_type):
        """Calculate option's intrinsic value at expiry"""
        if option_type == 'call':
            return max(0, S - K)
        else:  # put
            return max(0, K - S)
```

**Benefits:**
- Enforces a standard algorithm structure
- Allows subclasses to override only specific steps
- Reduces code duplication

## Observer Pattern

The Observer pattern is used to notify objects about changes in other objects. This is useful for updating visualizations or triggering actions when simulation data changes.

### Implementation:

```python
class Subject(ABC):
    def __init__(self):
        self._observers = []
        
    def attach(self, observer):
        if observer not in self._observers:
            self._observers.append(observer)
            
    def detach(self, observer):
        self._observers.remove(observer)
        
    def notify(self, *args, **kwargs):
        for observer in self._observers:
            observer.update(self, *args, **kwargs)
            
class SimulationMonitor(Subject):
    def __init__(self):
        super().__init__()
        self._current_price = None
        self._regime = None
        
    def update_state(self, price, regime):
        self._current_price = price
        self._regime = regime
        self.notify()
        
class Observer(ABC):
    @abstractmethod
    def update(self, subject, *args, **kwargs):
        pass
        
class VisualizationObserver(Observer):
    def update(self, subject, *args, **kwargs):
        # Update visualization with new data
        pass
```

**Benefits:**
- Decouples simulation from visualization
- Supports multiple observers
- Enables real-time monitoring of simulations

## Singleton Pattern

The Singleton pattern ensures a class has only one instance and provides a global point of access to it. This is useful for configuration managers and logging systems.

### Implementation:

```python
class ConfigManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
        
    def _load_config(self):
        # Load configuration from files
        self.config = {}
        
    def get_param(self, name, default=None):
        return self.config.get(name, default)
```

**Benefits:**
- Ensures a single configuration source
- Provides global access
- Lazy initialization of resources

## Adapter Pattern

The Adapter pattern allows classes with incompatible interfaces to work together. This is useful when integrating with external libraries or APIs.

### Implementation:

```python
class GoogleCloudStorageAdapter:
    def __init__(self, bucket_name):
        from google.cloud import storage
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)
        
    def save(self, data, filename):
        """Save data to Google Cloud Storage using our common interface"""
        blob = self.bucket.blob(filename)
        pickle_data = pickle.dumps(data)
        blob.upload_from_string(pickle_data)
        
    def load(self, filename):
        """Load data from Google Cloud Storage using our common interface"""
        blob = self.bucket.blob(filename)
        pickle_data = blob.download_as_string()
        return pickle.loads(pickle_data)
```

**Benefits:**
- Integrates external systems without changing their code
- Provides a consistent interface
- Encapsulates the complexity of external APIs

## Command Pattern

The Command pattern encapsulates a request as an object, allowing for parameterization of clients with different requests, queuing of requests, and logging of the requests. This is useful for simulation controls and batch processing.

### Implementation:

```python
class SimulationCommand(ABC):
    @abstractmethod
    def execute(self):
        pass
        
    @abstractmethod
    def undo(self):
        pass
        
class GenerateIndexDataCommand(SimulationCommand):
    def __init__(self, generator, params, output_file):
        self.generator = generator
        self.params = params
        self.output_file = output_file
        self.result = None
        
    def execute(self):
        self.result = self.generator.generate_data(**self.params)
        # Save result to file
        return self.result
        
    def undo(self):
        # Delete generated file
        if os.path.exists(self.output_file):
            os.remove(self.output_file)
```

**Benefits:**
- Decouples the execution of a command from its implementation
- Supports undo operations
- Allows for batching and scheduling of operations
