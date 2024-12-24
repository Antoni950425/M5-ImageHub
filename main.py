from m5stack import *
from m5ui import *
from uiflow import *
import wifiCfg
import urequests
import time
import gc
from io import BytesIO
import struct
import uos
import os

# Initialize
lcd.clear()
lcd.setRotation(1)  # Landscape mode
lcd.setBrightness(25)

# Settings
SSID = 'YOUR_WIFI_SSID'
PASS = 'YOUR_WIFI_PASSWORD'
URL = 'http://your.server.address:8080/image.jpg'  # Replace with your server URL

# Screen settings
SCREEN_WIDTH = 240
SCREEN_HEIGHT = 135
FONT_SIZE = 12  # Increased from 6 to 12 for better readability

# Add these constants after the existing settings
REQUIRED_DIRS = {'apps', 'blocks', 'res', 'img'}
REQUIRED_FILES = {'boot.py', 'main.py', 'temp.py', 'test.py'}
FLASH_PATH = '/flash'

last_memory_check = 0
MEMORY_CHECK_INTERVAL = 5000  # 5 seconds

# Add these constants at the top with other settings
LOADING_BAR_WIDTH = 160  # Width of loading bar in pixels
LOADING_BAR_HEIGHT = 4  # Height of loading bar
LOADING_BAR_Y = 85  # Y position of loading bar (below download text)

def debug(msg):
    print('[DEBUG]', msg)

def show_text(msg, y=60):
    debug('Show: ' + msg)
    # Calculate center position
    w = len(msg) * FONT_SIZE
    x = (SCREEN_WIDTH - w) // 2
    
    # Use a larger font for better visibility
    lcd.font(lcd.FONT_DejaVu18)
    
    # Draw a small black background rectangle for better text visibility
    bg_padding = 4
    lcd.rect(x - bg_padding, 
             y - bg_padding, 
             w + (bg_padding * 2), 
             FONT_SIZE + (bg_padding * 2), 
             0x000000, 
             0x000000)  # Black filled rectangle
    
    # Print text in white
    lcd.print(msg, x, y, 0xffffff)
    wait_ms(100)

def connect_wifi():
    show_text('Connecting...')
    try:
        wifiCfg.doConnect(SSID, PASS)
        if wifiCfg.wlan_sta.isconnected():
            show_text('Connected!')
            wait_ms(1000)  # Wait for network to stabilize
            return True
    except Exception as e:
        debug('WiFi Error: ' + str(e))
    show_text('WiFi Failed!')
    return False

def draw_loading_bar(progress):
    """Draw a loading bar with given progress (0-100)"""
    # Calculate positions
    bar_x = (SCREEN_WIDTH - LOADING_BAR_WIDTH) // 2
    
    # Draw background
    lcd.rect(bar_x, LOADING_BAR_Y, 
            LOADING_BAR_WIDTH, LOADING_BAR_HEIGHT, 
            0x666666, 0x666666)  # Gray background
    
    # Draw progress
    progress_width = int((LOADING_BAR_WIDTH * progress) // 100)
    if progress_width > 0:
        lcd.rect(bar_x, LOADING_BAR_Y,
                progress_width, LOADING_BAR_HEIGHT,
                0x00FF00, 0x00FF00)  # Green progress

def get_image():
    show_text('Downloading...')
    try:
        debug('Requesting URL: ' + URL)
        r = urequests.get(URL, stream=True)
        debug('Response status: ' + str(r.status_code))
        
        if r.status_code == 200:
            debug('Writing to flash...')
            
            # Remove existing image if present
            try:
                os.remove('/flash/img.jpg')
                gc.collect()
            except:
                pass
            
            # Open file for writing in smaller chunks
            with open('/flash/img.jpg', 'wb') as f:
                chunk_size = 512  # Reduced from 1024 to 512 for better memory handling
                chunks_downloaded = 0
                while True:
                    if not check_memory():
                        debug('Memory low during download')
                        r.close()
                        return False
                    
                    chunk = r.raw.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    chunks_downloaded += 1
                    
                    # Update progress bar with a sliding animation
                    progress = chunks_downloaded % 100
                    draw_loading_bar(progress)
                    
                    gc.collect()
                    wait_ms(5)  # Small delay between chunks
            
            r.close()
            gc.collect()
            debug('Download complete')
            # Show full progress bar at completion
            draw_loading_bar(100)
            wait_ms(100)
            return True
            
        debug('Bad status: ' + str(r.status_code))
        r.close()
    except Exception as e:
        debug('Download error: ' + str(e))
        try:
            r.close()
        except:
            pass
    
    show_text('Download Failed!')
    return False

def show_image():
    """Display the downloaded JPEG"""
    show_text('Displaying...')
    try:
        # Clear the screen and set black background
        lcd.clear()
        lcd.fillRect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0x0000)
        
        # Since the image is already pre-scaled to 240x135, no offset needed
        lcd.image(0, 0, '/flash/img.jpg')
        
        debug('Image displayed')
        return True
        
    except Exception as e:
        debug('Display error: ' + str(e))
        show_text('Display Error!')  # Simplified error message
        return False

def update():
    if get_image():
        if show_image():
            show_text('Ready!', SCREEN_HEIGHT - 20)
            wait_ms(1000)
            show_image()  # Refresh to clear status
        else:
            debug('Display failed')
    else:
        debug('Get image failed')

def cleanup_flash():
    """Simple cleanup of unnecessary files from flash directory"""
    try:
        # Get current contents
        contents = os.listdir(FLASH_PATH)
        
        for item in contents:
            # Skip required items
            if item in REQUIRED_DIRS or item in REQUIRED_FILES:
                continue
                
            full_path = FLASH_PATH + '/' + item
            try:
                # Check if it's a directory
                is_dir = (os.stat(full_path)[0] & 0x4000) != 0
                
                if is_dir:
                    if item not in REQUIRED_DIRS:
                        # Remove directory contents and directory
                        for subitem in os.listdir(full_path):
                            try:
                                os.remove(full_path + '/' + subitem)
                            except:
                                pass
                        try:
                            os.rmdir(full_path)
                        except:
                            pass
                else:
                    # Remove non-required files
                    if item not in REQUIRED_FILES:
                        try:
                            os.remove(full_path)
                        except:
                            pass
                            
            except:
                pass
                
    except Exception as e:
        print('Cleanup error:', e)

def check_memory():
    """Check and log memory status with rate limiting"""
    global last_memory_check
    current_time = time.ticks_ms()
    
    gc.collect()
    free = gc.mem_free()
    alloc = gc.mem_alloc()
    total = free + alloc
    
    # Only print debug if enough time has passed
    if time.ticks_diff(current_time, last_memory_check) > MEMORY_CHECK_INTERVAL:
        debug('Memory - Free: {}KB, Used: {}KB, Total: {}KB'.format(
            free // 1024, alloc // 1024, total // 1024))
        last_memory_check = current_time
    
    return free > 10240  # Ensure at least 10KB free

def safe_remove(path):
    """Safely remove a file with retries"""
    max_retries = 3
    for i in range(max_retries):
        try:
            if os.path.exists(path):
                os.remove(path)
            return True
        except Exception as e:
            debug('Remove retry {}/{}: {}'.format(i+1, max_retries, str(e)))
            gc.collect()
            wait_ms(100)
    return False

def main():
    debug('Starting main')
    show_text('Starting...')
    
    # Perform cleanup
    cleanup_flash()
    
    # Check memory after cleanup
    if not check_memory():
        show_text('Low memory!')
        wait_ms(3000)
        return
    
    # Connect to WiFi
    if not connect_wifi():
        wait_ms(3000)
        return
    
    # Initial update
    update()
    last = time.time()
    debug('Entering main loop')
    
    # Main loop
    while True:
        try:
            if btnA.wasPressed():
                if check_memory():
                    update()
                    last = time.time()
                else:
                    show_text('Low memory!')
                    wait_ms(1000)
            
            # Auto update check
            if time.time() - last >= 60:
                if check_memory():
                    update()
                    last = time.time()
                else:
                    show_text('Low memory!')
                    wait_ms(1000)
            
            wait_ms(100)
            gc.collect()
            
        except Exception as e:
            debug('Main loop error: ' + str(e))
            show_text('Error!')
            wait_ms(3000)

debug('Program start')
main() 