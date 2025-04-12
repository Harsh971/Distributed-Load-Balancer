import asyncio
import json

LB_HOST = 'localhost'
LB_PORT = 12000

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

async def client():
    reader, writer = await asyncio.open_connection(LB_HOST, LB_PORT)
    print("Connected to Load Balancer (persistent connection).")
    try:
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
            await send_json(writer, request)
            response = await recv_json(reader)
            if response:
                print(f"Response from server (via LB): {response}")
            else:
                print("No response received.")
    except Exception as e:
        print("Error:", e)
    finally:
        writer.close()
        await writer.wait_closed()

def main():
    asyncio.run(client())

if __name__ == "__main__":
    main()
