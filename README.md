# M5StickC-Plus Image Display System

## Table of Contents
- [Project Overview](#project-overview)
- [System Architecture](#system-architecture)
- [Directory Structure](#directory-structure)
- [Technical Specifications](#technical-specifications)
- [Features](#features)
- [Installation](#installation)
- [Development Notes](#development-notes)
- [Contributing](#contributing)
- [License](#license)
- [Authors](#authors)

## Project Overview

This project implements a web image display system using an M5StickC-Plus device with a supporting Python server for image processing. The system fetches images from a web source, processes them to the correct display dimensions, and shows them on the M5StickC-Plus LCD screen with proper error handling and user feedback.

## System Architecture

### Components

1. **M5StickC-Plus Client**
   - Handles image display and user interface
   - Manages WiFi connectivity
   - Implements memory-efficient image downloading
   - Provides visual feedback with loading bar and status messages

2. **Python Image Processing Server**
   - Pre-processes images to exact display dimensions (240x135)
   - Serves scaled images via HTTP
   - Implements automatic image refresh
   - Handles image download and scaling operations

## Directory Structure

```
/
├── esp32_client/
│   ├── main.py           # Main M5StickC-Plus program
│   └── boot.py           # Boot configuration
│
└── server/
    ├── image_server.py   # Image processing server
    ├── config/
    │   └── config.json   # Server configuration
    ├── images/           # Image storage
    ├── logs/            # Server logs
    └── venv/            # Python virtual environment
```

## Technical Specifications

### M5StickC-Plus Client

- Display: 135x240 LCD (ST7789v2 driver)
- Memory: ~47KB available RAM
- Operating Mode: Landscape (rotation 1)
- Screen Brightness: 25%
- Image Format: JPEG (240x135 pixels)

### Server Requirements

- Python 3.x
- PIL (Python Imaging Library)
- HTTP Server
- JSON Configuration
- Logging System

## Features

### Client Features

- WiFi connectivity with error handling
- Efficient image downloading with chunked transfer
- Progress bar for download status
- Memory management with garbage collection
- Auto-refresh every 60 seconds
- Manual refresh via Button A
- Status message display
- Error recovery mechanisms

### Server Features

- Image scaling to exact display dimensions
- Automatic image refresh
- RESTful image serving
- Configuration management
- Logging system
- Service management

## Installation

### Server Setup

1. Set up Python environment and install dependencies:

```bash
python -m venv server/venv
source server/venv/bin/activate
pip install pillow requests jsonschema
```

2. Configure the server:
   - Edit `server/config/config.json` with appropriate settings
   - Set up the service:

```bash
sudo cp image_server.service /etc/systemd/system/
sudo systemctl enable image_server
sudo systemctl start image_server
```

### Client Setup

1. Flash MicroPython to M5StickC-Plus
2. Upload `main.py` to the device
3. Configure WiFi settings in `main.py`:

```python
SSID = 'your_wifi_ssid'
PASS = 'your_wifi_password'
URL = 'http://your_server_ip:8080/image.jpg'
```

## Development Notes

### Memory Management

- Chunk-based downloads (512B chunks)
- Regular garbage collection
- Memory monitoring
- File cleanup routines

### Display Optimization

- Pre-scaled images from server
- Centered status messages
- Thin loading bar (4px)
- Black background for text visibility

### Error Handling

- Network connectivity recovery
- Memory allocation failures
- File system management
- Download timeouts

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Authors

For questions or support, please open an issue in the repository.