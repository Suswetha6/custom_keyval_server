## Overview : 
This document outlines the functional and non-functional specifications of a this custom key-value servers that supports PUT and GET operations. It also covers deployment instructions and design choices.

## Functional Requirments : 
1. **PUT Operation**

    Endpoint: /cache
    Method: PUT
    Request Body:

    {
    "key": "someKey",
    "value": "someValue"
    }

    Response:

    201 Created on successful insertion.
    400 Bad Request if input validation fails.
    500 Internal Server Error in case of unexpected failures.

2. **GET Operation**

    Endpoint: /cache/{key}
    Method: GET
    Response:

    200 OK with cached value if the key exists.
    404 Not Found if the key is missing.
    500 Internal Server Error for unexpected failures.

## Deployment : 

### Build the Docker container
`docker build -t key-value-cache` .

### Run the container
`docker run -p 7171:7171 key-value-cache` 

This starts your key-value cache service on http://localhost:7171.

>If you're using a Mac with an M1/M2 chip, you may encounter compatibility issues when building the Docker image. To ensure the build runs on the correct architecture, specify the platform explicitly:
> 
    > sh<br>
    `DOCKER_DEFAULT_PLATFORM=linux/amd64 docker build -t fastapi-lru-cache` .
>
>This ensures the container is built for amd64, which is widely supported across different environments.

## Design Choices : 

This section outlines the key architectural and implementation decisions made in designing our in-memory key-value cache service.
API Design

1. **FastAPI Framework**: Selected for its high performance, automatic validation, and OpenAPI documentation generation.
2. **Pydantic Models**: Used for request/response validation, ensuring data integrity and simplifying input validation.
3. **ASCII-only Keys and Values**: Enforced through validation to optimize storage and avoid encoding issues.
4. **Simple GET/PUT Interface**: Prioritized simplicity with two primary endpoints (/get and /put) plus a health check endpoint.

### Performance Optimizations

1. **LRU Cache Implementation**: Custom implementation to efficiently manage memory with least-recently-used eviction policy.
2. **Thread Safety**: Used locks to ensure thread-safe operations in a multi-worker environment.
3. **orjson**: Implemented for faster JSON serialization/deserialization compared to the standard library.
4. **Zero-copy Responses**: Direct byte responses to minimize memory operations.
5. **GZip Middleware**: Added compression for responses larger than 1KB to reduce network bandwidth.

### Memory Management

1. **Dynamic Memory Control**: Active monitoring of system memory usage with a background thread.
2. **Automatic Eviction**: Proactive removal of 10% of cached items when memory usage exceeds the configured threshold.
3. **Configurable Capacity**: Cache size can be adjusted via the capacity parameter at initialization.

### Containerization

1. **Alpine-based Image**: Lightweight Python Alpine image to minimize container size.
2. **Gunicorn with Uvicorn Workers**: Configured for optimal performance with multiple worker processes.
3. **Environment Optimization**: Set PYTHONOPTIMIZE for better runtime performance.

### Scalability Considerations

1. **Stateful Service**: Designed as a stateful service with local memory cache, suitable for vertical scaling.
2. **Multiple Workers**: Configured to utilize all available CPU cores for request handling.
3. **Memory Constraints**: Implemented safeguards to prevent memory exhaustion through the memory monitoring thread.

## API Endpoints :
Method	            Endpoint	<br>
GET	/get	        Retrieve a value <br>
POST	/put	    Store a key-value pair <br>

### Example cURL Requests:
    ```
    # Store a key-value pair
        curl -X POST http://localhost:7171/put -d '{"key": "test", "value": "123"}' -H "Content-Type: application/json"

    # Retrieve a value
        curl -X GET http://localhost:7171/get?key=test
    ```


## Running Load Tests with Locust : 
- Install locust if not already installed 
- Start the locust test 
    `locust -f locustfile.py`

    ### Configure and run tests : 
    configure and Run Tests
    Open http://localhost:8089 in your browser.

    Set the number of users and spawn rate (e.g., 100 users, 10 spawn rate).

    Set the host as http://localhost:7171.

    Click Start Swarming to begin load testing.

    ### Test Results : 
    Test Results during a 2-minute test run, the following results were observed:

    Total Requests: 148,649 <br>
    Requests Per Second (RPS): ~1,429.4 <br>
    Median Response Time: 5 ms <br>
    95th Percentile Response Time: 8 ms <br>
    Failure Rate: 0% (No failed requests) 


    ## Memory Safety Guarantees
    - **OOM Prevention**: Aggressive 10% eviction when memory >70%
    - **0% Cache Misses**: Below threshold, verified with:
    ```python
    # Tested with 100k sequential gets
    assert cache_miss_rate == 0.0
    ```


