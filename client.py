#!/usr/bin/env python3
"""
CS 457 Final Project - Sprint 3: Yahtzee CLI Client
Implements DNS resolution with graceful socket.gaierror handling, 4-byte
Big-Endian length-prefixed framing, and an interactive CLI interface.
"""

import argparse
import json
import socket
import struct
import sys
import threading

CATEGORIES = [
    "ones", "twos", "threes", "fours", "fives", "sixes",
    "three_of_a_kind", "four_of_a_kind", "full_house",
    "small_straight", "large_straight", "yahtzee", "chance"
]


# ---------------------------------------------------------------------------
# Framing & Socket Helpers (Sprint 1 Blueprint)
# ---------------------------------------------------------------------------

def recv_exact(sock, n_bytes):
    """Read exactly n_bytes from the TCP stream. Returns None on 0-byte EOF."""
    buf = bytearray()
    while len(buf) < n_bytes:
        chunk = sock.recv(n_bytes - len(buf))
        if not chunk:
            return None
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
# CLI Rendering Helpers
# ---------------------------------------------------------------------------

def render_board(player_id, msg):
    """Render the Yahtzee scorecard, current dice, and turn status in CLI."""
    active_player = msg.get("active_player")
    rolls_left = msg.get("rolls_remaining")
    dice = msg.get("current_dice", [])
    scores = msg.get("scores", {})
    players = list(scores.keys())

    print("\n" + "=" * 58)
    print("                 YAHTZEE SCOREBOARD")
    print("=" * 58)
    if len(players) == 2:
        p1, p2 = players[0], players[1]
        print(f"{'Category':<20} | {p1:<15} | {p2:<15}")
        print("-" * 58)
        for cat in CATEGORIES:
            v1 = scores[p1].get(cat, "-")
            v2 = scores[p2].get(cat, "-")
            print(f"{cat:<20} | {str(v1):<15} | {str(v2):<15}")
        print("-" * 58)
        t1 = scores[p1].get("total", 0)
        t2 = scores[p2].get("total", 0)
        print(f"{'TOTAL SCORE':<20} | {str(t1):<15} | {str(t2):<15}")
    print("=" * 58)

    dice_str = "  ".join(f"[{idx}]:{val}" for idx, val in enumerate(dice))
    print(f"Active Turn : {active_player}")
    print(f"Current Dice: {dice_str}   (Rolls Remaining: {rolls_left})")

    if active_player == player_id:
        print("\n>>> YOUR TURN! Commands:")
        print("  hold <idx...>  - Hold dice at indices 0-4 & reroll rest (e.g., 'hold 0 2 4')")
        print("  roll           - Reroll all 5 dice")
        print("  score <cat>    - Score a category (e.g., 'score full_house' or 'score threes')")
        print("  quit           - Disconnect and forfeit")
    else:
        print(f"\n--- Waiting for {active_player} to complete their turn... ---")
    print("> ", end="", flush=True)


# ---------------------------------------------------------------------------
# Receiver Thread & Main Loop
# ---------------------------------------------------------------------------

def listen_to_server(sock, player_id, stop_event):
    """Background listener thread that prints asynchronous server broadcasts."""
    try:
        while not stop_event.is_set():
            msg = recv_msg(sock)
            if msg is None:
                print("\n[INFO] Server closed the connection (EOF).")
                stop_event.set()
                break

            msg_type = msg.get("msg_type")

            if msg_type == "LOBBY_WAIT":
                print(f"\n[LOBBY] {msg.get('message')}")
            elif msg_type == "GAME_START":
                roles = msg.get("roles", {})
                first = msg.get("first_turn")
                print(f"\n[GAME START] Match initiated! Roles: {roles}. First turn: {first}")
            elif msg_type == "STATE_UPDATE":
                render_board(player_id, msg)
            elif msg_type == "ERROR":
                print(f"\n[SERVER ERROR - {msg.get('error_code')}] {msg.get('message')}")
                print("> ", end="", flush=True)
            elif msg_type == "GAME_OVER":
                print("\n" + "#" * 58)
                print("                      GAME OVER")
                print(f"  Winner       : {msg.get('winner')}")
                print(f"  Reason       : {msg.get('reason')}")
                print(f"  Final Scores : {msg.get('final_scores')}")
                print("#" * 58)
                stop_event.set()
                break
    except (ConnectionResetError, BrokenPipeError, OSError):
        if not stop_event.is_set():
            print("\n[ERROR] Lost connection to server abruptly.")
            stop_event.set()


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
    """Parse CLI arguments (-h, -i, -p)."""
    parser = argparse.ArgumentParser(
        description="CS 457 Two-Player CLI Yahtzee Client."
    )
    parser.add_argument(
        "-i", "--ip", "--hostname",
        dest="hostname",
        required=True,
        help="Server DNS hostname or IP address (e.g., server.struna.edu or localhost)."
    )
    parser.add_argument(
        "-p", "--port",
        dest="port",
        type=validate_port,
        required=True,
        help="Server TCP port (required, range 1024-65535)."
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Mandatory Requirement 2.2: Graceful DNS Resolution Exception Handling
    try:
        server_ip = socket.gethostbyname(args.hostname)
    except socket.gaierror:
        print(f"[ERROR] Unable to resolve DNS hostname '{args.hostname}'.")
        print("Please check your Cisco router DNS configuration ('ip dns server' / 'ip host') or verify domain spelling.")
        sys.exit(1)

    player_id = input("Enter your player alias (e.g., Kevin_S): ").strip()
    if not player_id:
        player_id = "Player"

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((server_ip, args.port))
    except OSError as exc:
        print(f"[ERROR] Could not connect to {args.hostname} ({server_ip}:{args.port}): {exc}")
        sys.exit(1)

    print(f"[CONNECTED] Connected to {args.hostname} ({server_ip}:{args.port}) as '{player_id}'.")

    # Send initial CONNECT message
    send_msg(sock, {
        "msg_type": "CONNECT",
        "player_id": player_id
    })

    stop_event = threading.Event()
    listener = threading.Thread(
        target=listen_to_server,
        args=(sock, player_id, stop_event),
        daemon=True
    )
    listener.start()

    # Main user input loop
    try:
        while not stop_event.is_set():
            user_input = input()
            if stop_event.is_set():
                break

            parts = user_input.strip().split()
            if not parts:
                continue

            cmd = parts[0].lower()

            if cmd == "quit":
                send_msg(sock, {
                    "msg_type": "DISCONNECT",
                    "player_id": player_id
                })
                stop_event.set()
                break

            elif cmd == "roll":
                send_msg(sock, {
                    "msg_type": "MOVE",
                    "player_id": player_id,
                    "payload": {
                        "action": "hold",
                        "dice_indices": []
                    }
                })

            elif cmd == "hold":
                try:
                    indices = [int(x) for x in parts[1:]]
                except ValueError:
                    print("[CLIENT] Indices must be integers 0-4 (e.g., 'hold 0 2 4').")
                    print("> ", end="", flush=True)
                    continue

                send_msg(sock, {
                    "msg_type": "MOVE",
                    "player_id": player_id,
                    "payload": {
                        "action": "hold",
                        "dice_indices": indices
                    }
                })

            elif cmd == "score":
                if len(parts) < 2:
                    print("[CLIENT] Specify a category (e.g., 'score threes' or 'score chance').")
                    print("> ", end="", flush=True)
                    continue
                category = parts[1].lower()
                send_msg(sock, {
                    "msg_type": "MOVE",
                    "player_id": player_id,
                    "payload": {
                        "action": "score",
                        "category": category
                    }
                })

            else:
                print("[CLIENT] Unknown command. Use 'hold <0-4>', 'roll', 'score <category>', or 'quit'.")
                print("> ", end="", flush=True)

    except (KeyboardInterrupt, EOFError):
        try:
            send_msg(sock, {
                "msg_type": "DISCONNECT",
                "player_id": player_id
            })
        except OSError:
            pass
    except (ConnectionResetError, BrokenPipeError, OSError):
        print("\n[ERROR] Connection lost while sending message.")
    finally:
        stop_event.set()
        sock.close()


if __name__ == "__main__":
    main()