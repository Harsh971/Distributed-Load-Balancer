import socket
import json
import sys
import time

def send_json(sock, message):
    """Send a JSON message with newline termination."""
    sock.sendall((json.dumps(message) + "\n").encode("utf-8"))

def recv_json(sock):
    """Receive a JSON message (newline-delimited)."""
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

def process_request(request):
    """
    For demonstration, assume the request is of the form:
      {"operation": "echo", "data": "Hello"}
    or a computation like:
      {"operation": "square", "value": 5}
    """
    op = request.get("operation")
    if op == "echo":
        return {"response": f"Echo: {request.get('data')}"}
    elif op == "square":
        try:
            value = float(request.get("value"))
            time.sleep(1)  # simulate computation delay
            return {"response": f"Square is {value ** 2}"}
        except Exception as e:
            return {"error": str(e)}
    else:
        return {"error": "Unknown operation"}

def handle_connection(conn, addr, server_id):
    """
    Handle a connection from the load balancer.
    The server can also respond to PING messages for health checks.
    """
    msg = recv_json(conn)
    if not msg:
        conn.close()
        return
    if msg.get("type") == "PING":
        send_json(conn, {"type": "PONG"})
    elif msg.get("type") is None:
        # Assume it's a client request forwarded by the load balancer.
        print(f"Server {server_id} received request from LB: {msg}")
        response = process_request(msg)
        # Add server ID to the response for demonstration.
        response["server_id"] = server_id
        send_json(conn, response)
    conn.close()

def main():
    if len(sys.argv) != 3:
        print("Usage: python server.py <server_id> <port>")
        sys.exit(1)
    server_id = sys.argv[1]
    port = int(sys.argv[2])
    
    srv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv_sock.bind(('localhost', port))
    srv_sock.listen(5)
    print(f"Backend Server {server_id} listening on port {port}")

    while True:
        conn, addr = srv_sock.accept()
        handle_connection(conn, addr, server_id)

if __name__ == "__main__":
    main()
