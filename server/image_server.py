import requests
from PIL import Image
from http.server import BaseHTTPRequestHandler, HTTPServer
import io
import time
import socket
import threading
import logging
from logging.handlers import RotatingFileHandler
import json
from jsonschema import validate

# Define the configuration schema
config_schema = {
    "type": "object",
    "properties": {
        "server": {
            "type": "object",
            "properties": {
                "port": {"type": "integer", "minimum": 1, "maximum": 65535},
                "image_url": {"type": "string", "format": "uri"},
                "refresh_interval": {"type": "integer", "minimum": 1}
            },
            "required": ["port", "image_url", "refresh_interval"]
        },
        "image": {
            "type": "object",
            "properties": {
                "target_width": {"type": "integer", "minimum": 1},
                "target_height": {"type": "integer", "minimum": 1}
            },
            "required": ["target_width", "target_height"]
        },
        "paths": {
            "type": "object",
            "properties": {
                "log_file": {"type": "string"},
                "image_path": {"type": "string"},
                "source_image_path": {"type": "string"}
            },
            "required": ["log_file", "image_path", "source_image_path"]
        }
    },
    "required": ["server", "image", "paths"]
}

def load_config():
    """Load and validate configuration from JSON file"""
    try:
        with open('/root/esp32_server/config/config.json', 'r') as f:
            config = json.load(f)
            validate(instance=config, schema=config_schema)
            return config
    except Exception as e:
        logging.error(f"Error loading config: {e}")
        raise

# Load configuration at startup
config = load_config()

# Update the logging configuration
logging.basicConfig(
    handlers=[RotatingFileHandler(
        config['paths']['log_file'],
        maxBytes=1024*1024,
        backupCount=5
    )],
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Use configuration values throughout the code
IMAGE_URL = config['server']['image_url']
TARGET_WIDTH = config['image']['target_width']
TARGET_HEIGHT = config['image']['target_height']
REFRESH_INTERVAL = config['server']['refresh_interval']
SERVER_PORT = config['server']['port']
IMAGE_PATH = config['paths']['image_path']

def scale_image(image_path, target_width, target_height):
    """Scales an image to the target dimensions using nearest-neighbor."""
    try:
        img = Image.open(image_path)
        scaled_img = img.resize((target_width, target_height), Image.NEAREST)
        scaled_img.save(IMAGE_PATH)
        logging.info("Image scaled successfully.")
    except Exception as e:
        logging.error(f"Error scaling image: {e}")

def download_image(url, image_path):
    """Downloads an image from a URL and saves it to a file."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(image_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logging.info("Image downloaded successfully.")
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Error downloading image: {e}")
        return False

def get_local_ip():
    """Get the local IP address of the machine."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
        s.close()
        return ip_address
    except Exception as e:
        logging.error(f"Error getting local IP: {e}")
        return "127.0.0.1"

class ImageServer(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/image.jpg":
            try:
                with open(config['paths']['image_path'], 'rb') as f:
                    image_data = f.read()
                self.send_response(200)
                self.send_header('Content-type', 'image/jpeg')
                self.send_header('Content-length', len(image_data))
                self.end_headers()
                self.wfile.write(image_data)
            except FileNotFoundError:
                self.send_response(404)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b"Image not found")
        elif self.path == "/ip":
            ip_address = get_local_ip()
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(ip_address.encode())
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"Not found")

def run_server(server_class=HTTPServer, handler_class=ImageServer, port=SERVER_PORT):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting server on port {port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        print("Server stopped.")

def main():
    while True:
        if download_image(IMAGE_URL, config['paths']['source_image_path']):
            scale_image(config['paths']['source_image_path'], 
                       TARGET_WIDTH, TARGET_HEIGHT)
        time.sleep(REFRESH_INTERVAL)

if __name__ == "__main__":
    # Start the image processing loop in a separate thread
    image_thread = threading.Thread(target=main)
    image_thread.daemon = True
    image_thread.start()

    # Run the HTTP server in the main thread
    run_server()