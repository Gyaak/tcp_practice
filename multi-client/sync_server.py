import threading
import socket


class MultiThreadTcpServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5) # 백로그 큐 크기
    
    def multi_client_handler(self):
        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"Connected to {addr}")
            # 클라이언트 처리를 위해 스레드 생성
            client_handler = threading.Thread(
                target=self.handle_client,
                args=(client_socket,),
                name=f"Client {addr}",
                daemon=True
                )
            client_handler.start()

    def handle_client(self, client_socket):
        current_thread = threading.current_thread()
        # 클라이언트를 처리하는 스레드 동작 시작
        print(f"[{current_thread.name} | ID={current_thread.ident}] 핸들러 진입")

        try:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    print(f"[{current_thread.name}] 클라이언트 연결 종료")
                    break
                print(f"[{current_thread.name}] Received:", data.decode())
        except Exception as e:
            print(f"[{current_thread.name}] 에러 발생:", e)
        finally:
            client_socket.close()
            print(f"[{current_thread.name}] 소켓 닫음")


if __name__ == "__main__":
    server = MultiThreadTcpServer("127.0.0.1", 12345)
    server.multi_client_handler()
