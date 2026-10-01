# Application Protocol Blueprint

## 1. Transport Layer & Packet Framing Mechanism
- **Protocol:** TCP
- **Data Format:** JSON (UTF-8 encoded)
- **Framing Rule:** I'm using a 4-byte Big-Endian length prefix for every message.

### Wire Stream Example (Continuous Stream):
Here is what the raw stream looks like when two messages are sent back-to-back:
```text
[4-Byte Length: 0x00000041] {"msg_type":"CONNECT","player_id":"Kevin_S","timestamp":1727000000} [4-Byte Length: 0x00000062] {"msg_type":"MOVE","player_id":"Kevin_S","payload":{"action":"score","category":"full_house"}}
```

## 2. Application Message Types

### 1. `CONNECT` (Client -> Server)
Sent when a player wants to join the room.
```json
{
  "msg_type": "CONNECT",
  "player_id": "Kevin_S"
}
```

### 2. `LOBBY_WAIT` (Server -> Client)
Lets the first player know they are in, but the server is still waiting on Player 2.
```json
{
  "msg_type": "LOBBY_WAIT",
  "message": "Waiting for opponent..."
}
```

### 3. `GAME_START` (Server -> Clients)
Broadcasted to both clients once the room is full.
```json
{
  "msg_type": "GAME_START",
  "roles": {"Kevin_S": "Player_1", "Opponent": "Player_2"},
  "first_turn": "Kevin_S"
}
```

### 4. `MOVE` (Client -> Server)
The active player's action (e.g., rolling, holding, or scoring).
```json
{
  "msg_type": "MOVE",
  "player_id": "Kevin_S",
  "payload": {
    "action": "hold", 
    "dice_indices": [0, 2, 4] 
  }
}
```

### 5. `STATE_UPDATE` (Server -> Clients)
Pushes the current board state (i.e., dice, rolls left, current scores, etc.) to both clients.
```json
{
  "msg_type": "STATE_UPDATE",
  "active_player": "Kevin_S",
  "rolls_remaining": 2,
  "current_dice": [3, 3, 5, 1, 3],
  "scores": {
    "Kevin_S": {"threes": 9, "total": 9},
    "Opponent": {"total": 0}
  }
}
```

### 6. `ERROR` (Server -> Client)
Sent if a client sends a bad request, like trying to score a category they already filled or playing out of turn.
```json
{
  "msg_type": "ERROR",
  "error_code": "INVALID_CATEGORY",
  "message": "You already scored a full house."
}
```

### 7. `DISCONNECT` (Client -> Server)
A clean quit message sent right before the client closes the socket.
```json
{
  "msg_type": "DISCONNECT",
  "player_id": "Kevin_S"
}
```

### 8. `GAME_OVER` (Server -> Clients)
Announces the final results and scores at the end of the 13 rounds, or if someone forfeits.
```json
{
  "msg_type": "GAME_OVER",
  "winner": "Kevin_S",
  "final_scores": {"Kevin_S": 245, "Opponent": 210},
  "reason": "standard_win" 
}
```

## 3. Connection Termination & Socket Lifecycle Management

**Graceful Disconnects:**
If a user quits normally, the client sends the `DISCONNECT` JSON message and calls `sock.close()`. The server sees this, ends the game, declares a forfeit for the remaining player, and closes its end of the sockets.

**Handling Dropped Connections:**
We need to handle multiple scenarios without crashing the server:
1. **0-Byte EOF (End-of-File):** The server's `recv()` loop will check if it receives `b""` (0 bytes). If it does, that means the TCP connection was closed by the other side. The server will immediately break the loop.
2. **Exceptions:** I'll be wrapping the network calls in a `try/except` blocks to catch errors, like `ConnectionResetError` and `BrokenPipeError`. 
3. If either of these happen, the server transitions to a `FORFEIT` state, tells the other player they won, and cleans up the threads.