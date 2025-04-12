import asyncio
import json
import sys

# --- Utility Functions ---

def fibonacci(n):
    if n < 0:
        return "Invalid input, must be non-negative"
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a

def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

# --- Request Processing Function ---

def process_request(request: dict):
    op = request.get("operation")
    print(f"Received operation: {op}")  # Debug logging
    if op == "fibonacci":
        try:
            n = int(request.get("value"))
        except Exception:
            return {"error": "Invalid input for Fibonacci. Please enter a non-negative integer."}
        result = fibonacci(n)
        return {"response": f"Fibonacci of {n} is {result}"}
    
    elif op == "prime":
        try:
            n = int(request.get("value"))
        except Exception:
            return {"error": "Invalid input for Prime Checker. Please enter a valid integer."}
        result = is_prime(n)
        return {"response": f"{n} is {'a prime number' if result else 'not a prime number'}."}
    
    elif op == "reverse":
        s = request.get("value")
        if s is None:
            return {"error": "No input provided for string reversal."}
        return {"response": f"Reversed string: {s[::-1]}"}
    
    elif op == "palindrome":
        s = request.get("value")
        if s is None:
            return {"error": "No input provided for palindrome check."}
        is_pal = s == s[::-1]
        return {"response": f"'{s}' is {'a palindrome' if is_pal else 'not a palindrome'}."}
    
    elif op == "wordcount":
        s = request.get("value")
        if s is None:
            return {"error": "No input provided for word count."}
        count = len(s.split())
        return {"response": f"Word count: {count}"}
    
    else:
        return {"error": "Unknown operation"}

# --- JSON Helper Functions ---

async def send_json(writer: asyncio.StreamWriter, message: dict):
    writer.write((json.dumps(message) + "\n").encode("utf-8"))
    await writer.drain()

async def recv_json(reader: asyncio.StreamReader):
    data = await reader.readline()
    if not data:
        return None
    try:
        return json.loads(data.decode("utf-8").strip())
    except Exception:
        return None

# --- Connection Handler ---

async def handle_connection(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, server_id: str):
    addr = writer.get_extra_info("peername")
    msg = await recv_json(reader)
    if msg is None:
        writer.close()
        await writer.wait_closed()
        return
    if msg.get("type") == "PING":
        await send_json(writer, {"type": "PONG"})
    else:
        print(f"Server {server_id} received request from {addr}: {msg}")
        response = process_request(msg)
        response["server_id"] = server_id
        await send_json(writer, response)
    writer.close()
    await writer.wait_closed()

# --- Main Server Startup ---

async def main():
    if len(sys.argv) != 3:
        print("Usage: python server.py <server_id> <port>")
        sys.exit(1)
    server_id = sys.argv[1]
    port = int(sys.argv[2])
    server = await asyncio.start_server(lambda r, w: handle_connection(r, w, server_id), "localhost", port)
    print(f"Backend Server {server_id} listening on port {port}")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
