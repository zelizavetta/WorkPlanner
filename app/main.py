import threading

def handle_client(conn, addr):
    print(f"New connection from {addr}")
    while True:
        try:
            message = conn.recv(1024).decode()
            if message:
                print(f"Message from {addr}: {message}")
                conn.send(message.encode())
        except Exception as e:
            print(f"Error with connection from {addr}: {e}")
            break
    conn.close()

def server_program():
    host = socket.gethostname()
    port = 5000

    server_socket = socket.socket()
    server_socket.bind((host, port))
    server_socket.listen()

    while True:
        conn, addr = server_socket.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"Active connections: {threading.activeCount() - 1}")

if __name__ == '__main__':
    server_program()