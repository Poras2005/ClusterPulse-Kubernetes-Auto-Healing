# test_apps/memory_hog/app.py
from flask import Flask
import time
import threading

app = Flask(__name__)
leak = [] # list grows forever — simulates a memory leak

@app.route('/health')
def health(): 
    return {'status':'ok'}, 200

@app.route('/metrics')
def metrics(): 
    # Prometheus text format
    return f'app_memory_bytes {len(leak) * 1000}\n', 200, \
           {'Content-Type':'text/plain'}

def leak_memory():
    while True:
        leak.append('x' * int(1.5 * 1024 * 1024)) # add 1.5MB every second
        time.sleep(1)

# Start the leak in a background thread
threading.Thread(target=leak_memory, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
