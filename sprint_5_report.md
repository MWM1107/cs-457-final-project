# CS 457 - Sprint 5: Impairment, Reconnection & Architectural Report

**Student Name:** Kevin Struna  
**Course:** CS 457 - Computer Networks  
**Target Server Domain:** `server.struna.edu` (`192.168.20.100`)  
**Walkthrough Video Link:** [sprint_5_video_walkthrough.mp4](./sprint_5_video_walkthrough.mp4)

---

## Part A: Impairment & Stateful Reconnection Testing

### 1. CML Link Condition Parameters
Applied link impairments on the `ks-R1 (Gi0/3) <-> ks-Server (eth0)` link (`192.168.20.0/24`):
- **Latency:** 150 ms
- **Jitter:** 20 ms
- **Packet Loss:** 8%

![CML Link Impairment Settings](./cml_link_impairment.jpeg)

---

### 2. Wireshark Link Degradation Analysis (`sprint_5_degraded_network.pcap`)

#### 2.1 TCP Retransmissions (`tcp.analysis.retransmission`)
- **Frame 38:** `192.168.20.100 -> 192.168.11.2` (`[TCP Retransmission]`, `Seq=292`, `Len=178`).
- **Frame 39:** `192.168.20.100 -> 192.168.10.2` (`[TCP Retransmission]`, `Seq=360`, `Len=178`).
- **Frame 109:** `192.168.20.100 -> 192.168.10.2` (`[TCP Retransmission]`, `Seq=322`, `Len=218`).

![TCP Retransmissions](./Retransmissions%20Screenshot.png)

#### 2.2 Duplicate Acknowledgments (`tcp.options.sack`)
Because each Yahtzee move and state update fits in a single packet, dropped ACKs caused the server to retransmit and the clients to reply with Duplicate Selective Acknowledgments (D-SACK):
- **Frame 40 (`192.168.11.2 -> 192.168.20.100`):** `Ack=470` with `SLE=292 SRE=470` (duplicate of Frame 38).
- **Frame 41 (`192.168.10.2 -> 192.168.20.100`):** `Ack=538` with `SLE=360 SRE=538` (duplicate of Frame 39).
- **Frame 110 (`192.168.10.2 -> 192.168.20.100`):** `Ack=540` with `SLE=322 SRE=540` (duplicate of Frame 109).

![TCP Duplicate ACKs](./Duplicate%20ACKs%20Screenshot.png)

#### 2.3 TCP Timeouts, RTT Delay Analysis & Abrupt Disconnect/Reconnect Trace
- **RTO Timeout (Frames 36 to 39):** Frame 36 (`14:56:04.373281`) to Frame 39 (`14:56:05.541179`) shows a **1.168-second timeout** before retransmission.
- **RTO Timeout (Frames 107 to 109):** Frame 107 (`14:58:23.440179`) to Frame 109 (`14:58:24.262545`) shows an **822 ms timeout**.
- **Disconnect & Reconnect (Frames 73 and 84–90):** Frame 73 shows the `[RST, ACK]` when `Kevin_S` pressed `Ctrl+C`. Frames 84–90 show `Kevin_S` reconnecting on port `54708` and receiving `STATE_RESUME`.

![TCP RTT Delays and Timeouts](./RTT%20Delay%20and%20Timeout%20Screenshot.png)

---

### 3. Stateful Reconnection Console Logs

#### 3.1 Server Console Output (`ks-Server` - `192.168.20.100`)

```text
inserthostname-here:~$ python3 server.py -p 8080
[FSM] State -> WAITING_FOR_PLAYERS
[SERVER] Yahtzee Server listening on 0.0.0.0:8080
[INFO] Player 'Kevin_S' connected from ('192.168.10.2', 51530).
[FSM] State -> LOBBY_WAIT
[INFO] Player 'Steven_S' connected from ('192.168.11.2', 34702).
[FSM] State -> GAME_START
[FSM] State -> PLAYER_TURN (Active: Kevin_S)
[FSM] State -> EVALUATE_MOVE (From: Kevin_S)
[FSM] State -> BROADCAST_STATE
[FSM] State -> PLAYER_TURN (Active: Kevin_S)
[FSM] State -> EVALUATE_MOVE (From: Kevin_S)
[FSM] State -> SCORE_UPDATE (Kevin_S scored 15 in chance)
[FSM] State -> CHECK_WIN_DRAW
[FSM] State -> PLAYER_TURN (Active: Steven_S)
[FSM] State -> EVALUATE_MOVE (From: Steven_S)
[FSM] State -> BROADCAST_STATE
[FSM] State -> PLAYER_TURN (Active: Steven_S)
[FSM] State -> EVALUATE_MOVE (From: Steven_S)
[FSM] State -> SCORE_UPDATE (Steven_S scored 0 in ones)
[FSM] State -> CHECK_WIN_DRAW
[FSM] State -> PLAYER_TURN (Active: Kevin_S)
[WARN] ConnectionResetError caught for 'Kevin_S': [Errno 104] Connection reset by peer
[FSM] State -> TEMPORARILY_DISCONNECTED ('Kevin_S' dropped)
[STATE PRESERVED] Holding game state & scores in memory. Starting 60s reconnect grace timer for 'Kevin_S'.
[RECONNECT] Player 'Kevin_S' reconnected from ('192.168.10.2', 54708)!
[RECONNECT] Re-binding socket and restoring preserved game state.
[FSM] State -> PLAYER_TURN (Active: Kevin_S)
[FSM] State -> EVALUATE_MOVE (From: Kevin_S)
[FSM] State -> SCORE_UPDATE (Kevin_S scored 3 in threes)
[FSM] State -> CHECK_WIN_DRAW
[FSM] State -> PLAYER_TURN (Active: Steven_S)
```

#### 3.2 Client 1 Console Output (`ks-Client1` - `192.168.10.2` Disconnect & Reconnect)

```text
inserthostname-here:~$ python3 client.py -i server.struna.edu -p 8080
Enter your player alias (e.g., Kevin_S): Kevin_S
[CONNECTED] Connected to server.struna.edu (192.168.20.100:8080) as 'Kevin_S'.

[LOBBY] Waiting for opponent...

[GAME START] Match initiated! Roles: {'Kevin_S': 'Player_1', 'Steven_S': 'Player_2'}. First turn: Kevin_S

==========================================================
                 YAHTZEE SCOREBOARD
==========================================================
Category             | Kevin_S         | Steven_S       
----------------------------------------------------------
ones                 | -               | -              
twos                 | -               | -              
threes               | -               | -              
fours                | -               | -              
fives                | -               | -              
sixes                | -               | -              
three_of_a_kind      | -               | -              
four_of_a_kind       | -               | -              
full_house           | -               | -              
small_straight       | -               | -              
large_straight       | -               | -              
yahtzee              | -               | -              
chance               | -               | -              
----------------------------------------------------------
TOTAL SCORE          | 0               | 0              
==========================================================
Active Turn : Kevin_S
Current Dice: [0]:1  [1]:3  [2]:2  [3]:5  [4]:6   (Rolls Remaining: 2)

>>> YOUR TURN! Commands:
  hold <idx...>  - Hold dice at indices 0-4 & reroll rest (e.g., 'hold 0 2 4')
  roll           - Reroll all 5 dice
  score <cat>    - Score a category (e.g., 'score full_house' or 'score threes')
  quit           - Disconnect and forfeit
> hold 0 1

==========================================================
                 YAHTZEE SCOREBOARD
==========================================================
Category             | Kevin_S         | Steven_S       
----------------------------------------------------------
ones                 | -               | -              
twos                 | -               | -              
threes               | -               | -              
fours                | -               | -              
fives                | -               | -              
sixes                | -               | -              
three_of_a_kind      | -               | -              
four_of_a_kind       | -               | -              
full_house           | -               | -              
small_straight       | -               | -              
large_straight       | -               | -              
yahtzee              | -               | -              
chance               | -               | -              
----------------------------------------------------------
TOTAL SCORE          | 0               | 0              
==========================================================
Active Turn : Kevin_S
Current Dice: [0]:1  [1]:3  [2]:5  [3]:4  [4]:2   (Rolls Remaining: 1)

>>> YOUR TURN! Commands:
  hold <idx...>  - Hold dice at indices 0-4 & reroll rest (e.g., 'hold 0 2 4')
  roll           - Reroll all 5 dice
  score <cat>    - Score a category (e.g., 'score full_house' or 'score threes')
  quit           - Disconnect and forfeit
> score chance

==========================================================
                 YAHTZEE SCOREBOARD
==========================================================
Category             | Kevin_S         | Steven_S       
----------------------------------------------------------
ones                 | -               | -              
twos                 | -               | -              
threes               | -               | -              
fours                | -               | -              
fives                | -               | -              
sixes                | -               | -              
three_of_a_kind      | -               | -              
four_of_a_kind       | -               | -              
full_house           | -               | -              
small_straight       | -               | -              
large_straight       | -               | -              
yahtzee              | -               | -              
chance               | 15              | -              
----------------------------------------------------------
TOTAL SCORE          | 15              | 0              
==========================================================
Active Turn : Steven_S
Current Dice: [0]:5  [1]:6  [2]:3  [3]:6  [4]:5   (Rolls Remaining: 2)

--- Waiting for Steven_S to complete their turn... ---
> 
==========================================================
                 YAHTZEE SCOREBOARD
==========================================================
Category             | Kevin_S         | Steven_S       
----------------------------------------------------------
ones                 | -               | 0              
twos                 | -               | -              
threes               | -               | -              
fours                | -               | -              
fives                | -               | -              
sixes                | -               | -              
three_of_a_kind      | -               | -              
four_of_a_kind       | -               | -              
full_house           | -               | -              
small_straight       | -               | -              
large_straight       | -               | -              
yahtzee              | -               | -              
chance               | 15              | -              
----------------------------------------------------------
TOTAL SCORE          | 15              | 0              
==========================================================
Active Turn : Kevin_S
Current Dice: [0]:6  [1]:1  [2]:3  [3]:6  [4]:4   (Rolls Remaining: 2)

>>> YOUR TURN! Commands:
  hold <idx...>  - Hold dice at indices 0-4 & reroll rest (e.g., 'hold 0 2 4')
  roll           - Reroll all 5 dice
  score <cat>    - Score a category (e.g., 'score full_house' or 'score threes')
  quit           - Disconnect and forfeit
> ^C
[CLIENT] Simulating abrupt disconnect (TCP RST)...
inserthostname-here:~$ python3 client.py -i server.struna.edu -p 8080
Enter your player alias (e.g., Kevin_S): Kevin_S
[CONNECTED] Connected to server.struna.edu (192.168.20.100:8080) as 'Kevin_S'.

[STATE_RESUME] Session restored! Resuming match without state loss.

[STATUS] Player 'Kevin_S' reconnected! Game resumed without state loss.

==========================================================
                 YAHTZEE SCOREBOARD
==========================================================
Category             | Kevin_S         | Steven_S       
----------------------------------------------------------
ones                 | -               | 0              
twos                 | -               | -              
threes               | -               | -              
fours                | -               | -              
fives                | -               | -              
sixes                | -               | -              
three_of_a_kind      | -               | -              
four_of_a_kind       | -               | -              
full_house           | -               | -              
small_straight       | -               | -              
large_straight       | -               | -              
yahtzee              | -               | -              
chance               | 15              | -              
----------------------------------------------------------
TOTAL SCORE          | 15              | 0              
==========================================================
Active Turn : Kevin_S
Current Dice: [0]:6  [1]:1  [2]:3  [3]:6  [4]:4   (Rolls Remaining: 2)

>>> YOUR TURN! Commands:
  hold <idx...>  - Hold dice at indices 0-4 & reroll rest (e.g., 'hold 0 2 4')
  roll           - Reroll all 5 dice
  score <cat>    - Score a category (e.g., 'score full_house' or 'score threes')
  quit           - Disconnect and forfeit
> score threes

==========================================================
                 YAHTZEE SCOREBOARD
==========================================================
Category             | Kevin_S         | Steven_S       
----------------------------------------------------------
ones                 | -               | 0              
twos                 | -               | -              
threes               | 3               | -              
fours                | -               | -              
fives                | -               | -              
sixes                | -               | -              
three_of_a_kind      | -               | -              
four_of_a_kind       | -               | -              
full_house           | -               | -              
small_straight       | -               | -              
large_straight       | -               | -              
yahtzee              | -               | -              
chance               | 15              | -              
----------------------------------------------------------
TOTAL SCORE          | 18              | 0              
==========================================================
Active Turn : Steven_S
Current Dice: [0]:6  [1]:2  [2]:3  [3]:6  [4]:3   (Rolls Remaining: 2)

--- Waiting for Steven_S to complete their turn... ---
> 
```

#### 3.3 Client 2 Console Output (`ks-Client2` - `192.168.11.2` Notification & Resumption)

```text
inserthostname-here:~$ python3 client.py -i server.struna.edu -p 8080
Enter your player alias (e.g., Kevin_S): Steven_S
[CONNECTED] Connected to server.struna.edu (192.168.20.100:8080) as 'Steven_S'.

[GAME START] Match initiated! Roles: {'Kevin_S': 'Player_1', 'Steven_S': 'Player_2'}. First turn: Kevin_S

[STATUS] Kevin_S disconnected. Waiting 60s for reconnect...

==========================================================
                 YAHTZEE SCOREBOARD
==========================================================
Category             | Kevin_S         | Steven_S       
----------------------------------------------------------
ones                 | -               | 0              
twos                 | -               | -              
threes               | -               | -              
fours                | -               | -              
fives                | -               | -              
sixes                | -               | -              
three_of_a_kind      | -               | -              
four_of_a_kind       | -               | -              
full_house           | -               | -              
small_straight       | -               | -              
large_straight       | -               | -              
yahtzee              | -               | -              
chance               | 15              | -              
----------------------------------------------------------
TOTAL SCORE          | 15              | 0              
==========================================================
Active Turn : Kevin_S
Current Dice: [0]:6  [1]:1  [2]:3  [3]:6  [4]:4   (Rolls Remaining: 2)

--- Waiting for Kevin_S to complete their turn... ---
> 
[STATE_RESUME] Session restored! Resuming match without state loss.

[STATUS] Player 'Kevin_S' reconnected! Game resumed without state loss.

==========================================================
                 YAHTZEE SCOREBOARD
==========================================================
Category             | Kevin_S         | Steven_S       
----------------------------------------------------------
ones                 | -               | 0              
twos                 | -               | -              
threes               | 3               | -              
fours                | -               | -              
fives                | -               | -              
sixes                | -               | -              
three_of_a_kind      | -               | -              
four_of_a_kind       | -               | -              
full_house           | -               | -              
small_straight       | -               | -              
large_straight       | -               | -              
yahtzee              | -               | -              
chance               | 15              | -              
----------------------------------------------------------
TOTAL SCORE          | 18              | 0              
==========================================================
Active Turn : Steven_S
Current Dice: [0]:6  [1]:2  [2]:3  [3]:6  [4]:3   (Rolls Remaining: 2)

>>> YOUR TURN! Commands:
  hold <idx...>  - Hold dice at indices 0-4 & reroll rest (e.g., 'hold 0 2 4')
  roll           - Reroll all 5 dice
  score <cat>    - Score a category (e.g., 'score full_house' or 'score threes')
  quit           - Disconnect and forfeit
> 
```

---

## Part B: Architectural Choices & Project Retrospective

### 1. Architectural Model Selection (Threads vs. Selectors)
- **Why I chose `threading`:** I used `threading.Thread` instead of `selectors` because Yahtzee only has 2 players. Having one thread per player let me use simple blocking `recv()` loops instead of managing non-blocking state callbacks.
- **Trade-offs:** Threads use more memory and context-switching overhead than `selectors`, which would be a problem with thousands of connections, but for 2 players in CML it doesn't matter.
- **Locking & State:** Since both client threads share the same scoreboard and dice variables, I used `threading.Lock()` (`self.game_state_lock`) so two threads can't update the game state at the same time.

---

### 2. Library Choices & Rationale

| Library | How I Used It |
| :--- | :--- |
| `socket` | TCP connections (`AF_INET`, `SOCK_STREAM`), DNS lookup (`gethostbyname`), and catching `socket.gaierror`. |
| `struct` | Packing and unpacking the 4-byte `!I` length header for message framing. |
| `json` | Encoding and decoding the game messages (`CONNECT`, `MOVE`, `STATE_UPDATE`, `STATE_RESUME`). |
| `threading` | Running client handler threads, the 60-second reconnect `Timer`, and `Lock` for thread safety. |
| `argparse` | Parsing `-h`, `-i`, and `-p` command-line flags. |
| `collections` | Using `Counter` to count matching dice faces for scoring categories like Full House and Yahtzee. |
| `random` | Rolling the 5 dice (1–6) on the server. |
| `sys` | Exiting cleanly (`sys.exit(1)`) on connection or DNS errors. |

---

### 3. Project Retrospective

#### What Went Right
- **4-Byte Length Header:** Using the 4-byte length prefix from Sprint 1 made reading packets reliable, even when the 8% packet loss in Sprint 5 caused delays and retransmissions.
- **Server-Side Game State:** Keeping all the scores and dice on `server.py` made `STATE_RESUME` easy to add, since the server already had everything saved in memory when a client dropped.
- **Testing With Another Player:** Testing the game in the command line with another player online was fun and went smoothly. 

#### What Could Be Improved
- **Installing Python & DNS in CML:** The Alpine Linux nodes in CML didn't have `python3` installed by default, so I had to wire up an External Connector (`ext-conn-0`) with NAT to install it, and then fix an IPv6 `NXDOMAIN` issue when `ks-R1` forwarded DNS queries outside the lab.
- **Terminal Scrollback:** Printing the full 26-line scoreboard on every update pushed the `[STATUS]` disconnect message above the visible terminal window on Client 2 unless I scrolled up.
- **New Game:** If I did this project again, I would choose to invent my own original game. Yahtzee is fun to play, but since AI was used in the project, it quickly prototyped and understood the rules.