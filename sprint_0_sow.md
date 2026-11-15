# CS 457 Project Statement of Work (SOW) & Protocol Specification Template

**Student Name:** Kevin Struna  
**Date:** 2026-09-17  
**Course:** CS 457 - Computer Networks  
**Target Server Domain:** `server.struna.edu`  

---

## 1. Game Selection & Scope (Sprint 0)

### 1.1 Game Overview
- **Chosen Game:** Yahtzee (Terminal Edition)
- **Player Capacity:** 2 Players (Simulated via 2 CML Client nodes)
- **Game Summary:** A two-player, turn-based CLI adaptation of the dice game Yahtzee. The server drives the game engine, rolling the virtual dice and maintaining the scorecard for both players.

### 1.2 Core Game Rules & Win/Draw Conditions
- **Turn Mechanics:** Players take alternating turns. On a player's turn, the server rolls five virtual dice. The active player can choose to hold on to specific dice and reroll the rest up to two additional times. At the end of the turn, the player must select an available category on their scorecard to record their points. The server then passes the turn to the opponent.
- **Victory Condition:** The game ends after 13 rounds when both players have filled in all the categories on their scorecards. The server will then tally the final points, and the player with the highest total score wins.
- **Draw/Tie Condition:** If both players finish the 13th round with the exact same total score, the game is a draw.
