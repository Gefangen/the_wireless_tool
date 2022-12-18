import asyncio
import websockets


async def recvMsg():
    uri = "ws://localhost:9999"
    async with websockets.connect(uri) as websocket:
        while True:
            greeting = await websocket.recv()
            print(f"< {greeting}")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(recvMsg())