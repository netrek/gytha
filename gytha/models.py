"""
Domain model classes for gytha: game objects and the Galaxy container.

Module-level state is wired up by gytha/__init__.py after it finishes
loading:

  me       - current player Ship    (set by SP_YOU handler)
  galaxy   - Galaxy singleton       (set after Galaxy() is constructed)
  screen   - pygame display surface (set by pg_init)
  b_info   - info-window sprite group (set by pg_init)
  opt      - parsed CLI options     (set at start of main)
  ac_done  - achievement callback   (set after ac_done is defined)

Sprite classes are also wired up after they are defined in __init__.py:

  Planet._TacticalSprite, Planet._GalacticSprite
  Ship._TacticalSprite,   Ship._GalacticSprite
  Torp._TacticalSprite
  Plasma._TacticalSprite
"""

import math
import pygame

from .constants import *
from .util import *
from .cap import Cap
from .motd import MOTD
from . import rcd
from . import sound
from .coords import n2ts, n_o, o_d, d2a, intragalactic, n_d

# Module-level state — set by __init__.py
me = None
galaxy = None
screen = None
b_info = None
opt = None
ac_done = lambda key: None  # replaced with the real function by __init__.py

NUMDETFRAMES = 10  # number of frames for a torp/plasma explosion animation


class Local:
    """Base class for all netrek game objects (ships, planets, torps, …)."""
    def __init__(self, n):
        self.n = n
        self.tactical = None
        self.galactic = None

    def __repr__(self):
        return 'Local(n=%r,\ntactical=%r,\ngalactic=%r)\n' % \
            (self.n, self.tactical, self.galactic)

    def op_info_update(self):
        for sprite in b_info:
            if sprite.track != self:
                return
            if not sprite.alive():
                return
            sprite.lines = self.op_info()
            sprite.pick()
            sprite.update()


class Planet(Local):
    """A netrek planet."""
    _TacticalSprite = None
    _GalacticSprite = None

    def __init__(self, n):
        Local.__init__(self, n)
        self.x = self.y = -10001
        self.name = ''
        self.owner = self.info = self.flags = self.armies = 0
        self.virgin = True
        self.tactical = self._TacticalSprite(self)
        self.galactic = self._GalacticSprite(self)
        self.nearby = False

    def __repr__(self):
        return Local.__repr__(self) + ('.Planet(name=%s)\n' % self.name)

    def sp_planet_loc(self, x, y, name):
        old = (self.x, self.y, self.name)
        if self.x != x or self.y != y:
            self.x = x
            self.y = y
            self.set_box(x, y)
        self.name = strnul(name)
        if old != (self.x, self.y, self.name):
            self.op_info_update()

    def sp_planet(self, owner, info, flags, armies):
        old = (self.owner, self.info, self.flags, self.armies)
        if not self.virgin:
            if self.owner != owner:
                if self.owner == me.team:
                    if galaxy.planets_same_owner(me.team) == 1:
                        sound.play('lps')
                    else:
                        sound.play('loss')
                if owner == me.team:
                    sound.play('gain')
                # FIXME: these sounds occur after a conquer parade too
        self.owner = owner
        self.info = info
        self.flags = flags
        self.armies = armies
        if old != (self.owner, self.info, self.flags, self.armies):
            self.op_info_update()
        self.virgin = False

    def op_info(self):
        lines = ['%s (a planet)' % self.name, '']
        if self.info & me.team:
            if self.armies != 0:
                lines.append(teams_long[self.owner].title() + ' ')
                lines.append('Armies %r' % self.armies)
            else:
                lines.append('Independent, no armies')
            lines.append('')
            if self.flags & PLFUEL: lines.append('FUELS')
            if self.flags & PLREPAIR: lines.append('REPAIRS')
            if self.flags & PLAGRI: lines.append('AGRICULTURAL')
            if self.flags & PLHOME: lines.append('HOME')
            if self.flags & PLCHEAP: lines.append('CHEAP')
            if self.flags & PLCORE: lines.append('CORE')
            for team in teams_playable:
                if self.info & team:
                    if team != self.owner:
                        name = teams_long[team].title()
                        lines.append('Scanned by %s ' % name)
        else:
            lines.append('Not scanned, please orbit to scan')
        return lines

    def set_box(self, x, y):
        """Create a proximity bounding box around the planet."""
        t = 13000
        wx = t * 2
        wy = t * 2
        sx = self.x - t
        sy = self.y - t
        if sx < 0:
            wx += sx
            sx = 0
        if sy < 0:
            wy += sy
            sy = 0
        self.box = pygame.Rect(sx, sy, wx, wy)

    def proximity(self, x, y):
        """Set planet visibility on tactical if we are within range."""
        if self.box.collidepoint(x, y):
            if not self.nearby:
                self.nearby = True
                self.tactical.show()
        else:
            if self.nearby:
                self.nearby = False
                self.tactical.hide()


class Ship(Local):
    """A netrek player ship."""
    _TacticalSprite = None
    _GalacticSprite = None

    def __init__(self, n):
        Local.__init__(self, n)
        # sp_pl_login
        self.rank = 0
        self.name = ''
        self.monitor = ''
        self.login = ''
        # sp_hostile
        self.war = 0
        self.hostile = 0
        # sp_player_info
        self.shiptype = CRUISER
        self.cap = galaxy.caps[CRUISER]
        self.team = 0
        self.mapchars = ''
        # sp_kills
        self.kills = 0  # hundredths
        self.sp_kills_me_shown = False
        # sp_player
        self.dir = 0
        self.speed = 0
        self.sp_player_me_speed_shown = False
        self.x = self.px = -(TWIDTH/2)
        self.y = self.py = -(TWIDTH/2)
        self.nearby = False
        # sp_flags
        self.flags = 0
        # sp_pstatus
        self.status = PFREE
        # sp_stats
        self.sp_stats_seen = False
        self.armies = 0
        self.planets = 0
        # sp_generic_32
        self.repair_time = 0
        self.pl_orbit = -1
        self.repair_time_shown = False

        self.planet = None  # planet we last locked on if flags & PFPLLOCK

        self.tactical = self._TacticalSprite(self)
        self.galactic = self._GalacticSprite(self)
        self.ppcf = 1  # planet proximity check fuse
        self.fuse = None

    def __repr__(self):
        return Local.__repr__(self) + ('.Ship(n=%r)\n' % (self.n))

    def op_info(self):
        lines = ['%s %s (a ship)' % (self.mapchars, self.name), '']
        lines.append(teams_long[self.team].title())
        lines.append(ships_long[self.shiptype].title() +
                     ' (' + ships_use[self.shiptype].title() + ')')
        lines.append('')
        if self.kills > 0:
            lines.append('Kills %.2f' % (self.kills / 100.0))
        else:
            lines.append('Mostly harmless')
        lines.append('')
        if self.team == me.team:
            lines.append('Is on your team')
        else:
            if self.war & me.team:
                lines.append('At war with you')
            else:
                if self.hostile & me.team:
                    lines.append('Hostile to you')
                else:
                    lines.append('At peace with you')
        lines.append('')
        if self.flags & PFSHIELD: lines.append('SHIELDS')
        if self.flags & PFBOMB: lines.append('BOMBING')
        if self.flags & PFORBIT: lines.append('ORBITING')
        if self.flags & PFCLOAK: lines.append('CLOAKED')
        if self.flags & PFROBOT: lines.append('ROBOT')
        if self.flags & PFPRACTR: lines.append('PRACTICE ROBOT')
        if self.flags & PFDOCK: lines.append('DOCKED')
        if self.flags & PFDOCKOK: lines.append('DOCKING PERMITTED')
        if self.flags & PFTWARP: lines.append('TRANSWARP ENGAGED')
        if self.flags & PFBPROBOT: lines.append('INTELLIGENT ROBOT')
        if self == me: lines.append('(this is you, by the way)')
        return lines

    def visibility(self):
        if self.status == PALIVE or self.status == PEXPLODE:
            self.galactic.show()
            if self == me or self.nearby:
                self.tactical.show()
            else:
                self.tactical.hide()
        else:
            self.galactic.hide()
            self.tactical.hide()

    def sp_you(self, current_me, hostile, swar, armies, flags, damage, shield,
               fuel, etemp, wtemp, whydead, whodead):
        if current_me == self:
            if not self.flags & PFORBIT:
                if flags & PFORBIT:
                    ac_done('Orbit')
            if self.armies == 0:
                if armies > 0:
                    ac_done('Pick')

        self.hostile = hostile
        self.swar = swar
        self.armies = armies
        self.flags = flags
        self.damage = damage
        self.shield = shield
        self.fuel = fuel
        self.etemp = etemp
        self.wtemp = wtemp
        self.whydead = whydead  # FIXME: display this data, on death
        self.whodead = whodead  # FIXME: display this data, on death
        self.sp_you_shown = False
        self.nearby = True

    def sp_pl_login(self, rank, name, monitor, login):
        self.rank = rank
        self.name = strnul(name)
        self.monitor = monitor
        self.login = login
        # FIXME: display this data, on player list

    def sp_hostile(self, war, hostile):
        self.war = war
        self.hostile = hostile
        self.op_info_update()
        # FIXME: display this data, on player list

    def sp_player_info(self, shiptype, team):
        self.shiptype = shiptype
        self.cap = galaxy.caps[shiptype]
        self.team = team
        self.mapchars = '%s%s' % (teams[team][:1].upper(), slot_decode(self.n))
        self.op_info_update()
        # FIXME: display this data, on player list

    def sp_kills(self, kills):
        if me == self:
            if self.kills != kills:
                self.sp_kills_me_shown = False
                if kills > 1000:
                    ac_done('Ten Kills')

        self.kills = kills
        self.op_info_update()
        # FIXME: display this data, on player list

    def sp_player(self, dir, speed, x, y):
        if me == self:
            if self.x < 0 and x > 0:
                self.px = self.x = x
                self.py = self.y = y
                galaxy.planets_proximity_check()
            if self.speed != speed:
                self.sp_player_me_speed_shown = False
        elif me:
            limit = TWIDTH // 2 + TWIDTH // 4
            nearby = (abs(me.x - x) < limit) or (abs(me.x - x) < limit)
            if nearby != self.nearby:
                self.nearby = nearby
                self.visibility()
        self.dir = d2a(dir)
        self.speed = speed
        self.x = x
        self.y = y
        # FIXME: display speed on tactical

        if me == self:
            self.ppcf -= 1
            if self.ppcf < 0:
                if abs(self.x - self.px) > 1000 or abs(self.y - self.py) > 1000:
                    self.px = self.x
                    self.py = self.y
                    galaxy.planets_proximity_check()
                self.ppcf = 20

    def sp_flags(self, flags):
        self.flags = flags
        self.op_info_update()

    def sp_pstatus(self, status):
        # was alive now exploding
        if self.status == PALIVE and status == PEXPLODE:
            if self == me:
                sound.play('death')
            galaxy.se.append(self)
            self.fuse = 10 * galaxy.ups / 10
        # was exploding now not
        if self.status == PEXPLODE and status != PEXPLODE:
            if self in galaxy.se:
                galaxy.se.remove(self)
        # store the status
        self.status = status
        # ship sprite visibility is brutally controlled by status
        # FIXME: do not show cloaked ships
        self.visibility()

    def sp_stats(self, armies, planets):
        if self == me:
            if self.sp_stats_seen:
                if self.armies != armies:
                    ac_done('Bombing')
                if self.planets != planets:
                    ac_done('Taking')
            else:
                self.sp_stats_seen = True
        self.armies = armies
        self.planets = planets

    def sp_generic_32(self, repair_time, pl_orbit):
        self.repair_time = repair_time
        self.pl_orbit = pl_orbit
        self.repair_time_shown = False

    def debug_draw(self):
        fx = 900
        fy = self.n * 30
        tx = 900 - (self.status * 10)
        ty = fy
        p = pygame.draw.line(screen, (255, 255, 255), (fx, fy), (tx, ty))
        q = pygame.draw.line(screen, (0, 0, 0), (tx, ty), (tx - 200, ty))
        return pygame.Rect.union(p, q)

    def aging(self):
        """If ship is exploding, decrement the explosion sequence fuse."""
        if self.status == PEXPLODE:
            self.fuse -= 1


class Torp(Local):
    """A netrek torpedo."""
    _TacticalSprite = None

    def __init__(self, n, gal):
        Local.__init__(self, n)
        self.n = n
        self.galaxy = gal
        self.ship = self.galaxy.ship(self.n // MAXTORP)
        self.fuse = 0
        self.status = TFREE
        self.sp_torp_info(0, self.status)
        self.sp_torp(0, 0, 0)
        self.tactical = self._TacticalSprite(self)

    def __repr__(self):
        return Local.__repr__(self) + ('.Torp(n=%r, ship.n=%r, fuse=%r, status=%r)\n' % (self.n, self.ship.n, self.fuse, self.status))

    def sp_torp_info(self, war, status):
        was = self.status
        self.war = war
        self.status = status
        if was == TFREE:
            if status != TFREE:
                if self not in self.galaxy.torps:
                    self.galaxy.torps[self.n] = self
                try: self.tactical.show()
                except: pass
        else:
            if status == TFREE:
                try: self.tactical.hide()
                except: pass
                self.x = -(TWIDTH/2)
                self.y = -(TWIDTH/2)
                del self.galaxy.torps[self.n]
            elif status == TEXPLODE:
                self.galaxy.te.append(self)
                self.fuse = NUMDETFRAMES * galaxy.ups / 10
                # FIXME: animate torp explosions over local time?
                # They vary according to update rate.
                if not opt.ubertweak:
                    (offset_x, offset_y) = n_o((self.x, self.y), (me.x, me.y))
                    if offset_x < TWIDTH/2 and offset_x < TWIDTH/2:
                        distance = o_d(offset_x, offset_y)
                        sound.texplode(distance)

    def sp_torp(self, dir, x, y):
        self.dir = dir
        self.x = x
        self.y = y

    def aging(self):
        """If torp is exploding, decrement the explosion sequence fuse."""
        if self.status == TEXPLODE:
            self.fuse -= 1
            if self.fuse <= 0:
                self.galaxy.te.remove(self)
                self.tactical.hide()
                self.x = -(TWIDTH/2)
                self.y = -(TWIDTH/2)
                self.status = TFREE
                del self.galaxy.torps[self.n]
        else:
            self.galaxy.te.remove(self)

    def debug_draw(self):
        fx = 0
        fy = self.n * 3
        tx = self.status * 50
        ty = fy
        p = pygame.draw.line(screen, (255, 255, 255), (fx, fy), (tx, ty))
        q = pygame.draw.line(screen, (0, 0, 0), (tx, ty), (tx + 200, ty))
        return pygame.Rect.union(p, q)


class Plasma(Local):
    """A netrek plasma torpedo."""
    _TacticalSprite = None

    def __init__(self, n):
        Local.__init__(self, n)
        self.ship = galaxy.ship(n)
        self.fuse = 0
        self.status = PTFREE
        self.sp_plasma_info(0, self.status)
        self.sp_plasma(0, 0)
        self.tactical = self._TacticalSprite(self)

    def sp_plasma_info(self, war, status):
        old = self.status

        self.war = war
        self.status = status

        try:
            if old == PTFREE:
                if status != PTFREE:
                    self.tactical.show()
            else:
                if status == PTFREE:
                    self.tactical.hide()
                elif status == PTEXPLODE:
                    galaxy.pe.append(self)
                    self.fuse = NUMDETFRAMES * galaxy.ups / 10
        except:
            pass

    def sp_plasma(self, x, y):
        self.x = x
        self.y = y

    def aging(self):
        """If plasma is exploding, decrement the explosion sequence fuse."""
        if self.status == PTEXPLODE:
            self.fuse -= 1
            if self.fuse <= 0:
                galaxy.pe.remove(self)
                self.tactical.hide()
                self.x = -(TWIDTH/2)
                self.y = -(TWIDTH/2)
                self.status = PTFREE


class Phaser(Local):
    """A netrek phaser (model and view combined)."""
    def __init__(self, n):
        Local.__init__(self, n)
        self.ship = galaxy.ship(n)
        self.status = PHFREE
        self.want = False  # is to be drawn on screen
        self.have = False  # has been drawn on screen
        self.sp_phaser(0, 0, 0, 0, 0)

    def draw(self):
        self.have = True
        if self.status == PHMISS:
            s_phaserrange = self.ship.cap.s_phaserrange
            phasedist = 6000
            factor = phasedist * s_phaserrange / 100
            angle = (self.dir - 64) / 128.0 * math.pi
            tx = int(factor * math.cos(angle))
            ty = int(factor * math.sin(angle))
            (tx, ty) = n2ts(me, self.ship.x + tx, self.ship.y + ty)
            (fx, fy) = n2ts(me, self.ship.x, self.ship.y)
        elif self.status == PHHIT2:
            target = galaxy.plasma(self.target)
            (tx, ty) = n2ts(me, target.x, target.y)
            (fx, fy) = n2ts(me, self.ship.x, self.ship.y)
        elif self.status == PHHIT:
            target = galaxy.ship(self.target)
            (tx, ty) = n2ts(me, target.x, target.y)
            (fx, fy) = n2ts(me, self.ship.x, self.ship.y)
        self.txty = (tx, ty)
        self.fxfy = (fx, fy)
        if self.ship == me:
            colour = (192, 192, 192)
        else:
            colour = brighten(team_colour(self.ship.team))
        # FIXME: incorrect colours have been sighted
        # FIXME: an enemy phaser makes our phaser invisible if the enemy has a higher ship number
        return pygame.draw.line(screen, colour, self.fxfy, self.txty, 4).inflate(8, 8)

    def undraw(self, colour):
        self.have = False
        return pygame.draw.line(screen, colour, self.fxfy, self.txty, 4).inflate(8, 8)

    def sp_phaser(self, status, direction, x, y, target):
        old = self.status

        self.status = status
        self.dir = direction
        self.x = x
        self.y = y
        self.target = target

        if old == PHFREE:
            if self.status != PHFREE:
                self.want = True
                if not opt.ubertweak:
                    if self.ship == me:
                        sound.play('phaser')
                    elif self.status == PHHIT and galaxy.ship(target) == me:
                        sound.play('inbound')
                if status == PHHIT2 and self.ship == me:
                    ac_done('Phaser Hit a Plasma')
                if status == PHHIT and self.ship == me:
                    if galaxy.ship(target).flags & PFCLOAK:
                        ac_done('Phaser Hit a Cloaked Enemy')
                    else:
                        ac_done('Phaser Hit')
        else:
            if self.status == PHFREE: self.want = False


class Tractor(Local):
    """A netrek tractor beam."""
    def __init__(self, n, ship):
        Local.__init__(self, n)
        self.ship = ship
        self.flags = self.target = 0
        self.want = False  # is to be drawn on screen
        self.have = False  # has been drawn on screen
        self.width = 11

    def draw(self):
        if self.ship.status != PALIVE:
            self.want = False
            return
        self.have = True
        them = galaxy.ship(self.target & (~0x40))
        self.txty = n2ts(me, them.x, them.y)
        self.fxfy = n2ts(me, self.ship.x, self.ship.y)
        # FIXME: use dotted line centre of tractor to periphery of
        # tractee, as per original design of netrek clients
        colour = (32, 64, 32)
        if self.flags & PFPRESS:
            colour = (64, 32, 32)
        return pygame.draw.line(screen, colour, self.fxfy, self.txty, self.width).inflate(self.width * 2, self.width * 2)

    def undraw(self, colour):
        self.have = False
        return pygame.draw.line(screen, colour, self.fxfy, self.txty, self.width).inflate(self.width * 2, self.width * 2)

    def sp_tractor(self, flags, target):
        self.want = False
        if target & 0x40:
            if flags & (PFTRACT | PFPRESS):
                if self.ship.status == PALIVE:
                    self.want = True
        self.flags = flags
        self.target = target


class Tag(Local):
    def __init__(self, xy):
        Local.__init__(self, 0)
        self.x, self.y = xy


class NegativeEnergyBarrier(Tag):
    def __init__(self, xy):
        Tag.__init__(self, xy)

    def op_info(self):
        return ['Negative Energy Barrier',
                '',
                'The edge of the playing area.',
                '',
                'Ships bounce off this harmlessly.',
                'Torpedos explode damaging ships nearby.',
                'Phasers do nothing.']


class Galaxy:
    """Container for all netrek game objects."""
    def __init__(self):
        self.planets = {}
        self.ships = {}
        self.torps = {}
        self.te = []  # exploding torps
        self.se = []  # exploding ships
        self.pe = []  # exploding plasma
        self.phasers = {}
        self.tractors = {}
        self.plasmas = {}
        self._torp_objs = {}
        self.caps = {}
        for n in range(NUM_TYPES):
            self.caps[n] = Cap(n)
        self.motd = MOTD()
        self.ups = 5   # default if SP_FEATURE UPS not received
        self.rps = 1   # tactical or galactic redraws per second
        self.frames = 0
        self.events = 0
        # sp_generic_32
        self.gameup = 0
        self.tournament_teams = 0
        self.tournament_age = 0
        self.tournament_age_units = 's'
        self.tournament_remain = 0
        self.tournament_remain_units = 's'
        self.starbase_remain = 0
        self.team_remain = 0
        # sp_queue
        self.sp_queue_pos = None
        self.message = None  # the MessageSprite
        # sp_sequence
        self.paced = False

    def __repr__(self):
        return 'Galaxy(\nships=%r, \ntorps=%r)\n' % (self.ships, self.torps)

    def pace(self):
        """Called when server packets indicate an update burst is starting."""
        self.paced = True
        self.plasma_aging()
        self.torp_aging()
        self.ship_aging()

    def planet(self, n):
        if n not in self.planets:
            self.planets[n] = Planet(n)
        return self.planets[n]

    def planets_proximity_check(self):
        for n, planet in self.planets.items():
            planet.proximity(me.x, me.y)

    def planets_same_owner(self, owner):
        number = 0
        for n, planet in self.planets.items():
            if planet.owner == owner:
                number += 1
        return number

    def ship(self, n):
        if n not in self.ships:
            self.ships[n] = Ship(n)
        return self.ships[n]

    def ship_aging(self):
        for s in self.se:
            s.aging()

    def ship_debug_draw(self):
        r = []
        for n, ship in self.ships.items():
            r.append(ship.debug_draw())
        return r

    def torp(self, n):
        if n not in self._torp_objs:
            self._torp_objs[n] = Torp(n, self)
        return self._torp_objs[n]

    def torp_aging(self):
        for t in self.te:
            t.aging()

    def torp_debug_draw(self):
        r = []
        for n, torp in self.torps.items():
            r.append(torp.debug_draw())
        return r

    def plasma_aging(self):
        for p in self.pe:
            p.aging()

    def phaser(self, n):
        if n not in self.phasers:
            self.phasers[n] = Phaser(n)
        return self.phasers[n]

    def phasers_undraw(self, colour):
        r = []
        for n, phaser in self.phasers.items():
            if phaser.have: r.append(phaser.undraw(colour))
        return r

    def phasers_draw(self):
        r = []
        for n, phaser in self.phasers.items():
            if phaser.want: r.append(phaser.draw())
        return r

    def tractor(self, n, ship):
        if n not in self.tractors:
            self.tractors[n] = Tractor(n, ship)
        return self.tractors[n]

    def tractors_undraw(self, colour):
        r = []
        for n, tractor in self.tractors.items():
            if tractor.have: r.append(tractor.undraw(colour))
        return r

    def tractors_draw(self):
        r = []
        for n, tractor in self.tractors.items():
            if tractor.want: r.append(tractor.draw())
        return r

    def plasma(self, n):
        if n not in self.plasmas:
            self.plasmas[n] = Plasma(n)
        return self.plasmas[n]

    def cap(self, n):
        if n not in self.caps:
            self.caps[n] = Cap(n)
        return self.caps[n]

    def is_enemy(self, thing):
        return thing.team != me.team

    def is_friend(self, thing):
        return thing.team == me.team

    def is_alive(self, thing):
        return thing.status == PALIVE

    def closest(self, xy, things, checks):
        """Return the closest thing to galactic coordinates, ignoring me."""
        x, y = xy
        closest = me
        minimum = GWIDTH
        for n, thing in things.items():
            if thing == me: continue
            disinterest = False
            for check in checks:
                if not check(thing):
                    disinterest = True
                    break
            if disinterest: continue
            distance = n_d((thing.x, thing.y), (x, y))
            if distance < minimum:
                closest = thing
                minimum = distance
        return closest

    def closest_planet(self, xy):
        return self.closest(xy, self.planets, [])

    def closest_ship(self, xy):
        return self.closest(xy, self.ships, [self.is_alive])

    def closest_enemy(self, xy):
        return self.closest(xy, self.ships, [self.is_enemy, self.is_alive])

    def closest_friend(self, xy):
        return self.closest(xy, self.ships, [self.is_friend, self.is_alive])

    def closest_thing(self, xy):
        if not intragalactic(xy):
            return NegativeEnergyBarrier(xy)
        cs = self.closest_ship(xy)
        cp = self.closest_planet(xy)
        x, y = xy
        dm = (me.x - x)**2 + (me.y - y)**2
        ds = (cs.x - x)**2 + (cs.y - y)**2
        dp = (cp.x - x)**2 + (cp.y - y)**2
        if dm < ds and dm < dp: return me
        if cs == me and cp != me: return cp
        if cs != me and cp == me: return cs
        if ds < dp: return cs
        return cp

    def sp_message(self, m_flags, m_recipt, m_from, mesg):
        if m_flags == (MVALID | MTEAM | MDISTR):
            d = rcd.msg()
            d.unpack(m_recipt, m_from, mesg)
            text = d.text(galaxy)
            # FIXME: portray RCDs graphically, e.g. action bubbles near ships
        else:
            text = strnul(mesg)
        if self.message != None:
            self.message.append(m_flags, m_recipt, m_from, text)

    def sp_generic_32(self, gameup, tournament_teams,
                      tournament_age, tournament_age_units, tournament_remain,
                      tournament_remain_units, starbase_remain, team_remain):
        self.gameup = gameup
        self.tournament_teams = tournament_teams
        self.tournament_age = tournament_age
        self.tournament_age_units = tournament_age_units
        self.tournament_remain = tournament_remain
        self.tournament_remain_units = tournament_remain_units
        self.starbase_remain = starbase_remain
        self.team_remain = team_remain

    def sp_queue(self, pos):
        self.sp_queue_pos = pos
