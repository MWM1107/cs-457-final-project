#!/usr/bin/env python3
"""
CS 457 Final Project - Sprint 3: Yahtzee Authoritative Game Server
Implements 4-byte Big-Endian length-prefixed framing, multi-threaded client
handling, thread-safe state synchronization, and the Yahtzee Game FSM.
"""

import argparse
from collections import Counter
import json
import random
import socket
import struct
import sys
import threading

VALID_CATEGORIES = [
    "ones", "twos", "threes", "fours", "fives", "sixes",
    "three_of_a_kind", "four_of_a_kind", "full_house",
    "small_straight", "large_straight", "yahtzee", "chance"
]

MAX_ROUNDS = 13  # 13 categories per player


# ---------------------------------------------------------------------------
# Framing & Socket Helpers (Sprint 1 Blueprint)
# ---------------------------------------------------------------------------

def recv_exact(sock, n_bytes):
    """Read exactly n_bytes from the TCP stream. Returns None on 0-byte EOF."""
    buf = bytearray()
    while len(buf) < n_bytes:
        chunk = sock.recv(n_bytes - len(buf))
        if not chunk:
            return None  # POSIX 0-byte EOF
        buf.extend(chunk)
    return bytes(buf)


def recv_msg(sock):
    """Receive a 4-byte Big-Endian length-prefixed JSON message."""
    header_bytes = recv_exact(sock, 4)
    if header_bytes is None:
        return None
    payload_len = struct.unpack("!I", header_bytes)[0]
    payload_bytes = recv_exact(sock, payload_len)
    if payload_bytes is None:
        return None
    return json.loads(payload_bytes.decode("utf-8"))


def send_msg(sock, payload_dict):
    """Send a 4-byte Big-Endian length-prefixed JSON message."""
    payload_bytes = json.dumps(payload_dict).encode("utf-8")
    header = struct.pack("!I", len(payload_bytes))
    sock.sendall(header + payload_bytes)


# ---------------------------------------------------------------------------
# Yahtzee Scoring Engine
# ---------------------------------------------------------------------------

def calculate_category_score(category, dice):
    """Calculate the score for a given Yahtzee category and 5-dice array."""
    counts = Counter(dice)
    unique_dice = set(dice)
    face_map = {
        "ones": 1, "twos": 2, "threes": 3,
        "fours": 4, "fives": 5, "sixes": 6
    }

    if category in face_map:
        target = face_map[category]
        return sum(d for d in dice if d == target)
    if category == "three_of_a_kind":
        return sum(dice) if any(c >= 3 for c in counts.values()) else 0
    if category == "four_of_a_kind":
        return sum(dice) if any(c >= 4 for c in counts.values()) else 0
    if category == "full_house":
        vals = sorted(counts.values())
        return 25 if vals == [2, 3] or vals == [5] else 0
    if category == "small_straight":
        straights = [{1, 2, 3, 4}, {2, 3, 4, 5}, {3, 4, 5, 6}]
        return 30 if any(s.issubset(unique_dice) for s in straights) else 0
    if category == "large_straight":
        return 40 if unique_dice in ({1, 2, 3, 4, 5}, {2, 3, 4, 5, 6}) else 0
    if category == "yahtzee":
        return 50 if len(counts) == 1 else 0
    if category == "chance":
        return sum(dice)
    return 0


# ---------------------------------------------------------------------------
# Game State & Server Concurrency Manager (Sprint 2 Architecture)
# ---------------------------------------------------------------------------

class YahtzeeServer:
    """Manages the FSM, thread lock, and connected clients for 2-player Yahtzee."""

    def __init__(self, port):
        self.port = port
        self.state = "INIT"
        self.game_state_lock = threading.Lock()
        self.reset_game_state()

    def reset_game_state(self):
        """Initialize or reset the game state for a new match."""
        self.client_sockets = {}   # player_id -> socket
        self.player_order = []     # [player1_id, player2_id]
        self.active_turn = None
        self.current_dice = [1, 1, 1, 1, 1]
        self.rolls_remaining = 2
        self.scorecards = {}       # player_id -> {category: score, "total": int}
        self.state = "WAITING_FOR_PLAYERS"
        print(f"[FSM] State -> {self.state}")

    def roll_new_turn_dice(self):
        """Roll 5 fresh dice at the start of a player's turn."""
        self.current_dice = [random.randint(1, 6) for _ in range(5)]
        self.rolls_remaining = 2

    def broadcast(self, msg_dict):
        """Send a JSON message to all connected clients (caller holds lock)."""
        for pid, sock in list(self.client_sockets.items()):
            try:
                send_msg(sock, msg_dict)
            except (ConnectionResetError, BrokenPipeError, OSError) as exc:
                print(f"[WARN] Failed to broadcast to {pid}: {exc}")

    def build_state_update(self):
        """Build the STATE_UPDATE payload matching Sprint 1 schema."""
        return {
            "msg_type": "STATE_UPDATE",
            "active_player": self.active_turn,
            "rolls_remaining": self.rolls_remaining,
            "current_dice": self.current_dice,
            "scores": self.scorecards
        }

    def handle_client(self, client_sock, addr):
        """Dedicated worker thread servicing a single client connection."""
        player_id = None
        try:
            # 1. Expect initial CONNECT message
            msg = recv_msg(client_sock)
            if not msg or msg.get("msg_type") != "CONNECT":
                send_msg(client_sock, {
                    "msg_type": "ERROR",
                    "error_code": "EXPECTED_CONNECT",
                    "message": "First message must be CONNECT."
                })
                client_sock.close()
                return

            requested_id = str(msg.get("player_id", "Player")).strip() or "Player"

            with self.game_state_lock:
                if len(self.player_order) >= 2:
                    send_msg(client_sock, {
                        "msg_type": "ERROR",
                        "error_code": "ROOM_FULL",
                        "message": "Game room is already full."
                    })
                    client_sock.close()
                    return

                # Prevent duplicate player aliases
                player_id = requested_id
                if player_id in self.client_sockets:
                    player_id = f"{requested_id}_2"

                self.client_sockets[player_id] = client_sock
                self.player_order.append(player_id)
                self.scorecards[player_id] = {"total": 0}
                print(f"[INFO] Player '{player_id}' connected from {addr}.")

                if len(self.player_order) == 1:
                    self.state = "LOBBY_WAIT"
                    print(f"[FSM] State -> {self.state}")
                    send_msg(client_sock, {
                        "msg_type": "LOBBY_WAIT",
                        "message": "Waiting for opponent..."
                    })
                elif len(self.player_order) == 2:
                    self.state = "GAME_START"
                    print(f"[FSM] State -> {self.state}")
                    p1, p2 = self.player_order[0], self.player_order[1]
                    self.active_turn = p1
                    self.roll_new_turn_dice()

                    self.broadcast({
                        "msg_type": "GAME_START",
                        "roles": {p1: "Player_1", p2: "Player_2"},
                        "first_turn": p1
                    })

                    self.state = "PLAYER_TURN"
                    print(f"[FSM] State -> {self.state} (Active: {self.active_turn})")
                    self.broadcast(self.build_state_update())

            # 2. Main Client Servicing Loop
            while True:
                msg = recv_msg(client_sock)
                if msg is None:
                    # 0-byte EOF detected
                    print(f"[INFO] EOF (0 bytes) received from '{player_id}'.")
                    self.handle_disconnect(player_id)
                    break

                msg_type = msg.get("msg_type")
                if msg_type == "DISCONNECT":
                    print(f"[INFO] DISCONNECT received from '{player_id}'.")
                    self.handle_disconnect(player_id)
                    break
                elif msg_type == "MOVE":
                    self.process_move(player_id, client_sock, msg)
                else:
                    with self.game_state_lock:
                        send_msg(client_sock, {
                            "msg_type": "ERROR",
                            "error_code": "INVALID_FORMAT",
                            "message": f"Unsupported msg_type: {msg_type}"
                        })

        except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError) as exc:
            print(f"[WARN] Abrupt connection drop for '{player_id}': {exc}")
            if player_id:
                self.handle_disconnect(player_id)
        except json.JSONDecodeError:
            print(f"[WARN] Malformed JSON received from '{player_id}'.")
            if player_id:
                self.handle_disconnect(player_id)

    def process_move(self, player_id, client_sock, msg):
        """Thread-safe evaluation of a client MOVE message."""
        with self.game_state_lock:
            if self.state != "PLAYER_TURN":
                send_msg(client_sock, {
                    "msg_type": "ERROR",
                    "error_code": "GAME_NOT_READY",
                    "message": "Game is not currently in an active turn state."
                })
                return

            self.state = "EVALUATE_MOVE"
            print(f"[FSM] State -> {self.state} (From: {player_id})")

            # Turn enforcement check
            if player_id != self.active_turn:
                self.state = "PLAYER_TURN"
                send_msg(client_sock, {
                    "msg_type": "ERROR",
                    "error_code": "OUT_OF_TURN",
                    "message": f"Not your turn. Waiting on {self.active_turn}."
                })
                return

            payload = msg.get("payload", {})
            if not isinstance(payload, dict):
                self.state = "PLAYER_TURN"
                send_msg(client_sock, {
                    "msg_type": "ERROR",
                    "error_code": "INVALID_PAYLOAD",
                    "message": "Payload must be a JSON object."
                })
                return

            action = payload.get("action")

            # Action 1: Hold / Reroll Dice
            if action in ("hold", "roll"):
                if self.rolls_remaining <= 0:
                    self.state = "PLAYER_TURN"
                    send_msg(client_sock, {
                        "msg_type": "ERROR",
                        "error_code": "NO_ROLLS_LEFT",
                        "message": "No rolls remaining. Please score a category."
                    })
                    return

                held_indices = payload.get("dice_indices", [])
                if not isinstance(held_indices, list) or any(
                    not isinstance(i, int) or i < 0 or i > 4 for i in held_indices
                ):
                    self.state = "PLAYER_TURN"
                    send_msg(client_sock, {
                        "msg_type": "ERROR",
                        "error_code": "INVALID_INDICES",
                        "message": "dice_indices must be integers between 0 and 4."
                    })
                    return

                for idx in range(5):
                    if idx not in held_indices:
                        self.current_dice[idx] = random.randint(1, 6)
                self.rolls_remaining -= 1

                self.state = "BROADCAST_STATE"
                print(f"[FSM] State -> {self.state}")
                self.broadcast(self.build_state_update())
                self.state = "PLAYER_TURN"
                print(f"[FSM] State -> {self.state} (Active: {self.active_turn})")

            # Action 2: Score a Category
            elif action == "score":
                category = str(payload.get("category", "")).lower().strip()
                if category not in VALID_CATEGORIES:
                    self.state = "PLAYER_TURN"
                    send_msg(client_sock, {
                        "msg_type": "ERROR",
                        "error_code": "UNKNOWN_CATEGORY",
                        "message": f"Invalid category '{category}'."
                    })
                    return

                player_card = self.scorecards[player_id]
                if category in player_card:
                    self.state = "PLAYER_TURN"
                    send_msg(client_sock, {
                        "msg_type": "ERROR",
                        "error_code": "INVALID_CATEGORY",
                        "message": f"You already scored '{category}'."
                    })
                    return

                self.state = "SCORE_UPDATE"
                pts = calculate_category_score(category, self.current_dice)
                player_card[category] = pts
                player_card["total"] += pts
                print(f"[FSM] State -> {self.state} ({player_id} scored {pts} in {category})")

                self.state = "CHECK_WIN_DRAW"
                print(f"[FSM] State -> {self.state}")

                # Check if both players have filled all 13 categories (+1 for "total" key)
                all_done = all(
                    len(card) >= MAX_ROUNDS + 1 for card in self.scorecards.values()
                )

                if all_done:
                    self.state = "GAME_OVER"
                    print(f"[FSM] State -> {self.state}")
                    p1, p2 = self.player_order[0], self.player_order[1]
                    s1 = self.scorecards[p1]["total"]
                    s2 = self.scorecards[p2]["total"]
                    if s1 > s2:
                        winner, reason = p1, "standard_win"
                    elif s2 > s1:
                        winner, reason = p2, "standard_win"
                    else:
                        winner, reason = "DRAW", "draw"

                    self.broadcast(self.build_state_update())
                    self.broadcast({
                        "msg_type": "GAME_OVER",
                        "winner": winner,
                        "final_scores": {p1: s1, p2: s2},
                        "reason": reason
                    })
                    self.cleanup_session()
                else:
                    # Switch active player for next turn
                    p1, p2 = self.player_order[0], self.player_order[1]
                    self.active_turn = p2 if self.active_turn == p1 else p1
                    self.roll_new_turn_dice()
                    self.state = "PLAYER_TURN"
                    print(f"[FSM] State -> {self.state} (Active: {self.active_turn})")
                    self.broadcast(self.build_state_update())

            else:
                self.state = "PLAYER_TURN"
                send_msg(client_sock, {
                    "msg_type": "ERROR",
                    "error_code": "INVALID_ACTION",
                    "message": "Action must be 'hold', 'roll', or 'score'."
                })

    def handle_disconnect(self, disconnected_player):
        """Handle graceful or abrupt client disconnect and declare forfeit if in-game."""
        with self.game_state_lock:
            if disconnected_player not in self.client_sockets:
                return

            if self.state in ("WAITING_FOR_PLAYERS", "LOBBY_WAIT"):
                self.cleanup_session()
                return

            self.state = "FORFEIT"
            print(f"[FSM] State -> {self.state} ('{disconnected_player}' left)")

            remaining_players = [
                p for p in self.player_order if p != disconnected_player
            ]
            winner = remaining_players[0] if remaining_players else "None"
            final_scores = {
                p: self.scorecards.get(p, {}).get("total", 0)
                for p in self.player_order
            }

            self.state = "GAME_OVER"
            print(f"[FSM] State -> {self.state} (Winner by forfeit: {winner})")

            for pid, sock in list(self.client_sockets.items()):
                if pid != disconnected_player:
                    try:
                        send_msg(sock, {
                            "msg_type": "GAME_OVER",
                            "winner": winner,
                            "final_scores": final_scores,
                            "reason": "forfeit"
                        })
                    except OSError:
                        pass

            self.cleanup_session()

    def cleanup_session(self):
        """Close active client sockets and reset server state (caller holds lock)."""
        self.state = "CLEANUP"
        print(f"[FSM] State -> {self.state}")
        for sock in self.client_sockets.values():
            try:
                sock.close()
            except OSError:
                pass
        self.reset_game_state()

    def start(self):
        """Bind listening socket to 0.0.0.0 and accept incoming connections."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind(("0.0.0.0", self.port))
            server_sock.listen(5)
            print(f"[SERVER] Yahtzee Server listening on 0.0.0.0:{self.port}")

            try:
                while True:
                    client_sock, addr = server_sock.accept()
                    worker = threading.Thread(
                        target=self.handle_client,
                        args=(client_sock, addr),
                        daemon=True
                    )
                    worker.start()
            except KeyboardInterrupt:
                print("\n[SERVER] Shutting down cleanly.")


# ---------------------------------------------------------------------------
# CLI Argument Parsing
# ---------------------------------------------------------------------------

def validate_port(value):
    """Validate that the port is an integer within 1024-65535."""
    try:
        port = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Invalid port '{value}'. Must be an integer."
        ) from exc
    if not (1024 <= port <= 65535):
        raise argparse.ArgumentTypeError(
            f"Port {port} out of range. Choose a port between 1024 and 65535."
        )
    return port


def parse_args():
    """Parse CLI arguments (-h, -p)."""
    parser = argparse.ArgumentParser(
        description="CS 457 Two-Player CLI Yahtzee Server."
    )
    parser.add_argument(
        "-p", "--port",
        dest="port",
        type=validate_port,
        required=True,
        help="Listening port (required, range 1024-65535; binds to 0.0.0.0)."
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    server = YahtzeeServer(args.port)
    server.start()