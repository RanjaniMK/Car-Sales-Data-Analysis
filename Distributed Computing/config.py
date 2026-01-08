# config.py - Configuration for the entire system

# TCP/IP Socket Configuration
TCP_HOST = 'localhost'
TCP_PORT = 9999
BUFFER_SIZE = 4096
MAX_CLIENTS = 10

# Dask Distributed Computing Configuration
DASK_SCHEDULER_HOST = 'localhost'
DASK_SCHEDULER_PORT = 8786
NUM_WORKERS = 4

# Streamlit Configuration
STREAMLIT_PORT = 8501
UPDATE_INTERVAL = 2  # seconds

# Data Configuration
DATA_CHUNK_SIZE = 10000  # rows per chunk for big data
TIME_COLUMN = 'date'
VALUE_COLUMN = 'sales'

# Time Series Analysis Parameters
FORECAST_PERIODS = 30  # days to forecast
SEASONALITY_PERIOD = 12  # monthly seasonality
MOVING_AVG_WINDOW = 7  # days

# File Paths
DATA_QUEUE_FILE = 'data/incoming_queue.csv'
PROCESSED_DATA_FILE = 'data/processed_data.parquet'
RESULTS_FILE = 'data/analysis_results.json'
