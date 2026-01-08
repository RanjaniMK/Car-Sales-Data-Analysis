# time_series_analyzer.py - Time Series Analysis for Car Sales

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.arima.model import ARIMA
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')
import config

class TimeSeriesAnalyzer:
    def __init__(self, data_path=None):
        self.data_path = data_path
        self.df = None
        self.results = {}
        
    def load_data(self, df=None):
        """Load data from file or DataFrame"""
        if df is not None:
            self.df = df
        elif self.data_path:
            try:
                if self.data_path.endswith('.parquet'):
                    self.df = pd.read_parquet(self.data_path)
                else:
                    self.df = pd.read_csv(self.data_path)
            except Exception as e:
                print(f"[ERROR] Loading data: {e}")
                return False
                
        if self.df is not None and 'date' in self.df.columns:
            self.df['date'] = pd.to_datetime(self.df['date'])
            self.df = self.df.sort_values('date')
            return True
        return False
        
    def aggregate_daily_sales(self):
        """Aggregate sales by date"""
        if self.df is None:
            return None
            
        daily_sales = self.df.groupby('date').agg({
            'sales': 'sum',
            'units_sold': 'sum',
            'price': 'mean'
        }).reset_index()
        
        return daily_sales
        
    def calculate_moving_averages(self, window=7):
        """Calculate moving averages"""
        daily_sales = self.aggregate_daily_sales()
        if daily_sales is None:
            return None
            
        daily_sales[f'MA_{window}'] = daily_sales['sales'].rolling(window=window).mean()
        daily_sales[f'MA_{window*2}'] = daily_sales['sales'].rolling(window=window*2).mean()
        
        return daily_sales
        
    def detect_seasonality(self):
        """Detect seasonal patterns"""
        daily_sales = self.aggregate_daily_sales()
        if daily_sales is None or len(daily_sales) < 14:
            return None
            
        try:
            # Ensure we have enough data points
            if len(daily_sales) >= 14:
                decomposition = seasonal_decompose(
                    daily_sales['sales'].fillna(method='ffill'),
                    model='additive',
                    period=min(7, len(daily_sales) // 2)
                )
                
                return {
                    'trend': decomposition.trend.dropna().tolist(),
                    'seasonal': decomposition.seasonal.dropna().tolist(),
                    'residual': decomposition.resid.dropna().tolist()
                }
        except Exception as e:
            print(f"[WARNING] Seasonality detection: {e}")
            return None
            
    def forecast_sales(self, periods=30):
        """Forecast future sales using ARIMA"""
        daily_sales = self.aggregate_daily_sales()
        if daily_sales is None or len(daily_sales) < 10:
            return None
            
        try:
            # Prepare data
            ts_data = daily_sales.set_index('date')['sales'].fillna(method='ffill')
            
            # Fit ARIMA model
            model = ARIMA(ts_data, order=(1, 1, 1))
            fitted_model = model.fit()
            
            # Forecast
            forecast = fitted_model.forecast(steps=periods)
            
            # Create forecast dates
            last_date = daily_sales['date'].max()
            forecast_dates = [last_date + timedelta(days=i+1) for i in range(periods)]
            
            forecast_df = pd.DataFrame({
                'date': forecast_dates,
                'forecast': forecast.values
            })
            
            return forecast_df
            
        except Exception as e:
            print(f"[WARNING] Forecasting: {e}")
            return None
            
    def detect_anomalies(self, threshold=3):
        """Detect anomalies using z-score"""
        daily_sales = self.aggregate_daily_sales()
        if daily_sales is None:
            return None
            
        # Calculate z-scores
        daily_sales['z_score'] = np.abs(
            (daily_sales['sales'] - daily_sales['sales'].mean()) / daily_sales['sales'].std()
        )
        
        anomalies = daily_sales[daily_sales['z_score'] > threshold]
        
        return anomalies[['date', 'sales', 'z_score']]
        
    def calculate_growth_metrics(self):
        """Calculate growth rates and trends"""
        daily_sales = self.aggregate_daily_sales()
        if daily_sales is None or len(daily_sales) < 2:
            return None
            
        # Day-over-day growth
        daily_sales['daily_growth'] = daily_sales['sales'].pct_change() * 100
        
        # Week-over-week growth
        if len(daily_sales) >= 7:
            daily_sales['weekly_growth'] = (
                (daily_sales['sales'] - daily_sales['sales'].shift(7)) / 
                daily_sales['sales'].shift(7) * 100
            )
        
        return daily_sales
        
    def run_full_analysis(self):
        """Run complete time series analysis"""
        if not self.load_data():
            return None
            
        self.results = {
            'summary': {
                'total_sales': float(self.df['sales'].sum()),
                'avg_daily_sales': float(self.df.groupby('date')['sales'].sum().mean()),
                'total_units': int(self.df['units_sold'].sum()),
                'date_range': {
                    'start': str(self.df['date'].min()),
                    'end': str(self.df['date'].max())
                }
            },
            'moving_averages': self.calculate_moving_averages(),
            'seasonality': self.detect_seasonality(),
            'forecast': self.forecast_sales(config.FORECAST_PERIODS),
            'anomalies': self.detect_anomalies(),
            'growth_metrics': self.calculate_growth_metrics()
        }
        
        return self.results

if __name__ == "__main__":
    # Test with sample data
    analyzer = TimeSeriesAnalyzer(config.DATA_QUEUE_FILE)
    results = analyzer.run_full_analysis()
    
    if results:
        print("[ANALYSIS] Complete")
        print(f"Total Sales: ${results['summary']['total_sales']:,.2f}")
        print(f"Avg Daily Sales: ${results['summary']['avg_daily_sales']:,.2f}")
