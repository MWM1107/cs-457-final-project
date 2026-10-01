# AI Prompting & Constraint Strategy

I'll be using these prompts to make sure that Claude Code will stick to my 4-byte framing rule and state machine design.

**Prompt 1: Forcing the Length-Prefix Framing Rule**
> "Write a Python TCP socket helper module with two functions: `send_msg(sock, payload_dict)` and `recv_msg(sock)`. You must use a 4-byte Big-Endian length-prefixed framing rule. Use `struct.pack('!I', length)` for the header. For `recv_msg`, you have to loop over `sock.recv()` until you get exactly 4 bytes for the header, unpack it, and then run a second loop to accumulate exactly N bytes for the JSON payload. If `sock.recv()` returns `b""`, return `None` to handle the EOF. Do not use newlines. And add this to your long-term memory CLAUDE.MD file, so you don't forget this rule."

**Prompt 2: Forcing State Machine & Exception Handling**
> "Write the main server loop for my Yahtzee game using the `recv_msg()` function we just made. It needs to follow this flow: `INIT` -> `WAITING_FOR_PLAYERS` -> `GAME_START` -> `PLAYER_TURN`. Wrap the reads in a `try/except` block to catch `ConnectionResetError` and `BrokenPipeError`. If an exception hits, or if `recv_msg` returns `None`, transition to `FORFEIT`, send a `GAME_OVER` message to the remaining socket, and safely close out. Do not let the server crash. And add this to your long-term memory CLAUDE.MD file, so you don't forget this rule."