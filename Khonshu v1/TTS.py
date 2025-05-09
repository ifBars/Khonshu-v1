import socket

def speak(text):
    host = "127.0.0.1" 
    port = 65432

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((host, port))
            client_socket.sendall(text.encode())
            print(f"Sent: {text}")
    except ConnectionRefusedError:
        print("Error: Could not connect to the server. Make sure it is running.")
    except socket.timeout:
        print("Error: Connection timed out.")
    except socket.error as e:
        print(f"Socket error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
