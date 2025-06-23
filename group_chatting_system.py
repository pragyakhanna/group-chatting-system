import socket
import threading
import struct

# Server Configuration
CRDS_HOST = 'localhost'  # Chat Room Directory Server host
CRDS_PORT = 5000         # CRDS port

# Chat Room Directory (name -> (multicast_address, port))
chat_rooms = {}

# Server Handler
def handle_client(conn, addr):
    global chat_rooms
    print(f"[NEW CONNECTION] {addr} connected.")
    
    while True:
        try:
            data = conn.recv(1024).decode()
            if not data:
                break
            
            parts = data.split()
            command = parts[0]
            
            if command == "getdir":
                response = str(chat_rooms)
            elif command == "makeroom" and len(parts) == 4:
                name, ip, port = parts[1], parts[2], int(parts[3])
                if name in chat_rooms:
                    response = "Room already exists."
                else:
                    chat_rooms[name] = (ip, port)
                    response = f"Room {name} created."
            elif command == "deleteroom" and len(parts) == 2:
                name = parts[1]
                if name in chat_rooms:
                    del chat_rooms[name]
                    response = f"Room {name} deleted."
                else:
                    response = "Room not found."
            elif command == "bye":
                response = "Goodbye!"
                conn.send(response.encode())
                break
            else:
                response = "Invalid command."
            
            conn.send(response.encode())
        except:
            break
    
    conn.close()
    print(f"[DISCONNECTED] {addr} disconnected.")

# Start Server
def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((CRDS_HOST, CRDS_PORT))
    server.listen()
    print(f"[LISTENING] Server is running on {CRDS_HOST}:{CRDS_PORT}")
    
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

# Client Class
class ChatClient:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.name = "Anonymous"
    
    def connect(self):
        self.client.connect((CRDS_HOST, CRDS_PORT))
        print("Connected to the Chat Room Directory Server.")
        self.main_menu()
    
    def send_command(self, command):
        self.client.send(command.encode())
        return self.client.recv(1024).decode()
    
    def main_menu(self):
        while True:
            cmd = input("Command: ")
            if cmd == "connect":
                self.connect()
            elif cmd.startswith("name "):
                self.name = cmd.split(" ", 1)[1]
                print(f"Name set to {self.name}")
            elif cmd.startswith("chat "):
                room_name = cmd.split(" ", 1)[1]
                self.chat_mode(room_name)
            elif cmd == "bye":
                print(self.send_command(cmd))
                self.client.close()
                break
            else:
                print(self.send_command(cmd))
    
    def chat_mode(self, room_name):

        # Fetch room list before joining
        rooms = self.send_command("getdir")
        chat_rooms = eval(rooms)  # Convert string to dictionary

        if room_name not in chat_rooms:
            print("Room does not exist. Please create one first.")
            return

        multicast_group, port = chat_rooms[room_name]
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", port))
        mreq = struct.pack("4sl", socket.inet_aton(multicast_group), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        
        print(f"Joined chat room {room_name}. Type messages to send. Press Ctrl+C to exit.")
        
        def receive_messages():
            while True:
                try:
                    msg, _ = sock.recvfrom(1024)
                    print(msg.decode())
                except:
                    break
        
        threading.Thread(target=receive_messages, daemon=True).start()
        
        while True:
            try:
                msg = input()
                sock.sendto(f"{self.name}: {msg}".encode(), (multicast_group, port))
            except KeyboardInterrupt:
                print("Leaving chat room...")
                break
        
        sock.close()

#Run Server or Client


if __name__ == "__main__":
    choice = input("Run as (server/client)? ").strip().lower()
    if choice == "server":
        start_server()
    elif choice == "client":
        client = ChatClient()
        #client.connect()
        client.main_menu()
    else:
        print("Invalid choice.")
