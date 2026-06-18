"""
Overlay drawing classes: tactical/galactic decorations, HUD sprites, and
the message/info window widgets.

Module-level state is wired by gytha/__init__.py at various init points:

  galaxy      - Galaxy singleton          (set after Galaxy() creation)
  me          - current player Ship       (set by SP_YOU handler)
  nt          - network client            (set after nt_init(), before pg_init)
  r_us        - play area rect            (set by pg_init, before sprites)
  r_sg        - subgalactic rect          (set by pg_init, before sprites)
  r_main      - full window rect          (set by pg_init, before sprites)
  screen      - pygame display surface    (set by pg_init, before sprites)
  opt         - parsed CLI options        (set at start of main)
  b_info      - info-window sprite group  (set by pg_init)
  UE_BOUNCER  - custom event type int     (set right after import)
  ac_done     - achievement callback      (set after ac_done is defined)
  sp_warning  - SP_WARNING singleton      (set by pg_init)
  cp_message  - CP_MESSAGE singleton      (set by pg_init)
"""

import time
import pygame
from pygame.locals import *

from .constants import *
from .util import *
from .cache import ic, fc
from .coords import n2ts, n2gs, n2ss, n_o, o_d, n_d
from . import coords
from . import sound

# Module-level state — set by __init__.py
galaxy = None
me = None
nt = None
r_us = None
r_sg = None
r_main = None
screen = None
opt = None
b_info = None
UE_BOUNCER = None
ac_done = lambda key: None
sp_warning = None
cp_message = None


class Halos:
    def __init__(self):
        self.arcs = []
        self.rect = []

    def arc(self, surface, colour, xy, r, w):
        self.arcs.append((xy, r, w))
        return pygame.draw.circle(surface, colour, xy, r, w)

    def draw_planets(self, surface, threshold):
        for n, planet in galaxy.planets.items():
            if planet.owner != me.team: continue
            colour = (0, 64, 0)
            if planet.x < 0: continue
            if planet.y < 0: continue
            (offset_x, offset_y) = n_o((planet.x, planet.y), (me.x, me.y))
            if offset_x < TWIDTH/2 and offset_x < TWIDTH/2: continue
            distance = o_d(offset_x, offset_y)
            radius = distance - threshold
            if radius < 100: continue
            radius = radius // 20
            cx, cy = n2ts(me, planet.x, planet.y)
            width = 1
            self.rect.append(self.arc(surface, colour, (cx, cy), radius, width))

    def draw_ships(self, surface, threshold):
        for n, ship in galaxy.ships.items():
            if ship.status != PALIVE: continue
            if ship == me: continue
            colour = (64, 0, 0)
            if ship.team == me.team: colour = (0, 64, 0)
            if ship.x < 0: continue
            if ship.y < 0: continue
            (offset_x, offset_y) = n_o((ship.x, ship.y), (me.x, me.y))
            if offset_x < TWIDTH/2 and offset_x < TWIDTH/2: continue
            distance = o_d(offset_x, offset_y)
            radius = distance - threshold
            if radius < 100: continue
            radius = radius // 20
            cx, cy = n2ts(me, ship.x, ship.y)
            width = 1
            self.rect.append(self.arc(surface, colour, (cx, cy), radius, width))

    def draw_lock(self, surface, threshold):
        if not me.flags & PFPLLOCK:
            return
        planet = me.planet
        colour = (0, 0, 64)
        distance = n_d((planet.x, planet.y), (me.x, me.y))
        radius = distance - threshold
        if radius < 100: return
        radius = radius // 20
        cx, cy = n2ts(me, planet.x, planet.y)
        width = 4
        self.rect.append(self.arc(surface, colour, (cx, cy), radius, width))

    def draw(self, surface):
        if not opt.halos:
            return []
        self.arcs = []
        self.rect = []
        if me.x < 0 or me.y < 0: return self.rect
        threshold = 9700
        #self.draw_planets(surface, threshold)
        self.draw_ships(surface, threshold)
        self.draw_lock(surface, threshold)
        return self.rect

    def undraw(self, surface, colour):
        if not opt.halos:
            return []
        for (xy, r, w) in self.arcs:
            pygame.draw.circle(surface, colour, xy, r, w)
        return self.rect


class Lines:
    def __init__(self):
        self.lines = []
        self.rect = []

    def line(self, sx, sy, ex, ey):
        self.lines.append((sx, sy, ex, ey))
        return pygame.draw.line(screen, (255, 0, 0), (sx, sy), (ex, ey))

    def draw(self):
        self.lines = []
        self.rect = []


class Borders(Lines):
    def __init__(self):
        Lines.__init__(self)
        n = GWIDTH / 10
        self.inner = pygame.Rect((n, n), (GWIDTH-n-n, GWIDTH-n-n))

    def limit(self, v1, v2, vmin, vmax):
        return (max(vmin, v1), min(vmax-1, v2))

    def draw(self):
        self.lines = []
        self.rect = []
        if self.inner.collidepoint(me.x, me.y): return self.rect
        x1, y1 = n2ts(me, 0, 0)
        x2, y2 = n2ts(me, GWIDTH, GWIDTH)
        if r_us.left < x1 < r_us.right:
            (sy, ey) = self.limit(y1, y2, r_us.top, r_us.bottom)
            self.rect.append(self.line(x1, sy, x1, ey))
        if r_us.top < y1 < r_us.bottom:
            (sx, ex) = self.limit(x1, x2, r_us.left, r_us.right)
            self.rect.append(self.line(sx, y1, ex, y1))
        if r_us.left < x2 < r_us.right:
            (sy, ey) = self.limit(y1, y2, r_us.top, r_us.bottom)
            self.rect.append(self.line(x2, sy, x2, ey))
        if r_us.top < y2 < r_us.bottom:
            (sx, ex) = self.limit(x1, x2, r_us.left, r_us.right)
            self.rect.append(self.line(sx, y2, ex, y2))
        return self.rect

    def undraw(self, colour):
        for (sx, sy, ex, ey) in self.lines:
            pygame.draw.line(screen, colour, (sx, sy), (ex, ey))
        return self.rect

    def draw_debug_planet_proximity_boxes(self):
        for n, planet in galaxy.planets.items():
            (x1, y1, w, h) = planet.box
            x2 = x1 + w
            y2 = y1 + h
            x1, y1 = n2ts(me, x1, y1)
            x2, y2 = n2ts(me, x2, y2)
            self.rect.append(self.line(x1, y1, x2, y2))
            self.rect.append(self.line(x1, y2, x1, y2))


class LocatorSprite(pygame.sprite.Sprite):
    """Box on the galactic view showing the current tactical area."""
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.pick()

    def update(self):
        self.pick()
        self.rect.center = n2gs(me.x, me.y)

    def pick(self):
        self.image = ic.get('locator.png')
        self.rect = self.image.get_rect()


class Alerts:
    """Red/yellow/green alert border around the play area."""
    def __init__(self):
        self.reset()

    def reset(self):
        self.lines = []
        self.rect = []

    def line(self, sx, sy, ex, ey):
        self.lines.append((sx, sy, ex, ey))
        self.rect.append(pygame.draw.line(screen, self.colour, (sx, sy), (ex, ey)))

    def draw_box(self, l, t, r, b):
        self.line(l, t, r, t)
        self.line(r, t, r, b)
        self.line(r, b, l, b)
        self.line(l, b, l, t)

    def draw_box_thick(self, l, t, r, b):
        self.draw_box(l, t, r, b)
        self.draw_box(l+1, t+1, r-1, b-1)

    def pick_colour(self):
        self.colour = (0, 64, 0)
        if me.flags & PFYELLOW:
            self.colour = (128, 128, 0)
        elif me.flags & PFRED:
            self.colour = (255, 64, 64)

    def undraw(self, colour):
        for (sx, sy, ex, ey) in self.lines:
            pygame.draw.line(screen, colour, (sx, sy), (ex, ey))
        return self.rect


class TacticalAlerts(Alerts):
    def __init__(self):
        Alerts.__init__(self)

    def draw(self):
        self.reset()
        self.pick_colour()
        self.draw_box_thick(r_us.left, r_us.top, r_us.right-1, r_us.bottom-1)
        return self.rect


class GalacticAlerts(Alerts):
    def __init__(self):
        Alerts.__init__(self)

    def draw(self):
        self.reset()
        self.pick_colour()
        l, t = n2gs(0, 0)
        r, b = n2gs(GWIDTH-1, GWIDTH-1)
        self.draw_box_thick(l, t, r, b)
        # FIXME: bottom line not visible if main height = 600, why?
        return self.rect


class Subgalactic(Alerts):
    def __init__(self):
        Alerts.__init__(self)

    def draw(self):
        self.reset()
        def draw_box(x, y, s):
            self.draw_box(x-s, y-s, x+s, y+s)
        def draw_diamond(x, y, s):
            self.line(x, y-s, x+s, y)
            self.line(x, y+s, x+s, y)
            self.line(x, y+s, x-s, y)
            self.line(x, y-s, x-s, y)
        self.colour = (64, 64, 64)
        x, y = n2ss(me.x, me.y)
        draw_box(x, y, 20)
        self.colour = (92, 92, 92)
        self.draw_box_thick(r_sg.left, r_sg.top, r_sg.right-1, r_sg.bottom-1)
        for n, planet in galaxy.planets.items():
            x, y = n2ss(planet.x, planet.y)
            self.colour = team_colour(planet.owner)
            draw_diamond(x, y, 4)
        for n, ship in galaxy.ships.items():
            if ship.status != PALIVE: continue
            if not ship.x or not ship.y:
                continue
            x, y = n2ss(ship.x, ship.y)
            self.colour = (255, 255, 255)
            if ship != me:
                self.colour = brighten(team_colour(ship.team))
            draw_box(x, y, 1)
        return self.rect


class DebugSprite(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.font = fc.get(FONT_SANS_MONO, 20)
        self.maxrps = 0
        self.minrps = 1000
        self.rps = []
        self.nrps = 10
        self.frames = 0
        self.last = self.now = time.time()
        self.pick()

    def update(self):
        self.pick()

    def pick(self):
        self.now = nt.time
        x = ' '
        x += 'ups %d ' % galaxy.ups
        fps = (galaxy.frames - self.frames) / (self.now - self.last)
        x += 'fps %.1f ' % fps
        self.frames = galaxy.frames
        self.last = self.now
        x += 'events %d ' % galaxy.events
        rps = galaxy.rps
        self.rps.append(rps)
        if len(self.rps) > self.nrps:
            del self.rps[0]
        x += 'rps %d ' % rps
        s = 0
        for e in self.rps:
            s += e
        avg = s / len(self.rps)
        x += 'avg %d ' % avg
        if galaxy.rps < fps:
            x += ' DISPLAY LAG'
        print(x)
        self.text = x
        self.image = self.font.render(self.text, 1, (255, 255, 255))
        self.rect = self.image.get_rect(centerx=r_us.centerx, bottom=r_us.bottom-50)


class ReportSprite(pygame.sprite.Sprite):
    """Status bar showing speed, fuel, damage, flags, and game state."""
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.font = fc.get(FONT_SANS_MONO, 20)
        self.fuel = self.damage = self.shield = self.armies = 0
        self.image = self.font.render('--', 1, (255, 255, 255))
        self.rect = self.image.get_rect(centerx=r_us.centerx, bottom=r_us.bottom-2)

    def update(self):
        if me.sp_you_shown and \
           me.sp_player_me_speed_shown and \
           me.sp_kills_me_shown and \
           me.repair_time_shown and \
           galaxy.sp_generic_32_shown: return
        self.pick()
        me.sp_you_shown = True
        me.sp_player_me_speed_shown = True
        me.sp_kills_me_shown = True
        me.repair_time_shown = True
        galaxy.sp_generic_32_shown = True

    def flags(self):
        r = ''
        f = me.flags
        if f & PFPRESS: f ^= PFTRACT
        f ^= PFSEEN
        x = ['SHIELDS',      'REPAIRING',     'BOMBING',       'ORBITING',
             'CLOAKED',      'WEAPONS-HOT',   'ENGINES-HOT',   'ROBOT',
             'BEAM-UP',      'BEAM-DOWN',     'SELF-DESTRUCT', None,
             None,           None,            'SHIP-LOCK',     'PLANET-LOCK',
             'COPILOT',      'DECLARING-WAR', 'PRACTICE',      'DOCKED',
             'REFIT',        'REFITTING',     'TRACTOR',       'PRESSOR',
             'DOCKING-OK',   'UNSEEN',        'CYBORG',        'OBSERVING',
             None,           'OBSERVE',       'TRANSWARP',     'BPROBOT']
        for n in range(32):
            if f & (1 << n):
                if x[n]:
                    r += x[n] + ' '
        f = galaxy.gameup ^ GU_UNSAFE
        if f & GU_BOT_IN_GAME: f ^= GU_PRET
        if f & GU_PRACTICE: f ^= GU_CHAOS
        if f & GU_CONQUER:
            f ^= GU_PAUSED
            ac_done('A conquer parade!')
            sound.conquer()
        x = ['safe-idle',   # ^GU_UNSAFE
             'practice',    # GU_PRACTICE
             'chaos',       # GU_CHAOS
             'paused',      # GU_PAUSED
             'league',      # GU_INROBOT
             'newbie',      # GU_NEWBIE
             'pre-t',       # GU_PRET
             'pre-t-bots',  # GU_BOT_IN_GAME
             'conquer-parade', # GU_CONQUER
             'puck',        # GU_PUCK
             'dog',         # GU_DOG
             'drafting',    # GU_INL_DRAFTING
             'drafted',     # GU_INL_DRAFTED
             ]
        for n in range(32):
            if f & (1 << n):
                if x[n]:
                    r += '(' + x[n] + ') '
        return r

    def pick(self):
        x = ' '
        if me.armies > 0:                   x += "A %d " % me.armies
        if me.kills  > 0:                   x += "K %.2f " % (me.kills / 100.0)
        if me.shiptype != STARBASE:
            if me.speed > 0:                x += "S %d " % me.speed
        else:
            if me.speed != me.cap.s_maxspeed: x += "S %d " % me.speed
        if me.fuel   < me.cap.s_maxfuel:    x += "F %d " % me.fuel
        if me.damage > 0:                   x += "D %d " % me.damage
        if me.shield < me.cap.s_maxshield:  x += "S %d " % me.shield
        if me.etemp  > 0:                   x += "E %d " % (me.etemp / 10)
        if me.wtemp  > 0:                   x += "W %d " % (me.wtemp / 10)
        x += self.flags()
        if me.flags & PFREPAIR:
            x += '[%d] ' % me.repair_time
        if galaxy.tournament_remain != 0:
            x += '{%d%s} ' % (galaxy.tournament_remain, galaxy.tournament_remain_units)
        self.text = x
        self.image = self.font.render(self.text, 1, (255, 255, 255))
        self.rect = self.image.get_rect(centerx=r_us.centerx, bottom=r_us.bottom-2)


class WarningSprite(pygame.sprite.Sprite):
    """Transient red warning text near the top of the play area."""
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.font = fc.get(FONT_SANS, 24)
        self.last = ''
        self.time = 0
        self.pick('')

    def update(self):
        if sp_warning.seen: return
        sp_warning.seen = True
        text = sp_warning.text
        if self.last != text:
            self.last = text
            self.pick(text)
            self.time = 1000
            length = len(text)
            if length > 32: self.time = 2500
            if length > 64: self.time = 5000
        pygame.time.set_timer(UE_BOUNCER, self.time)

    def ue(self, event):
        pygame.time.set_timer(UE_BOUNCER, 0)
        self.pick('')

    def pick(self, text):
        self.image = self.font.render(text, 1, (255, 0, 0))
        self.rect = self.image.get_rect(centerx=r_us.centerx, top=r_us.top+2)


class MessageLine:
    def __init__(self, m_flags, m_recipt, m_from, mesg):
        self.text = mesg
        self.colour = (128, 128, 128)
        if m_from != 0xff:
            self.colour = team_colour(galaxy.ship(m_from).team)
        self.expires = nt.time + 15
        self.expired = False


class InfoSprite(pygame.sprite.Sprite):
    """Pop-up information window for screen objects, help, and achievements."""
    def __init__(self, lines, track=None, expires=7,
                 fillcolour=(48, 24, 48, 128), bordercolour=(255, 128, 255)):
        pygame.sprite.Sprite.__init__(self)
        self.font = fc.get(FONT_SANS_CONDENSED, 18)
        self.lines = lines
        self.pad = 20
        self.border = 2
        self.track = track
        self.expires = nt.time + expires
        self.expired = False
        self.fillcolour = fillcolour
        self.bordercolour = bordercolour
        self.pick()
        self.update()
        self.add(b_info)

    def update(self):
        if nt.time > self.expires:
            self.kill()
            return
        if self.track:
            if not coords.is_galactic:
                self.rect.center = n2ts(me, self.track.x, self.track.y)
            else:
                self.rect.center = n2gs(self.track.x, self.track.y)
        else:
            self.rect.center = (r_us.centerx, r_us.centery)

    def pick(self):
        x = self.border + self.pad
        y = self.border + self.pad
        surfaces = []
        longest = 0
        for line in self.lines:
            surface = self.font.render(line, 1, (250, 250, 250))
            surfaces.append(surface)
            rect = surface.get_rect()
            y = y + rect.height + 1
            longest = max(longest, rect.width)
        x += longest
        x += self.pad + self.border
        y += self.pad + self.border
        self.image = pygame.Surface((x, y), pygame.SRCALPHA, 32)
        self.image.fill(self.fillcolour)
        x = self.border + self.pad
        y = self.border + self.pad
        w = x
        for surface in surfaces:
            rect = surface.get_rect(left=x, top=y)
            self.image.blit(surface, rect)
            y = y + rect.height + 1
            if rect.right > w: w = rect.right
        x = w
        x += self.pad + self.border
        y += self.pad + self.border
        rect = pygame.Rect(0, 0, x - self.border, y - self.border)
        pygame.draw.rect(self.image, self.bordercolour, rect, self.border)
        self.rect = self.image.get_rect(centerx=r_us.centerx, centery=r_us.centery)


class MessageSprite(pygame.sprite.Sprite):
    """Incoming/outgoing message window with message composition support."""
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        galaxy.message = self
        self.width = 900
        self.height = 400
        size = 16
        if r_main.width < 801:
            size = 14
            self.width = 750
        self.font = fc.get(FONT_SANS_MONO, size)
        self.maximum = 10
        self.dirty = True
        self.lines = []
        self.head = ''
        intro = ['Welcome to Netrek',
                 ' ',
                 'You are now in your ship',
                 'Press a number to start moving',
                 'Use right mouse button to steer',
                 'Use left mouse button to fire torpedoes',
                 'Press m to send a message',
                 ' ']
        for line in intro:
            self.append(0, 0, 0xff, line)
        self.pick()

    def append(self, m_flags, m_recipt, m_from, mesg):
        """Add a received message to the display."""
        # FIXME: show only team and individual messages by default
        # messages to ALL are not generally useful.
        self.lines.append(MessageLine(m_flags, m_recipt, m_from, mesg))
        if len(self.lines) > self.maximum:
            del self.lines[0]
        self.dirty = True

    def update(self):
        for line in self.lines:
            if not line.expired:
                if line.expires < nt.time:
                    line.expired = True
                    self.dirty = True
        if self.dirty:
            self.pick()
            self.dirty = False

    def pick(self):
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA, 32)
        surfaces = []
        for line in self.lines:
            text = line.text
            if line.expired and self.head == '':
                text = ''
            colour = line.colour
            if self.head != '':
                colour = brighten(colour)
            ts = self.font.render(text, 1, colour)
            surfaces.append(ts)
        y = 0
        for surface in surfaces:
            rect = surface.get_rect(left=0, top=y)
            self.image.blit(surface, rect)
            y = y + rect.height + 1
        y = y + 10
        if self.head != '':
            box_top = y - 1
            line = self.head + '->' + self.tail + '  ' + self.text
            surface = self.font.render(line, 1, (255, 255, 255))
            rect = surface.get_rect(left=0, top=y)
            self.image.blit(surface, rect)
            y = y + rect.height + 1
            (line, colour) = self.hint()
            surface = self.font.render(line, 1, colour)
            rect = surface.get_rect(left=0, top=y)
            self.image.blit(surface, rect)
            y = y + rect.height + 1
            rect = pygame.Rect(0, box_top, self.width, (y - box_top))
            pygame.draw.rect(self.image, (128, 128, 255), rect, 1)
        self.rect = self.image.get_rect(centerx=r_us.centerx, top=r_us.top+100)
        # FIXME: darken on red alert
        # FIXME: flexible user chosen position
        # FIXME: place in quadrant away from action depending on team

    def start(self):
        """Start composing an outgoing message."""
        self.dirty = True
        self.group = 0
        self.indiv = 0
        self.head = ' ' + me.mapchars
        self.tail = ''
        self.text = ''

    def abort(self):
        """Abort message composition."""
        self.dirty = True
        self.head = ''

    def retarget(self):
        """Return to target selection for outgoing message."""
        self.dirty = True
        self.tail = ''

    def target(self, event):
        """Process target selection; return True if a valid target was chosen."""
        self.dirty = True
        if (event.mod & KMOD_SHIFT):
            targs = {K_a: [MALL, 'ALL'], K_g: [MGOD, 'GOD']}
            if event.key in targs:
                (self.group, self.tail) = targs[event.key]
                return True
            targs = {K_f: FED, K_r: ROM, K_k: KLI, K_o: ORI}
            if event.key in targs:
                self.group = MTEAM
                self.indiv = targs[event.key]
                self.tail = teams[self.indiv].upper()
                return True
        if event.key == K_t or event.key == K_SPACE:
            self.group = MTEAM
            self.indiv = me.team
            self.tail = teams[self.indiv].upper()
            return True
        if event.key == K_EQUALS:
            self.group = MINDIV
            self.indiv = me.n
            self.tail = me.mapchars + ' '
            return True
        slot = slot_encode(event.unicode)
        if slot == -1:
            return False
        ship = galaxy.ship(slot)
        if ship == None:
            return False
        if ship.status == PFREE:
            return False
        self.group = MINDIV
        self.indiv = ship.n
        self.tail = ship.mapchars + ' '
        return True

    def typing(self, event):
        """Accumulate typed characters into the outgoing message buffer."""
        self.dirty = True
        self.text = self.text + event.unicode

    def backspace(self):
        self.dirty = True
        self.text = self.text[:-1]

    def is_empty(self):
        return len(self.text) == 0

    def send(self):
        """Send the composed message to the server and loop it back locally."""
        mesg = str(self.text)
        line = self.head + '->' + self.tail + '  ' + self.text
        self.head = self.tail = self.text = ''
        self.dirty = True
        nt.send(cp_message.data(self.group, self.indiv, mesg))
        # Messages sent to god, other teams, or individual players are not
        # echoed by the server, so loop them back to our own display.
        if ((self.group == MGOD) or
                (self.group == MTEAM and self.indiv != me.team) or
                (self.group == MINDIV and self.indiv != me.n)):
            galaxy.sp_message(0, 0, 0, line)

    def hint(self):
        """Generate contextual input hint during message composition."""
        if len(self.text) > (80 - 12):
            return ('          ' + ' ' * len(self.text) + '^ GO BACK', (255, 128, 128))
        if len(self.text) > (79 - 12):
            return ('          ' + ' ' * len(self.text) + '^ STOP', (255, 128, 128))
        if len(self.text) > 12:
            return ('          ' + ' ' * len(self.text) + '^ type', (128, 255, 128))
        if len(self.text) > 0:
            return ('          ' + ' ' * len(self.text) + '^ type, press enter to send, or ESC to abort', (128, 255, 128))
        if self.tail != '':
            return ('          ' + ' ' * len(self.text) + '^ type, or backspace', (128, 255, 128))
        if self.head != '':
            return ('     ^ t for team, A for all, F, R, K, O, a ship number, or ESC to abort', (128, 128, 255))
        return ('bogus', (255, 255, 255))
