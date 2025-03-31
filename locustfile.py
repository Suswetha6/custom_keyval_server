import string
import random
import uuid
from locust import HttpUser, task, constant

import random
import string
from locust import HttpUser, task, constant
import psutil
import os

# Configuration
KEY_POOL_SIZE = 10_000
VALUE_LENGTH = 256
PUT_RATIO = 0.5
MEMORY_MONITOR_INTERVAL = 5  # seconds

class CacheUser(HttpUser):
    host = "http://localhost:7171"
    wait_time = constant(0)
    
    def on_start(self):
        # Initialize shared test data
        self.key_pool = [f"key_{i}" for i in range(KEY_POOL_SIZE)]
        self.value_pool = [
            ''.join(random.choices(string.ascii_letters, k=VALUE_LENGTH)) 
            for _ in range(KEY_POOL_SIZE)
        ]
        
        # Start memory monitoring
        if self.environment.runner.user_count == 1:  # Only run once
            self.environment.runner.greenlet.spawn(self.monitor_memory)

    @task
    def mixed_load(self):
        if random.random() < PUT_RATIO:
            self.put_request()
        else:
            self.get_request()

    def put_request(self):
        key = random.choice(self.key_pool)
        value = random.choice(self.value_pool)
        self.client.post(
            "/put",
            json={"key": key, "value": value},
            name="/put"
        )

    def get_request(self):
        key = random.choice(self.key_pool)
        self.client.get(
            f"/get?key={key}",
            name="/get"
        )

    def monitor_memory(self):
        """Check memory usage and force eviction if needed"""
        process = psutil.Process(os.getpid())
        while True:
            mem_percent = process.memory_percent()
            self.environment.events.request.fire(
                request_type="MEM",
                name="Memory Usage",
                response_time=mem_percent,
                response_length=0
            )
            
            if mem_percent > 70:  # Simulate heavy load
                self.client.post(
                    "/put",
                    json={
                        "key": "memory_pressure_key",
                        "value": 'x' * VALUE_LENGTH * 100  # Large value
                    },
                    name="OOM_TEST"
                )
            gevent.sleep(MEMORY_MONITOR_INTERVAL)


