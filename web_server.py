#!/usr/bin/env python3
"""
web_server.py  –  Chess Online via Browser
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Install : pip install fastapi uvicorn
Run     : python web_server.py
Local   : http://localhost:8000
Internet: ngrok http 8000   →  share the https URL

Room flow
─────────
  1. Player A visits /new  →  redirected to /game/<room_id>
  2. Player A copies the URL and sends it to Player B
  3. Player B opens the URL  →  game starts (A=White, B=Black)
"""

import sys, os, json, uuid, asyncio, copy
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse
import uvicorn

from board import Board
from piece import King, Queen, Rook, Bishop, Knight, Pawn
from square import Square
from move import Move
from opening import identify_opening

app   = FastAPI()
rooms: dict = {}          # room_id -> GameRoom


# ─────────────────────────────────────────────────────────────────────────────
# Game room
# ─────────────────────────────────────────────────────────────────────────────

class GameRoom:
    def __init__(self, rid: str):
        self.room_id      = rid
        self.board        = Board()
        self.move_history : list = []
        self.players      : dict = {}   # 'white'|'black' -> WebSocket
        self.next_player  = 'white'
        self.game_state   = 'waiting'   # waiting|playing|check|checkmate|stalemate|finished

    # ── Board serialisation ──────────────────────────────────────────────────
    def board_repr(self):
        return [
            [f"{sq.piece.color}_{sq.piece.name}" if sq.piece else None
             for sq in row]
            for row in self.board.squares
        ]

    def find_king_pos(self, color):
        try:
            r, c = self.board._find_king(color)
            return [r, c]
        except Exception:
            return None

    # ── Valid moves for a square ─────────────────────────────────────────────
    def get_valid_moves(self, row, col):
        sq = self.board.squares[row][col]
        if not sq.piece:
            return [], []
        self.board.calc_moves(sq.piece, row, col, filter_checks=True)
        brd = self.board_repr()
        moves    = [[m.final.row, m.final.col] for m in sq.piece.moves]
        captures = [[r, c] for r, c in moves if brd[r][c]]
        sq.piece.clear_moves()
        return moves, captures

    # ── Apply a move ─────────────────────────────────────────────────────────
    def do_move(self, fr, fc, tr, tc):
        piece = self.board.squares[fr][fc].piece
        if not piece or piece.color != self.next_player:
            return False, "wrong_piece"
        self.board.calc_moves(piece, fr, fc, filter_checks=True)
        move = Move(Square(fr, fc), Square(tr, tc))
        if not self.board.valid_move(piece, move):
            return False, "illegal"
        captured = self.board.squares[tr][tc].has_piece()
        self.board.move(piece, move)
        self.move_history.append(move)
        self.next_player = 'black' if self.next_player == 'white' else 'white'
        # Detect state
        if self.board.is_checkmate(self.next_player):
            self.game_state = 'checkmate'
        elif self.board.is_stalemate(self.next_player):
            self.game_state = 'stalemate'
        elif self.board.in_check(self.next_player):
            self.game_state = 'check'
        else:
            self.game_state = 'playing'
        return True, captured

    # ── Broadcast helpers ────────────────────────────────────────────────────
    async def broadcast(self, msg: dict):
        dead = []
        for color, ws in self.players.items():
            try:
                await ws.send_text(json.dumps(msg))
            except Exception:
                dead.append(color)
        for c in dead:
            self.players.pop(c, None)

    async def send_to(self, color: str, msg: dict):
        ws = self.players.get(color)
        if ws:
            try:
                await ws.send_text(json.dumps(msg))
            except Exception:
                pass


# ─────────────────────────────────────────────────────────────────────────────
# HTTP routes
# ─────────────────────────────────────────────────────────────────────────────

@app.get('/')
async def landing():
    return HTMLResponse(LANDING_HTML)

@app.get('/new')
async def new_game():
    rid = str(uuid.uuid4())[:8]
    rooms[rid] = GameRoom(rid)
    return RedirectResponse(f'/game/{rid}')

@app.get('/game/{room_id}')
async def game_page(room_id: str):
    if room_id not in rooms:
        rooms[room_id] = GameRoom(room_id)
    # Replace ALL occurrences (title, badge, JS const, WS URL)
    html = GAME_HTML.replace('__ROOM_ID__', room_id)
    return HTMLResponse(html)


# ─────────────────────────────────────────────────────────────────────────────
# WebSocket
# ─────────────────────────────────────────────────────────────────────────────

@app.websocket('/ws/{room_id}')
async def ws_endpoint(websocket: WebSocket, room_id: str):
    await websocket.accept()

    if room_id not in rooms:
        rooms[room_id] = GameRoom(room_id)
    room = rooms[room_id]

    # Assign a color
    if 'white' not in room.players:
        color = 'white'
    elif 'black' not in room.players:
        color = 'black'
    else:
        await websocket.send_text(json.dumps({'type': 'full'}))
        await websocket.close()
        return

    room.players[color] = websocket
    await websocket.send_text(json.dumps({'type': 'assigned', 'color': color}))

    if len(room.players) == 2:
        room.game_state = 'playing'
        await room.broadcast({
            'type':        'start',
            'board':       room.board_repr(),
            'next_player': room.next_player,
            'state':       room.game_state,
            'king_pos':    None,
        })
    else:
        await websocket.send_text(json.dumps({'type': 'waiting'}))

    try:
        async for raw in websocket.iter_text():
            data = json.loads(raw)
            t    = data.get('type')

            # ── Request valid moves ─────────────────────────────────────────
            if t == 'get_moves' and color == room.next_player:
                moves, captures = room.get_valid_moves(data['row'], data['col'])
                await websocket.send_text(json.dumps({
                    'type':     'moves',
                    'moves':    moves,
                    'captures': captures,
                    'row':      data['row'],
                    'col':      data['col'],
                }))

            # ── Make a move ─────────────────────────────────────────────────
            elif (t == 'move'
                  and color == room.next_player
                  and room.game_state not in ('finished', 'checkmate', 'stalemate')):
                ok, result = room.do_move(
                    data['from_row'], data['from_col'],
                    data['to_row'],   data['to_col'],
                )
                if ok:
                    opening  = identify_opening(room.move_history)
                    king_pos = (room.find_king_pos(room.next_player)
                                if room.game_state == 'check' else None)
                    await room.broadcast({
                        'type':        'update',
                        'board':       room.board_repr(),
                        'next_player': room.next_player,
                        'state':       room.game_state,
                        'opening':     opening,
                        'captured':    result,
                        'king_pos':    king_pos,
                        'last_move':   {
                            'fr': data['from_row'], 'fc': data['from_col'],
                            'tr': data['to_row'],   'tc': data['to_col'],
                        },
                    })
                    if room.game_state in ('checkmate', 'stalemate'):
                        room.game_state = 'finished'
                else:
                    await websocket.send_text(json.dumps({'type': 'invalid'}))

    except WebSocketDisconnect:
        room.players.pop(color, None)
        await room.broadcast({'type': 'disconnect', 'color': color})
        if not room.players:
            rooms.pop(room_id, None)


# ─────────────────────────────────────────────────────────────────────────────
# Landing page HTML
# ─────────────────────────────────────────────────────────────────────────────

LANDING_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Chess Online ♟</title>
  <meta name="description" content="Play chess online with anyone – share a link, no account needed.">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --purple:  #7c3aed;
      --purple2: #4f46e5;
      --bg:      #0d1117;
      --text:    #e2e8f0;
      --muted:   #94a3b8;
      --border:  rgba(255,255,255,0.09);
      --glass:   rgba(255,255,255,0.04);
    }
    html, body { min-height: 100vh; }
    body {
      font-family: 'Inter', sans-serif;
      background: radial-gradient(ellipse 80% 55% at 50% 15%, #1c0a4a 0%, var(--bg) 65%);
      display: flex; flex-direction: column;
      align-items: center; justify-content: center;
      color: var(--text); padding: 32px 16px;
    }

    /* ── Hero ── */
    .hero { text-align: center; max-width: 580px; }
    .logo-wrap { margin-bottom: 20px; }
    .logo { font-size: 80px; filter: drop-shadow(0 6px 28px rgba(140,80,255,0.55)); }
    h1 {
      font-size: clamp(36px, 7vw, 56px);
      font-weight: 900; letter-spacing: -2px;
      background: linear-gradient(135deg, #fff 30%, #a78bfa 100%);
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .sub { margin-top: 12px; font-size: 18px; color: var(--muted); font-weight: 300; }

    /* ── Cards ── */
    .cards { display: flex; gap: 18px; margin-top: 52px; flex-wrap: wrap; justify-content: center; }
    .card {
      background: var(--glass);
      border: 1px solid var(--border);
      border-radius: 18px; padding: 28px 26px;
      width: 250px; backdrop-filter: blur(20px);
      transition: transform .2s, border-color .2s, box-shadow .2s;
    }
    .card:hover {
      transform: translateY(-5px);
      border-color: rgba(124,58,237,.45);
      box-shadow: 0 16px 40px rgba(0,0,0,.4);
    }
    .card-icon { font-size: 32px; margin-bottom: 10px; }
    .card h2   { font-size: 18px; font-weight: 700; margin-bottom: 8px; }
    .card p    { font-size: 13px; color: var(--muted); margin-bottom: 22px; line-height: 1.6; }

    .btn {
      width: 100%; padding: 12px;
      border: none; border-radius: 10px;
      font-family: 'Inter', sans-serif; font-size: 15px; font-weight: 600;
      cursor: pointer; transition: opacity .15s, transform .1s;
    }
    .btn:hover  { opacity: .88; transform: scale(1.02); }
    .btn:active { transform: scale(.97); }
    .btn-primary   { background: linear-gradient(135deg, var(--purple), var(--purple2)); color: #fff; }
    .btn-secondary { background: rgba(255,255,255,.07); color: var(--text); border: 1px solid var(--border); }

    input[type=text] {
      width: 100%; padding: 10px 14px;
      background: rgba(255,255,255,.05);
      border: 1px solid var(--border); border-radius: 8px;
      color: var(--text); font-family: 'Inter', sans-serif; font-size: 13px;
      margin-bottom: 10px; outline: none; transition: border-color .15s;
    }
    input[type=text]:focus { border-color: var(--purple); }
    input[type=text]::placeholder { color: #475569; }

    /* ── Features ── */
    .features {
      margin-top: 56px; display: flex;
      gap: 20px 32px; flex-wrap: wrap; justify-content: center;
    }
    .feat { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #64748b; }
    .feat-icon { font-size: 16px; }
  </style>
</head>
<body>
  <div class="hero">
    <div class="logo-wrap"><div class="logo">♟</div></div>
    <h1>Chess Online</h1>
    <p class="sub">Play with anyone, anywhere — share a link, no account needed.</p>

    <div class="cards">
      <!-- Create -->
      <div class="card">
        <div class="card-icon">🎮</div>
        <h2>Create Game</h2>
        <p>Start a new game. You play White — share the link with your opponent.</p>
        <button class="btn btn-primary" id="create-btn" onclick="createGame()">Create New Game</button>
      </div>

      <!-- Join -->
      <div class="card">
        <div class="card-icon">🔗</div>
        <h2>Join Game</h2>
        <p>Received an invite link? Paste the room code or full URL below.</p>
        <input type="text" id="room-input" placeholder="Room code or invite URL…">
        <button class="btn btn-secondary" onclick="joinRoom()">Join Game →</button>
      </div>
    </div>

    <div class="features">
      <div class="feat"><span class="feat-icon">♟</span> Check &amp; Checkmate detection</div>
      <div class="feat"><span class="feat-icon">📖</span> Opening book (40+ openings)</div>
      <div class="feat"><span class="feat-icon">⚡</span> Real-time WebSocket</div>
      <div class="feat"><span class="feat-icon">🌐</span> Works over internet via ngrok</div>
    </div>
  </div>

  <script>
    function createGame() {
      document.getElementById('create-btn').textContent = 'Creating…';
      location.href = '/new';
    }
    function joinRoom() {
      const val = document.getElementById('room-input').value.trim();
      if (!val) return;
      const match = val.match(/game\\/([a-f0-9-]{6,36})/i);
      const rid   = match ? match[1] : val.replace(/[^a-f0-9-]/gi, '');
      if (rid) location.href = `/game/${rid}`;
    }
    document.getElementById('room-input').addEventListener('keydown', e => {
      if (e.key === 'Enter') joinRoom();
    });
  </script>
</body>
</html>
"""


# ─────────────────────────────────────────────────────────────────────────────
# Game page HTML (board + UI + WebSocket JS)
# ─────────────────────────────────────────────────────────────────────────────

GAME_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Chess ♟ – Room __ROOM_ID__</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --purple: #7c3aed; --purple2: #4f46e5;
      --bg: #0d1117; --text: #e2e8f0; --muted: #94a3b8;
      --border: rgba(255,255,255,0.09); --glass: rgba(255,255,255,0.04);
      --sq: 60px;
      --board-size: calc(var(--sq) * 8);
    }
    html, body { height: 100%; }
    body {
      font-family: 'Inter', sans-serif;
      background: var(--bg); color: var(--text);
      display: flex; flex-direction: column; min-height: 100vh;
    }

    /* ── Header ── */
    header {
      padding: 10px 20px;
      background: rgba(255,255,255,0.025);
      border-bottom: 1px solid var(--border);
      display: flex; align-items: center; gap: 12px;
    }
    header .logo { font-size: 20px; }
    header h1    { font-size: 15px; font-weight: 700; flex: 1; }
    .room-badge {
      background: rgba(124,58,237,0.18); border: 1px solid rgba(124,58,237,0.4);
      color: #c4b5fd; padding: 3px 12px; border-radius: 20px;
      font-size: 12px; font-weight: 600; letter-spacing: .04em;
    }
    .btn-sm {
      padding: 6px 14px; border: 1px solid var(--border);
      background: var(--glass); color: var(--text);
      border-radius: 8px; font-size: 12px; font-weight: 500;
      cursor: pointer; font-family: 'Inter', sans-serif;
      transition: background .15s;
    }
    .btn-sm:hover { background: rgba(255,255,255,.1); }

    /* ── Main layout ── */
    main {
      flex: 1; display: flex;
      align-items: center; justify-content: center;
      gap: 24px; padding: 20px 16px; flex-wrap: wrap;
    }

    /* ── Board area ── */
    .board-area { display: flex; flex-direction: column; align-items: flex-start; gap: 4px; }
    .board-row  { display: flex; align-items: center; }

    /* Coordinate labels */
    .rank-label {
      width: 18px; height: var(--sq);
      display: flex; align-items: center; justify-content: center;
      font-size: 11px; font-weight: 600; color: #475569;
    }
    .file-labels { display: flex; margin-left: 18px; }
    .file-label  {
      width: var(--sq);
      text-align: center; font-size: 11px; font-weight: 600; color: #475569;
      padding-top: 4px;
    }

    /* ── Board ── */
    #board {
      display: grid;
      grid-template-columns: repeat(8, var(--sq));
      grid-template-rows: repeat(8, var(--sq));
      border-radius: 4px; overflow: hidden;
      box-shadow: 0 24px 80px rgba(0,0,0,.7), 0 0 0 2px rgba(255,255,255,.08);
    }
    .sq {
      width: var(--sq); height: var(--sq);
      display: flex; align-items: center; justify-content: center;
      cursor: pointer; position: relative; user-select: none;
    }
    .sq.light { background: #f0d9b5; }
    .sq.dark  { background: #b58863; }

    /* State highlights */
    .sq.selected   { background: #f5f07a !important; }
    .sq.last-from,
    .sq.last-to    { filter: brightness(.78) saturate(1.3); }
    .sq.in-check   { background: #e63946 !important; animation: pulse-check 1s ease-in-out infinite alternate; }
    @keyframes pulse-check { from { background: #e63946; } to { background: #ff6b77; } }

    /* Valid move dot */
    .sq.valid::after {
      content: ''; position: absolute; pointer-events: none;
      width: 28px; height: 28px;
      background: rgba(0,0,0,.23); border-radius: 50%;
      z-index: 2;
    }
    /* Valid capture ring (square already has piece) */
    .sq.valid.has-piece::after {
      width: calc(var(--sq) - 4px); height: calc(var(--sq) - 4px);
      background: transparent;
      border: 5px solid rgba(0,0,0,.23);
      border-radius: 50%;
    }

    /* Piece */
    .sq .piece {
      font-size: 42px; line-height: 1; z-index: 1; pointer-events: none;
      transition: transform .08s;
    }
    .sq .piece.wp { color: #fff;    text-shadow: 0 0 1px #222, 0 2px 5px rgba(0,0,0,.55); }
    .sq .piece.bp { color: #1a1a2e; text-shadow: 0 0 2px rgba(255,255,255,.15), 0 1px 3px rgba(0,0,0,.5); }
    .sq:hover .piece { transform: scale(1.08); }

    /* ── Side panel ── */
    .panel { width: 260px; display: flex; flex-direction: column; gap: 12px; }
    .card {
      background: var(--glass); border: 1px solid var(--border);
      border-radius: 14px; padding: 16px;
    }
    .card-title {
      font-size: 10px; font-weight: 700; text-transform: uppercase;
      letter-spacing: .1em; color: #475569; margin-bottom: 10px;
    }

    /* Turn badge */
    .turn-badge {
      display: inline-flex; align-items: center; gap: 8px;
      padding: 8px 14px; border-radius: 10px;
      font-weight: 600; font-size: 14px; width: 100%;
    }
    .turn-badge.my-turn  { background: rgba(34,197,94,.13);  color: #4ade80; border: 1px solid rgba(34,197,94,.25); }
    .turn-badge.wait     { background: rgba(148,163,184,.08); color: var(--muted); border: 1px solid rgba(148,163,184,.15); }
    .turn-badge.in-check { background: rgba(239,68,68,.13);  color: #f87171; border: 1px solid rgba(239,68,68,.25); }

    .color-indicator {
      display: flex; align-items: center; gap: 10px;
      margin-bottom: 10px; font-size: 14px; color: var(--muted);
    }
    .color-dot { width: 14px; height: 14px; border-radius: 50%; flex-shrink: 0; }
    .color-dot.white { background: #fff; box-shadow: 0 0 0 1px rgba(0,0,0,.2); }
    .color-dot.black { background: #1a1a2e; box-shadow: 0 0 0 1px rgba(255,255,255,.15); }

    /* Opening */
    #opening-name { font-size: 14px; font-weight: 600; color: #c4b5fd; min-height: 20px; }

    /* Share link */
    .share-box {
      background: rgba(0,0,0,.35); border: 1px solid var(--border);
      border-radius: 8px; padding: 8px 12px;
      font-family: monospace; font-size: 11px; color: var(--muted);
      word-break: break-all; margin-bottom: 8px;
    }
    .btn-copy {
      width: 100%; padding: 9px;
      background: rgba(124,58,237,.15); border: 1px solid rgba(124,58,237,.35);
      color: #c4b5fd; border-radius: 8px;
      font-size: 13px; font-weight: 600; cursor: pointer;
      font-family: 'Inter', sans-serif; transition: background .15s;
    }
    .btn-copy:hover { background: rgba(124,58,237,.25); }
    .copied { background: rgba(34,197,94,.15) !important; color: #4ade80 !important; border-color: rgba(34,197,94,.3) !important; }

    /* ── Waiting overlay ── */
    #waiting {
      display: none; position: fixed; inset: 0;
      background: rgba(10,10,20,.93); backdrop-filter: blur(14px);
      z-index: 80; flex-direction: column; align-items: center; justify-content: center; gap: 20px;
    }
    #waiting.show { display: flex; }
    .spinner {
      width: 52px; height: 52px;
      border: 4px solid rgba(255,255,255,.08);
      border-top-color: var(--purple);
      border-radius: 50%; animation: spin .75s linear infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    .wait-title { font-size: 22px; font-weight: 700; }
    .wait-sub   { font-size: 13px; color: var(--muted); text-align: center; max-width: 320px; line-height: 1.6; }
    .wait-link  {
      background: rgba(0,0,0,.4); border: 1px solid var(--border);
      border-radius: 10px; padding: 10px 20px;
      font-family: monospace; font-size: 12px; color: var(--muted);
      word-break: break-all; text-align: center; max-width: 360px;
    }

    /* ── Game over overlay ── */
    #gameover {
      display: none; position: fixed; inset: 0;
      background: rgba(8,8,18,.88); backdrop-filter: blur(12px);
      z-index: 90; flex-direction: column; align-items: center; justify-content: center; gap: 14px;
    }
    #gameover.show { display: flex; }
    .ov-icon  { font-size: 72px; animation: pop .4s cubic-bezier(.17,.67,.38,1.3); }
    .ov-title { font-size: clamp(36px, 7vw, 52px); font-weight: 900; color: #f59e0b; }
    .ov-sub   { font-size: 22px; color: var(--text); }
    .ov-hint  { font-size: 13px; color: var(--muted); margin-top: 4px; }
    @keyframes pop { from { transform: scale(0); } to { transform: scale(1); } }
    .btn-ov {
      margin-top: 12px; padding: 13px 32px;
      background: linear-gradient(135deg, var(--purple), var(--purple2));
      color: #fff; border: none; border-radius: 12px;
      font-size: 16px; font-weight: 700; cursor: pointer;
      font-family: 'Inter', sans-serif; transition: transform .1s;
    }
    .btn-ov:hover { transform: scale(1.04); }

    @media (max-width: 640px) {
      :root { --sq: 44px; }
      .panel { width: 100%; max-width: calc(var(--board-size) + 18px); }
      main { gap: 16px; padding: 12px 8px; }
    }
  </style>
</head>
<body>
  <header>
    <span class="logo">♟</span>
    <h1>Chess Online</h1>
    <span class="room-badge" id="room-badge">Room: __ROOM_ID__</span>
    <button class="btn-sm" onclick="location.href='/'">← Home</button>
  </header>

  <main>
    <!-- Board -->
    <div class="board-area">
      <div class="board-row">
        <div id="ranks"></div>
        <div id="board"></div>
      </div>
      <div id="files" class="file-labels"></div>
    </div>

    <!-- Side panel -->
    <div class="panel">

      <div class="card">
        <div class="card-title">You</div>
        <div class="color-indicator">
          <div class="color-dot" id="my-color-dot"></div>
          <span>Playing as <strong id="my-color-label">—</strong></span>
        </div>
        <div class="turn-badge wait" id="turn-badge">⏳ Waiting…</div>
      </div>

      <div class="card">
        <div class="card-title">Opening</div>
        <div id="opening-name">—</div>
      </div>

      <div class="card">
        <div class="card-title">Invite Link</div>
        <div class="share-box" id="share-url"></div>
        <button class="btn-copy" id="copy-btn" onclick="copyLink()">📋 Copy Invite Link</button>
      </div>

    </div>
  </main>

  <!-- Waiting for opponent -->
  <div id="waiting">
    <div class="spinner"></div>
    <div class="wait-title">Waiting for opponent…</div>
    <div class="wait-link" id="wait-link"></div>
    <button class="btn-copy" onclick="copyLink()" style="width:200px">📋 Copy Link</button>
    <div class="wait-sub">Send this link to your opponent. The game starts automatically when they join.</div>
  </div>

  <!-- Game over -->
  <div id="gameover">
    <div class="ov-icon" id="ov-icon">🏆</div>
    <div class="ov-title" id="ov-title">Checkmate!</div>
    <div class="ov-sub"   id="ov-sub">White wins</div>
    <div class="ov-hint">Want to play again?</div>
    <button class="btn-ov" onclick="location.href='/new'">New Game</button>
    <button class="btn-sm" style="font-size:13px;padding:8px 18px" onclick="location.href='/'">Back to Home</button>
  </div>

  <script>
    // ── Constants ──────────────────────────────────────────────────────────
    const ROOM_ID   = '__ROOM_ID__';
    const SHARE_URL = `${location.protocol}//${location.host}/game/${ROOM_ID}`;

    document.getElementById('share-url').textContent = SHARE_URL;
    document.getElementById('wait-link').textContent  = SHARE_URL;

    const FILES = ['a','b','c','d','e','f','g','h'];
    const RANKS = ['8','7','6','5','4','3','2','1'];

    // Unicode chess pieces (hollow = white player, filled = black player)
    const UNICODE = {
      white_king:'♔', white_queen:'♕', white_rook:'♖',
      white_bishop:'♗', white_knight:'♘', white_pawn:'♙',
      black_king:'♚', black_queen:'♛', black_rook:'♜',
      black_bishop:'♝', black_knight:'♞', black_pawn:'♟',
    };

    // ── Client state ───────────────────────────────────────────────────────
    let myColor       = null;
    let board         = Array.from({length:8}, () => Array(8).fill(null));
    let selected      = null;          // {row, col}
    let validMoves    = [];            // [[r,c], ...]
    let validCaptures = [];
    let nextPlayer    = 'white';
    let gameState     = 'waiting';
    let flipped       = false;
    let lastMove      = null;          // {fr,fc,tr,tc}
    let checkKing     = null;          // [row, col] when in check

    // ── WebSocket ──────────────────────────────────────────────────────────
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${proto}//${location.host}/ws/${ROOM_ID}`);

    ws.onmessage = ({ data }) => {
      const msg = JSON.parse(data);

      switch (msg.type) {

        case 'assigned':
          myColor = msg.color;
          flipped = myColor === 'black';
          document.getElementById('my-color-dot').className = `color-dot ${myColor}`;
          document.getElementById('my-color-label').textContent =
            myColor.charAt(0).toUpperCase() + myColor.slice(1);
          break;

        case 'waiting':
          document.getElementById('waiting').classList.add('show');
          break;

        case 'start':
          document.getElementById('waiting').classList.remove('show');
          board      = msg.board;
          nextPlayer = msg.next_player;
          gameState  = msg.state;
          renderBoard();
          updateTurnUI();
          break;

        case 'moves':
          selected      = { row: msg.row, col: msg.col };
          validMoves    = msg.moves;
          validCaptures = msg.captures;
          renderBoard();
          break;

        case 'update':
          board         = msg.board;
          nextPlayer    = msg.next_player;
          gameState     = msg.state;
          checkKing     = msg.king_pos;
          lastMove      = msg.last_move;
          selected      = null;
          validMoves    = [];
          validCaptures = [];
          if (msg.opening)
            document.getElementById('opening-name').textContent = '♟ ' + msg.opening;
          renderBoard();
          updateTurnUI();
          if (gameState === 'checkmate') showGameOver('checkmate', nextPlayer);
          if (gameState === 'stalemate') showGameOver('stalemate', null);
          break;

        case 'invalid':
          selected = null; validMoves = []; validCaptures = [];
          renderBoard();
          break;

        case 'full':
          alert('This room is full! Create a new game.'); location.href = '/';
          break;

        case 'disconnect':
          document.getElementById('turn-badge').className = 'turn-badge wait';
          document.getElementById('turn-badge').textContent = '⚠️ Opponent disconnected';
          break;
      }
    };

    ws.onerror = () => {
      document.getElementById('turn-badge').textContent = '⚠️ Connection lost';
    };

    // ── Board rendering ────────────────────────────────────────────────────
    function renderBoard() {
      const boardEl = document.getElementById('board');
      const ranksEl = document.getElementById('ranks');
      const filesEl = document.getElementById('files');

      boardEl.innerHTML = '';
      ranksEl.innerHTML = '';
      filesEl.innerHTML = '<div style="width:18px"></div>'; // spacer for rank column

      for (let di = 0; di < 8; di++) {
        // flipped=false (white): di=0 → row=0 (rank 8 at top), rank 1 at bottom ✓
        // flipped=true  (black): di=0 → row=7 (rank 1 at top), rank 8 at bottom ✓
        const actualRow = flipped ? 7 - di : di;

        // Rank label
        const rl = document.createElement('div');
        rl.className = 'rank-label';
        rl.textContent = String(8 - actualRow);
        ranksEl.appendChild(rl);

        // File label: white sees a→h left-to-right; black sees h→a left-to-right
        const actualCol = flipped ? 7 - di : di;
        const fl = document.createElement('div');
        fl.className = 'file-label';
        fl.textContent = FILES[actualCol];
        filesEl.appendChild(fl);
      }

      // Squares
      for (let di = 0; di < 8; di++) {
        for (let dj = 0; dj < 8; dj++) {
          const row = flipped ? 7 - di : di;
          const col = flipped ? 7 - dj : dj;

          const isLight    = (row + col) % 2 === 0;
          const isSelected = selected && selected.row === row && selected.col === col;
          const isValid    = validMoves.some(([r,c]) => r===row && c===col);
          const isCapture  = validCaptures.some(([r,c]) => r===row && c===col);
          const isLastFrom = lastMove && lastMove.fr===row && lastMove.fc===col;
          const isLastTo   = lastMove && lastMove.tr===row && lastMove.tc===col;
          const isCheck    = checkKing && checkKing[0]===row && checkKing[1]===col
                             && gameState === 'check';
          const hasPiece   = board[row][col] !== null;

          const sq = document.createElement('div');
          sq.className = [
            'sq',
            isLight    ? 'light'     : 'dark',
            isSelected ? 'selected'  : '',
            isValid    ? 'valid'     : '',
            isValid && hasPiece ? 'has-piece' : '',
            isLastFrom ? 'last-from' : '',
            isLastTo   ? 'last-to'   : '',
            isCheck    ? 'in-check'  : '',
          ].filter(Boolean).join(' ');

          const pieceStr = board[row][col];
          if (pieceStr) {
            const isWhitePiece = pieceStr.startsWith('white');
            const span = document.createElement('span');
            span.className = `piece ${isWhitePiece ? 'wp' : 'bp'}`;
            span.textContent = UNICODE[pieceStr] || '';
            sq.appendChild(span);
          }

          sq.addEventListener('click', () => handleClick(row, col));
          boardEl.appendChild(sq);
        }
      }
    }

    // ── Click handler ──────────────────────────────────────────────────────
    function handleClick(row, col) {
      if (!['playing', 'check'].includes(gameState)) return;
      if (nextPlayer !== myColor) return;

      const pieceStr = board[row][col];
      const isValidDest = validMoves.some(([r,c]) => r===row && c===col);

      // ① Clicking a valid destination → make the move
      if (selected && isValidDest) {
        ws.send(JSON.stringify({
          type: 'move',
          from_row: selected.row, from_col: selected.col,
          to_row:   row,          to_col:   col,
        }));
        selected = null; validMoves = []; validCaptures = [];
        return;
      }

      // ② Clicking own piece → select it
      if (pieceStr && pieceStr.startsWith(myColor)) {
        ws.send(JSON.stringify({ type: 'get_moves', row, col }));
        return;
      }

      // ③ Clicking elsewhere → deselect
      selected = null; validMoves = []; validCaptures = [];
      renderBoard();
    }

    // ── Turn / status UI ───────────────────────────────────────────────────
    function updateTurnUI() {
      const badge = document.getElementById('turn-badge');
      if (gameState === 'check' && nextPlayer === myColor) {
        badge.className   = 'turn-badge in-check';
        badge.textContent = '⚠️ Check! Defend your king.';
      } else if (nextPlayer === myColor) {
        badge.className   = 'turn-badge my-turn';
        badge.textContent = '✅ Your turn – move a piece';
      } else if (gameState === 'check') {
        badge.className   = 'turn-badge wait';
        badge.textContent = '⏳ Opponent is in check!';
      } else {
        badge.className   = 'turn-badge wait';
        badge.textContent = "⏳ Opponent's turn";
      }
    }

    // ── Game over overlay ──────────────────────────────────────────────────
    function showGameOver(type, loser) {
      if (type === 'checkmate') {
        const winner = loser === 'white' ? 'Black' : 'White';
        document.getElementById('ov-icon').textContent  = winner === 'White' ? '♔' : '♚';
        document.getElementById('ov-title').textContent = 'Checkmate!';
        document.getElementById('ov-sub').textContent   = `${winner} wins 🏆`;
      } else {
        document.getElementById('ov-icon').textContent  = '🤝';
        document.getElementById('ov-title').textContent = 'Stalemate!';
        document.getElementById('ov-sub').textContent   = "It's a draw";
      }
      document.getElementById('gameover').classList.add('show');
    }

    // ── Copy link ──────────────────────────────────────────────────────────
    function copyLink() {
      navigator.clipboard.writeText(SHARE_URL)
        .then(() => {
          const btn = document.getElementById('copy-btn');
          btn.textContent = '✅ Copied!';
          btn.classList.add('copied');
          setTimeout(() => {
            btn.textContent = '📋 Copy Invite Link';
            btn.classList.remove('copied');
          }, 2000);
        })
        .catch(() => prompt('Copy this link:', SHARE_URL));
    }

    // Initial render
    renderBoard();
    document.getElementById('waiting').classList.add('show');
  </script>
</body>
</html>
"""


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import socket, io
    # Ensure UTF-8 output on Windows terminals
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        local_ip = '127.0.0.1'

    print()
    print("  [Chess Online] Web Server started")
    print("  " + "-" * 46)
    print(f"  Local   -> http://localhost:8000")
    print(f"  Network -> http://{local_ip}:8000")
    print()
    print("  For internet play (share with anyone):")
    print("    ngrok http 8000  (then share the https URL)")
    print("  " + "-" * 46)
    print()

    uvicorn.run(app, host='0.0.0.0', port=8000, log_level='warning')
