import socket
import json

LB_HOST = 'localhost'
LB_PORT = 12000

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

def main():
    print("Client ready. (Each request uses a new connection)")
    task_id = 1
    while True:
        print("\nEnter an operation:")
        print("1. Echo")
        print("2. Square")
        print("3. Exit")
        choice = input("Your choice: ").strip()
        if choice == "3":
            break
        elif choice == "1":
            data = input("Enter message to echo: ")
            request = {"operation": "echo", "data": data}
        elif choice == "2":
            value = input("Enter a number to square: ")
            request = {"operation": "square", "value": value}
        else:
            print("Invalid choice.")
            continue
        
        try:
            # Create a new connection for each request:
            client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_sock.connect((LB_HOST, LB_PORT))
            send_json(client_sock, request)
            response = recv_json(client_sock)
            if response:
                print(f"Response from server (via LB): {response}")
            else:
                print("No response received.")
            client_sock.close()
        except Exception as e:
            print("Error communicating with load balancer:", e)
        
        task_id += 1

if __name__ == "__main__":
    main()
