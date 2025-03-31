from fastapi import FastAPI, Query
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel, Field, field_validator
from starlette.responses import Response
import uvicorn
from collections import deque
import threading
import os
import psutil
import time
import orjson

# Initialize FastAPI app
app = FastAPI()

#adding gzip middleware 
app.add_middleware(GZipMiddleware,minimum_size=1000)

class LRUCache:

    def __init__(self, capacity=100000, memory_limit_percent=70):
        self.cache = {}
        self.queue = deque()  # Keeps track of LRU order
        self.capacity = capacity
        self.lock = threading.Lock()
        self.memory_limit_percent = memory_limit_percent
        self.process = psutil.Process(os.getpid())
        
        # Start a background thread to monitor memory
        self.monitor_thread = threading.Thread(target=self._monitor_memory, daemon=True)
        self.monitor_thread.start()
    
    def get(self, key):
        try:
            self.lock.acquire()
            if key not in self.cache:
                return None
            # Move to end (most recently used)
            self.queue.remove(key)
            self.queue.append(key)
            return self.cache[key]
        finally:
            self.lock.release()
    
    def put(self, key, value):
        try:
            self.lock.acquire()
            if key in self.cache:
                self.queue.remove(key)
            elif len(self.cache) >= self.capacity:
                # Remove LRU element
                oldest_key = self.queue.popleft()
                del self.cache[oldest_key]

            # Insert at end (most recently used)
            self.cache[key] = value
            self.queue.append(key)
        finally:
            self.lock.release()
    
    def _monitor_memory(self):
        while True:
            # Check every second
            time.sleep(1)
            memory_percent = self.process.memory_percent()
            
            # If memory usage is above our threshold, aggressively evict
            if memory_percent > self.memory_limit_percent:
                with self.lock:
                    # Calculate how many items to remove (10% of cache size)
                    items_to_remove = max(1, int(len(self.cache) * 0.1))
                    print(f"Memory usage at {memory_percent}%, evicting {items_to_remove} items")
                    for _ in range(items_to_remove):
                        if len(self.cache) > 0:
                            oldest_key = self.queue.popleft()
                            del self.cache[oldest_key]


# Initialize our cache
cache = LRUCache()

# Define request/response models
class PutRequest(BaseModel):
    key: str = Field(..., max_length=256)
    value: str = Field(..., max_length=256)
    
    @field_validator('key', 'value')
    @classmethod
    def check_ascii(cls, v: str) -> str:
        """Validate that the string contains only ASCII characters."""
        try:
            v.encode('ascii')  # Faster than checking each character
            return v
        except UnicodeEncodeError:
            raise ValueError('Only ASCII characters are allowed')

# Define API endpoints
@app.post("/put")
async def put_key_value(request: PutRequest):
    try : 
        cache.put(request.key, request.value)
        return Response(
            content=orjson.dumps({"status": "OK", "message": "Key inserted/updated successfully."}),
            media_type="application/json"
        )
    except Exception as e:
        return Response(
            content=orjson.dumps({"status": "ERROR", "message": str(e)}),
            media_type="application/json",
            status_code=500
        )


@app.get("/get")
async def get_value(key: str = Query(..., max_length=256)):
    value = cache.get(key)
    if value is None:
        return Response(
            content=b'{"status":"ERROR","message":"Key not found."}',
            media_type="application/json",
            status_code=404
        )
    # Zero-copy response
    return Response(
        content=orjson.dumps({"status": "OK", "key": key, "value": value}),
        media_type="application/json"
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "OK"}
