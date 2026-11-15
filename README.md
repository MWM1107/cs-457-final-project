# CS 457 Final Project: Networked Two-Player CLI Yahtzee

**Author:** Kevin Struna  
**Course:** CS 457 - Computer Networks  
**Server FQDN:** `server.struna.edu` (`192.168.20.100`)  
**Video Walkthrough:** [sprint_5_video_walkthrough.mp4](./docs/sprint_5/sprint_5_video_walkthrough.mp4)

---

## 1. Project Overview

This project implements an authoritative, two-player networked command-line **Yahtzee** game over TCP sockets in Python 3. It is deployed across a multi-subnet Cisco Modeling Labs (CML) topology where a single Cisco IOSv router (`ks-R1`) provides Layer 3 routing across three `/24` subnets, dynamic DHCP address allocation for client nodes, and authoritative DNS resolution for `server.struna.edu`.

### Key Features
* **Custom Length-Prefixed Framing:** Uses a 4-byte Big-Endian unsigned integer (`!I`) header followed by UTF-8 JSON payloads to guarantee message boundary delineation across TCP streams.
* **Multi-Threaded Concurrency:** Spawns dedicated worker threads per client protected by a `threading.Lock()` mutex to prevent race conditions during state updates.
* **Graceful DNS Resolution Handling:** Resolves hostnames via `socket.gethostbyname()` and catches `socket.gaierror` cleanly with actionable troubleshooting output.
* **Stateful Disconnect & Reconnect Recovery:** Preserves active game state, dice, turn order, and scorecards in memory for a 60-second grace period if a client drops (`ConnectionResetError` / EOF), broadcasting `STATE_RESUME` upon reconnection.

---

## 2. Requirements

* **Python Version:** Python 3.8+ (uses standard library modules only: `socket`, `struct`, `json`, `threading`, `argparse`, `collections`, `random`, `sys`).
* **Network Environment:** Localhost (`127.0.0.1`) or Cisco Modeling Labs (CML) 1-router multi-subnet topology (`sprint_4_topology.yaml`).

---

## 3. CLI Flags & Execution Instructions

### 3.1 Starting the Server (`server.py`)
The server binds to `0.0.0.0` on a specified TCP port between `1024` and `65535`:

```bash
# Display help
python3 server.py -h

# Launch server on port 8080
python3 server.py -p 8080
```

### 3.2 Starting the Client (`client.py`)
Each client resolves the server hostname (or IP) and connects to the specified TCP port:

```bash
# Display help
python3 client.py -h

# Connect via DNS hostname in CML
python3 client.py -i server.struna.edu -p 8080

# Connect locally for development/testing
python3 client.py -i localhost -p 8080
```

### 3.3 In-Game CLI Commands
During your active turn (`>>> YOUR TURN!`), enter any of the following commands at the `>` prompt:
* `hold <idx...>` — Hold dice at space-separated indices `0`–`4` and reroll the rest (e.g., `hold 0 2 4`).
* `roll` — Reroll all 5 dice (up to 2 rerolls per turn).
* `score <category>` — Score the current dice in one of the 13 categories (`ones`, `twos`, `threes`, `fours`, `fives`, `sixes`, `three_of_a_kind`, `four_of_a_kind`, `full_house`, `small_straight`, `large_straight`, `yahtzee`, `chance`).
* `quit` — Intentionally disconnect and forfeit the match.
* `Ctrl + C` — Simulate an abrupt TCP disconnect (`RST`) to test the 60-second stateful reconnection grace period.

---

## 4. CML Network Architecture Summary

| Node Name | Interface | IP Address / Mask | Default Gateway | Role |
| :--- | :--- | :--- | :--- | :--- |
| `ks-R1` | `Gi0/1`, `Gi0/2`, `Gi0/3` | `.10.1`, `.11.1`, `.20.1` (`/24`) | Connected (`C`) | Default Gateway, DHCP Server, Authoritative DNS (`server.struna.edu`) |
| `ks-Client1` | `eth0` | `192.168.10.2/24` (DHCP) | `192.168.10.1` | Player 1 Client Endpoint (Subnet A) |
| `ks-Client2` | `eth0` | `192.168.11.2/24` (DHCP) | `192.168.11.1` | Player 2 Client Endpoint (Subnet B) |
| `ks-Server` | `eth0` | `192.168.20.100/24` (Static) | `192.168.20.1` | Authoritative Yahtzee Game Server (Subnet C) |

---

## 5. Repository Layout & Deliverable Package

```text
.
├── README.md                          # Project overview, setup, CLI flags, and architecture
├── client.py                          # Production Yahtzee client with DNS error handling & STATE_RESUME
├── server.py                          # Production multi-threaded Yahtzee server with 60s stateful recovery
├── sprint_0_sow.md                    # Sprint 0: Statement of Work (SOW)
├── sprint_1_protocol.md               # Sprint 1: Custom TCP Framing & JSON Protocol Blueprint
├── sprint_1_fsm.md                    # Sprint 1: Game Server Finite State Machine (FSM) Specification
├── sprint_2_concurrency.md            # Sprint 2: Concurrency Architecture & Mermaid Sequence Diagram
├── sprint_4_topology.yaml             # Sprint 4: Exported CML 1-Router Network Topology
└── docs/
    ├── sprint_0/                      # Sprint 0 artifacts
    ├── sprint_1/                      # Sprint 1 protocol & FSM artifacts
    ├── sprint_2/                      # Sprint 2 concurrency & sequence diagram artifacts
    ├── sprint_3/                      # Sprint 3 intermediate execution logs
    ├── sprint_4/                      # Sprint 4 DNS PCAP, topology YAML, & verification report
    └── sprint_5/
        ├── sprint_5_report.md         # Sprint 5 Combined Impairment, Reconnection & Retrospective Report
        ├── sprint_5_degraded_network.pcap # Wireshark trace of degraded link & stateful reconnect
        ├── cml_link_impairment.jpeg   # CML Gi0/3 link conditioning screenshot
        ├── Retransmissions Screenshot.png
        ├── Duplicate ACKs Screenshot.png
        └── RTT Delay and Timeout Screenshot.png
```