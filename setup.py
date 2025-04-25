from setuptools import setup, find_packages

setup(
    name="market_sim",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "scipy>=1.10.0",
        "python-dotenv>=1.0.0",
        "matplotlib>=3.8.0",
        "mplfinance>=0.12.10b0",
        "fastapi>=0.110.0",
        "uvicorn>=0.29.0"
    ],
)