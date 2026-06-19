# Ideas and deferred work

A triage list for features, improvements, and known gaps.
Items marked **FIXME** were inline comments in the source; they are
collected here so they can be prioritised without hunting through files.

---

## Packaging

- `python setup.py bdist_rpm`
- `python setup.py bdist_deb`

---

## Visualisation

- Graph of game history: planets and armies over time.
- Flowchart for tasks like taking.
- Heatmap of enemy concentration.
- Ways-to-damage diagram.
- Isosurfaces of distance to targets.
- Halo of distance to targets (experimental `--halos` flag exists).
- Tactical edge pointers: a short line drawn from centre of tactical to
  the edge, last few pixels visible in the colour of the ship represented.

---

## Strategic advisor

- Input: operating mode — want explosions / maximise stats / help team win.
- Input: planet ownership, ship positions, number of kills.
- Input: team ship classes, positions, stated roles based on RCDs.
- Output: priority list of roles, which roles are in use, on screen.

---

## Graphics / Cairo

- Scalable graphics via Cairo: http://www.pygame.org/wiki/CairoPygame

---

## UI — server list (`PhaseServers`)

- Connect asynchronously — do not block and hang during connect.
- Expire old multicast entries when servers leave.
- Fix placement problem: newly available multicast server placed at
  first position despite that position being taken by a metaserver entry.
- Discover servers from a local cache to populate the list faster.

---

## UI — outfit / ship selection (`PhaseOutfit`)

- Automatic quit timeout display.
- Show number of players on each team.
- Display "in bronco you should remain with your team".
- Slide ships into team positions, omitting unavailable teams.
- Click on team icon sends CP_OUTFIT with most recent ship type.
- Click on ship icon requests CP_OUTFIT with team and ship.
- Show logged-in players.
- Show planet status.
- Show `whydead` (cause of last death).
- Show keyboard shortcut for space bar (rejoin).
- Make team/ship graphics sprites rather than painting directly on screen.
- Add a BACK button: disconnect, reconnect, return to login.
- Add a "become observer" button (disconnect, reconnect as observer slot).
- Add a "become player" button (same pattern).
- Add a "relinquish slot" button for rejoining at the end of the queue.

---

## UI — login (`PhaseLogin`)

- Just press Enter for guest (avoid needing Tab).
- Force no echo for password field (bug #1187683521).
- Password prompt appears momentarily if guest is selected — fix timing.

---

## UI — queue (`PhaseQueue`)

- No open items.

---

## UI — disconnected (`PhaseDisconnected`)

- Show last few lines of the message log.
- If freed by the captain in a clue game, automatically return as an
  observer slot.
- Offer "rejoin as player" and "rejoin as observer" buttons.

---

## UI — in-flight general

- Add a console widget in a corner.
- Add action-menu items around the tactical edge.
- Add mouse-over info query on screen objects.
- Watch for MOUSEMOTION and update object information panes for planets
  and ships (on tactical or galactic).
- Adopt netrek-client-cow tractor key policy: `$` all-off, `_` tractor
  off and reapply, `^` pressor off and reapply.
- Message history: recall with up/down arrows.
- Add graphic indicator of connection status.
- Keymap feature: allow function keys to be bound to actions.
- Dashboard should show percentages or proportions (per Petria).
- Mouse-over hint for the word "clue" — explain the term (per Petria).
- Add a help/documentation button accessible from the metaserver list
  (will force disconnection) containing tutorial, ship classes, and rank
  information.
- Sort keyboard-help entries in a learning-friendly order rather than
  table-insertion order.

---

## UI — tactical view

- Planets to be partial-alpha as ships close in.
- When another slot frees, free all of that slot's torpedos.
- Galactic view centred correctly for `--width=800 --height=600
  --no-fullscreen`.

---

## UI — galactic / subgalactic

- Non-moving ships do not appear on the galactic view.

---

## Network / protocol (`packets.py`)

- Update team selection icons in response to SP_MASK
  (bug #1187683470).
- Process feature packets received from server beyond the initial
  handshake.
- Generate correct response data for ping packets
  (bug #1215317195, reported by Zach).
- Lower update rate while `GU_UNSAFE` flag is set.
- Display t-mode state, and other server feature-packet state.
- Allow playing on another server while queued on one.
- ECONNRESET not properly reported in disconnection diagnosis.

---

## Game features

- Planets to be partial-alpha in tactical view as ships close in.
- Scanning unknown planets.
- Achievements for ship-class policy the client implements for new
  players.
- Configuration settings stored in YAML.
- New version notification.
- Explanation of how to get an account on a netrek server.
- Dual display support.

---

## Observing

- When you join as an observer, use `l` to lock on a player.
  (Currently not well supported; phases skip observer-specific display.)

---

## Performance / architecture

- `Galaxy` stores game objects in lists accessed by index; consider
  dicts keyed by slot for O(1) lookup.
- Several methods are very long (`PhaseFlight` key handlers,
  `MessageSprite`); candidate for sub-method extraction.
- Some decades-old FIXME comments are dead-ends; audit and remove.
