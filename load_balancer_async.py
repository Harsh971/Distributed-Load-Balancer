import asyncio
import json
import time
from asyncio import StreamReader, StreamWriter
import redis.asyncio as redis

# Load Balancer configuration
LB_HOST = 'localhost'
LB_PORT = 12000

# List of backend servers: (host, port, identifier)
backend_servers = [
    ("localhost", 13001, "A"),
    ("localhost", 13002, "B"),
    ("localhost", 13003, "C")
]

# In-memory health status for each backend: key=(host,port), value=True/False
server_status = {(host, port): True for host, port, _ in backend_servers}
next_server_index = 0
status_lock = asyncio.Lock()

# Connect to Redis (make sure Redis is running on localhost:6379 in WSL2)
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

# ------------------ Logging Helper ------------------
async def log_to_redis(message: str):
    """Push a log message into Redis and trim the log list to the most recent 100 entries."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {message}"
    await redis_client.lpush("lb_logs", log_message)
    await redis_client.ltrim("lb_logs", 0, 99)

# ------------------ JSON Helper Functions ------------------
async def send_json(writer: StreamWriter, message: dict):
    writer.write((json.dumps(message) + "\n").encode("utf-8"))
    await writer.drain()

async def recv_json(reader: StreamReader):
    data = await reader.readline()
    if not data:
        return None
    try:
        return json.loads(data.decode("utf-8").strip())
    except Exception:
        return None

# ------------------ Backend Server Selection ------------------
async def choose_backend_server():
    """Select the next available backend server using round-robin, skipping unhealthy ones."""
    global next_server_index
    async with status_lock:
        for _ in range(len(backend_servers)):
            server = backend_servers[next_server_index]
            next_server_index = (next_server_index + 1) % len(backend_servers)
            host, port, identifier = server
            if server_status.get((host, port), False):
                return server
    return None

# ------------------ Request Forwarding ------------------
async def forward_request(request: dict):
    """Forward a client request to an available backend server and return its response."""
    attempts = 0
    while attempts < len(backend_servers):
        server = await choose_backend_server()
        if not server:
            break
        host, port, identifier = server
        try:
            reader, writer = await asyncio.open_connection(host, port)
            await send_json(writer, request)
            response = await recv_json(reader)
            writer.close()
            await writer.wait_closed()
            if response:
                response['server_id'] = identifier
                await log_to_redis(f"Forwarded request {request} to server {identifier}, received response {response}")
                return response
        except Exception as e:
            error_msg = f"Error connecting to backend server {server}: {e}"
            print(error_msg)
            await log_to_redis(error_msg)
            async with status_lock:
                server_status[(host, port)] = False
        attempts += 1
    error_response = {"error": "All backend servers are down or unresponsive."}
    await log_to_redis(f"Returning error response: {error_response} for request {request}")
    return error_response

# ------------------ Client Connection Handler ------------------
async def handle_client(reader: StreamReader, writer: StreamWriter):
    addr = writer.get_extra_info('peername')
    print(f"Client connected from {addr}")
    await log_to_redis(f"Client connected from {addr}")
    try:
        while True:
            request = await recv_json(reader)
            if request is None:
                break
            print(f"Received request from {addr}: {request}")
            await log_to_redis(f"Received request from {addr}: {request}")
            # Increment request metric in Redis
            await redis_client.incr("requests_processed")
            response = await forward_request(request)
            await send_json(writer, response)
    except Exception as e:
        error_msg = f"Error handling client {addr}: {e}"
        print(error_msg)
        await log_to_redis(error_msg)
    finally:
        writer.close()
        await writer.wait_closed()
        print(f"Client disconnected from {addr}")
        await log_to_redis(f"Client disconnected from {addr}")

# ------------------ Health Check for Backend Servers ------------------
async def health_check(server):
    """Periodically check the health of a backend server."""
    host, port, identifier = server
    while True:
        try:
            reader, writer = await asyncio.open_connection(host, port)
            await send_json(writer, {"type": "PING"})
            response = await recv_json(reader)
            if response and response.get("type") == "PONG":
                async with status_lock:
                    server_status[(host, port)] = True
            writer.close()
            await writer.wait_closed()
        except Exception:
            async with status_lock:
                server_status[(host, port)] = False
        # Update Redis with current health status
        await redis_client.hset("backend_health", f"{host}:{port}", str(server_status[(host, port)]))
        await log_to_redis(f"Health check for server {identifier} at {host}:{port} - status: {server_status[(host, port)]}")
        await asyncio.sleep(5)

# ------------------ Main Function ------------------
async def main():
    # Initialize metric in Redis
    await redis_client.set("requests_processed", 0)
    await log_to_redis("Initialized requests_processed to 0")
    # Start health checks for each backend server
    for server in backend_servers:
        asyncio.create_task(health_check(server))
    server = await asyncio.start_server(handle_client, LB_HOST, LB_PORT)
    addr = server.sockets[0].getsockname()
    startup_msg = f"Load Balancer listening on {addr}"
    print(startup_msg)
    await log_to_redis(startup_msg)
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
