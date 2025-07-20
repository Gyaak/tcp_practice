import asyncio
import sys

class ChatClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    async def start(self):
        reader, writer = await asyncio.open_connection(self.host, self.port)

        # 서버 환영 메시지 및 이름 요청 읽기
        welcome = await reader.readuntil()  # "Send your name!" 끝까지 읽음
        print(welcome.decode().strip())

        # 사용자 이름 입력 및 전송
        username = input("> ").strip()
        writer.write((username + "\n").encode())
        await writer.drain()

        # 수신 & 전송을 병렬로 수행
        await asyncio.gather(
            self._listen(reader),
            self._send_loop(writer)
        )

    async def _listen(self, reader):
        while True:
            data = await reader.read(1024)
            if not data:
                print("서버 연결 종료")
                return
            print(data.decode().strip())

    async def _send_loop(self, writer):
        loop = asyncio.get_event_loop()
        while True:
            line = await loop.run_in_executor(None, sys.stdin.readline)
            if not line:
                continue
            msg = line.rstrip()

            if msg.lower() == "exit":
                print("종료 메시지 전송 — 클라이언트 종료")
                writer.close()
                await writer.wait_closed()
                return
            
            writer.write((msg + "\n").encode())
            await writer.drain()

if __name__ == "__main__":
    client = ChatClient("127.0.0.1", 12345)
    try:
        asyncio.run(client.start())
    except KeyboardInterrupt:
        print("\n클라이언트 강제 종료") 
