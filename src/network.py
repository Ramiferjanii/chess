"""
network.py – Two-player online chess via WebSockets
Uses asyncio + websockets (pip install websockets).

Usage
-----
Server (host):
    python network.py server [port=5555]

Client (guest):
    python network.py client <host_ip> [port=5555]

The game process imports Network and calls:
    net.send(move_dict)   – send a move to opponent
    net.poll()            – returns a move_dict or None (non-blocking)
    net.connected         – True when session is live
    net.role              – 'server' or 'client'
    net.close()
"""

import asyncio
import json
import threading
import queue
import sys
import websockets


# ── Protocol helpers ──────────────────────────────────────────────────────────

def encode_move(move):
    """Serialise a Move object → JSON string."""
    return json.dumps({
        'ir': move.initial.row,
        'ic': move.initial.col,
        'fr': move.final.row,
        'fc': move.final.col,
    })


def decode_move(data):
    """Deserialise JSON string → plain dict (caller reconstructs Move)."""
    return json.loads(data)


# ── Network class ─────────────────────────────────────────────────────────────

class Network:
    """Thread-safe wrapper around a WebSocket connection."""

    DEFAULT_PORT = 5555

    def __init__(self):
        self.connected  = False
        self.role       = None          # 'server' | 'client'
        self._ws        = None
        self._recv_q    = queue.Queue() # incoming moves (dicts)
        self._send_q    = queue.Queue() # outgoing moves (json str)
        self._loop      = None
        self._thread    = None
        self._stop_evt  = asyncio.Event()

    # ── Public API (called from main pygame thread) ───────────────────────────

    def start_server(self, port=DEFAULT_PORT):
        """Host a game; block until one client connects."""
        self.role = 'server'
        self._run_in_thread(self._server_main(port))

    def start_client(self, host, port=DEFAULT_PORT):
        """Join a hosted game."""
        self.role = 'client'
        self._run_in_thread(self._client_main(host, port))

    def send(self, move):
        """Queue a Move object to be sent to the opponent."""
        self._send_q.put(encode_move(move))

    def poll(self):
        """Return a move dict from the opponent, or None if none waiting."""
        try:
            return self._recv_q.get_nowait()
        except queue.Empty:
            return None

    def close(self):
        if self._loop and not self._loop.is_closed():
            self._loop.call_soon_threadsafe(self._stop_evt.set)

    # ── Internal async machinery ──────────────────────────────────────────────

    def _run_in_thread(self, coro):
        """Start the async event loop in a background daemon thread."""
        def _target():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._stop_evt = asyncio.Event()
            try:
                self._loop.run_until_complete(coro)
            finally:
                self._loop.close()

        self._thread = threading.Thread(target=_target, daemon=True)
        self._thread.start()

    async def _handler(self, ws):
        """Shared send/recv coroutine used by both roles."""
        self._ws = ws
        self.connected = True
        print(f"[Network] Connected as {self.role}")

        async def sender():
            while True:
                # drain the send queue
                while not self._send_q.empty():
                    data = self._send_q.get_nowait()
                    await ws.send(data)
                await asyncio.sleep(0.02)

        async def receiver():
            async for message in ws:
                self._recv_q.put(decode_move(message))

        send_task = asyncio.create_task(sender())
        recv_task = asyncio.create_task(receiver())
        stop_task = asyncio.create_task(self._stop_evt.wait())

        done, pending = await asyncio.wait(
            [send_task, recv_task, stop_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for t in pending:
            t.cancel()
        self.connected = False
        print("[Network] Disconnected.")

    async def _server_main(self, port):
        print(f"[Network] Hosting on port {port}  –  waiting for opponent…")
        async with websockets.serve(self._handler, '0.0.0.0', port):
            await self._stop_evt.wait()

    async def _client_main(self, host, port):
        uri = f'ws://{host}:{port}'
        print(f"[Network] Connecting to {uri} …")
        try:
            async with websockets.connect(uri) as ws:
                await self._handler(ws)
        except Exception as e:
            print(f"[Network] Connection failed: {e}")


# ── Standalone launcher ───────────────────────────────────────────────────────

if __name__ == '__main__':
    net = Network()
    if len(sys.argv) >= 2 and sys.argv[1] == 'server':
        port = int(sys.argv[2]) if len(sys.argv) >= 3 else Network.DEFAULT_PORT
        net.start_server(port)
    elif len(sys.argv) >= 3 and sys.argv[1] == 'client':
        host = sys.argv[2]
        port = int(sys.argv[3]) if len(sys.argv) >= 4 else Network.DEFAULT_PORT
        net.start_client(host, port)
    else:
        print("Usage:")
        print("  python network.py server [port]")
        print("  python network.py client <host> [port]")
        sys.exit(1)

    print("Network started. Press Ctrl-C to exit.")
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        net.close()
