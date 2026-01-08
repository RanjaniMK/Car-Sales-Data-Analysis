# distributed_worker.py - Distributed Computing with Dask

import dask
import dask.dataframe as dd
from dask.distributed import Client, LocalCluster
import pandas as pd
import config
from time_series_analyzer import TimeSeriesAnalyzer

class DistributedProcessor:
    def __init__(self):
        self.client = None
        self.cluster = None
        
    def start_cluster(self, n_workers=config.NUM_WORKERS):
        """Start Dask local cluster"""
        try:
            self.cluster = LocalCluster(
                n_workers=n_workers,
                threads_per_worker=2,
                memory_limit='2GB'
            )
            self.client = Client(self.cluster)
            print(f"[DASK] Cluster started with {n_workers} workers")
            print(f"[DASK] Dashboard: {self.client.dashboard_link}")
            return True
        except Exception as e:
            print(f"[DASK ERROR] {e}")
            return False
            
    def load_large_dataset(self, file_path, chunksize=config.DATA_CHUNK_SIZE):
        """Load large CSV as Dask DataFrame"""
        try:
            # Read as Dask DataFrame for distributed processing
            ddf = dd.read_csv(
                file_path,
                parse_dates=['date'],
                blocksize=f'{chunksize} rows'
            )
            print(f"[DASK] Loaded dataset with {ddf.npartitions} partitions")
            return ddf
        except Exception as e:
            print(f"[DASK ERROR] Loading data: {e}")
            return None
            
    def distributed_aggregation(self, ddf):
        """Perform distributed aggregation"""
        try:
            # Group by date and aggregate
            daily_agg = ddf.groupby('date').agg({
                'sales': ['sum', 'mean', 'count'],
                'units_sold': 'sum',
                'price': 'mean'
            }).compute()
            
            print("[DASK] Aggregation complete")
            return daily_agg
        except Exception as e:
            print(f"[DASK ERROR] Aggregation: {e}")
            return None
            
    def distributed_time_series_analysis(self, ddf):
        """Distribute time series analysis across workers"""
        try:
            # Convert to pandas for analysis (after aggregation)
            df = ddf.compute()
            
            # Partition by car model for parallel analysis
            models = df['car_model'].unique()
            
            futures = []
            for model in models:
                model_data = df[df['car_model'] == model]
                
                # Submit analysis task to cluster
                future = self.client.submit(
                    self.analyze_model_sales,
                    model_data,
                    model
                )
                futures.append(future)
                
            # Gather results
            results = self.client.gather(futures)
            
            print(f"[DASK] Analyzed {len(results)} car models")
            return results
            
        except Exception as e:
            print(f"[DASK ERROR] Time series analysis: {e}")
            return None
            
    @staticmethod
    def analyze_model_sales(model_data, model_name):
        """Analyze sales for a specific car model"""
        analyzer = TimeSeriesAnalyzer()
        analyzer.load_data(model_data)
        
        results = {
            'model': model_name,
            'total_sales': float(model_data['sales'].sum()),
            'avg_price': float(model_data['price'].mean()),
            'total_units': int(model_data['units_sold'].sum()),
            'forecast': None
        }
        
        # Try to forecast if enough data
        try:
            forecast = analyzer.forecast_sales(periods=7)
            if forecast is not None:
                results['forecast'] = forecast.to_dict('records')
        except:
            pass
            
        return results
        
    def process_streaming_data(self, file_path):
        """Process data in streaming fashion"""
        try:
            # Read in chunks
            chunks = pd.read_csv(file_path, chunksize=config.DATA_CHUNK_SIZE)
            
            results = []
            for i, chunk in enumerate(chunks):
                # Submit chunk processing to cluster
                future = self.client.submit(self.process_chunk, chunk, i)
                results.append(future)
                
            # Gather all results
            processed = self.client.gather(results)
            
            # Combine results
            combined = pd.concat(processed, ignore_index=True)
            print(f"[DASK] Processed {len(combined)} records in streaming mode")
            
            return combined
            
        except Exception as e:
            print(f"[DASK ERROR] Streaming: {e}")
            return None
            
    @staticmethod
    def process_chunk(chunk, chunk_id):
        """Process a single chunk of data"""
        # Add derived features
        chunk['revenue'] = chunk['sales'] * chunk['units_sold']
        chunk['chunk_id'] = chunk_id
        
        # Aggregate by date
        daily = chunk.groupby('date').agg({
            'sales': 'sum',
            'revenue': 'sum',
            'units_sold': 'sum'
        }).reset_index()
        
        return daily
        
    def stop_cluster(self):
        """Stop Dask cluster"""
        if self.client:
            self.client.close()
        if self.cluster:
            self.cluster.close()
        print("[DASK] Cluster stopped")

if __name__ == "__main__":
    # Test distributed processing
    processor = DistributedProcessor()
    
    if processor.start_cluster():
        # Load and process data
        ddf = processor.load_large_dataset(config.DATA_QUEUE_FILE)
        
        if ddf is not None:
            # Run distributed aggregation
            results = processor.distributed_aggregation(ddf)
            
            # Run distributed time series analysis
            model_results = processor.distributed_time_series_analysis(ddf)
            
            print("[DASK] Processing complete")
            
        processor.stop_cluster()
