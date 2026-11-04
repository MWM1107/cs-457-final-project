# Sprint 3: Intermediate Gameplay Execution Log

This log demonstrates graceful DNS failure handling (`socket.gaierror`), simultaneous two-client connections (`Kevin_S` and `Steven_S`), server-side FSM state transitions, and synchronous scoreboard broadcasts across 3 complete turns on `localhost:8080`.

---

## 1. Server Console Output (`server.py`)

```text
PS C:\GitHub Repos\cs-457-final-project> python server.py -p 8080 
[FSM] State -> WAITING_FOR_PLAYERS
[SERVER] Yahtzee Server listening on 0.0.0.0:8080
[INFO] Player 'Kevin_S' connected from ('127.0.0.1', 62654).
[FSM] State -> LOBBY_WAIT
[INFO] Player 'Steven_S' connected from ('127.0.0.1', 62656).
[FSM] State -> GAME_START
[FSM] State -> PLAYER_TURN (Active: Kevin_S)
[FSM] State -> EVALUATE_MOVE (From: Kevin_S)
[FSM] State -> BROADCAST_STATE
[FSM] State -> PLAYER_TURN (Active: Kevin_S)
[FSM] State -> EVALUATE_MOVE (From: Kevin_S)
[FSM] State -> SCORE_UPDATE (Kevin_S scored 19 in chance)
[FSM] State -> CHECK_WIN_DRAW
[FSM] State -> PLAYER_TURN (Active: Steven_S)
[FSM] State -> EVALUATE_MOVE (From: Steven_S)
[FSM] State -> BROADCAST_STATE
[FSM] State -> PLAYER_TURN (Active: Steven_S)
[FSM] State -> EVALUATE_MOVE (From: Steven_S)
[FSM] State -> SCORE_UPDATE (Steven_S scored 1 in ones)
[FSM] State -> CHECK_WIN_DRAW
[FSM] State -> PLAYER_TURN (Active: Kevin_S)
[FSM] State -> EVALUATE_MOVE (From: Kevin_S)
[FSM] State -> SCORE_UPDATE (Kevin_S scored 3 in threes)
[FSM] State -> CHECK_WIN_DRAW
[FSM] State -> PLAYER_TURN (Active: Steven_S)
```

## 2. Client 1 Console Output (Kevin_S & Graceful DNS Error Test)

```text
PS C:\GitHub Repos\cs-457-final-project> python client.py -i server.struna.edu -p 8080 
[ERROR] Unable to resolve DNS hostname 'server.struna.edu'.
Please check your Cisco router DNS configuration ('ip dns server' / 'ip host') or verify domain spelling.
PS C:\GitHub Repos\cs-457-final-project> python client.py -i localhost -p 8080 
Enter your player alias (e.g., Kevin_S): Kevin_S
[CONNECTED] Connected to localhost (127.0.0.1:8080) as 'Kevin_S'.

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
Current Dice: [0]:6  [1]:4  [2]:5  [3]:2  [4]:1   (Rolls Remaining: 2)

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
Current Dice: [0]:6  [1]:4  [2]:1  [3]:4  [4]:4   (Rolls Remaining: 1)

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
chance               | 19              | -              
----------------------------------------------------------
TOTAL SCORE          | 19              | 0              
==========================================================
Active Turn : Steven_S
Current Dice: [0]:4  [1]:1  [2]:3  [3]:5  [4]:2   (Rolls Remaining: 2)

--- Waiting for Steven_S to complete their turn... ---
> 
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
chance               | 19              | -              
----------------------------------------------------------
TOTAL SCORE          | 19              | 0              
==========================================================
Active Turn : Steven_S
Current Dice: [0]:5  [1]:5  [2]:1  [3]:6  [4]:2   (Rolls Remaining: 1)

--- Waiting for Steven_S to complete their turn... ---
> 
==========================================================
                 YAHTZEE SCOREBOARD
==========================================================
Category             | Kevin_S         | Steven_S       
----------------------------------------------------------
ones                 | -               | 1              
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
chance               | 19              | -              
----------------------------------------------------------
TOTAL SCORE          | 19              | 1              
==========================================================
Active Turn : Kevin_S
Current Dice: [0]:3  [1]:2  [2]:1  [3]:1  [4]:1   (Rolls Remaining: 2)

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
ones                 | -               | 1              
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
chance               | 19              | -              
----------------------------------------------------------
TOTAL SCORE          | 22              | 1              
==========================================================
Active Turn : Steven_S
Current Dice: [0]:2  [1]:3  [2]:5  [3]:2  [4]:1   (Rolls Remaining: 2)

--- Waiting for Steven_S to complete their turn... ---
>
```

## 3. Client 2 Console Output (Steven_S)

```text
PS C:\GitHub Repos\cs-457-final-project> python client.py -i localhost -p 8080 
Enter your player alias (e.g., Kevin_S): Steven_S
[CONNECTED] Connected to localhost (127.0.0.1:8080) as 'Steven_S'.

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
Current Dice: [0]:6  [1]:4  [2]:5  [3]:2  [4]:1   (Rolls Remaining: 2)

--- Waiting for Kevin_S to complete their turn... ---
> 
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
Current Dice: [0]:6  [1]:4  [2]:1  [3]:4  [4]:4   (Rolls Remaining: 1)

--- Waiting for Kevin_S to complete their turn... ---
> 
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
chance               | 19              | -              
----------------------------------------------------------
TOTAL SCORE          | 19              | 0              
==========================================================
Active Turn : Steven_S
Current Dice: [0]:4  [1]:1  [2]:3  [3]:5  [4]:2   (Rolls Remaining: 2)

>>> YOUR TURN! Commands:
  hold <idx...>  - Hold dice at indices 0-4 & reroll rest (e.g., 'hold 0 2 4')
  roll           - Reroll all 5 dice
  score <cat>    - Score a category (e.g., 'score full_house' or 'score threes')
  quit           - Disconnect and forfeit
> roll

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
chance               | 19              | -              
----------------------------------------------------------
TOTAL SCORE          | 19              | 0              
==========================================================
Active Turn : Steven_S
Current Dice: [0]:5  [1]:5  [2]:1  [3]:6  [4]:2   (Rolls Remaining: 1)

>>> YOUR TURN! Commands:
  hold <idx...>  - Hold dice at indices 0-4 & reroll rest (e.g., 'hold 0 2 4')
  roll           - Reroll all 5 dice
  score <cat>    - Score a category (e.g., 'score full_house' or 'score threes')
  quit           - Disconnect and forfeit
> score ones

==========================================================
                 YAHTZEE SCOREBOARD
==========================================================
Category             | Kevin_S         | Steven_S       
----------------------------------------------------------
ones                 | -               | 1              
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
chance               | 19              | -              
----------------------------------------------------------
TOTAL SCORE          | 19              | 1              
==========================================================
Active Turn : Kevin_S
Current Dice: [0]:3  [1]:2  [2]:1  [3]:1  [4]:1   (Rolls Remaining: 2)

--- Waiting for Kevin_S to complete their turn... ---
> 
==========================================================
                 YAHTZEE SCOREBOARD
==========================================================
Category             | Kevin_S         | Steven_S       
----------------------------------------------------------
ones                 | -               | 1              
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
chance               | 19              | -              
----------------------------------------------------------
TOTAL SCORE          | 22              | 1              
==========================================================
Active Turn : Steven_S
Current Dice: [0]:2  [1]:3  [2]:5  [3]:2  [4]:1   (Rolls Remaining: 2)

>>> YOUR TURN! Commands:
  hold <idx...>  - Hold dice at indices 0-4 & reroll rest (e.g., 'hold 0 2 4')
  roll           - Reroll all 5 dice
  score <cat>    - Score a category (e.g., 'score full_house' or 'score threes')
  quit           - Disconnect and forfeit
>
```