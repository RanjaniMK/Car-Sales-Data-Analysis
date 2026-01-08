# tcp_server.py - Multi-threaded TCP Server for receiving car sales data

import socket
import threading
import json
import pandas as pd
from datetime import datetime
import queue
import config

# Thread-safe queue for incoming data
data_queue = queue.Queue()

class CarSalesServer:
    def __init__(self, host=config.TCP_HOST, port=config.TCP_PORT):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        
    def start(self):
        """Start the TCP server"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(config.MAX_CLIENTS)
        self.running = True
        
        print(f"[SERVER] Listening on {self.host}:{self.port}")
        
        # Start data processing thread
        processor_thread = threading.Thread(target=self.process_data_queue)
        processor_thread.daemon = True
        processor_thread.start()
        
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                print(f"[SERVER] Connection from {address}")
                
                # Handle client in separate thread
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address)
                )
                client_thread.start()
            except Exception as e:
                print(f"[SERVER] Error: {e}")
                
    def handle_client(self, client_socket, address):
        """Handle individual client connections"""
        try:
            while True:
                data = client_socket.recv(config.BUFFER_SIZE)
                if not data:
                    break
                    
                # Decode and parse JSON data
                message = data.decode('utf-8')
                sales_data = json.loads(message)
                
                # Add to processing queue
                data_queue.put(sales_data)
                
                # Send acknowledgment
                ack = json.dumps({"status": "received", "timestamp": str(datetime.now())})
                client_socket.send(ack.encode('utf-8'))
                
        except Exception as e:
            print(f"[CLIENT ERROR] {address}: {e}")
        finally:
            client_socket.close()
            print(f"[SERVER] Connection closed: {address}")
            
    def process_data_queue(self):
        """Process incoming data from queue and save to file"""
        batch = []
        while True:
            try:
                # Get data from queue
                sales_data = data_queue.get(timeout=1)
                batch.append(sales_data)
                
                # Save batch every 100 records
                if len(batch) >= 100:
                    self.save_batch(batch)
                    batch = []
                    
            except queue.Empty:
                # Save remaining data if any
                if batch:
                    self.save_batch(batch)
                    batch = []
                    
    def save_batch(self, batch):
        """Save batch of data to CSV file"""
        try:
            df = pd.DataFrame(batch)
            df.to_csv(config.DATA_QUEUE_FILE, mode='a', 
                     header=not pd.io.common.file_exists(config.DATA_QUEUE_FILE),
                     index=False)
            print(f"[SERVER] Saved batch of {len(batch)} records")
        except Exception as e:
            print(f"[SAVE ERROR] {e}")
            
    def stop(self):
        """Stop the server"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()

if __name__ == "__main__":
    server = CarSalesServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n[SERVER] Shutting down...")
        server.stop()
