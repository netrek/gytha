"""
User interface display phase classes and top-level game control flow.

Module-level state — set by gytha/__init__.py:

  screen             - main display surface           (set by pg_init)
  opt                - parsed CLI options             (set at start of main)
  nt                 - server Client connection       (set after nt_init)
  mc                 - MetaClient connection          (set in main)
  galaxy             - Galaxy game object container   (set after Galaxy())
  me                 - current player Ship            (set by SP_YOU hook)
  r_main             - full window Rect               (set by pg_init)
  r_us               - tactical/galactic area Rect    (set by pg_init)
  background         - black background Surface       (set by pg_init)
  b_info             - info overlay sprite group      (set by pg_init)
  b_warning          - warning sprite group           (set by pg_init)
  b_warning_sprite   - WarningSprite instance        (set by pg_init)
  b_reports          - reports sprite group           (set by pg_init)
  b_message          - message sprite group           (set by pg_init)
  g_planets          - galactic planet sprite group   (set by pg_init)
  g_players          - galactic ship sprite group     (set by pg_init)
  g_locator          - galactic locator sprite group  (set by pg_init)
  t_planets          - tactical planet sprite group   (set by pg_init)
  t_players          - tactical ship sprite group     (set by pg_init)
  t_torps            - tactical torp sprite group     (set by pg_init)
  t_plasma           - tactical plasma sprite group   (set by pg_init)
  WELCOME            - welcome text lines             (set after defined)
  INSTRUCTIONS_SERVERS - server list help text        (set after defined)
  UE_TIMER           - custom event type for timer    (set after defined)
  NETWORK_DATA_READY - custom event type for network  (set after defined)

  Injected callables (set by __init__.py after they are defined there):
  pg_quit, nt_start_thread, nt_shutdown
  ac_save, ac_done, ac_done_later, ac_deliver, ac_progress
"""
import sys
import time

import pygame
from pygame.locals import *

from .constants import *
from .util import *
from .cache import ic, fc
from .bouncer import Bouncer
from .sprites import Text, Texts, Field, IconButton, IconTextButton, HorizontalAssemblyButton
from .coords import n2ts, n2gs, cursor, s2d, n_d
from . import coords
from . import rcd
from . import mercenary
from .client import ServerDisconnectedError
from .models import Tag
from .overlays import InfoSprite, GalacticAlerts, TacticalAlerts, Borders, Halos, Subgalactic
from .packets import (
    cp_bye, cp_quit, cp_login, cp_updates, cp_outfit, cp_direction,
    cp_phaser, cp_torp, cp_beam, cp_bomb, cp_cloak, cp_det_torps, cp_det_mytorp,
    cp_message, cp_dockperm, cp_orbit, cp_planlock, cp_plasma, cp_playlock,
    cp_practr, cp_repress, cp_repair, cp_shield, cp_tractor, cp_speed,
    cp_refit, cp_socket, cp_feature,
    sp_warning, sp_login, sp_mask, sp_pickok, sp_badversion,
)

# Module-level state — set by gytha/__init__.py
screen = None
opt = None
nt = None
mc = None
galaxy = None
me = None
r_main = None
r_us = None
background = None
b_info = None
b_warning = None
b_warning_sprite = None
b_reports = None
b_message = None
g_planets = None
g_players = None
g_locator = None
t_planets = None
t_players = None
t_torps = None
t_plasma = None
ph_flight = None
ph_tactical = None
ph_galactic = None
rounds = 0
WELCOME = []
INSTRUCTIONS_SERVERS = []
UE_TIMER = None
NETWORK_DATA_READY = None

# Injected callables — set by __init__.py after they are defined there
pg_quit = None
nt_start_thread = None
nt_shutdown = None
ac_save = None
ac_done = None
ac_done_later = None
ac_deliver = None
ac_progress = None


""" user interface display phases
"""

class Phase:
    """ display phases common code """
    def __init__(self):
        self.ue_hz = 10
        self.ue_delay = 1000 // self.ue_hz
        self.screenshot = 0
        self.run = False
        self.eh_md = [] # event handlers, mouse down
        self.eh_mu = [] # event handlers, mouse up
        self.eh_mm = [] # event handlers, mouse movement
        self.eh_ue = [] # event handlers, user events (timers)

    def eh_add_clickable(self, b):
        self.eh_md.append(b.md)
        self.eh_mu.append(b.mu)
        self.eh_mm.append(b.mm)

    def eh_del_clickable(self, b):
        if b.md in self.eh_md: self.eh_md.remove(b.md)
        if b.mu in self.eh_mu: self.eh_mu.remove(b.mu)
        if b.mm in self.eh_mm: self.eh_mm.remove(b.mm)

    def network_sink(self):
        # Network I/O is handled by the background NetworkThread; nothing to
        # do here.  PhaseServers overrides this to poll the metaserver.
        pass

    def display_sink_event(self, event):
        if event.type == NETWORK_DATA_READY:
            if not nt.connected:
                raise ServerDisconnectedError
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.md(event)
        elif event.type == pygame.KEYDOWN:
            self.kb(event)
        elif event.type == pygame.QUIT:
            nt.send(cp_bye.data())
            ac_save()
            # FIXME: exit main instead of calling sys.exit
            sys.exit(0)
        elif event.type == pygame.MOUSEMOTION:
            self.mm(event)
        elif event.type > pygame.USEREVENT:
            self.ue(event)
        elif event.type == pygame.MOUSEBUTTONUP:
            self.mu(event)
        elif event.type == pygame.VIDEOEXPOSE:
            pygame.display.flip()

    def display_sink(self):
        n = 0
        for event in pygame.event.get():
            self.display_sink_event(event)
            n += 1
        return n

    def display_sink_wait(self):
        self.display_sink()
        event = pygame.event.wait()
        self.display_sink_event(event)

    def ue(self, event):
        for eh in self.eh_ue:
            if eh(event): return True
        return False

    def ue_set(self, hz):
        self.ue_hz = hz
        self.ue_delay = 1000 // hz
        pygame.time.set_timer(UE_TIMER, self.ue_delay)

    def ue_clear(self):
        pygame.time.set_timer(UE_TIMER, 0)

    def mm(self, event):
        # FIXME: watch for MOUSEMOTION and update object information panes
        # for planets or ships (on tactical or galactic)
        for eh in self.eh_mm:
            if eh(event): return True
        return False

    def md(self, event):
        for eh in self.eh_md:
            if eh(event): return True
        return False

    def mu(self, event):
        for eh in self.eh_mu:
            if eh(event): return True
        return False

    def kb(self, event):
        if event.key == K_q or event.key == K_ESCAPE:
            self.quit(event)
        elif event.key == K_PRINT:
            self.snap(event)

    def exit(self, status):
        screen.fill((0, 0, 0))
        pygame.display.flip()
        if opt.debug:
            ic.statistics()
        pg_quit()
        # FIXME: exit main instead of calling sys.exit
        sys.exit(status)

    def quit(self, event):
        if nt.mode != None:
            nt.send(cp_quit.data())
            nt.has_quit = True
        else:
            self.exit(0)

    def snap(self, event):
        name = "gytha-%04d.jpeg" % self.screenshot
        try:
            pygame.image.save(screen, name)
            print("snapshot taken,", name)
            self.screenshot += 1
        except:
            pass

    def cycle(self):
        """ free-wheeling cycle; blocks in pygame.event.wait() until a
        network, display, or timer event arrives. """
        while self.run:
            self.display_sink_wait()

    def cycle_wait(self):
        """ display-waiting cycle for phases that use USEREVENT timers. """
        while self.run:
            self.display_sink_wait()

    def cycle_wait_display(self):
        """ display waiting cycle, use when local user event timers
        are needed, and no network events """
        while self.run:
            self.display_sink_wait()

class PhaseNonFlight(Phase):
    def __init__(self):
        Phase.__init__(self)
        self.buttons = pygame.sprite.OrderedUpdates(())
        self.warn_on = False
        self.warn_fuse = 0

    def background(self, name="invalid.png"):
        # centre a background image onto the screen
        screen.fill((0,0,0))
        if opt.no_backgrounds: return
        if r_main.width > 1024 or r_main.height > 1000:
            background = ic.get_scale2xed(name)
        else:
            background = ic.get(name)
        bh = background.get_height()
        bw = background.get_width()
        tr = background.get_rect(center=(r_main.centerx, r_main.centery))
        screen.blit(background, tr)

    def _place_top_left(self, rect, arg):
        return rect(left=1, top=1)

    def _place_top_right(self, rect, arg):
        return rect(right=r_main.right-1, top=1)

    def _place_bottom_right(self, rect, arg):
        return rect(right=r_main.right-1, bottom=r_main.bottom-1)

    def _place_bottom_left(self, rect, arg):
        return rect(left=r_main.left+1, bottom=r_main.bottom-1)

    def _add_button(self, button):
        button.draw()
        self.eh_add_clickable(button)
        self.buttons.add(button)

    def _del_button(self, button):
        button.clear()
        self.eh_del_clickable(button)
        self.buttons.remove(button)

    def add_quit_button(self, clicked, image='activity-stop.png',
                        placement=None):
        self.b_quit = IconTextButton(clicked, True, image,
                                     'QUIT', 18, (192, 192, 192),
                                     self._place_bottom_right, None)
        self._add_button(self.b_quit)

    def add_list_button(self, clicked, image='system-restart.png'):
        self.b_list = IconTextButton(clicked, False, image,
                                     'Server List', 18, (192, 192, 192),
                                     self._place_bottom_left, None)
        self._add_button(self.b_list)

    def add_tips_button(self, clicked):
        self.b_tips = IconTextButton(clicked, False, 'help.png',
                                     'Tips for Getting Started',
                                     18, (192, 192, 192),
                                     self.place_above_welcome, 10)
        self._add_button(self.b_tips)

    def add_join_button(self, clicked):
        self.b_join = IconTextButton(clicked, False, 'go-previous.png',
                                     'Play Again', 18, (192, 192, 192),
                                     self.place_above_blame, 20)
        self._add_button(self.b_join)
        # FIXME: show shortcut space bar

    def del_join_button(self):
        self._del_button(self.b_join)
        del self.b_join

    def text(self, text, x, y, size=72, colour=(255, 255, 255)):
        font = fc.get(FONT_SANS, size)
        ts = font.render(text, 1, colour)
        tr = ts.get_rect(center=(x, y))
        screen.blit(ts, tr)
        return tr

    def blame(self):
        text_a = "software by quozl@us.netrek.org and stephen@thorne.id.au"
        text_b = ""
        if not opt.no_backgrounds: text_b += "backgrounds by hubble, "
        text_b += "ships by pascal"
        tra = self.text(text_a, r_main.centerx, r_main.bottom-90, 16)
        trb = self.text(text_b, r_main.centerx, r_main.bottom-70, 16)
        self.blame_rect = pygame.Rect.union(tra, trb)

    def place_above_blame(self, rect, arg):
        return rect(centerx=self.blame_rect.centerx,
                    bottom=self.blame_rect.top-arg)

    def welcome(self, colour=(255, 255, 255)):
        font = fc.get(FONT_SANS, 15)
        x = r_main.centerx - 300
        y = int(r_main.bottom * 0.79)
        wr = None
        for line in WELCOME:
            ts = font.render(line, 1, colour)
            tr = ts.get_rect(left=x, top=y)
            y = tr.bottom
            screen.blit(ts, tr)
            if wr:
                wr = pygame.Rect.union(wr, tr)
            else:
                wr = tr
        self.welcome_rect = wr

    def place_above_welcome(self, rect, arg):
        return rect(centerx=self.welcome_rect.centerx,
                    bottom=self.welcome_rect.top-arg)

    def warn(self, message, ms=0):
        font = fc.get(FONT_SANS, 32)
        text = font.render(message, 1, (255, 127, 127))
        self.warn_br = text.get_rect(centerx=r_main.centerx,
                                     bottom=r_main.bottom)
        self.warn_bg = screen.subsurface(self.warn_br.clip(screen.get_rect())).copy()
        r1 = screen.blit(text, self.warn_br)
        pygame.display.update(r1)
        self.warn_on = True
        self.warn_fuse = ms // self.ue_delay

    def unwarn(self):
        if self.warn_on:
            r1 = screen.blit(self.warn_bg, self.warn_br)
            pygame.display.update(r1)
            self.warn_on = False

    def warn_ue(self):
        if self.warn_fuse > 0:
            self.warn_fuse = self.warn_fuse - 1
            if self.warn_fuse == 0:
                self.unwarn()

    def mm(self, event):
        for eh in self.eh_mm:
            if eh(event):
                r = []
                for s in self.buttons:
                    if s.update():
                        s.clear()
                        r.append(s.draw())
                if len(r):
                    pygame.display.update(r)
                return True
        return False

class PhaseSplash(PhaseNonFlight):
    """ splash screen, shows welcome for a short time, and the player
    is to either wait for the timer to expire, or click to cancel """
    def __init__(self, screen):
        PhaseNonFlight.__init__(self)
        self.background("hubble-helix.jpg")
        self.text("netrek", r_main.centerx, r_main.centery, 144)
        self.bouncer = Bouncer(200, 200, r_main.centerx, r_main.centery,
                               'torp-explode-20.png', 'torp-explode-20.png')
        self.welcome()
        self.add_quit_button(self.quit)
        if not opt.debug: ic.preload_scan()
        pygame.display.flip()
        if opt.screenshots:
            pygame.image.save(screen, "gytha-splash.jpeg")
        if not opt.debug: ic.preload_early()
        self.ue_set(100)
        self.fuse_max = self.fuse = opt.splashtime // self.ue_delay
        self.run = True
        self.cycle_wait_display() # returns after self.leave is called
        if not opt.debug: ic.preload_rest()
        self.ue_clear()

    def ue(self, event):
        self.fuse -= 1
        if self.fuse < 0:
            self.leave()
        else:
            self.bouncer.update(self.fuse, self.fuse_max)
        if not opt.debug: ic.preload_one()

    def md(self, event):
        if Phase.md(self, event): return
        self.leave()

    def kb(self, event):
        self.leave()

    def leave(self):
        self.b_quit.clear()
        pygame.display.flip()
        self.run = False

class PhaseTips(PhaseNonFlight):
    """ playing tips documentation screen, shows tips text, and the
    player is to click on the server list or quit button """
    def __init__(self, screen):
        PhaseNonFlight.__init__(self)
        self.background("hubble-helix.jpg")
        self.text('netrek', r_main.centerx, 100, 92)
        self.text('tips', r_main.centerx, 175, 64)
        self.draw_tips()
        self.add_quit_button(self.quit)
        self.add_list_button(self.list)
        pygame.display.flip()
        if opt.screenshots:
            pygame.image.save(screen, "gytha-tips.jpeg")
        self.run = True
        self.cycle_wait_display() # returns after self.leave is called

    def draw_tips(self):
        tips = [
    "1.  when you enter the game, press the number 4 to start moving, other",
    "numbers are slower or faster,",
    "",
    "2.  you are the ship in the centre of the screen,",
            # FIXME: but not if you are in galactic view
    "",
    "3.  use right-click on the mouse to steer toward a point in space, you",
    "will find it easier to turn at lower speeds,",
    "",
    "4.  use left-click on the mouse to fire a torpedo, they travel over time",
    "so you have to point ahead of your target, they hurt enemy ships but",
    "usually pass right through your team,",
    "",
    "5.  use middle-click on your mouse to fire a phaser, it is instant so",
    "point at your target, it works better the closer the enemy is,",
    "",
    "6.  the aim of the game is to capture planets, killing enemies is only a",
    "means to an end, and dying is a good thing, because you get a new ship,",
    "",
    "7.  but if someone kills you, they can begin to capture planets, so it",
    "is best to not die in vain,",
    "",
    "8.  people in your team will try to communicate so that you can all do",
    "things together, because when you cooperate better than the other team,",
    "you win,",
    "",
    "9.  you capture planets by getting a kill, picking up armies 'z', bombing",
    "the enemy planet 'b', then dropping the armies 'x' until it changes team.",
    "",
# (client does not yet support observing well)
#    "Observing is a good way to learn.  When you join as an observer, you",
#    "won't see much until you use 'l' (lower-case L) to lock on to a player.",
#    "Choose a good player and watch what they do.",
#    "",
    "For more information on Netrek, visit http://netrek.org/beginner",
]
        size = 20
        x = r_main.centerx - 380
        y = 260
        if r_main.height < 1000:
            size = 15
            x = r_main.centerx - 280
            y = 210
        if r_main.height < 601:
            size = 10
            x = r_main.centerx - 180
        font = fc.get(FONT_SANS, size)
        for line in tips:
            ts = font.render(line, 1, (255, 255, 255))
            tr = ts.get_rect(left=x, top=y)
            y = tr.bottom
            screen.blit(ts, tr)

    def list(self, event):
        self.leave()

    def leave(self):
        self.b_quit.clear()
        pygame.display.flip()
        self.run = False

class PhaseServers(PhaseNonFlight):
    """ metaserver list, a list of services is shown, the list is
    derived from the metaserver and multicast discovery, and the
    player is to either select one with mouse, wait for the list to
    update, or quit. """
    def __init__(self, screen, mc):
        self.cancelled = False
        PhaseNonFlight.__init__(self)
        self.screen = screen
        self.background("hubble-orion.jpg")
        x = r_main.centerx
        self.text('netrek', x, 100, 92)
        self.text('server list', x, 175, 64)
        self.welcome(colour=(128, 128, 128))
        self.add_quit_button(self.quit)
        self.add_tips_button(self.tips)
        self.instructions = None
        self.pinger = None
        pygame.display.flip()
        self.bouncer = Bouncer(225, 20, x, 240)
        self.dy = 40 # vertical spacing
        self.n = 0 # number of servers shown so far
        self.run = True
        self.mc = mc
        self.mc.uncork(self.update)
        self.timing = False
        self.sent = pygame.time.get_ticks()
        self.lag = 0
        self.ue_set(100)
        self.fuse_max = opt.metaserver_refresh_interval * 1000 // self.ue_delay
        self.fuse = self.fuse_max // 2
        self.warn('pick a server to connect to', 2500)
        self.cycle_wait() # returns after self.leave is called
        self.ue_clear()

    def server_icon(self):
        # IMAGERY: servers-icon.png
        return [ic.get('servers-icon.png'), None]

    def server_name(self, server):
        """ server name, shade by age """
        colour = 96
        age = server['age']
        if age < 3000: colour = 128
        if age < 300: colour = 192
        if age < 180: colour = 255
        colour = (colour, colour, colour)
        font = fc.get(FONT_SANS, 22)
        text = server['name'] + ' ' + server['comment']
        return [font.render(text, 1, colour), 40]

    def server_queue(self, server):
        font = fc.get(FONT_SANS, 22)
        text = 'Queue of ' + str(server['queue'])
        return [font.render(text, 1, (255, 64, 64)), r_main.centerx - 120]

    def server_players(self, server):
        s = []
        # per player icon
        gx = r_main.centerx - 55
        for x in range(min(server['players'], 16)):
            # per player icon
            # IMAGERY: servers-player.png
            s.append([ic.get('servers-player.png'), gx])
            # space them out for visual counting
            if (x % 4) == 3:
                gx = gx + 35
            else:
                gx = gx + 30
        return s

    def update(self, name):
        """ called by MetaClient for each server for which a packet is received
        """
        # FIXME: seen once, placement problem, a newly available
        # multicast server is placed at first position despite first
        # position being taken already by a metaserver entry.
        # FIXME: old multicast entries not expired when they leave.
        redraw = []
        # defer instructions until at least one server appears
        if not self.instructions and r_us.height > 600:
            self.instructions = Texts(INSTRUCTIONS_SERVERS,
                                      r_main.centerx - 300,
                                      r_main.height * 0.53, 8, 15,
                                      name=FONT_SANS)
            rs = self.instructions.draw()
            for r in rs:
                redraw.append(r)
        server = self.mc.servers[name]
        if self.timing and server['source'] == 'r':
            self.lag = pygame.time.get_ticks() - self.sent
            x = 'ping ' + str(self.lag) + ' ms'
            def place(rect, arg):
                x, y = arg
                return rect(centerx=x, centery=y)
            self.pinger = Text(x, place, (r_main.centerx, 240), 14, (255, 255, 255))
            redraw.append(self.pinger.draw())
            self.timing = False
        if 'y' not in server:
            y = 300 + self.dy * self.n
            self.n += 1
        else:
            y = server['y']
            button = server['button']
            redraw.append(button.clear())
            self.eh_del_clickable(button)
            self.buttons.remove(button)
        s = []
        s.append(self.server_icon())
        s.append(self.server_name(server))
        if server['queue'] > 0:
            s.append(self.server_queue(server))
        else:
            s += self.server_players(server)
        s.append([pygame.Surface((1, 1), pygame.SRCALPHA, 32), r_main.width-110])
        def place_y(rect, y):
            return rect(left=55, centery=y)
        button = HorizontalAssemblyButton(self.join, s, 0, place_y, y)
        button.buttons = [1, 2]
        self.buttons.add(button)
        self.eh_add_clickable(button)
        button.check_cursor_under()
        self.mc.servers[name]['y'] = y
        self.mc.servers[name]['button'] = button
        redraw.append(button.draw())
        pygame.display.update(redraw)

    def network_sink(self):
        """ Poll the metaserver socket (non-blocking); called from ue()
        at 100 Hz so responses appear promptly without blocking the loop. """
        self.mc.recv()

    def ue(self, event):
        self.warn_ue()
        self.bouncer.update(self.fuse, self.fuse_max)
        self.network_sink()  # non-blocking poll for metaserver replies

        self.fuse -= 1
        if self.fuse < 0:
            if self.pinger:
                pygame.display.update(self.pinger.clear())
                self.pinger = None
            self.sent = pygame.time.get_ticks()
            self.timing = True
            self.mc.query(opt.metaserver)
            self.fuse = self.fuse_max

    def md(self, event):
        if Phase.md(self, event): return
        self.unwarn()
        if event.button != 1 and event.button != 2:
            self.warn('not that button, mate', 500)
            return
        y = event.pos[1]
        if abs(self.bouncer.cy - y) < 50:
            self.warn('that is the metaserver query refresh timer, mate', 2000)
            return

    def join(self, event):
        self.unwarn()
        if event.button != 1 and event.button != 2:
            self.warn('not that button, mate', 500)
            return
        y = event.pos[1]
        distance = self.dy
        chosen = None
        for k, v in self.mc.servers.items():
            dy = abs(v['y'] - y)
            if dy < distance:
                distance = dy
                chosen = v['name']
        if chosen == None:
            self.warn('click on a server, mate', 1000)
            return
        if opt.screenshots:
            pygame.image.save(screen, "gytha-servers.jpeg")
        pygame.display.update(self.b_quit.clear())
        self.warn('connecting, standby')
        opt.chosen = chosen
        if event.button == 2:
            opt.name = 'guest'
            opt.mercenary = True
        # FIXME: do not block and hang during connect, do it asynchronously
        if not nt.connect(opt.chosen, opt.port):
            # FIXME: handle connection failure more gracefully by
            # explaining what went wrong, rather than be this obtuse
            self.unwarn()
            self.warn('connection failure', 2000)
            pygame.display.update(self.b_quit.draw())
            return
        nt_start_thread()
        self.leave()

    def tips(self, event):
        self.cancelled = True
        self.leave()

    def leave(self):
        pygame.display.update(self.b_tips.clear())
        pygame.display.update(self.b_quit.clear())
        self.run = False

class PhaseQueue(PhaseNonFlight):
    """ queue, the player is told their position in the queue, the
    position updates as other players leave, or our player may
    quit. """
    def __init__(self, screen):
        self.cancelled = False
        if me != None:
            return
        PhaseNonFlight.__init__(self)
        self.background("hubble-crab.jpg")
        x = r_main.centerx
        self.text('netrek', x, 100, 92)
        self.text(opt.chosen, x, 185, 64)
        self.blame()
        self.add_quit_button(self.quit)
        self.add_list_button(self.list)
        self.warn('connected, standby')
        pygame.display.flip()
        self.run = True
        if opt.screenshots:
            pygame.image.save(screen, "gytha-queue.jpeg")
        while self.run:
            self.display_sink_wait()
            self.data()

    def data(self):
        if me != None:
            self.proceed()
            return
        if galaxy.sp_queue_pos == None:
            return
        self.unwarn()
        self.warn('standby, you are at queue position ' +
                  str(galaxy.sp_queue_pos))
        pygame.display.flip()

    def list(self, event):
        self.cancelled = True
        nt.send(cp_bye.data())
        nt_shutdown()
        self.proceed()

    def quit(self, event):
        self.list(event)
        Phase.quit(self, event)

    def proceed(self):
        self.b_quit.clear()
        self.b_list.clear()
        self.run = False

class PhaseLogin(PhaseNonFlight):
    """ login, the server message of the day (MOTD) is displayed, and
    the player is to type a character name and password, the name may
    be guest, or the player may quit. """
    def __init__(self, screen):
        PhaseNonFlight.__init__(self)
        self.background("hubble-crab.jpg")
        x = r_main.centerx
        self.text('netrek', x, 100, 92)
        self.text(opt.chosen, x, 185, 64)
        self.blame()
        pygame.display.flip()
        self.add_quit_button(self.quit)
        self.add_list_button(self.list)
        self.unwarn()
        self.warn('connected, as slot %s, ready to login' % slot_decode(me.n))
        self.texts = Texts(galaxy.motd.get(), 100, 250, 24, 16)
        pygame.display.flip()
        self.name = Field("type a name ? ", "", x, r_main.height * 0.75)
        self.focused = self.name
        self.password = None
        self.run = True
        if opt.screenshots:
            pygame.image.save(screen, "gytha-login.jpeg")
        self.cancelled = False
        self.cycle() # returns when login is complete, or cancelled

    def tab(self):
        # FIXME: just press enter for guest
        """ move to next field """
        self.focused.leave()
        if self.focused == self.password:
            self.chuck_cp_login()
        elif self.focused == self.name:
            if self.password == None:
                self.password = Field("password ? ", "",
                                      r_main.centerx, r_main.height*0.8,
                                      echo=False)
                # FIXME: password prompt appears momentarily if guest selected
                # FIXME: #1187683521 force no echo for password
            else:
                self.password.enter()
            self.focused = self.password
            if self.name.value == 'guest' or self.name.value == 'Guest':
                self.password.leave()
                self.password.undraw()
                self.password.value = ''
                self.chuck_cp_login()
            else:
                self.chuck_cp_login_attempt()

    def chuck_cp_login_attempt(self):
        self.catch_sp_login_attempt()
        nt.send(cp_login.data(1, str(self.name.value),
                              str(self.password.value), 'gytha'))

    def throw_sp_login_attempt(self, accept, flags, keymap):
        if accept == 1:
            self.warn('server has this name listed')
        else:
            self.warn('server ignorant of this name')

    def catch_sp_login_attempt(self):
        global sp_login
        sp_login.catch(self.throw_sp_login_attempt)

    def chuck_cp_login(self):
        self.catch_sp_login()
        nt.send(cp_updates.data(1000000//opt.updates))
        nt.send(cp_login.data(0, str(self.name.value),
                              str(self.password.value), 'gytha'))

    def throw_sp_login(self, accept, flags, keymap):
        if accept == 1:
            self.proceed()
        else:
            self.warn('name and password refused by server')
            self.password.value = ''
            self.password.unhighlight()
            self.focused = self.name
            self.focused.enter()

    def catch_sp_login(self):
        global sp_login
        sp_login.catch(self.throw_sp_login)

    def untab(self):
        if self.focused == self.password:
            self.focused.leave()
            self.focused = self.name
            self.focused.redraw()

    def kb(self, event):
        self.unwarn()
        shift = event.mod & KMOD_SHIFT
        control = event.mod & KMOD_CTRL
        if event.key == K_LSHIFT or event.key == K_RSHIFT: pass
        elif event.key == K_LCTRL or event.key == K_RCTRL: pass
        elif event.key == K_d and control:
            self.list(event)
        elif event.key == K_w and control:
            self.focused.delete()
        elif event.key == K_TAB and shift:
            self.untab()
        elif event.key == K_TAB or event.key == K_RETURN:
            self.tab()
        elif event.key == K_BACKSPACE:
            self.focused.backspace()
        elif event.key > 31 and event.key < 255 and not control:
            self.focused.append(event.unicode)
        else:
            return Phase.kb(self, event)

    def list(self, event):
        self.cancelled = True
        nt.send(cp_bye.data())
        nt_shutdown()
        self.proceed()

    def quit(self, event):
        self.list(event)
        Phase.quit(self, event)

    def proceed(self):
        self.b_quit.clear()
        self.b_list.clear()
        self.run = False

class PhaseOutfit(PhaseNonFlight):
    """ team and ship selection, the available teams and ships are
    displayed, and the player may select one, or quit """
    # FIXME: automatic quit timeout display
    # FIXME: add a become observer button that disconnects, reconnects, using same login credentials
    # FIXME: add a become player button as above
    # FIXME: add a relinquish slot button, for rejoining end of queue
    # FIXME: add a BACK button that disconnects, reconnects, for login
    def display_sink_event(self, event):
        super().display_sink_event(event)
        if event.type > pygame.USEREVENT:
            pygame.display.flip()

    def __init__(self, screen):
        PhaseNonFlight.__init__(self)
        self.run = True
        self.box = None
        self.last_team = None
        self.last_ship = CRUISER
        self.cancelled = False
        self.visible = pygame.sprite.OrderedUpdates(())
        self.angle = 0
        self.screenshot = False
        self.tips = None
        self.add_quit_button(self.quit)
        if not opt.server:
            self.add_list_button(self.list)

    def do(self):
        """ unlike the earlier display phases, this one exists for the
        duration of the session on a server, so the initialisation is
        split between first off (above) and per refit (below). """
        self.run = True
        self.background("hubble-spire.jpg")
        x = r_main.centerx
        self.text('netrek', x, 100, 92)
        self.text(opt.chosen, x, 185, 64)
        self.text('ship and race', x, 255, 64)
        self.blame()
        self.b_quit.draw()
        if not opt.server:
            self.b_list.draw()
        self.join_enabled = (self.last_team != None and not nt.has_quit)
        if self.join_enabled:
            # offer rejoin if a team was previously selected and
            # player did not quit
            self.add_join_button(self.join)
        pygame.display.flip()
        box_l = int(r_main.width * 0.212)
        box_t = 300
        box_r = r_main.width - box_l
        box_b = r_main.height - 250
        sx = (box_r - box_l) / 8
        sy = (box_b - box_t) / 8
        r = []
        self.sprites = []
        # FIXME: display number of players on each team
        # FIXME: make these sprites rather than paint on screen
        table = [[FED, -1, +1], [ROM, -1, -1], [KLI, +1, -1], [ORI, +1, +1]]
        for row in table:
            (team, dx, dy) = row
            # box centre
            # FIXME: slide ships into race on race positions, omitting other races
            x = (box_r - box_l) // 2 + box_l
            y = (box_b - box_t) // 2 + box_t
            permit = [CRUISER, ASSAULT, SCOUT, BATTLESHIP, DESTROYER, STARBASE]
            if rounds < 50: permit = permit[:-1]
            if rounds < 20: permit = [CRUISER, ASSAULT, SCOUT]
            if rounds < 10: permit = [CRUISER]
            for ship in permit:
                x = x + dx * sx
                y = y + dy * sy
                # IMAGERY: ???-??.png
                def place_xy(rect, arg):
                    (x, y) = arg
                    return rect(centerx=x, centery=y)
                sprite = IconButton(self.pick, teams[team]+'-'+ships[ship]+'.png', place_xy, (x, y))
                sprite.description = teams_long[team] + ' ' + ships_long[ship] + ', ' + ships_use[ship]
                sprite.x = x
                sprite.y = y
                sprite.ship = ship
                sprite.team = team
                sprite.visible = False
                sprite.suck()
                self.sprites.append(sprite)
        # FIXME: add minature galactic, showing ownership, player
        # positions if any, with ships to choose in each race space or
        # just outside the corner.
        # FIXME: display "in bronco you should remain with your team"
        # FIXME: show logged in players
        # FIXME: show planet status
        # FIXME: show whydead
        if not nt.has_quit:
            self.warn("pick a ship")
        pygame.display.flip()
        sp_mask.catch(self.mask)
        pygame.display.flip()
        self.ue_set(10)
        self.cycle() # returns when choice accepted by server, or user cancels
        self.ue_clear()
        sp_mask.uncatch()
        if self.join_enabled:
            self.del_join_button()
        for sprite in self.sprites:
            if sprite.visible:
                self.visible.remove(sprite)
                self._del_button(sprite)
                r.append(sprite.clear())
                sprite.visible = False

    def mask(self, mask):
        r = []
        for sprite in self.sprites:
            if mask & sprite.team:
                if not sprite.visible:
                    self.visible.add(sprite)
                    self._add_button(sprite)
                    r.append(sprite.blit())
                    sprite.visible = True
            else:
                if sprite.visible:
                    self.visible.remove(sprite)
                    self._del_button(sprite)
                    r.append(sprite.clear())
                    sprite.visible = False
        if len(r) > 0:
            pygame.display.update(r)
            if opt.screenshots:
                if not self.screenshot:
                    pygame.image.save(screen, "gytha-outfit.jpeg")
                    self.screenshot = True
        if mask != 0 and opt.mercenary:
            opt.team = teams[mercenary.pick(mask, galaxy)]
            opt.ship = "cruiser"
            opt.mercenary = False
        self.auto()

    def auto(self):
        # attempt auto-refit if command line arguments are supplied
        if opt.team != None and opt.ship != None:
            while me is None:
                time.sleep(0.01)  # network thread updates me
            for team, name in teams_long.items():
                if opt.team == name[:len(opt.team)]:
                    opt.team = None
                    for ship, name in ships.items():
                        if opt.ship == name[:len(opt.ship)]:
                            self.team(teams_numeric[team], ship)
                            return
                    for ship, name in ships_long.items():
                        if opt.ship == name[:len(opt.ship)]:
                            self.team(teams_numeric[team], ship)
                            return
                    break

    def team(self, team, ship):
        self.last_team = team
        self.last_ship = ship
        sp_pickok.catch(self.sp_pickok)
        nt.send(cp_outfit.data(team, ship))

    def sp_pickok(self, state):
        global rounds

        if state == 1:
            self.run = False
            rounds += 1
            return

        self.unwarn()

        if 'You need a rank' in sp_warning.text:
            self.warn('you lack rank to fly that ship')
            self.last_team = None
            return

        if 'Please confirm change of teams' in sp_warning.text:
            self.warn('changing team may insult, click again?')
            return

        self.warn('outfit request refused by server')

    def nearest(self, pos):
        (x, y) = pos
        nearest = None
        minimum = 70**2
        for sprite in self.sprites:
            if not sprite.visible: continue
            distance = (sprite.x - x)**2 + (sprite.y - y)**2
            if distance < minimum:
                nearest = sprite
                minimum = distance
        return nearest

    def pick(self, event):
        self.unwarn()
        nearest = self.nearest(event.pos)
        if nearest != None:
            self.team(teams_numeric[nearest.team], nearest.ship)
        # FIXME: click on team icon sends CP_OUTFIT most recent ship
        # FIXME: click on ship icon requests CP_OUTFIT with team and ship

    def mm(self, event):
        PhaseNonFlight.mm(self, event)
        nearest = self.nearest(event.pos)
        if nearest != self.box:
            self.unwarn()
            if nearest != None:
                self.warn(nearest.description)
            self.box = nearest

    def kb(self, event):
        self.unwarn()
        shift = event.mod & KMOD_SHIFT
        control = event.mod & KMOD_CTRL
        if event.key == K_LSHIFT or event.key == K_RSHIFT: pass
        elif event.key == K_LCTRL or event.key == K_RCTRL: pass
        elif event.key == K_d and control:
            self.list(event)
        elif event.key == K_SPACE or event.key == K_RETURN:
            self.join(event)
        elif event.key == K_f: self.team(0, self.last_ship)
        elif event.key == K_r: self.team(1, self.last_ship)
        elif event.key == K_k: self.team(2, self.last_ship)
        elif event.key == K_o: self.team(3, self.last_ship)
        else:
            return Phase.kb(self, event)

    def join(self, event):
        if self.last_team != None:
            self.team(self.last_team, self.last_ship)

    def list(self, event):
        nt.send(cp_bye.data())
        nt_shutdown()
        self.cancelled = True
        self.proceed()

    def quit(self, event):
        nt.send(cp_bye.data())
        nt_shutdown()
        self.exit(0)

    def proceed(self):
        self.b_quit.clear()
        if not opt.server:
            self.b_list.clear()
        self.run = False


class PhaseFlight(Phase):
    def __init__(self, name):
        Phase.__init__(self)
        self.run = True
        self.name = name
        self.set_keys()
        self.eh_ue.append(b_warning_sprite.ue)
        self.modal_handler = None
        self.event_triggers_update = False
        self.eh_md.append(self.md_us)
        self.op_warp_count = 0
        self.op_turn_count = 0
        self.hinted = False

    def cycle(self):
        """ main in-flight event loop, returns when no longer flying """
        # at least one initial screen update is required to form the
        # playing field
        self.update()
        galaxy.frames += 1
        # loop until termination requested, or no longer flying
        while self.run:
            # Block until any event arrives: NETWORK_DATA_READY (posted by
            # the network thread), USEREVENT timer, or a UI event.
            event = pygame.event.wait()
            self.display_sink_event(event)
            # drain any additional queued events without blocking
            n = self.display_sink()
            if n > 0:
                galaxy.events += 1
                if self.event_triggers_update:
                    self.update()
                    self.event_triggers_update = False
            # if a server update cycle completed, redraw
            if galaxy.paced:
                self.update()
                galaxy.paced = False
                galaxy.frames += 1
            if me.status == POUTFIT: break # no longer flying

    def update(self):
        raise NotImplemented

    def md_us(self, event):
        """ tactical window mouse button down event handler
        """
        if not r_us.collidepoint(event.pos):
            return False # event not handled

        if not me: return True # event handled
        (x, y) = event.pos
        if event.button == 3:
            nt.send(cp_direction.data(s2d(me, x, y)))
            if ph_flight == ph_tactical:
                self.op_turn_count += 1
                if self.op_turn_count == 15:
                    ac_done('Turning')
                else:
                    # first turning after green alert shows pending achievements
                    ac_deliver()
        elif event.button == 2:
            nt.send(cp_phaser.data(s2d(me, x, y)))
        elif event.button == 1:
            nt.send(cp_torp.data(s2d(me, x, y)))
        return True

    def is_control(self, event):
        return event.mod & KMOD_CTRL

    def is_shift(self, event):
        return event.mod & KMOD_SHIFT

    def is_escape(self, event):
        return (event.key == K_ESCAPE or
                (event.key == K_LEFTBRACKET and
                self.is_control(event)))

    def kb(self, event):

        # ignore the shift and control keys on their own
        if event.key == K_LSHIFT or event.key == K_RSHIFT: return
        if event.key == K_LCTRL or event.key == K_RCTRL: return

        # check for control key sequences pressed
        if (self.is_control(event)):
            if event.key in self.keys_control:
                (handler, argument) = self.keys_control[event.key][:2]
                handler(event, argument)
                return

        # check for message entry mode
        if self.modal_handler is not None:
            self.modal_handler(event)
            return

        # check for shift key sequences pressed
        if (self.is_shift(event)):
            if event.key in self.keys_shift:
                (handler, argument) = self.keys_shift[event.key][:2]
                handler(event, argument)
                return

        # check for normal keys pressed
        if event.key in self.keys_normal:
            (handler, argument) = self.keys_normal[event.key][:2]
            handler(event, argument)
            return

        return Phase.kb(self, event)

    def set_keys(self):
        """ define dictionaries to map keys to operations """
        self.keys_normal = {
            K_0: (self.op_warp, 0, 'engine stop'),
            K_1: (self.op_warp, 1),
            K_2: (self.op_warp, 2),
            K_3: (self.op_warp, 3),
            K_4: (self.op_warp, 4, 'cruise'),
            K_5: (self.op_warp, 5),
            K_6: (self.op_warp, 6),
            K_7: (self.op_warp, 7),
            K_8: (self.op_warp, 8),
            K_9: (self.op_warp, 9),
            K_SEMICOLON: (self.op_planet_lock, None, 'lock on planet'),
            K_b: (self.op_bomb, None, 'start bombing'),
            K_c: (self.op_cloak_toggle, None, 'cloak (on/off)'),
            K_d: (self.op_det, None, 'detonate nearby enemy torps'),
            K_e: (self.op_docking_toggle, None),
            K_f: (self.op_plasma, None),
            K_h: (self.op_help, None, 'help'),
            K_i: (self.op_info, None, 'show info about object'),
            K_k: (self.op_course, None),
            K_l: (self.op_player_lock, None, 'lock on player'),
            K_m: (self.op_message, None, 'compose a message'),
            K_o: (self.op_orbit, None, 'orbit planet'),
            K_p: (self.op_phaser, None),
            K_r: (self.op_refit, None, 'refit'),
            K_s: (self.op_shield_toggle, None, 'shields (on/off)'),
            K_t: (self.op_torp, None),
            K_u: (self.op_shield_toggle, None),
            K_x: (self.op_beam_down, None, 'beam down'),
            K_y: (self.op_pressor_toggle, None, 'pressor'),
            K_z: (self.op_beam_up, None, 'beam up'),
            K_BACKSPACE: (self.op_dismiss, None),
            K_ESCAPE: (self.op_dismiss, None),
            }
        self.keys_control = {
            K_HASH: (self.op_distress, rcd.dist_type_other2),
            K_0: (self.op_distress, rcd.dist_type_pop),
            K_1: (self.op_distress, rcd.dist_type_save_planet),
            K_2: (self.op_distress, rcd.dist_type_base_ogg),
            K_3: (self.op_distress, rcd.dist_type_help1),
            K_4: (self.op_distress, rcd.dist_type_help2),
            K_5: (self.op_distress, rcd.dist_type_asw),
            K_6: (self.op_distress, rcd.dist_type_asbomb),
            K_7: (self.op_distress, rcd.dist_type_doing1),
            K_8: (self.op_distress, rcd.dist_type_doing2),
            K_9: (self.op_distress, rcd.dist_type_pickup),
            K_AT: (self.op_distress, rcd.dist_type_other1),
            K_b: (self.op_distress, rcd.dist_type_bomb),
            K_c: (self.op_distress, rcd.dist_type_space_control),
            K_e: (self.op_distress, rcd.dist_type_escorting,
                  'signal taker you are escort'),
            K_f: (self.op_distress, rcd.dist_type_free_beer),
            K_h: (self.op_distress, rcd.dist_type_crippled),
            K_l: (self.op_distress, rcd.dist_type_controlling),
            K_m: (self.op_distress, rcd.dist_type_bombing),
            K_n: (self.op_distress, rcd.dist_type_no_gas),
            K_o: (self.op_distress, rcd.dist_type_ogg),
            K_p: (self.op_distress, rcd.dist_type_ogging),
            K_t: (self.op_distress, rcd.dist_type_take,
                  'signal team you are taker'),
            K_LEFTBRACKET: (self.op_dismiss, None),
            }
        self.keys_shift = {
            K_COMMA: (self.op_warp_down, None),
            K_PERIOD: (self.op_warp_up, None),
            K_0: (self.op_warp, 10),
            K_1: (self.op_warp, 11),
            K_2: (self.op_warp, 12, 'max warp'),
            K_3: (self.op_warp_half, None),
            K_4: (self.op_null, None),
            K_5: (self.op_warp_full, None),
            K_6: (self.op_null, None),
            K_7: (self.op_null, None),
            K_8: (self.op_practice, None),
            K_9: (self.op_warp, 10),
            K_c: (self.op_snap, None),
            K_a: (self.op_achievements, None, 'show achievements'),
            K_d: (self.op_det_me, None, 'cancel my torps'),
            K_e: (self.op_distress, rcd.dist_type_generic, 'emergency'),
            K_f: (self.op_distress, rcd.dist_type_carrying, 'carrying'),
            K_h: (self.op_help_keyboard, None),
            K_r: (self.op_repair, None, 'repair (on/off)'),
            K_t: (self.op_tractor_toggle, None, 'tractor (on/off)'),
            K_z: (self.op_debug_dump, None),
            }

    def op_null(self, event, arg):
        pass

    def op_beam_down(self, event, arg):
        nt.send(cp_beam.data(2))
        if me.flags & PFORBIT:
            if me.pl_orbit == -1:
                ac_done('Drop')
            else:
                planet = galaxy.planet(me.pl_orbit)
                if planet.owner != me.team:
                    ac_done('Drop')
                    if planet.flags & PLAGRI:
                        ac_done('Drop on Agricultural')
                    if planet.flags & PLHOME:
                        ac_done('Drop on Enemy Homeworld')

    def op_beam_up(self, event, arg):
        nt.send(cp_beam.data(1))

    def op_bomb(self, event, arg):
        nt.send(cp_bomb.data())

    def op_cloak_toggle(self, event, arg):
        if not me: return
        if me.flags & PFCLOAK:
            nt.send(cp_cloak.data(0))
            if me.speed > 0:
                ac_done('Cloaked Flight')
        else:
            nt.send(cp_cloak.data(1))

    def op_course(self, event, arg):
        (x, y) = pygame.mouse.get_pos()
        nt.send(cp_direction.data(s2d(me, x, y)))

    def op_det(self, event, arg):
        nt.send(cp_det_torps.data())
        if me.flags & PFRED:
            if (me.speed > 1) and (me.speed < 6):
                ac_done('Detonate')

    def op_det_me(self, event, arg):
        if not me: return
        base = me.n * MAXTORP
        for x in range(base, base + MAXTORP):
            torp = galaxy.torp(x)
            if torp.status == TMOVE or torp.status == TSTRAIGHT:
                nt.send(cp_det_mytorp.data(x))

    def op_distress(self, event, arg):
        if not me: return
        mesg = rcd.pack(arg, cursor(me), me, galaxy)
        if mesg:
            nt.send(cp_message.data(MDISTR | MTEAM, me.team, mesg))
            if arg == rcd.dist_type_take:
                if me.armies > 0:
                    ac_done('Calling a Take')
            if arg == rcd.dist_type_escorting:
                if me.armies == 0:
                    ac_done('Calling Escort')

    def op_docking_toggle(self, event, arg):
        if not me: return
        if me.flags & PFDOCKOK:
            nt.send(cp_dockperm.data(0))
        else:
            nt.send(cp_dockperm.data(1))

    def op_achievements(self, event, arg):
        ac_progress()

    def op_info(self, event, arg):
        b_info.empty()

        thing = galaxy.closest_thing(cursor(me))
        InfoSprite(thing.op_info(), track=thing)
        ac_done_later('Using Information')

    def op_help(self, event, arg):
        b_info.empty()

        tips = [
            "Netrek Help",
            "",
            "Press a number to set engine speed,",
            "",
            "You are the ship in the centre of the screen,",
            # FIXME: but not if you are in galactic view
            "",
            "Right-click to steer,",
            "",
            "Left-click to fire torpedo, point ahead of target,",
            "",
            "Middle-click to fire phaser, point at target,",
            "",
            "To orbit a planet point at it and press ' ; ',",
            "",
            "Killing enemy ships only moves them home,",
            "",
            "People in your team will try to communicate, please listen,",
            "",
            "Capture planets by getting a kill,",
            "   ... pick up armies from your planet with ' z ',",
            "   ... bomb the enemy planet with ' b ',",
            "   ... beam down the armies with ' x ',",
            "   ... repeat until it changes team.",
            "",
            "If someone kills you, they can begin to capture your planets,",
            "so come straight back in and defend!",
            "",
            "Press shift H for keyboard help, or ESC to clear"]

        InfoSprite(tips, expires=10+len(tips)*2)
        ac_done_later('Using Help')

    def op_help_keyboard(self, event, arg):
        b_info.empty()

        tips = ['Netrek Keyboard Help', '']
        gap = '  '
        for key, key_tuple in self.keys_normal.items():
            if len(key_tuple) < 3: continue
            name = pygame.key.name(key)
            tips.append(name + gap + key_tuple[2])
        for key, key_tuple in self.keys_shift.items():
            if len(key_tuple) < 3: continue
            name = 'shift ' + pygame.key.name(key).upper()
            tips.append(name + gap + key_tuple[2])
        for key, key_tuple in self.keys_control.items():
            if len(key_tuple) < 3: continue
            name = 'control ' + pygame.key.name(key)
            tips.append(name + gap + key_tuple[2])
        # FIXME: sort these in a fashion that leads to learning
        # rather than the default order in the table
        tips.append('enter' + gap + 'switch view')
        tips.append('')
        tips.append('Press ESC to clear keyboard help.')

        InfoSprite(tips, expires=20+len(tips))
        ac_done_later('Using Keyboard Help')

    def op_dismiss(self, event, arg):
        b_info.empty()
        ac_deliver()

    def op_orbit(self, event, arg):
        nt.send(cp_orbit.data(1))
        if (me.flags & PFRED) and (me.speed == 2) and \
               (me.flags & PFCLOAK) and not (me.flags & PFPLLOCK):
            nearest = galaxy.closest_planet((me.x, me.y))
            distance = n_d((me.x, me.y), (nearest.x, nearest.y))
            if distance < 900:
                ac_done('Planet Hook')
                # ignores possibility of tractor or pressor

    def op_phaser(self, event, arg):
        (x, y) = pygame.mouse.get_pos()
        nt.send(cp_phaser.data(s2d(me, x, y)))

    def op_planet_lock(self, event, arg):
        nearest = galaxy.closest_planet(cursor(me))
        if nearest != me:
            nt.send(cp_planlock.data(nearest.n))
            me.planet = nearest
            if me.speed > 3:
                ac_done('Planet Lock')

    def op_plasma(self, event, arg):
        (x, y) = pygame.mouse.get_pos()
        nt.send(cp_plasma.data(s2d(me, x, y)))

    def op_player_lock(self, event, arg):
        nearest = galaxy.closest_ship(cursor(me))
        if nearest != me:
            nt.send(cp_playlock.data(nearest.n))

    def op_practice(self, event, arg):
        nt.send(cp_practr.data())

    def op_pressor_toggle(self, event, arg):
        if not me: return
        nearest = galaxy.closest_ship(cursor(me))
        if nearest != me:
            if me.flags & PFPRESS:
                nt.send(cp_repress.data(0, nearest.n))
            else:
                nt.send(cp_repress.data(1, nearest.n))

    def op_repair(self, event, arg):
        if not me: return
        nt.send(cp_repair.data(1))

    def op_shield_toggle(self, event, arg):
        if not me: return
        if me.flags & PFSHIELD:
            ac_done('Shields Lowered')
            nt.send(cp_shield.data(0))
        else:
            nt.send(cp_shield.data(1))

    def op_torp(self, event, arg):
        (x, y) = pygame.mouse.get_pos()
        nt.send(cp_torp.data(s2d(me, x, y)))

# FIXME: adopt netrek-client-cow tractor off, and reapply keys, $ (all
# off) _ (tractor off and reapply), ^ (pressor off and reapply)
    def op_tractor_toggle(self, event, arg):
        if not me: return
        nearest = galaxy.closest_ship(cursor(me))
        if nearest != me:
            if me.flags & PFTRACT:
                nt.send(cp_tractor.data(0, nearest.n))
            else:
                nt.send(cp_tractor.data(1, nearest.n))

    def op_warp(self, event, arg):
        nt.send(cp_speed.data(arg))
        self.hint_dismiss()
        self.op_warp_count += 1
        if self.op_warp_count == 6:
            ac_done('Moving')

    def op_warp_half(self, event, arg):
        if me: self.op_warp(event, me.cap.s_maxspeed // 2)

    def op_warp_full(self, event, arg):
        if me: self.op_warp(event, me.cap.s_maxspeed)

    def op_warp_down(self, event, arg):
        if me: self.op_warp(event, me.speed - 1)

    def op_warp_up(self, event, arg):
        if me: self.op_warp(event, me.speed + 1)

    def op_message(self, event, arg):
        if me:
            galaxy.message.start()
            self.modal_handler = self.op_message_target
            self.event_triggers_update = True

    def op_message_target(self, event):
        self.event_triggers_update = True
        if self.is_escape(event) or \
               event.key == K_BACKSPACE or \
               event.key == K_m:
            galaxy.message.abort()
            self.modal_handler = None
            return
        if galaxy.message.target(event):
            self.modal_handler = self.op_message_typing

    def op_message_typing(self, event):
        self.event_triggers_update = True
        if self.is_escape(event):
            galaxy.message.abort()
            self.modal_handler = None
            return
        if event.key == K_BACKSPACE:
            if galaxy.message.is_empty():
                galaxy.message.retarget()
                self.modal_handler = self.op_message_target
                return
            galaxy.message.backspace()
            return
        if event.key == K_RETURN:
            galaxy.message.send()
            self.modal_handler = None
            return
        galaxy.message.typing(event)
        # FIXME: message history, up & down arrow recall

    def op_snap(self, event, arg):
        self.snap(event)

    def op_refit(self, event, arg):
        if me:
            self.modal_handler = self.op_refit_next
            self.event_triggers_update = True
            sp_warning.synthetic('Scout, Destroyer, Cruiser, '
                                 'Battleship, Assault, Outpost?')

    def op_refit_next(self, event):
        key = pygame.key.name(event.key)
        if key in ship_keys:
            nt.send(cp_refit.data(ship_keys[key]))
        self.modal_handler = None

    def tips(self):
        tips = galaxy.motd.tips()
        if not tips:
            ac_deliver()
            return

        b_info.empty()
        tips.append('')
        tips.append('Press ESC to clear tips.')
        InfoSprite(tips, expires=10+len(tips))

    def hint(self):
        if self.hinted:
            return False

        tips = ['Press h for help']
        InfoSprite(tips, expires=300, track=Tag((me.x, me.y + 3000)))
        self.hinted = True
        return True

    def hint_dismiss(self):
        b_info.empty()

    def op_debug_dump(self, event, arg):
        print(galaxy)


class PhaseFlightGalactic(PhaseFlight):
    def __init__(self):
        PhaseFlight.__init__(self, 'galactic')
        self.alerts = GalacticAlerts()

    def do(self):
        self.run = True
        screen.set_clip(r_us) # restrict drawing
        screen.blit(background, (0, 0))
        # draw static background, team borders and team names
        r = []
        xc, yc = n2gs(GWIDTH/2, GWIDTH/2)
        x1, y1 = n2gs(0, 0)
        x2, y2 = n2gs(GWIDTH, GWIDTH)
        r += [pygame.draw.line(screen, (96, 96, 96), (xc, y1), (xc, y2))]
        r += [pygame.draw.line(screen, (96, 96, 96), (x1, yc), (x2, yc))]
        t = (galaxy.tournament_teams & 0xf) | (galaxy.tournament_teams >> 4)
        if t == 0:
            t = ALL_TEAMS

        if r_us.width == 1000 and r_us.height == 1000:

            if t & ROM:
                ts = ic.get('team-box-rom.png')
                tr = ts.get_rect(left=x1, top=y1)
                screen.blit(ts, tr)
                r += [tr]

            if t & FED:
                ts = ic.get('team-box-fed.png')
                tr = ts.get_rect(left=x1, bottom=y2)
                screen.blit(ts, tr)
                r += [tr]

            if t & ORI:
                ts = ic.get('team-box-ori.png')
                tr = ts.get_rect(right=x2, bottom=y2)
                screen.blit(ts, tr)
                r += [tr]

            if t & KLI:
                ts = ic.get('team-box-kli.png')
                tr = ts.get_rect(right=x2, top=y1)
                screen.blit(ts, tr)
                r += [tr]

        size = 24
        font = fc.get(FONT_SANS, size)

        ts = font.render('Romulan', 1, (255, 64, 64))
        tr = ts.get_rect(left=x1+2, top=y1+2)
        screen.blit(ts, tr)
        r += [tr]

        ts = font.render('Federation', 1, (255, 255, 64))
        tr = ts.get_rect(left=x1+2, bottom=y2-2)
        screen.blit(ts, tr)
        r += [tr]

        ts = font.render('Orion', 1, (64, 255, 255))
        tr = ts.get_rect(right=x2-2, bottom=y2-2)
        screen.blit(ts, tr)
        r += [tr]

        ts = font.render('Klingon', 1, (64, 255, 64))
        tr = ts.get_rect(right=x2-2, top=y1+2)
        screen.blit(ts, tr)
        r += [tr]

        # FIXME: galactic to be centered on main screen for
        # --width=800 --height=600 --no-fullscreen

        pygame.display.update(r)
        self.bg = screen.copy()
        screen.set_clip(r_main)
        self.cycle()

    def kb(self, event):
        global ph_flight
        if (event.key == K_RETURN or event.key == K_TAB) and self.modal_handler is None:
            ph_flight = ph_tactical
            coords.is_galactic = False
            self.run = False
            ac_done('Using the Galactic Map')
        else:
            return PhaseFlight.kb(self, event)

    def update(self):
        t0 = time.time()
        screen.set_clip(r_us) # restrict drawing
        r = [] # sequence of dirty rectangles for update
        r += self.alerts.undraw((0,0,0))
        b_info.clear(screen, self.bg)
        b_warning.clear(screen, self.bg)
        b_reports.clear(screen, self.bg)
        g_players.clear(screen, self.bg)
        g_planets.clear(screen, self.bg)
        g_locator.clear(screen, self.bg)

        g_locator.update()
        g_planets.update()
        g_players.update()
        b_warning.update()
        b_reports.update()
        b_info.update()

        r += g_locator.draw(screen)
        r += g_planets.draw(screen)
        r += g_players.draw(screen)
        r += b_reports.draw(screen)
        r += b_warning.draw(screen)
        r += self.alerts.draw()
        r += b_info.draw(screen)
        pygame.display.update(r)
        screen.set_clip(r_main)
        t1 = time.time()
        galaxy.rps = int ( 1 / ( t1 - t0 ) )

class PhaseFlightTactical(PhaseFlight):
    def __init__(self):
        PhaseFlight.__init__(self, 'tactical')
        self.borders = Borders()
        self.alerts = TacticalAlerts()
        self.subgalactic = Subgalactic()
        self.halos = Halos()

        self.co = (0, 0, 0)
        self.bg = screen.copy()
        self.bg.fill(self.co)

        self.pace = 0

    def do(self):
        global background

        self.saved_background = background
        self.run = True
        screen.blit(self.bg, (0, 0))
        self.cycle()
        background = self.saved_background

    def kb(self, event):
        global ph_flight
        if (event.key == K_RETURN or event.key == K_TAB) and self.modal_handler is None:
            ph_flight = ph_galactic
            coords.is_galactic = True
            self.run = False
        else:
            return PhaseFlight.kb(self, event)

    # FIXME: console in a corner
    # FIXME: action menu items around edge
    # FIXME: menu item "?" or mouse-over, to do modal information
    # query on a screen object.

    def extra(self):
        """ some extra graphics bits, where we tune automatically how
        much extra graphics are done according to the measured
        performance of the essential graphics, ... otherwise once we
        fall behind in graphics update the network packet will be
        already waiting, and we shall begin to display-lag.  """

        # if we are incapable of a greater local frame rate than the
        # server is configured to send us updates for, defer one in
        # ten of these extra graphics updates
        if galaxy.rps < galaxy.ups:
            self.pace += 1
            if self.pace < 10: return []
            self.pace = 0

        # update halos
        r = []
        self.halos.undraw(screen, self.co)
        r += self.halos.undraw(self.bg, self.co)
        self.halos.draw(screen)
        r += self.halos.draw(self.bg)
        return r

    def update(self):
        """ clear, update, and redraw all tactical sprites and non-sprites """

        t0 = time.time()
        screen.set_clip(r_us) # restrict drawing
        r = [] # sequence of dirty rectangles for update
        b_info.clear(screen, self.bg)
        b_message.clear(screen, self.bg)
        b_warning.clear(screen, self.bg)
        b_reports.clear(screen, self.bg)
        r += self.alerts.undraw(self.co)
        r += self.borders.undraw(self.co)
        r += galaxy.phasers_undraw(self.co)
        t_torps.clear(screen, self.bg)
        t_plasma.clear(screen, self.bg)
        t_players.clear(screen, self.bg)
        r += galaxy.tractors_undraw(self.co)
        t_planets.clear(screen, self.bg)
        r += self.subgalactic.undraw(self.co)

        # design note, the sprite clear method does not return a dirty
        # rectangle, because it is merged with the dirty rectangle
        # returned by the sprite draw method, per group class
        # RenderUpdates, which is a subclass of the group class
        # OrderedUpdates that we use here.

        r += self.extra()
        t_planets.update()
        t_players.update()
        t_plasma.update()
        t_torps.update()
        b_warning.update()
        b_reports.update()
        b_message.update()
        b_info.update()

        r += self.subgalactic.draw()
        r += t_planets.draw(screen)
        r += galaxy.tractors_draw()
        r += t_players.draw(screen)
        r += t_plasma.draw(screen)
        r += t_torps.draw(screen)
        r += galaxy.phasers_draw()
        r += self.borders.draw()
        r += self.alerts.draw()
        r += b_reports.draw(screen)
        r += b_warning.draw(screen)
        r += b_message.draw(screen)
        r += b_info.draw(screen)

        pygame.display.update(r)
        screen.set_clip(r_main)
        t1 = time.time()
        galaxy.rps = int ( 1 / ( t1 - t0 ) )

        #r_debug = galaxy.torp_debug_draw()
        #pygame.display.update(r_debug)
        #r_debug = galaxy.ship_debug_draw()
        #pygame.display.update(r_debug)

class PhaseDisconnected(PhaseNonFlight):
    def display_sink_event(self, event):
        if event.type == NETWORK_DATA_READY:
            return
        super().display_sink_event(event)

    def __init__(self, screen):
        PhaseNonFlight.__init__(self)
        self.background("hubble-helix.jpg")
        x = r_main.centerx
        self.text('netrek', x, 100, 92)
        self.text(opt.chosen, x, 185, 64)
        self.text('disconnected', x, 255, 64)
        y = 455
        size = 12
        if r_main.width < 801:
            size = 10
            y = 350
        self.texts = Texts(self.diagnosis(), 50, y, size, 18)
        self.add_quit_button(self.quit)
        if not opt.server:
            self.add_list_button(self.list)
        pygame.display.flip()
        self.run = True
        self.cycle()
        # FIXME: show last few lines of message log
        # FIXME: if freed by captain in clue game from player slot
        # automatically return as an observer slot
        # FIXME: offer rejoin as player and rejoin as observer buttons

    def diagnosis(self):
        if sp_badversion.why == None:
            return ['Connection was closed by the server.',
                    '',
                    'You may have been idle for too int.',
                    'You may have a network problem.',
                    'You may have been ejected by vote.',
                    'You may have been freed by the captain in a clue game.',
                    'You may have been disconnected by the server owner.',
                    'The server may be broken.',
                    '',
                    'Technical data: read(2) returned zero on',
                    # FIXME: ECONNRESET is not properly reported here.
                    nt.diagnostics()]

        x = []
        s = ['Protocol version in CP_SOCKET is not supported by server.',
             'Access denied by server.',
             'No free slots on server queue.',
             'Banned from server.',
             'Game shutdown by server.',
             'Server daemon stalled, internal error.',
             'Server reports internal error.']

        # FIXME: how to contact a server owner, noted by Gerdesas, design as
        # either a new feature packet with sysdef text setting, or
        # default to first user@host in .motd if an old server.

        l = [['You have either connected to a server that does not support',
              'this client, or the server itself is insane.',
              '',
              'Try a different server,',
              'or report this to the server owner,',
              'or report this to the client developer.'],

             ['The server has your IP address, or a range of addresses, in a',
              'configuration file, due to a prior denial of service attack.',
              '',
              'Try a different server,',
              'or try a different service provider,',
              'or ask the server owner about it.'],

             ['The server was not able to place you in the queue, perhaps',
              'due to a denial of service attack happening right now.',
              '',
              'Or if you were in a clue game, the captain has freed your slot',
              'so that another player can join.',
              '',
              'Or in a pickup game the players ejected you.',
              '',
              'Try a different server,',
              'or rejoin as an observer of the clue game.'],

             ['The server has your IP address in the list of bans,',
              'usually because you were banned by the players or the owner.',
              '',
              'Try a different server,',
              'and if you were misbehaving try not to in future.'],

             ['The server was shutdown by the owner,',
              'probably only temporarily.',
              '',
              'Try a different server,',
              'or try this server later,',
              'or ask the server owner about it.']]

        try:
            x.append(s[sp_badversion.why])
        except:
            x.append('Unknown cause.')
        x.append('')
        try:
            for y in l[sp_badversion.why]:
                x.append(y)
        except:
            x.append('Try again later.')
        x.append('')
        x.append('Technical data: '
                 'received SP_BADVERSION packet, '
                 'reason code %d' % sp_badversion.why)
        return x

    def list(self, event):
        self.run = False


def mc_choose():
    ph_servers = PhaseServers(screen, mc)
    while ph_servers.cancelled:
        del ph_servers
        ph_tips = PhaseTips(screen)
        mc.query(opt.metaserver)
        ph_servers = PhaseServers(screen, mc)

def mc_choose_first():
    """ show splash screen, then server list, accept a choice, connect """
    ph_splash = PhaseSplash(screen)
    mc_choose()

def mc_choose_again():
    """ requery metaserver, show server list, accept a choice, connect """
    mc.query(opt.metaserver)
    mc_choose()

def nt_play_a_slot():
    """ keep playing on a server, until user chooses a quit option, or
    a list option to return to the server list """
    global ph_flight, ph_galactic, ph_tactical

    ph_outfit = PhaseOutfit(screen)
    ph_galactic = PhaseFlightGalactic()
    ph_tactical = PhaseFlightTactical()

    while True:
        # choose a team and ship
        ph_outfit.do()
        if ph_outfit.cancelled: break # quit or list chosen during outfit
        # at this point, team and ship choice is accepted by server

        # Wait for SP_PSTATUS to move status out of POUTFIT.
        # The network thread updates me.status in the background.
        # Pump events so the window stays responsive during initial state dump.
        while me.status == POUTFIT:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    nt.send(cp_bye.data())
                    ac_save()
                    sys.exit(0)
                elif event.type == pygame.VIDEOEXPOSE:
                    pygame.display.flip()
            time.sleep(0.01)

        ph_flight = ph_tactical
        if not ph_tactical.hint():
            if me.flags & PFGREEN:
                ph_tactical.tips()
        while True:
            # clear screen before starting a display mode
            screen.blit(background, (0, 0))
            # FIXME: might place display mode independent static
            # content on screen here, or not clear the whole screen
            pygame.display.flip()
            ph_flight.do()
            if me.status == POUTFIT: break # ship has died

        try:
            ac_save()
        except:
            print('achievements were not saved due to an exception')

def nt_play():
    """ keep playing, until user chooses a quit option """
    if opt.server == None: mc_choose_first()
    while True:
        # at this point, a new connection to a server has just been established
        try:
            nt.send(cp_socket.data())
            nt.send(cp_feature.data('S', 0, 0, 1, 'FEATURE_PACKETS'))
            # FIXME: allow play on another server while queued
            ph_queue = PhaseQueue(screen)
            if ph_queue.cancelled:
                if mc == None: break
                # return to metaserver list
                mc_choose_again()
                continue

            if opt.name == '':
                ph_login = PhaseLogin(screen)
                if ph_login.cancelled:
                    if mc == None: break
                    # return to metaserver list
                    mc_choose_again()
                    continue

            nt_play_a_slot()

        except ServerDisconnectedError:
            PhaseDisconnected(screen)

        if mc == None: break

        # return to metaserver list
        mc_choose_again()
