import socket
import threading
import time
import random


class SimpleTcpClient:
    def __init__(self, host, port, client_id):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_id = client_id
    def send_message(self, message):
        self.client_socket.sendall(message.encode())

    def start(self):
        self.client_socket.connect((self.host, self.port))
        while True:
            try:
                self.send_message(f"Hello from Client {self.client_id}")
                time.sleep(random.randint(1, 10))
            except Exception as e:
                print(f"Client {self.client_id} 에러 발생: {e}")
                break


if __name__ == "__main__":
    
    HOST = '127.0.0.1'
    PORT = 12345
    CLIENT_NUM = 10

    for i in range(CLIENT_NUM):
        try:
            client = SimpleTcpClient(HOST, PORT, i)
            threading.Thread(target=client.start, daemon=True).start()
        except Exception as e:
            print(f"Client {i} 재시도 중...")
            time.sleep(5)
            # retry
            client = SimpleTcpClient(HOST, PORT, i)
            threading.Thread(target=client.start, daemon=True).start()


    # (선택) 메인 스레드는 종료되지 않도록 무한 대기
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("클라이언트 종료 중…")
