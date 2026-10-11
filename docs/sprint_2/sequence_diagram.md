# State & Score Broadcast Sequence Diagram

This diagram illustrates the round-trip flow when a client attempts to make a move (scoring a Yahtzee category). It shows the server's thread-safe validation, turn enforcement, and the synchronous broadcast used to keep both clients' scoreboards updated.

```mermaid
sequenceDiagram
    autonumber
    actor P1 as Client 1 (Player 1)
    participant Server as Game Server
    actor P2 as Client 2 (Player 2)

    P1->>Server: MOVE (action: "score", category: "full_house")
    
    Note over Server: Server acquires threading.Lock()
    Note over Server: Validates: Is it Player 1's turn?<br>Is "full_house" empty?
    
    alt Valid Move & Turn
        Note over Server: Update P1 Scorecard<br>Calculate New Total<br>Switch Turn to Player 2
        Server-->>P1: STATE_UPDATE (Scores, Turn: Player 2)
        Server-->>P2: STATE_UPDATE (Scores, Turn: Player 2)
    else Invalid Category or Out of Turn
        Note over Server: State remains unchanged
        Server-->>P1: ERROR ("Category already filled" or "Not your turn")
    end
    
    Note over Server: Server releases threading.Lock()