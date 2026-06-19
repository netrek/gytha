# CLAUDE.md — Gytha Netrek Client

Developer and AI-assistant reference. Records architecture rules and constraints
that are not obvious from the code alone, mostly surfaced during debugging.

---

## Quick reference

| Item | Value |
|---|---|
| Entry point | `gytha.py` → `gytha.main()` |
| Primary source | `gytha/__init__.py` (~550 lines) + modules below |
| Runtime | Python ≥ 3.8, Pygame ≥ 2.6.1 |
| Server port | 2592 TCP/UDP |
| Metaserver port | 3521 UDP |
| Test system A | Ubuntu 26.04, LXC container, X11 over SSH |
| Test system B | Ubuntu 24.04 bare metal, local Xorg |

Run windowed against a local server:

```
python3 gytha.py --server localhost --name guest --no-fullscreen
```

---

## Module structure

The original monolithic `gytha/__init__.py` (5 700 lines) has been split into
focused modules. `__init__.py` now holds only startup/init functions and
module-level wiring.

| Module | Contents |
|---|---|
| `gytha/__init__.py` | `main()`, `pg_init()`, `nt_init()`, `mc_init()`, wiring |
| `gytha/phases.py` | All `Phase` subclasses, `nt_play()`, `nt_play_a_slot()` |
| `gytha/achievements.py` | `ac_load/save/done/deliver/progress`, guidance data |
| `gytha/packets.py` | `CP_*` / `SP_*` packet classes, metaclass registries |
| `gytha/overlays.py` | HUD sprite classes (alerts, borders, info, messages) |
| `gytha/game_sprites.py` | In-game sprite classes (planets, ships, torps, plasma) |
| `gytha/models.py` | Domain model classes (`Galaxy`, `Ship`, `Planet`, …) |
| `gytha/coords.py` | Coordinate conversion functions |
| `gytha/options.py` | `argparse` parser |
| `gytha/constants.py` | Protocol constants, team/ship tables |
| `gytha/util.py` | Shared utility functions |
| `gytha/client.py` | `NetworkThread`, `Client` (TCP/UDP) |
| `gytha/bouncer.py` | Animated bouncer widget |
| `gytha/sprites.py` | Base sprite/widget classes |
| `gytha/cache.py` | Image and font caches |

### Module-level state injection pattern

Each extracted module declares its shared state as `None` at module level.
`__init__.py` injects the real objects after they are created:

```python
# in gytha/__init__.py — after galaxy = Galaxy()
phases.galaxy = galaxy
packets.galaxy = galaxy

# in pg_init() — after sprite groups are created
phases.screen = screen
phases.b_info = b_info
achievements.b_info = b_info

# in _sync_me() — called by SP_YOU.handler() on every ship update
phases.me = new_me
achievements.me = new_me
```

Callables that phases.py needs from `__init__.py` (to avoid circular imports)
are injected as references after their definitions:

```python
phases.pg_quit = pg_quit
phases.nt_shutdown = nt_shutdown
phases.ac_save = ac_save   # etc.
```

---

## Architecture overview

### Phase (screen) lifecycle

The game is a pipeline of `Phase` subclasses:

```
PhaseSplash → PhaseServers ⇄ PhaseTips
                   ↓
              PhaseQueue
                   ↓
              PhaseLogin
                   ↓
              PhaseOutfit
                   ↓
              PhaseFlight (PhaseFlightTactical / PhaseFlightGalactic)
```

Each phase's `do()` method:
1. Draws the initial screen and calls `pygame.display.flip()`.
2. Enters `self.cycle()`, which loops on `display_sink_wait()`.
3. `display_sink_wait()` calls `pygame.event.wait()` and dispatches to
   `display_sink_event(event)`.
4. Event handlers mutate phase state; setting `self.run = False` breaks the loop.
5. `do()` continues after `cycle()` returns, then transfers control to the next phase.

### Network thread

`NetworkThread` (daemon thread, `gytha/client.py`) runs `select.select()` on the
TCP and UDP sockets, dispatches packet handlers (`SP_*.handler()`) directly in its
own thread, then posts a `NETWORK_DATA_READY` custom pygame event to wake the main
thread.

```
Main thread                         NetworkThread
──────────────────────────────────  ──────────────────────────────────
pygame.event.wait()  ← blocks       select([tcp, udp], [], [], 0.5)
                                    ↓ data ready
                                    SP_foo.handler(data)   # <-- in NetworkThread
                                    pygame.event.post(NETWORK_DATA_READY)
↓ woken by NETWORK_DATA_READY
display_sink_event()
redraw + pygame.display.flip()
```

---

## Critical constraints

### 1. Thread safety — `pygame.display.flip()` is main-thread only

SDL2 forbids display operations from any thread other than the one that created
the display context. Calling `pygame.display.flip()` from `NetworkThread` (or any
other background thread) produces:

```
pygame.error: Could not make GL context current: BadAccess
```

**Rule:** `pygame.display.flip()` must only appear in code that runs on the main
thread — that is, inside `display_sink_event()`, `do()`, or functions called
synchronously from those.

**Gotcha:** `proceed()` is called from packet-handler callbacks such as
`throw_sp_login()` and `throw_sp_queue()`, which run inside `NetworkThread`.
`proceed()` must never call `pygame.display.flip()`. The successor phase redraws
the screen when it starts, so the flip is unnecessary anyway.

### 2. Custom event type allocation order

`pygame.event.custom_type()` allocates event IDs sequentially starting at
`USEREVENT + 1`. The three custom event types **must** be allocated in this exact
order, before any `pygame.time.set_timer()` call:

```python
UE_TIMER           = pygame.event.custom_type()  # phase update timer
UE_BOUNCER         = pygame.event.custom_type()  # warn-fuse / bouncer
NETWORK_DATA_READY = pygame.event.custom_type()  # network thread wakeup
```

If `NETWORK_DATA_READY` is allocated first it collides with `UE_TIMER`. The 100 Hz
phase timer then fires events that the network-event handler treats as data-ready,
causing a spurious `ServerDisconnectedError` during startup.

### 3. `nt_shutdown()` — always use the wrapper

After `nt.shutdown()` returns, `NetworkThread` may have already posted one or more
`NETWORK_DATA_READY` events that are sitting in the pygame event queue. If the next
phase processes those stale events it sees `nt.connected == False` and raises
`ServerDisconnectedError`.

**Rule:** Never call `nt.shutdown()` directly. Use the `nt_shutdown()` wrapper
defined in `gytha/__init__.py`:

```python
def nt_shutdown():
    nt.shutdown()
    pygame.event.clear(NETWORK_DATA_READY)
```

### 4. `SP_MASK.last_mask` — late-registration replay

The server sends `SP_MASK` packets during the login burst, before
`PhaseOutfit.do()` has called `sp_mask.catch(callback)`. Without mitigation those
early packets are silently discarded and ship icons appear one-at-a-time as the
server re-sends masks at ~1 Hz.

Fix: `SP_MASK.last_mask` stores the most recently received mask value.
`catch(callback)` replays it immediately if non-None. `uncatch()` deliberately
does **not** clear `last_mask` so the replay survives phase transitions.

### 5. `NetworkThread._stop_event` naming

`NetworkThread` uses `self._stop_event = threading.Event()` rather than
`self._stop`. `threading.Thread._stop` is an internal CPython method called by
`Thread.join()` → `_wait_for_tstate_lock()`. Shadowing it with a
`threading.Event()` instance causes:

```
TypeError: 'Event' object is not callable
```

---

## Packet protocol

### Client packets (CP_*)

`ClientPacket` is a metaclass. Any class whose name starts with `CP_` is
automatically registered: its format string is stored in `cp_table` and a
singleton instance is injected into the module namespace as the lowercase name
(e.g. `CP_LOGIN` → `cp_login`).

```python
class ClientPacket(type):
    def __new__(cls, name, bases, dct):
        client_packet = type.__new__(cls, name, bases, dct)
        if name.startswith('CP_'):
            cp_table[client_packet.code] = client_packet.format
            globals()[name.lower()] = client_packet()
        return client_packet
```

All CP classes inherit from `CP(metaclass=ClientPacket)`.

### Server packets (SP_*)

`ServerPacket` is the mirror metaclass. Any `SP_*` subclass is registered in
`sp_table` keyed by its `code` integer, mapping to `(packet_size, instance)`.
The singleton instance is also injected into the module namespace as the lowercase
name (e.g. `SP_MASK` → `sp_mask`).

`SP.find(number)` is the dispatch entry point called from `client.py` to look up
the handler for an incoming packet type byte.

SP handler methods (`SP_*.handler(data)`) run inside `NetworkThread`. They must
not call `pygame.display.flip()` or any other SDL2 display function.

---

## Global state

The most important shared names and where they live after extraction:

| Name | Type | Canonical home | Also injected into |
|---|---|---|---|
| `screen` | `pygame.Surface` | `__init__` (set by `pg_init`) | `phases`, `overlays` |
| `galaxy` | `Galaxy` | `__init__` | `phases`, `packets`, `models`, `overlays` |
| `me` | `Ship` | `__init__` | `phases`, `achievements`, `packets`, `models`, `game_sprites`, `overlays` |
| `nt` | `Client` | `__init__` | `phases`, `packets`, `overlays` |
| `mc` | `MetaClient` | `__init__` | `phases` |
| `opt` | namespace | `__init__` | `phases`, `achievements`, `packets`, `models`, `game_sprites`, `overlays` |
| `r_main` | `Rect` | `__init__` (set by `pg_init`) | `phases`, `overlays` |
| `r_us` | `Rect` | `__init__` (set by `pg_init`) | `phases`, `coords`, `overlays` |
| `ph_flight` | `Phase` | `phases` (internal) | — |
| `UE_TIMER` | `int` | `__init__` | `phases`, `overlays` |
| `UE_BOUNCER` | `int` | `__init__` | `overlays` |
| `NETWORK_DATA_READY` | `int` | `__init__` | `phases` |

Sprite groups (`t_planets`, `g_players`, `b_warning`, etc.) are created in
`pg_init()` and injected into `phases`, `game_sprites`, `models`, and `overlays`.
