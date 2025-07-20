import asyncio

class ChatServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        # {writer: (username, room)}
        self.clients = {}
        # {room_name: [(writer, username), ...]}
        self.rooms = {}
    
    async def start(self):
        """서버를 시작하고 클라이언트 접속을 기다립니다."""
        server = await asyncio.start_server(self.handle_client, self.host, self.port)
        print(f"[*] 서버가 {self.host}:{self.port} 에서 시작되었습니다.")
        async with server:
            await server.serve_forever()
    
    async def handle_client(self, reader, writer):
        """클라이언트별로 생성되어 접속부터 종료까지의 모든 과정을 처리합니다."""
        username = None
        room = None
        
        try:
            # --- 1. 로그인 절차 ---
            username, room = await self.welcome(reader, writer)
            if not username: # 로그인 중 연결이 끊긴 경우
                return

            # --- 2. 메인 메시지 루프 ---
            while True:
                data = await reader.read(1024)
                message = data.decode().strip()

                # 비정상 종료 (클라이언트가 창을 닫음) -> data가 비게 됨
                if not data:
                    print(f"[-] {username} 와의 연결이 비정상적으로 끊겼습니다.")
                    break # 루프를 빠져나가 finally 블록에서 정리

                # 정상 종료 ('exit' 입력)
                if message == "exit":
                    print(f"[-] {username} 님이 'exit'을 입력하여 접속을 종료합니다.")
                    break # 루프를 빠져나가 finally 블록에서 정리

                # 받은 메시지를 다른 클라이언트에게 브로드캐스트
                await self.broadcast(message, room, username)
        
        except ConnectionResetError:
            # 데이터 수신 중 갑자기 연결이 끊겼을 때 발생할 수 있는 오류 처리
            print(f"[-] {username} 와의 연결이 초기화되었습니다.")
        except Exception as e:
            print(f"[!] {username} 처리 중 에러 발생: {e}")

        finally:
            # --- 3. 정리 및 연결 종료 ---
            # 루프가 어떤 이유로든 끝나면 항상 이 블록이 실행됩니다.
            if writer in self.clients:
                username, room = self.clients[writer]

                # 클라이언트 정보 삭제
                del self.clients[writer]
                # 방에서 클라이언트 제거
                if room in self.rooms:
                    # writer 객체로 비교하여 정확한 클라이언트 제거
                    self.rooms[room] = [(w, u) for w, u in self.rooms[room] if w != writer]
                    
                    # 퇴장 메시지 브로드캐스트
                    await self.broadcast(f"님이 채팅방을 나갔습니다.", room, username)
                    print(f"[-] {username} 님이 {room} 방에서 나갔습니다.")

                    # 방이 비었다면 방 자체를 삭제
                    if not self.rooms[room]:
                        del self.rooms[room]
                        print(f"[*] {room} 방이 비어서 삭제되었습니다.")
            
            # --- 여기가 핵심! ---
            # 클라이언트와의 연결을 명시적으로 종료합니다.
            if not writer.is_closing():
                print(f"[*] {writer.get_extra_info('peername')} 와의 연결을 닫습니다.")
                writer.close()
                await writer.wait_closed()

    async def welcome(self, reader, writer):
        """클라이언트가 처음 접속했을 때 이름과 방을 설정하도록 안내합니다."""
        addr = writer.get_extra_info('peername')
        print(f"[+] 새로운 클라이언트 접속: {addr}")

        try:
            writer.write(b"[Welcome to the chat server] Send your name!\n")
            await writer.drain()
            username = (await reader.read(1024)).decode().strip()
            if not username: return None, None

            room_list_str = ", ".join(self.rooms.keys()) if self.rooms else "None"
            writer.write(b"Enter the room name to join or create a new room\n")
            writer.write(f"Room list: {room_list_str}\n".encode())
            await writer.drain()
            room = (await reader.read(1024)).decode().strip()
            if not room: return None, None

            if room not in self.rooms:
                self.rooms[room] = []
                print(f"[*] 새로운 방 생성: {room}")

            self.clients[writer] = (username, room)
            self.rooms[room].append((writer, username))
            
            await self.broadcast(f"님이 {room} 방에 참여했습니다.", room, username)
            print(f"[+] {username} 님이 {room} 방에 참여했습니다.")
            return username, room
        except (ConnectionError, BrokenPipeError, asyncio.IncompleteReadError):
            print(f"[-] 클라이언트({addr})가 환영 과정에서 접속을 종료했습니다.")
            return None, None

    async def broadcast(self, message, room, sender_username):
        """같은 방에 있는 다른 클라이언트들에게 메시지를 전송합니다."""
        if room not in self.rooms:
            return
            
        full_message = f"[{sender_username}] {message}\n"
        # 메시지를 보낼 때 연결이 끊겼을 수 있는 클라이언트를 감지하기 위해 리스트 복사
        for client_writer, client_username in self.rooms[room]:
            if client_writer != self.get_writer_by_username(sender_username):
                try:
                    client_writer.write(full_message.encode())
                    await client_writer.drain()
                except (ConnectionError, BrokenPipeError):
                    print(f"[!] {client_username} 에게 메시지 전송 실패 (연결 끊김)")

    def get_writer_by_username(self, username):
        """사용자 이름으로 writer 객체를 찾습니다."""
        for writer, (uname, _) in self.clients.items():
            if uname == username:
                return writer
        return None

if __name__ == "__main__":
    server = ChatServer("127.0.0.1", 12345)
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("\n[*] 서버를 종료합니다.")
