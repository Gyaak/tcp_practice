import asyncio


class AsyncTcpServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    async def multi_client_handler(self):
        server = await asyncio.start_server(self.handle_client, self.host, self.port)
        async with server:
            await server.serve_forever()
    
    async def handle_client(self, reader, writer):
        print(f"Connected to {writer.get_extra_info('peername')}")
        try:
            while True:
                data = await reader.read(1024)
                if not data:
                    break
                print(f"Received: {data.decode()}")
                writer.write(data)
                await writer.drain()
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            writer.close()
            print(f"Client {writer.get_extra_info('peername')} disconnected")

if __name__ == "__main__":
    server = AsyncTcpServer("127.0.0.1", 12345)
    asyncio.run(server.multi_client_handler())

