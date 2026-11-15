# Game State Machine (FSM) Specification

Here is the state diagram for the server logic. It maps out how the server handles turn orders, validates incoming JSON moves, and safely manages abrupt network drops without crashing.

```mermaid
stateDiagram-v2
    [*] --> INIT
    
    INIT --> WAITING_FOR_PLAYERS : Server Started
    WAITING_FOR_PLAYERS --> LOBBY_WAIT : Player 1 Connects
    LOBBY_WAIT --> GAME_START : Player 2 Connects
    
    GAME_START --> PLAYER_TURN : Assign Roles & Initialize Scorecards
    
    PLAYER_TURN --> EVALUATE_MOVE : Valid JSON MOVE Received
    PLAYER_TURN --> PLAYER_TURN : Invalid Format (Send ERROR)
    
    EVALUATE_MOVE --> PLAYER_TURN : Move Out-of-Turn / Invalid Rule (Send ERROR)
    EVALUATE_MOVE --> BROADCAST_STATE : Valid Roll/Hold (Rolls Left > 0)
    EVALUATE_MOVE --> SCORE_UPDATE : Valid Score Selection
    
    BROADCAST_STATE --> PLAYER_TURN : Wait for Next Action
    
    SCORE_UPDATE --> CHECK_WIN_DRAW : Update Scorecard
    
    CHECK_WIN_DRAW --> PLAYER_TURN : Rounds < 13 (Switch Active Player)
    CHECK_WIN_DRAW --> GAME_OVER : Rounds == 13 (All Categories Filled)
    
    %% Handling network drops and quits
    WAITING_FOR_PLAYERS --> CLEANUP : TCP EOF / RST
    LOBBY_WAIT --> CLEANUP : TCP EOF / RST
    PLAYER_TURN --> FORFEIT : DISCONNECT / TCP EOF / RST
    
    FORFEIT --> GAME_OVER : Declare Opponent Winner
    GAME_OVER --> CLEANUP : Broadcast Final Scores
    CLEANUP --> [*] : Close Sockets & Release Threads