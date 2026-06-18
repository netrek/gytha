# Code Assessment — Gytha Netrek Client

Survey of deviations from idiomatic Python / Pygame style.
This is a reference document for future refactoring work, not a task list.

---

## 1. Module imbalance

`gytha/__init__.py` is ~5 700 lines and contains approximately 59 classes and
24 module-level functions. Every other module in `gytha/` is 31–373 lines.

The file mixes five largely independent concerns:
- Game-object domain model (Planet, Ship, Torp, …)
- Rendering sprites (PlanetTacticalSprite, ShipGalacticSprite, …)
- Network protocol (CP_*/SP_* metaclass registries, ~74 packet classes)
- UI phases / screens (Phase, PhaseLogin, PhaseFlight, …)
- Application wiring (pg_init, nt_init, main game loop)

### Recommended splits

| New file | Contents to move | Est. lines |
|---|---|---|
| `gytha/models.py` | `Local`, `Planet`, `Ship`, `Torp`, `Plasma`, `Phaser`, `Tractor`, `Tag`, `NegativeEnergyBarrier`, `Galaxy` | ~900 |
| `gytha/game_sprites.py` | `PlanetSprite`, `PlanetGalacticSprite`, `PlanetTacticalSprite`, `ShipSprite`, `ShipGalacticSprite`, `ShipTacticalSprite`, `TorpSprite`, `TorpTacticalSprite`, `PlasmaSprite`, `PlasmaTacticalSprite` | ~550 |
| `gytha/overlays.py` | `Halos`, `Lines`, `Borders`, `LocatorSprite`, `Alerts`, `TacticalAlerts`, `GalacticAlerts`, `Subgalactic`, `DebugSprite`, `ReportSprite`, `WarningSprite`, `MessageLine`, `InfoSprite`, `MessageSprite` | ~700 |
| `gytha/coords.py` | `n2ss`, `n2gs`, `n2ts`, `gs2n`, `ts2n`, `s2g`, `cursor`, `intragalactic`, `d2a`, `s2d`, `n_o`, `o_d`, `n_d` | ~80 |
| `gytha/packets.py` | `ClientPacket`, `CP` base, all `CP_*` classes; `ServerPacket`, `SP` base, all `SP_*` classes | ~800 |
| `gytha/phases.py` | `Phase`, `PhaseNonFlight`, `PhaseSplash`, `PhaseTips`, `PhaseServers`, `PhaseQueue`, `PhaseLogin`, `PhaseOutfit`, `PhaseFlight`, `PhaseFlightGalactic`, `PhaseFlightTactical`, `PhaseDisconnected` | ~1800 |
| `gytha/achievements.py` | `ac_load`, `ac_save`, `ac_done_now`, `ac_done`, `ac_done_later`, `ac_deliver`, `ac_progress` | ~100 |

After these splits `__init__.py` would be ~400–500 lines covering only init,
display setup, network setup, and the top-level game-loop functions (`nt_play`,
`nt_play_a_slot`, `main`).

**Dependency ordering note:** `packets.py` depends on `models.py` (SP handlers
reference `galaxy`, `me`, etc.). `game_sprites.py` and `overlays.py` depend on
`models.py` and `coords.py`. `phases.py` depends on all of the above. Move in that
order to avoid circular imports.

---

## 2. Module-level globals

`__init__.py` has approximately 30 module-level names used as mutable shared state:

**Display geometry** — `r_main`, `r_us`, `r_sg`, `galactic_factor`,
`subgalactic_factor`

**Game state** — `galaxy`, `me`, `rounds`, `screen`, `background`

**Sprite groups** — `t_planets`, `t_players`, `t_torps`, `t_plasma`, `g_planets`,
`g_players`, `g_locator`, `b_warning`, `b_warning_sprite`, `b_reports`,
`b_message`, `b_info`

**Network / config** — `nt`, `mc`, `opt`, `sp` (the SP base instance), `cp_table`,
`sp_table`

**Phase references** — `ph_flight`, `ph_galactic`, `ph_tactical`

**Event type constants** — `UE_TIMER`, `UE_BOUNCER`, `NETWORK_DATA_READY`

These globals are accessed directly inside class methods, packet handlers, and
rendering code throughout the file. This makes reasoning about data flow hard,
prevents unit testing of individual components, and creates implicit coupling
between unrelated classes.

A `GameState` dataclass or plain object bundling at least `(galaxy, me, screen,
r_main, r_us, opt)` and passed explicitly to sprites and phases would reduce the
coupling significantly, even if not eliminating it entirely.

---

## 3. Star imports

```python
from .constants import *
from .util import *
```

These import ~130 names into `__init__.py`'s namespace without any indication of
origin. Examples: `GWIDTH`, `TWIDTH`, `FED`, `KLI`, `PFSHIELD`, `team_decode`,
`team_colour`. Replacing these with explicit imports makes it possible to search
for a name's definition without ambiguity and avoids accidental shadowing.

---

## 4. Packet metaclass — document the pattern

`ClientPacket` and `ServerPacket` are metaclasses that auto-register classes and
inject lowercase singleton instances into `globals()` at class-definition time.
This is powerful but surprising: a class body statement `class CP_SPEED(CP): ...`
has the side-effect of creating a `cp_speed` module-level variable.

Future contributors who add a packet class must:
- Name it `CP_*` or `SP_*` (the name prefix triggers registration).
- Set `code` to the correct protocol byte and `format` to a `struct` format string.
- For SP classes, implement `handler(self, data)`.

This pattern is not documented in any docstring. The metaclass bodies should have
a short comment explaining the auto-registration and singleton injection.

---

## 5. Long methods

Several methods exceed 100 lines and would benefit from sub-method extraction:

| Location | Approx. lines | Note |
|---|---|---|
| `PhaseFlight.display_sink_event()` | ~150 | Keyboard event dispatch |
| `PhaseFlight.do()` | ~80 | Flight initialisation |
| `PhaseOutfit.do()` | ~60 | Outfit screen setup and tear-down |
| `MessageSprite` class | ~266 | Complex routing + state machine |
| `Galaxy.__init__()` | ~80 | Object-list setup |

---

## 6. Galaxy uses lists with numeric indices

`Galaxy` stores ships, planets, torps, and plasma in Python lists indexed by slot
number (e.g. `self.ships[n]`). Lookup by slot is O(1) only because slot numbers
are sequential and bounded. If the data were stored in dicts (`{slot: obj}`) the
intent would be explicit, unused slots would not consume list entries, and the
`closest_*` methods could use `values()` directly.

---

## 7. FIXME comments — actionable vs stale

There are approximately 30 `FIXME` comments in `__init__.py`. Several are from the
original C client port and reference ticket numbers or describe features that were
never ported. A one-pass audit should:

- Delete FIXMEs for features that are now superseded or out of scope.
- Convert actionable FIXMEs to issues in the Ditz database (`bugs/`).
- Leave FIXMEs only where there is an actual known defect in the current code.

Notable examples:
- `# FIXME: detect failure of either rx or tx path` (client.py:319) — UDP fallback,
  still relevant.
- `# FIXME: bug #1215317195 reported by Zach …` (line ~2735) — old Sourceforge
  ticket, unlikely still relevant.
- `# FIXME: disabled until rcd.msg.text() method fully written` (rcd.py:31) — the
  `text()` method exists but is incomplete; the FIXME is still valid.

---

## 8. `sound.py` and `cache.py` use module-level singletons

`cache.py` creates `ic = IC()` and `fc = FC()` at import time. `sound.py` uses a
module-level `sounds = {}` dict populated by `prepare()`. These are reasonable for
a single-window game, but they make the modules non-reusable and untestable in
isolation. Low priority, but worth noting.

---

## Priority order for future work

1. Write `coords.py` — self-contained, no dependencies within `__init__.py`.
2. Write `models.py` — no Pygame dependency, easiest to test in isolation.
3. Write `packets.py` — depends on `models.py` globals; tackle globals question first.
4. Write `game_sprites.py` and `overlays.py` — depend on models + coords.
5. Write `phases.py` — largest extraction, depends on everything above.
6. Write `achievements.py` — small, independent.
7. Clean up globals — bundle into a `GameState` object once splits are done.
8. Replace star imports with explicit imports.
