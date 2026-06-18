"""
Netrek protocol packet classes: CP_* (client) and SP_* (server).

Module-level state — set by gytha/__init__.py:

  opt      - parsed CLI options          (set at start of main)
  me       - current player Ship         (set by SP_YOU handler)
  galaxy   - Galaxy game object container (set after Galaxy())
  nt       - server Client connection    (set after nt_init())
  VERSION  - client version string       (set after VERSION = ...)

  _me_update_hooks - callables invoked with new_me after SP_YOU fires.
                     Populated by __init__.py to keep its own `me` in sync.
"""
import struct

from .constants import *
from .util import *
from . import rcd
from . import models
from . import game_sprites
from . import overlays

# Module-level state — set by gytha/__init__.py
opt = None
me = None
galaxy = None
nt = None
VERSION = None
_me_update_hooks = []


""" netrek protocol documentation, from server include/packets.h

	general protocol state outline

	starting state

	CP_SOCKET
	CP_FEATURE, optional, to indicate feature packets are known
	SP_MOTD
	SP_FEATURE, only if CP_FEATURE was seen
	SP_QUEUE, optional, repeats until slot is available
	SP_YOU, indicates slot number assigned

	login state, player slot status is POUTFIT
	client shows name and password prompt and accepts input

	CP_LOGIN
	CP_FEATURE
	SP_LOGIN
	SP_YOU
	SP_PLAYER_INFO
	various other server packets

	outfit state, player slot status is POUTFIT
	client shows team selection window

	SP_MASK, sent regularly during outfit

	client accepts team selection input
	CP_OUTFIT
	SP_PICKOK, signals server acceptance of alive state

	alive state,
	server places ship in game and play begins

	SP_PSTATUS, indicates PDEAD state
	client animates explosion

	SP_PSTATUS, indicates POUTFIT state
	clients returns to team selection window

	CP_QUIT
	CP_BYE
"""

""" client originated packets
"""

cp_table = {}

def _pb(x):
    """Encode str or pass bytes through for struct 's' fields."""
    if isinstance(x, str):
        return x.encode('ascii', errors='replace')
    return bytes(x)

class ClientPacket(type):
    def __new__(cls, name, bases, dct):
        client_packet = type.__new__(cls, name, bases, dct)

        if name.startswith('CP_'):
            cp_table[client_packet.code] = client_packet.format
            globals()[name.lower()] = client_packet()

        return client_packet

class CP(metaclass=ClientPacket):
    code = -1
    format = ''

    def data(self, *args):
        if opt.cp: print(self.__class__.__name__, args)
        return struct.pack(self.format, self.code, *args)

class CP_SOCKET(CP):
    code = 27
    format = '!bbbxI'

    def data(self):
        if opt.cp: print("CP_SOCKET")
        return struct.pack(self.format, self.code, 4, 10, 0)

class CP_BYE(CP):
    code = 29
    format = '!bxxx'

    def data(self):
        if opt.cp: print("CP_BYE")
        return struct.pack(self.format, self.code)

class CP_LOGIN(CP):
    code = 8
    format = '!bbxx16s16s16s'

    def data(self, query, name, password, login):
        if opt.cp: print(f"CP_LOGIN query={query} name={name}")
        return struct.pack(self.format, self.code, query,
                           _pb(name), _pb(password), _pb(login))

class CP_OUTFIT(CP):
    code = 9
    format = '!bbbx'

    def data(self, race, ship=ASSAULT):
        if opt.cp: print(f"CP_OUTFIT team={race_decode(race)} ship={ship}")
        return struct.pack(self.format, self.code, race, ship)

class CP_SPEED(CP):
    code = 2
    format = '!bbxx'

    def data(self, speed):
        if opt.cp: print(f"CP_SPEED speed={speed}")
        return struct.pack(self.format, self.code, speed)

class CP_DIRECTION(CP):
    code = 3
    format = '!bBxx'

    def data(self, direction):
        if opt.cp: print(f"CP_DIRECTION direction={direction}")
        return struct.pack(self.format, self.code, direction & 255)

class CP_PLANLOCK(CP):
    code = 15
    format = '!bbxx'

    def data(self, pnum):
        if opt.cp: print(f"CP_PLANLOCK pnum={pnum}")
        return struct.pack(self.format, self.code, pnum)

class CP_PLAYLOCK(CP):
    code = 16
    format = '!bbxx'

    def data(self, pnum):
        if opt.cp: print(f"CP_PLAYLOCK pnum={pnum}")
        return struct.pack(self.format, self.code, pnum)

class CP_UPDATES(CP):
    code = 31
    format = '!bxxxI'

    def data(self, usecs):
        if opt.cp: print(f"CP_UPDATES usecs={usecs}")
        return struct.pack(self.format, self.code, usecs)

class CP_BOMB(CP):
    code = 17
    format = '!bbxx'

    def data(self, state=1):
        if opt.cp: print(f"CP_BOMB state={state}")
        return struct.pack(self.format, self.code, state)

class CP_BEAM(CP):
    code = 18
    format = '!bbxx'

    def data(self, state=1):
        if opt.cp: print(f"CP_BEAM state={state}")
        return struct.pack(self.format, self.code, state)

class CP_CLOAK(CP):
    code = 19
    format = '!bbxx'

    def data(self, state=1):
        if opt.cp: print(f"CP_CLOAK state={state}")
        return struct.pack(self.format, self.code, state)

class CP_REPAIR(CP):
    code = 13
    format = '!bbxx'

    def data(self, state=1):
        if opt.cp: print(f"CP_REPAIR state={state}")
        return struct.pack(self.format, self.code, state)

class CP_SHIELD(CP):
    code = 12
    format = '!bbxx'

    def data(self, state=1):
        if opt.cp: print(f"CP_SHIELD state={state}")
        return struct.pack(self.format, self.code, state)

class CP_MESSAGE(CP):
    code = 1
    format = "!bBBx80s"

    def data(self, group, indiv, mesg):
        if opt.cp: print(f"CP_MESSAGE group={group} indiv={indiv} mesg={mesg}")
        return struct.pack(self.format, self.code, group, indiv, _pb(mesg))

class CP_PHASER(CP):
    code = 4
    format = '!bBxx'

    def data(self, direction):
        if opt.cp: print(f"CP_PHASER direction={direction}")
        return struct.pack(self.format, self.code, direction & 255)

class CP_PLASMA(CP):
    code = 5
    format = '!bBxx'

    def data(self, direction):
        if opt.cp: print(f"CP_PLASMA direction={direction}")
        return struct.pack(self.format, self.code, direction & 255)

class CP_TORP(CP):
    code = 6
    format = '!bBxx'

    def data(self, direction):
        if opt.cp: print(f"CP_TORP direction={direction}")
        return struct.pack(self.format, self.code, direction & 255)

class CP_QUIT(CP):
    code = 7
    format = '!bxxx'

    def data(self):
        if opt.cp: print("CP_QUIT")
        return struct.pack(self.format, self.code)

class CP_WAR(CP):
    code = 10
    format = '!bbxx'

    def data(self, newmask):
        if opt.cp: print(f"CP_WAR newmask={newmask}")
        return struct.pack(self.format, self.code, newmask)

class CP_PRACTR(CP):
    code = 11
    format = '!bxxx'

    def data(self):
        if opt.cp: print("CP_PRACTR")
        return struct.pack(self.format, self.code)

class CP_ORBIT(CP):
    code = 14
    format = '!bbxx'

    def data(self, state=1):
        if opt.cp: print(f"CP_ORBIT ={state}")
        return struct.pack(self.format, self.code, state)

class CP_DET_TORPS(CP):
    code = 20
    format = '!bxxx'

    def data(self):
        if opt.cp: print("CP_DET_TORPS")
        return struct.pack(self.format, self.code)

class CP_DET_MYTORP(CP):
    code = 21
    format = '!bxh'

    def data(self, tnum):
        if opt.cp: print("CP_DET_MYTORP")
        return struct.pack(self.format, self.code, tnum)

class CP_COPILOT(CP):
    code = 22
    format = '!bbxx'

    def data(self, state=1):
        if opt.cp: print("CP_COPILOT")
        return struct.pack(self.format, self.code, state)

class CP_REFIT(CP):
    code = 23
    format = '!bbxx'

    def data(self, ship):
        if opt.cp: print(f"CP_REFIT ship={ship}")
        return struct.pack(self.format, self.code, ship)

class CP_TRACTOR(CP):
    code = 24
    format = '!bbbx'

    def data(self, state, pnum):
        if opt.cp: print(f"CP_TRACTOR state={state} pnum={pnum}")
        return struct.pack(self.format, self.code, state, pnum)

class CP_REPRESS(CP):
    code = 25
    format = '!bbbx'

    def data(self, state, pnum):
        if opt.cp: print(f"CP_REPRESS state={state} pnum={pnum}")
        return struct.pack(self.format, self.code, state, pnum)

class CP_COUP(CP):
    code = 26
    format = '!bxxx'

    def data(self):
        if opt.cp: print("CP_COUP")
        return struct.pack(self.format, self.code)

class CP_OPTIONS(CP):
    code = 28
    format = "!bxxxI96s"

    def data(self, flags, keymap):
        if opt.cp: print(f"CP_OPTIONS flags={flags} keymap={keymap}")
        return struct.pack(self.format, self.code, flags, _pb(keymap))

class CP_DOCKPERM(CP):
    code = 30
    format = '!bbxx'

    def data(self, state):
        if opt.cp: print(f"CP_DOCKPERM state={state}")
        return struct.pack(self.format, self.code, state)

class CP_RESETSTATS(CP):
    code = 32
    format = '!bbxx'

    def data(self, verify):
        if opt.cp: print(f"CP_RESETSTATS verify={verify}")
        return struct.pack(self.format, self.code, verify)

class CP_RESERVED(CP):
    code = 33
    format = "!bxxx16s16s"

    def data(self, data, resp):
        if opt.cp: print("CP_RESERVED")
        return struct.pack(self.format, self.code, _pb(data), _pb(resp))

class CP_SCAN(CP):
    code = 34
    format = '!bbxx'

    def data(self, pnum):
        if opt.cp: print(f"CP_SCAN pnum={pnum}")
        return struct.pack(self.format, self.code, pnum)

class CP_UDP_REQ(CP):
    code = 35
    format = '!bbbxi'

    def data(self, request, connmode, port):
        if opt.cp: print("CP_UDP_REQ request=%d connmode=%d port=%d" % (request, connmode, port))
        return struct.pack(self.format, self.code, request, connmode, port)

class CP_FEATURE(CP):
    code = 60
    format = "!bcbbi80s"

    def data(self, type, arg1, arg2, value, name):
        if opt.cp: print("CP_FEATURE type=%s arg1=%d arg2=%d value=%d name=%s" % (type, arg1, arg2, value, name))
        return struct.pack(self.format, self.code, _pb(type), arg1, arg2, value, _pb(name))

class CP_PING_RESPONSE(CP):
    code = 42
    format = "!bBbxll"

    def data(self, number, pingme, cp_sent, cp_recv):
        if opt.cp: print(f"CP_PING_RESPONSE pingme={pingme}")
        return struct.pack(self.format, self.code, number, pingme, cp_sent, cp_recv)
        # FIXME: bug #1215317195 reported by Zach, pinging the player
        # using "!" results in O0 PING stats: Avg: 364 ms, Stdv: 19
        # ms, Loss: ^@100.0%/nan% s->c/c->s


""" server originated packets
"""

sp_table = {}

class ServerPacket(type):
    def __new__(cls, name, bases, dct):
        server_packet = type.__new__(cls, name, bases, dct)

        if dct['code'] not in sp_table:
            obj = server_packet()
            sp_table[server_packet.code] = (
                struct.calcsize(server_packet.format), obj)
            if name.lower() not in globals():
                globals()[name.lower()] = obj

        return server_packet

class SP(metaclass=ServerPacket):
    code = -1
    format = ''

    def find(self, number):
        """ given a packet type return a tuple consisting of
            (size, instance), or (1, self) if type not known
        """
        if number not in sp_table:
            return (1, self)
        return sp_table[number]

    def handler(self, data):
        raise NotImplemented


class SP_MOTD(SP):
    code = 11
    format = '!bxxx80s'

    def handler(self, data):
        (ignored, message) = struct.unpack(self.format, data)
        message = strnul(message)
        if opt.sp: print(f"SP_MOTD message={message}")
        galaxy.motd.add(message)

class SP_YOU(SP):
    code = 12
    format = '!bbbbbbxxIlllhhhh'

    def handler(self, data):
        global me
        (ignored, pnum, hostile, swar, armies, tractor, flags, damage,
         shield, fuel, etemp, wtemp, whydead, whodead) = struct.unpack(self.format, data)
        if opt.sp: print(f"SP_YOU pnum={pnum} hostile={team_decode(hostile)} swar={team_decode(swar)} armies={armies} tractor={tractor} flags={flags} damage={damage} shield={shield} fuel={fuel} etemp={etemp} wtemp={wtemp} whydead={whydead} whodead={whodead}")
        ship = galaxy.ship(pnum)
        ship.sp_you(me, hostile, swar, armies, flags, damage, shield, fuel, etemp, wtemp, whydead, whodead)
        me = ship
        models.me = me
        game_sprites.me = me
        overlays.me = me
        for hook in _me_update_hooks:
            hook(me)
        trac = galaxy.tractor(pnum, ship)
        trac.sp_tractor(flags, tractor)
        if nt.mode == COMM_TCP and ship.speed == 0:
            galaxy.pace()
        if opt.name:
            nt.send(cp_updates.data(1000000//opt.updates))
            nt.send(cp_login.data(0, opt.name, opt.password, opt.login))
            opt.name = None

class SP_QUEUE(SP):
    code = 13
    format = '!bxh'

    def handler(self, data):
        (ignored, pos) = struct.unpack(self.format, data)
        if opt.sp: print(f"SP_QUEUE pos={pos}")
        galaxy.sp_queue(pos);

class SP_PL_LOGIN(SP):
    code = 24
    format = "!bbbx16s16s16s"

    def handler(self, data):
        (ignored, pnum, rank, name, monitor,
         login) = struct.unpack(self.format, data)
        if opt.sp: print(f"SP_PL_LOGIN pnum={pnum} rank={rank} name={strnul(name)} monitor={strnul(monitor)} login={strnul(login)}")
        ship = galaxy.ship(pnum)
        ship.sp_pl_login(rank, name, monitor, login)

class SP_HOSTILE(SP):
    code = 22
    format = "!bbbb"

    def handler(self, data):
        (ignored, pnum, war, hostile) = struct.unpack(self.format, data)
        if opt.sp: print(f"SP_HOSTILE pnum={pnum} war={team_decode(war)} hostile={team_decode(hostile)}")
        ship = galaxy.ship(pnum)
        ship.sp_hostile(war, hostile)

class SP_PLAYER_INFO(SP):
    code = 2
    format = "!bbbb"

    def handler(self, data):
        (ignored, pnum, shiptype, team) = struct.unpack(self.format, data)
        if opt.sp: print(f"SP_PLAYER_INFO pnum={pnum} shiptype={shiptype} team={team_decode(team)}")
        ship = galaxy.ship(pnum)
        ship.sp_player_info(shiptype, team)

class SP_KILLS(SP):
    code = 3
    format = "!bbxxI"

    def handler(self, data):
        (ignored, pnum, kills) = struct.unpack(self.format, data)
        if opt.sp: print(f"SP_KILLS pnum={pnum} kills={kills}")
        ship = galaxy.ship(pnum)
        ship.sp_kills(kills)

class SP_PSTATUS(SP):
    code = 20
    format = "!bbbx"

    def handler(self, data):
        (ignored, pnum, status) = struct.unpack(self.format, data)
        if opt.sp: print(f"SP_PSTATUS pnum={pnum} status={status}")
        ship = galaxy.ship(pnum)
        ship.sp_pstatus(status)

class SP_PLAYER(SP):
    code = 4
    format = "!bbBbll"

    def handler(self, data):
        (ignored, pnum, dir, speed, x, y) = struct.unpack(self.format, data)
        if opt.sp: print(f"SP_PLAYER pnum={pnum} dir={dir} speed={speed} x={x} y={y}")
        ship = galaxy.ship(pnum)
        ship.sp_player(dir, speed, x, y)
        if nt.mode == COMM_TCP and ship == me:
            galaxy.pace()

class SP_FLAGS(SP):
    code = 18
    format = "!bbbxI"

    def handler(self, data):
        (ignored, pnum, tractor, flags) = struct.unpack(self.format, data)
        if opt.sp: print(f"SP_FLAGS pnum={pnum} tractor={tractor} flags={flags}")
        ship = galaxy.ship(pnum)
        ship.sp_flags(flags)
        trac = galaxy.tractor(pnum, ship)
        trac.sp_tractor(flags, tractor)

class SP_PLANET_LOC(SP):
    code = 26
    format = "!bbxxll16s"

    def handler(self, data):
        (ignored, pnum, x, y, name) = struct.unpack(self.format, data)
        if opt.sp: print(f"SP_PLANET_LOC pnum={pnum} x={x} y={y} name={strnul(name)}")
        planet = galaxy.planet(pnum)
        planet.sp_planet_loc(x, y, name)

class SP_LOGIN(SP):
    code = 17
    format = "!bbxxl96s"
    callback = None

    def uncatch(self):
        self.callback = None

    def catch(self, callback):
        self.callback = callback

    def handler(self, data):
        (ignored, accept, flags, keymap) = struct.unpack(self.format, data)
        if opt.sp: print(f"SP_LOGIN accept={accept} flags={flags}")
        if self.callback:
            self.callback(accept, flags, keymap)
            self.uncatch()
        if accept == 1:
            nt.send(cp_ping_response.data(0, 1, 0, 0))

class SP_MASK(SP):
    code = 19
    format = "!bbxx"
    callback = None
    last_mask = None

    def uncatch(self):
        self.callback = None

    def catch(self, callback):
        self.callback = callback
        if self.last_mask is not None:
            callback(self.last_mask)

    def handler(self, data):
        (ignored, mask) = struct.unpack(self.format, data)
        if opt.sp: print(f"SP_MASK mask={team_decode(mask)}")
        self.last_mask = mask
        if self.callback:
            self.callback(mask)
        # FIXME: #1187683470 update team selection icons in response to SP_MASK

class SP_PICKOK(SP):
    code = 16
    format = "!bbxx"
    callback = None
    versioned = False

    def uncatch(self):
        self.callback = None

    def catch(self, callback):
        self.callback = callback

    def version(self):
        if self.versioned: return
        self.versioned = True
        nt.send(cp_message.data(MINDIV | MCONFIG, me.n, "@gytha %s" % VERSION))

    def handler(self, data):
        (ignored, state) = struct.unpack(self.format, data)
        if opt.sp: print(f"SP_PICKOK state={state}")
        if state == 1:
            self.version()
        nt.sp_pickok()
        if self.callback:
            self.callback(state)
            self.uncatch()

class SP_RESERVED(SP):
    code = 25
    format = "!bxxx16s"

    def handler(self, data):
        (ignored, data) = struct.unpack(self.format, data)
        text = struct.unpack('16b', data)
        if opt.sp: print(f"SP_RESERVED data={text}")
        resp = data
        # FIXME: generate correct response data
        nt.send(cp_reserved.data(data, resp))

class SP_TORP_INFO(SP):
    code = 5
    format = "!bbbxhxx"

    def handler(self, data):
        (ignored, war, status, tnum) = struct.unpack(self.format, data)
        if opt.sp: print("SP_TORP_INFO war=%s status=%d tnum=%d" % (str(team_decode(war)), status, tnum))
        torp = galaxy.torp(tnum)
        torp.sp_torp_info(war, status)

class SP_TORP(SP):
    code = 6
    format = "!bBhll"

    def handler(self, data):
        (ignored, dir, tnum, x, y) = struct.unpack(self.format, data)
        if opt.sp: print("SP_TORP dir=%d tnum=%d x=%d y=%d" % (dir, tnum, x, y))
        torp = galaxy.torp(tnum)
        torp.sp_torp(dir, x, y)

class SP_PLASMA_INFO(SP):
    code = 8
    format = "!bbbxhxx"

    def handler(self, data):
        (ignored, war, status, pnum) = struct.unpack(self.format, data)
        if opt.sp: print(f"SP_PLASMA_INFO war={team_decode(war)} status={status} pnum={pnum}")
        plasma = galaxy.plasma(pnum)
        plasma.sp_plasma_info(war, status)

class SP_PLASMA(SP):
    code = 9
    format = "!bxhll"

    def handler(self, data):
        (ignored, pnum, x, y) = struct.unpack(self.format, data)
        if opt.sp: print(f"SP_PLASMA pnum={pnum} x={x} y={y}")
        plasma = galaxy.plasma(pnum)
        plasma.sp_plasma(x, y)

class SP_STATUS(SP):
    code = 14
    format = "!bbxxIIIIIL"

    def handler(self, data):
        (ignored, tourn, armsbomb, planets, kills, losses, time, timeprod) = struct.unpack(self.format, data)
        if opt.sp: print(f"SP_STATUS tourn={tourn} armsbomb={armsbomb} planets={planets} kills={kills} losses={losses} time={time} timepro={timeprod}")
        # FIXME: display t-mode state, and hey, the other things might be fun

class SP_PHASER(SP):
    code = 7
    format = "!bbbBlll"

    def handler(self, data):
        (ignored, pnum, status, dir, x, y, target) = struct.unpack(self.format, data)
        if opt.sp: print(f"SP_PHASER pnum={pnum} status={status} dir={dir}x={x}y={y} target={target}")
        phaser = galaxy.phaser(pnum)
        phaser.sp_phaser(status, dir, x, y, target)

class SP_PLANET(SP):
    code = 15
    format = "!bbbbhxxl"

    def handler(self, data):
        (ignored, pnum, owner, info, flags, armies) = struct.unpack(self.format, data)
        if opt.sp: print(f"SP_PLANET pnum={pnum} owner={owner} info={info} flags={flags} armies={armies}")
        planet = galaxy.planet(pnum)
        planet.sp_planet(owner, info, flags, armies)

class SP_MESSAGE(SP):
    code = 1
    format = "!bBBB80s"

    def handler(self, data):
        (ignored, m_flags, m_recpt, m_from, mesg) = struct.unpack(self.format, data)
        if opt.sp: print(f"SP_MESSAGE m_flags={m_flags} m_recpt={m_recpt} m_from={m_from} mesg={strnul(mesg)}")
        galaxy.sp_message(m_flags, m_recpt, m_from, mesg)

class SP_STATS(SP):
    code = 23
    format = "!bbxx13l"

    def handler(self, data):
        (ignored, pnum, tkills, tlosses, kills, losses, tticks, tplanets, tarmies, sbkills, sblosses, armies, planets, maxkills, sbmaxkills) = struct.unpack(self.format, data)
        if opt.sp: print(f"SP_STATS pnum={pnum} tkills={tkills} tlosses={tlosses} kills={kills} losses={losses} tticks={tticks} tplanets={tplanets} tarmies={tarmies} sbkills={sbkills} sblosses={sblosses} armies={armies} planets={planets} maxkills={maxkills} sbmaxkills={sbmaxkills}")
        ship = galaxy.ship(pnum)
        ship.sp_stats(armies+tarmies, planets+tplanets)

class SP_WARNING(SP):
    code = 10
    format = '!bxxx80s'
    text = ''
    seen = False

    def handler(self, data):
        (ignored, message) = struct.unpack(self.format, data)
        if opt.sp: print(f"SP_WARNING message={strnul(message)}")
        self.text = strnul(message)
        self.seen = False

    def synthetic(self, text):
        self.text = text
        self.seen = False

class SP_FEATURE(SP):
    code = 60
    format = "!bcbbi80s"

    def handler(self, data):
        (ignored, type, arg1, arg2, value, name) = struct.unpack(self.format, data)
        name = strnul(name)
        if opt.sp:
            print("SP_FEATURE type=%s arg1=%d arg2=%d value=%d name=%s" % (type, arg1, arg2, value, name))
        if (type, arg1, arg2, value, name) == ('S', 0, 0, 1, 'FEATURE_PACKETS'):
            # server says features packets are okay to send,
            # so send this client's features
            if rcd.cp_feature: # we want binary RCDs in SP_MESSAGE packets
                nt.send(cp_feature.data('S', 0, 0, 1, 'RC_DISTRESS'))
            nt.send(cp_feature.data('S', 0, 0, 1, 'SHIP_CAP'))
            nt.send(cp_feature.data('S', 2, 0, 1, 'SP_GENERIC_32'))
            nt.send(cp_feature.data('S', 0, 0, 1, 'TIPS'))
            nt.send(cp_feature.data('S', 0, 0, 1, 'SHOW_ALL_TRACTORS'))

        if name == 'UPS':
            galaxy.ups = value
        # FIXME: process the other feature packets received

class SP_BADVERSION(SP):
    code = 21
    format = "!bbxx"
    why = None

    def handler(self, data):
        (ignored, why) = struct.unpack(self.format, data)
        self.why = why

class SP_PING(SP):
    """ only received if client sends CP_PING_RESPONSE after SP_LOGIN """
    code = 46
    format = "!bBHBBBB"

    def handler(self, data):
        (ignored, number, lag, tloss_sc, tloss_cs, iloss_sc, iloss_cs) = struct.unpack(self.format, data)
        if opt.sp: print("SP_PING")
        nt.send(cp_ping_response.data(0, 1, 0, 0))

class SP_UDP_REPLY(SP):
    """ only received if client sends CP_UDP_REQ """
    code = 28
    format = "!bbxxi"

    def handler(self, data):
        (ignored, reply, port) = struct.unpack(self.format, data)
        if opt.sp: print("SP_UDP_REPLY reply=%d port=%d" % (reply, port))
        nt.sp_udp_reply(reply, port)

class SP_SEQUENCE(SP):
    """ the first packet the server sends in an update, followed by a
    variable number of packets with no terminating indication.  only
    received if client sends CP_UDP_REQ requesting COMM_UDP, """
    code = 29
    format = "!bBH"

    def handler(self, data):
        (ignored, flag, sequence) = struct.unpack(self.format, data)
        galaxy.pace()
        if opt.sp:
            print()  # mark start of new update in dump
            print("SP_SEQUENCE flag=%d sequence=%d" % (flag, sequence))

class SP_SHIP_CAP(SP):
    """ only received if client sends CP_FEATURE feature packet SHIP_CAP """
    code = 39
    format = "!bbHHHiiiiiiHHH1sx16s2sH"

    def handler(self, data):
        (ignored, operation, s_type, s_torpspeed, s_phaserrange, s_maxspeed, s_maxfuel, s_maxshield, s_maxdamage, s_maxwpntemp, s_maxegntemp, s_width, s_height, s_maxarmies, s_letter, s_name, s_desig, s_bitmap) = struct.unpack(self.format, data)
        if opt.sp: print("SP_SHIP_CAP operation=%d s_type=%d s_torpspeed=%d s_phaserrange=%d s_maxspeed=%d s_maxfuel=%d s_maxshield=%d s_maxdamage=%d s_maxwpntemp=%d s_maxegntemp=%d s_width=%d s_height=%d s_maxarmies=%d s_letter=%s s_name=%s s_desig=%s s_bitmap=%d" % (operation, s_type, s_torpspeed, s_phaserrange, s_maxspeed, s_maxfuel, s_maxshield, s_maxdamage, s_maxwpntemp, s_maxegntemp, s_width, s_height, s_maxarmies, s_letter, s_name, s_desig, s_bitmap))
        try:
            cap = galaxy.cap(s_type)
        except:
            print("SP_SHIP_CAP s_type was invalid: %d" % s_type)
            return
        # check operation, zero add or change, one remove
        if operation == 1:
            cap.reset(s_type)
            return
        if operation != 0:
            print("SP_SHIP_CAP operation was invalid: %d" % operation)
            return
        cap.seen = False
        cap.s_torpspeed = s_torpspeed
        cap.s_phaserrange = s_phaserrange
        cap.s_maxspeed = s_maxspeed
        cap.s_maxfuel = s_maxfuel
        cap.s_maxshield = s_maxshield
        cap.s_maxdamage = s_maxdamage
        cap.s_maxwpntemp = s_maxwpntemp
        cap.s_maxegntemp = s_maxegntemp
        cap.s_width = s_width
        cap.s_height = s_height
        cap.s_maxarmies = s_maxarmies
        cap.s_letter = s_letter
        cap.s_name = s_name
        cap.s_desig = s_desig
        cap.s_bitmap = s_bitmap

class SP_GENERIC_32(SP):
    """ only received if client sends CP_FEATURE of SP_GENERIC_32 """
    code = 32
    format = "!b1s30x"

    def handler(self, data):
        (ignored, version) = struct.unpack(self.format, data)
        if version == 'a':
            (ignored, version, repair_time, pl_orbit) = struct.unpack("b1shh26x", data)
            if opt.sp: print("SP_GENERIC_32 rt=%d or=%d" % (repair_time, pl_orbit))
            if me:
                me.sp_generic_32(repair_time, pl_orbit)
        elif version == 'b':
            (ignored, version, repair_time, pl_orbit, gameup, \
             tournament_teams, tournament_age, tournament_age_units, \
             tournament_remain, tournament_remain_units, starbase_remain, \
             team_remain) = struct.unpack("!b1sHbHBBsBsBB18x", data)
            if opt.sp: print(
                "SP_GENERIC_32 rt=%d or=%d gu=0x%x "
                "tt=%x ta=%d%s tr=%d%s sr=%d su=%d" % (
                    repair_time, pl_orbit, gameup, tournament_teams,
                    tournament_age, tournament_age_units, tournament_remain,
                    tournament_remain_units, starbase_remain, team_remain))
            if me:
                me.sp_generic_32(repair_time, pl_orbit)
            galaxy.sp_generic_32(gameup, tournament_teams, \
                tournament_age, tournament_age_units, tournament_remain, \
                tournament_remain_units, starbase_remain, team_remain)
            # FIXME: lower update rate while ^GU_UNSAFE
