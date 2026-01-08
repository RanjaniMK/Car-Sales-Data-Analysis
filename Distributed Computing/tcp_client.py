# tcp_client.py - TCP Client for sending car sales data

import socket
import json
import time
import random
from datetime import datetime, timedelta
import config

class CarSalesClient:
    def __init__(self, host=config.TCP_HOST, port=config.TCP_PORT):
        self.host = host
        self.port = port
        
    def send_data(self, sales_record):
        """Send a single sales record to server"""
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((self.host, self.port))
            
            # Send JSON data
            message = json.dumps(sales_record)
            client_socket.send(message.encode('utf-8'))
            
            # Receive acknowledgment
            response = client_socket.recv(config.BUFFER_SIZE)
            ack = json.loads(response.decode('utf-8'))
            
            client_socket.close()
            return ack
            
        except Exception as e:
            print(f"[CLIENT ERROR] {e}")
            return None
            
    def generate_sample_data(self):
        """Generate sample car sales data"""
        car_models = ['Sedan', 'SUV', 'Hatchback', 'Coupe', 'Truck', 'Van']
        regions = ['North', 'South', 'East', 'West', 'Central']
        
        return {
            'date': (datetime.now() - timedelta(days=random.randint(0, 365))).strftime('%Y-%m-%d'),
            'car_model': random.choice(car_models),
            'region': random.choice(regions),
            'sales': random.randint(50, 500),
            'price': round(random.uniform(20000, 80000), 2),
            'units_sold': random.randint(1, 20),
            'dealer_id': f"D{random.randint(1000, 9999)}"
        }
        
    def simulate_stream(self, num_records=100, delay=0.1):
        """Simulate streaming car sales data"""
        print(f"[CLIENT] Sending {num_records} records to {self.host}:{self.port}")
        
        for i in range(num_records):
            sales_data = self.generate_sample_data()
            ack = self.send_data(sales_data)
            
            if ack:
                print(f"[CLIENT] Sent record {i+1}/{num_records} - Status: {ack['status']}")
            else:
                print(f"[CLIENT] Failed to send record {i+1}")
                
            time.sleep(delay)
            
        print("[CLIENT] Data streaming complete")

if __name__ == "__main__":
    client = CarSalesClient()
    
    # Simulate sending 1000 records
    client.simulate_stream(num_records=1000, delay=0.05)
