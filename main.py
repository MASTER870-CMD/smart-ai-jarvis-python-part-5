import sys
import os
import threading
import time
import webview
from app import app

def start_flask():
    """Run Flask in background thread"""
    app.run(port=5000, debug=False, use_reloader=False, threaded=True)

def main():
    # Start Flask in a background thread
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()
    
    # Wait for Flask to start
    time.sleep(2)
    
    # Create and show the webview window
    window = webview.create_window(
        title='AI NEXUS | Neural Interface System',
        url='http://127.0.0.1:5000',
        width=1400,
        height=900,
        resizable=True,
        fullscreen=False
    )
    
    # Start the webview (blocking call)
    webview.start(debug=False)

if __name__ == '__main__':
    main()
