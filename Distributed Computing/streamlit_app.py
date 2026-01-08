# streamlit_app.py - Real-time Car Sales Dashboard

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import json
import os
import config
from time_series_analyzer import TimeSeriesAnalyzer
from distributed_worker import DistributedProcessor

# Page configuration
st.set_page_config(
    page_title="Car Sales Analytics Dashboard",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .stProgress > div > div > div > div {
        background-color: #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()
if 'processor' not in st.session_state:
    st.session_state.processor = None
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = True

# Title and header
st.title("🚗 Real-Time Car Sales Analytics Dashboard")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Data source
    data_source = st.selectbox(
        "Data Source",
        ["TCP Stream", "Upload File", "Sample Data"]
    )
    
    # Auto-refresh toggle
    auto_refresh = st.checkbox("Auto Refresh", value=True)
    st.session_state.auto_refresh = auto_refresh
    
    if auto_refresh:
        refresh_interval = st.slider("Refresh Interval (seconds)", 1, 10, 2)
    
    # Distributed computing
    st.subheader("Distributed Computing")
    use_distributed = st.checkbox("Enable Dask Cluster", value=False)
    
    if use_distributed:
        num_workers = st.slider("Number of Workers", 1, 8, 4)
        if st.button("Start Cluster"):
            with st.spinner("Starting Dask cluster..."):
                st.session_state.processor = DistributedProcessor()
                if st.session_state.processor.start_cluster(num_workers):
                    st.success(f"Cluster started with {num_workers} workers")
                    st.info(f"Dashboard: {st.session_state.processor.client.dashboard_link}")
    
    st.markdown("---")
    st.subheader("📊 Analysis Options")
    show_forecast = st.checkbox("Show Forecast", value=True)
    show_anomalies = st.checkbox("Show Anomalies", value=True)
    show_seasonality = st.checkbox("Show Seasonality", value=False)

def load_data():
    """Load data from configured source"""
    try:
        if os.path.exists(config.DATA_QUEUE_FILE):
            df = pd.read_csv(config.DATA_QUEUE_FILE)
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            return df
        else:
            # Generate sample data if file doesn't exist
            return generate_sample_data()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return generate_sample_data()

def generate_sample_data():
    """Generate sample car sales data"""
    import random
    
    dates = pd.date_range(end=datetime.now(), periods=365, freq='D')
    car_models = ['Sedan', 'SUV', 'Hatchback', 'Coupe', 'Truck', 'Van']
    regions = ['North', 'South', 'East', 'West', 'Central']
    
    data = []
    for date in dates:
        for _ in range(random.randint(5, 15)):
            data.append({
                'date': date,
                'car_model': random.choice(car_models),
                'region': random.choice(regions),
                'sales': random.randint(50, 500),
                'price': round(random.uniform(20000, 80000), 2),
                'units_sold': random.randint(1, 20),
                'dealer_id': f"D{random.randint(1000, 9999)}"
            })
    
    return pd.DataFrame(data)

def create_sales_trend_chart(df):
    """Create sales trend chart"""
    daily_sales = df.groupby('date')['sales'].sum().reset_index()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily_sales['date'],
        y=daily_sales['sales'],
        mode='lines',
        name='Daily Sales',
        line=dict(color='#1f77b4', width=2)
    ))
    
    # Add 7-day moving average
    daily_sales['MA7'] = daily_sales['sales'].rolling(window=7).mean()
    fig.add_trace(go.Scatter(
        x=daily_sales['date'],
        y=daily_sales['MA7'],
        mode='lines',
        name='7-Day MA',
        line=dict(color='#ff7f0e', width=2, dash='dash')
    ))
    
    fig.update_layout(
        title="Sales Trend Over Time",
        xaxis_title="Date",
        yaxis_title="Sales ($)",
        hovermode='x unified',
        height=400
    )
    
    return fig

def create_forecast_chart(analyzer, df):
    """Create forecast chart"""
    forecast_df = analyzer.forecast_sales(30)
    
    if forecast_df is None:
        return None
    
    # Historical data
    daily_sales = df.groupby('date')['sales'].sum().reset_index()
    
    fig = go.Figure()
    
    # Historical
    fig.add_trace(go.Scatter(
        x=daily_sales['date'],
        y=daily_sales['sales'],
        mode='lines',
        name='Historical',
        line=dict(color='#1f77b4', width=2)
    ))
    
    # Forecast
    fig.add_trace(go.Scatter(
        x=forecast_df['date'],
        y=forecast_df['forecast'],
        mode='lines',
        name='Forecast',
        line=dict(color='#2ca02c', width=2, dash='dot')
    ))
    
    fig.update_layout(
        title="Sales Forecast (30 Days)",
        xaxis_title="Date",
        yaxis_title="Sales ($)",
        hovermode='x unified',
        height=400
    )
    
    return fig

def create_model_distribution(df):
    """Create car model distribution chart"""
    model_sales = df.groupby('car_model')['sales'].sum().reset_index()
    
    fig = px.pie(
        model_sales,
        values='sales',
        names='car_model',
        title="Sales by Car Model",
        hole=0.4
    )
    
    fig.update_layout(height=400)
    return fig

def create_region_heatmap(df):
    """Create regional sales heatmap"""
    region_model = df.groupby(['region', 'car_model'])['sales'].sum().reset_index()
    pivot = region_model.pivot(index='region', columns='car_model', values='sales')
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns,
        y=pivot.index,
        colorscale='Blues',
        text=pivot.values,
        texttemplate='%{text:.0f}',
        textfont={"size": 10}
    ))
    
    fig.update_layout(
        title="Sales Heatmap: Region vs Car Model",
        xaxis_title="Car Model",
        yaxis_title="Region",
        height=400
    )
    
    return fig

# Main dashboard
def main():
    # Load data
    df = load_data()
    
    if df is not None and len(df) > 0:
        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_sales = df['sales'].sum()
            st.metric("Total Sales", f"${total_sales:,.0f}", 
                     delta=f"{(total_sales/1000000):.1f}M")
        
        with col2:
            avg_price = df['price'].mean()
            st.metric("Avg Price", f"${avg_price:,.0f}")
        
        with col3:
            total_units = df['units_sold'].sum()
            st.metric("Total Units Sold", f"{total_units:,}")
        
        with col4:
            unique_dealers = df['dealer_id'].nunique()
            st.metric("Active Dealers", f"{unique_dealers}")
        
        st.markdown("---")
        
        # Time series analysis
        analyzer = TimeSeriesAnalyzer()
        analyzer.load_data(df)
        
        # Charts row 1
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(create_sales_trend_chart(df), use_container_width=True)
        
        with col2:
            if show_forecast:
                forecast_chart = create_forecast_chart(analyzer, df)
                if forecast_chart:
                    st.plotly_chart(forecast_chart, use_container_width=True)
            else:
                st.plotly_chart(create_model_distribution(df), use_container_width=True)
        
        # Charts row 2
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(create_model_distribution(df), use_container_width=True)
        
        with col2:
            st.plotly_chart(create_region_heatmap(df), use_container_width=True)
        
        # Anomaly detection
        if show_anomalies:
            st.subheader("🔍 Anomaly Detection")
            anomalies = analyzer.detect_anomalies(threshold=2.5)
            
            if anomalies is not None and len(anomalies) > 0:
                st.dataframe(anomalies.head(10), use_container_width=True)
            else:
                st.info("No anomalies detected")
        
        # Recent data table
        st.subheader("📋 Recent Transactions")
        st.dataframe(df.sort_values('date', ascending=False).head(20), use_container_width=True)
        
        # Last update time
        st.session_state.last_update = datetime.now()
        st.caption(f"Last updated: {st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S')}")
        
    else:
        st.warning("No data available. Start the TCP server and send data.")
        st.info("Run `python tcp_server.py` and `python tcp_client.py` to begin streaming data.")

# Auto-refresh
if st.session_state.auto_refresh:
    time.sleep(refresh_interval if 'refresh_interval' in locals() else 2)
    st.rerun()
else:
    if st.button("🔄 Refresh Data"):
        st.rerun()

# Run main
main()
