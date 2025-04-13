from flask import Flask, render_template_string, request, jsonify
import redis
import socket
import json
import subprocess
import psutil

app = Flask(__name__)
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

LB_HOST = 'localhost'
LB_PORT = 12000

# Mapping of backend servers:
# Key: "localhost:port" maps to a tuple (server filename, server_id)
servers = {
    "localhost:13001": ("server.py", "A"),
    "localhost:13002": ("server.py", "B"),
    "localhost:13003": ("server.py", "C")
}

server_processes = {}  # Dictionary to store server process objects

def send_json(sock, message):
    """Send a JSON message with newline termination."""
    sock.sendall((json.dumps(message) + "\n").encode("utf-8"))

def recv_json(sock):
    """Receive a newline-delimited JSON message."""
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

def forward_request_to_lb(request_data):
    """Connect to the load balancer, send the request, and return the response."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((LB_HOST, LB_PORT))
            send_json(s, request_data)
            response = recv_json(s)
            return response
    except Exception as e:
        return {"error": str(e)}

def is_server_running(port):
    """Check if any process is running that includes the given port in its command line."""
    for proc in psutil.process_iter(attrs=['pid', 'cmdline']):
        try:
            if proc.info['cmdline'] and f"{port}" in " ".join(proc.info['cmdline']):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False

@app.route("/", methods=["GET", "POST"])
def dashboard():
    result = None
    # Process the "Submit a Request" form if the POST data contains the "operation" field.
    if request.method == "POST" and "operation" in request.form:
        operation = request.form.get("operation")
        value = request.form.get("value")
        # Build the JSON request based on the selected operation.
        if operation in ["fibonacci", "prime", "reverse", "palindrome", "wordcount"]:
            request_data = {"operation": operation, "value": value}
        else:
            request_data = {"error": "Invalid operation"}
        result = forward_request_to_lb(request_data)

    # Build a dictionary of server statuses.
    server_status = {
        server: "Healthy" if is_server_running(server.split(":")[1]) else "Down"
        for server in servers
    }

    # Retrieve the latest 50 log entries from Redis.
    logs = redis_client.lrange("lb_logs", 0, 50)
    logs_text = "\n".join(logs)

    html_template = '''
    <html>
    <head>
        <title>Distributed Load Balancer Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; }
            table, th, td { border: 1px solid #333; border-collapse: collapse; padding: 8px; }
            pre { background: #f4f4f4; padding: 10px; }
            form { margin-bottom: 20px; }
            .section { margin-bottom: 40px; }
        </style>
        <script>
            function manageServer(port, action) {
                fetch(`/${action}_server?port=` + port, { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    alert(data.message);
                    location.reload();
                });
            }
        </script>
    </head>
    <body>
        <h1>Distributed Load Balancer Dashboard</h1>
        
        <div class="section">
            <h2>Backend Server Health</h2>
            <table>
                <tr>
                    <th>Server (Host:Port)</th>
                    <th>Status</th>
                    <th>Actions</th>
                </tr>
                {% for server, status in server_status.items() %}
                <tr>
                    <td>{{ server }}</td>
                    <td>{{ status }}</td>
                    <td>
                        <button onclick="manageServer('{{ server.split(':')[1] }}', 'start')">Start</button>
                        <button onclick="manageServer('{{ server.split(':')[1] }}', 'stop')">Stop</button>
                    </td>
                </tr>
                {% endfor %}
            </table>
        </div>
        
        <div class="section">
            <h2>Submit a Request</h2>
            <form method="post" action="/">
                <label for="operation">Operation:</label>
                <select id="operation" name="operation">
                    <option value="fibonacci">Fibonacci</option>
                    <option value="prime">Prime Checker</option>
                    <option value="reverse">String Reversal</option>
                    <option value="palindrome">Palindrome Checker</option>
                    <option value="wordcount">Word Count</option>
                </select>
                <br><br>
                <label for="value">Input:</label>
                <input type="text" id="value" name="value" required>
                <br><br>
                <input type="submit" value="Submit">
            </form>
            {% if result %}
                <h3>Response from Load Balancer:</h3>
                <pre>{{ result }}</pre>
            {% endif %}
        </div>
        
        <div class="section">
            <h2>Load Balancer Logs</h2>
            <pre>{{ logs_text }}</pre>
        </div>
    </body>
    </html>
    '''
    return render_template_string(html_template,
                                  server_status=server_status,
                                  logs_text=logs_text,
                                  result=result)

# Route to start a server process.
@app.route('/start_server', methods=['POST'])
def start_server():
    port = request.args.get("port")
    key = f"localhost:{port}"
    if key in servers:
        if not is_server_running(port):
            server_file, server_id = servers[key]
            # Start the server with both the server ID and the port.
            process = subprocess.Popen(["python", server_file, server_id, port])
            server_processes[port] = process
            return jsonify({"message": f"Server on port {port} started successfully."})
        else:
            return jsonify({"message": f"Server on port {port} is already running."})
    return jsonify({"message": "Invalid port number."})

# Route to stop a server process.
@app.route('/stop_server', methods=['POST'])
def stop_server():
    port = request.args.get("port")
    found = False
    for proc in psutil.process_iter(attrs=['pid', 'cmdline']):
        try:
            if proc.info['cmdline'] and f"{port}" in " ".join(proc.info['cmdline']):
                proc.terminate()
                found = True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    if found:
        return jsonify({"message": f"Server on port {port} stopped successfully."})
    else:
        return jsonify({"message": f"No server found running on port {port}."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
