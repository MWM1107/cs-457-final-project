# Server Concurrency & Architecture Design

## 1. Concurrency Model Selection
For this Yahtzee server, I am using the **Multi-Threading** model (`threading.Thread` in Python). 

### Connection Lifecycle
1. **Listening:** The server's main thread creates a TCP listening socket, binds it to the port, and enters a `while True` loop calling `sock.accept()`.
2. **Client Registration:** When a client connects, the main thread accepts the connection, adds the new client's socket to a shared dictionary, and immediately spawns a dedicated worker thread (`threading.Thread(target=handle_client, args=(client_sock,))`) to listen for incoming messages from that specific user. 
3. **Active Loop Servicing:** Inside the worker thread, the server runs a `while True` loop calling the custom `recv_msg()` function we built in Sprint 1. This allows the server to simultaneously listen for incoming data from both Player 1 and Player 2 without one blocking the other.
4. **Teardown:** If a client drops or sends a `DISCONNECT`, their specific worker thread handles the socket closure, triggers the forfeit logic, and terminates itself gracefully.

## 2. Thread Safety & Lock Acquisition Strategy
Because multiple threads are running at the same time, we have to prevent race conditions where both threads try to change the game state simultaneously.

### Shared Resources
The following variables exist in the main server memory and are shared across both client worker threads:
- `client_sockets` (Dictionary mapping Player IDs to their socket objects)
- `active_turn` (String tracking whose turn it is)
- `dice_state` (Array of the current 5 dice values)
- `rolls_remaining` (Integer tracking the current player's rolls)
- `scorecards` (Dictionary holding both players' 13 Yahtzee categories and total scores)

### Locking Mechanism (`threading.Lock`)
I am using a single `game_state_lock = threading.Lock()` to isolate and protect the shared state. 

**Critical Sections:**
Whenever a worker thread receives a `MOVE` message from a client, it must acquire the lock before processing it:
```python
with game_state_lock:
    # 1. Validate if it is this player's turn
    # 2. Validate the move (e.g., category is empty, rolls > 0)
    # 3. Mutate the dice_state or scorecards
    # 4. Switch the active_turn if the player scored
    # 5. Broadcast STATE_UPDATE to both client_sockets