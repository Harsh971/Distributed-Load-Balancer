import socket
import threading
import json
import time

# Configuration
LB_HOST = 'localhost'
LB_PORT = 12000

# List of backend servers (host, port)
# You can start multiple backend servers on different ports.
backend_servers = [
    ("localhost", 13001),
    ("localhost", 13002),
    ("localhost", 13003)
]

# Status of backend servers: { (host,port): True/False } (True = healthy)
server_status = {server: True for server in backend_servers}
# Lock for synchronizing access to server_status and next_server_index
status_lock = threading.Lock()

# Round-robin pointer
next_server_index = 0

def send_json(sock, message):
    """Helper: send a JSON message with newline termination."""
    try:
        sock.sendall((json.dumps(message) + "\n").encode("utf-8"))
    except Exception as e:
        print("Error sending message:", e)

def recv_json(sock):
    """Helper: receive a JSON message (newline-delimited)."""
    data = b""
    while b"\n" not in data:
        chunk = sock.recv(1024)
        if not chunk:
            return None
        data += chunk
    try:
        return json.loads(data.decode("utf-8").strip())
    except Exception:
        return None

def choose_server():
    """Select the next available backend server using round-robin.
       If the selected server is down, skip to the next one.
    """
    global next_server_index
    with status_lock:
        for _ in range(len(backend_servers)):
            server = backend_servers[next_server_index]
            next_server_index = (next_server_index + 1) % len(backend_servers)
            if server_status.get(server, False):
                return server
    return None

def forward_request_to_server(request):
    """
    Forward the client request to one of the backend servers.
    Returns the response received from the server, or an error message.
    """
    # Try each available server (in worst-case, all servers are down)
    attempts = 0
    while attempts < len(backend_servers):
        server = choose_server()
        if not server:
            break
        host, port = server
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(3)  # timeout after 3 seconds
                s.connect((host, port))
                send_json(s, request)
                response = recv_json(s)
                if response:
                    return response
        except Exception as e:
            print(f"Error connecting to backend server {server}: {e}")
            # Mark this server as down
            with status_lock:
                server_status[server] = False
        attempts += 1
    return {"error": "All backend servers are down or unresponsive."}

def handle_client(conn, addr):
    """Handle an incoming client connection."""
    print(f"Client connected from {addr}")
    try:
        # Receive the client request (assume one request per connection for simplicity)
        request = recv_json(conn)
        if not request:
            conn.close()
            return

        print(f"Received request from client {addr}: {request}")
        # Forward the request to a backend server
        response = forward_request_to_server(request)
        print(f"Forwarding response to client {addr}: {response}")
        send_json(conn, response)
    except Exception as e:
        print(f"Error handling client {addr}: {e}")
    finally:
        conn.close()

def health_check(server):
    """
    Periodically check if a backend server is healthy.
    For simplicity, attempt to connect and send a simple ping.
    """
    host, port = server
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                s.connect((host, port))
                # Send a ping message
                send_json(s, {"type": "PING"})
                # Expect a pong response
                response = recv_json(s)
                if response and response.get("type") == "PONG":
                    with status_lock:
                        server_status[server] = True
        except Exception:
            with status_lock:
                server_status[server] = False
        time.sleep(5)  # check every 5 seconds

def start_health_checks():
    """Start a health check thread for each backend server."""
    for server in backend_servers:
        threading.Thread(target=health_check, args=(server,), daemon=True).start()

def main():
    start_health_checks()
    lb_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lb_sock.bind((LB_HOST, LB_PORT))
    lb_sock.listen(5)
    print(f"Load Balancer listening on {LB_HOST}:{LB_PORT}")

    while True:
        conn, addr = lb_sock.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    main()
