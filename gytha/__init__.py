#!/usr/bin/python

"""
    netrek client pygame, aka gytha
    Copyright (C) 2007-2026  James Cameron (quozl@us.netrek.org)

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

http://www.cs.cmu.edu/afs/cs.cmu.edu/user/jch/netrek/humor

From: markiel@callisto.pas.rochester.edu (Andrew Markiel)
Newsgroups: rec.games.netrek
Subject: Re: Beginer!
Date: Thu, 4 Nov 93 00:33:05 GMT

STHOMAS@utcvm.utc.edu wrote:
>      I read many of the netrek postings and it seems real intresting.  Would
> anyone be willing to post instructions on how to get onto Netrek and begin
> playinf.  Particularly comand cods to get in.

Certainly! Most of them you can fish out of the code (it's written in sea),
but I can give you some pointers.

The idea behind netrek is that your race starts with 10 oysters, which
produce pearls (certain "agricultural" oysters produce pearls much faster
and thus are very valuable). The object of the game is to capture all of
the enemy's oysters by destroying all of their pearls and capturing them
with your own pearls. Each team has 8 fish attacking and defending the
oysters.

One of the most important ideas is to destroy enemy pearls (once you
destroy all the pearls on an enemy oyster, it becomes uncontrolled and
you can capture it by delivering one of your own pearls). You do this
by perching on the oyster and hitting 'b' (for bash), which causes
you to destroy the enemy pearls there.

If the oyster has more than 4 pearls, then it will be open and you
can attack all of them; however, once the oyster has less than 5, it
will close up with the pearls inside and you can't bash them anymore
(however, if you get lucky, you can bash several pearls in one swing
and thus reduce the number of pearls to below 4 before it closes up..
lobsters are very good at this).

Once the oyster is closed up, the only way to destroy the rest of the
pearls inside is to deliver your own pearls to the oyster. When you
put one of your own pearls next to the oyster, it will open up slightly
to crush it, which allows you to grab one of the ones inside and destroy
it before it closes again. Thus, for an oyster with 4 pearls, you need
to deliver 4 of your own pearls to be able to destroy all of the ones
inside, which makes the oyster uncontrolled. Then, if you put another
one of your own pearls inside, you will capture the oyster and it will
start making pearls for you.

The tricky bit is that to carry pearls around, you have to have a net
to carry them in. You make the net out of the scales of the enemy fish
that you defeat. Defeating one enemy fish gives you enough scales to
carry 2 pearls (unless you are in a lobster, in which case you have
enough to carry three pearls). They maximum number of pearls you can
carry depends on fish type. When your fish is defeated in combat,
you lose all your scales and any pearls you are carrying, and get sent
back to your spawning grounds to get a new fish. 

You fight either by tossing pebbles at the enemy fish, or by using
your scraper to scrape the scales off of them; note that after a
lot of fighting you get tired, and can't attack until you get more food
(indicated by your food stat, note that many other things, including
movement, consume food). You can get a little food anywhere, but certain
oysters provide food, which means that if you perch on a freindly food
oyster you will replace your food reserves much faster.

There are six types of fish you can control: salmon, dogfish, crabs,
bluefin, lobsters, and the mighty bass. You can always switch to
another fish by going back to your spawning ground and requesting
a new fish (and you keep whatever scales you had).

Salmon are small and fast. The have fast pebbles but very weak
scrapers, and they are too weak for most combat. They are best used
either for carrying pearls, or for bashing enemy pearls in their
backfield (every good team needs a salmon basher).

Dogfish are a little tougher than salmon, and also conserve food well.
However, they also have weak scrapers and thus aren't so useful in combat.
In fact, these fish tend to be seldom seen anymore.

Crabs are the workfish. They have lots of food and really good
scrapers, which makes them good for fighting enemy fish. Nowadays
these fish are used more than any other.

Bluefin are very big fish, but are slow and don't use food effectively,
so they tend to be useful only in close range fights near a food oyster.

Lobsters are an intersting sort of fish. They are very slow, but are
very good at bashing enemy pearls (if they get lucky, they can bash
4 pearls in one swing). They also can carry three pearls for each
enemy fish destroyed, which can be quite useful.

The bass is a very special fish. You side only can have one at a time,
and if it gets defeated it takes 30 minutes to put it back together
again. You also have a certain rank to take one. However, they are
very big and tough, and serve as a repository for pearls (where they
can't be bashed).

An interesting tactic is the bass og (it's short for ogtopus). This
is where your 8 fish surround the enemy bass (like the 8 arms of an
ogtopus). Then you wade in and beat the carp out of him. You can do
it with less fish, but it's not as effective.


Hope this helps. If you have more questions, the FAQ should be posted
in a few days.

> Stephen Thomas  University of Tennesee at Chattanooga

-Grey Elf
markiel@callisto.pas.rochester.edu

"""
import os, sys, time, socket, errno, select, struct, pygame, math, glob

from pygame.locals import *

# Custom pygame event types. pygame.event.custom_type() allocates from
# USEREVENT+1 upward, so all three must be claimed here to avoid collision.
# pygame.event.custom_type() is Pygame 2.0.1+; fall back for older builds.
try:
    UE_TIMER = pygame.event.custom_type()          # phase update timer
    UE_BOUNCER = pygame.event.custom_type()        # warn-fuse / bouncer timer
    NETWORK_DATA_READY = pygame.event.custom_type()# network thread wakeup
except AttributeError:
    UE_TIMER = pygame.USEREVENT + 1
    UE_BOUNCER = pygame.USEREVENT + 2
    NETWORK_DATA_READY = pygame.USEREVENT + 10

# a global namespace until complexity grows too far
from .cache import ic, fc
from .constants import *
from .sprites import MultipleImageSprite
from .sprites import Icon, Text, Texts
from .sprites import IconButton, IconTextButton, HorizontalAssemblyButton, Field
from .bouncer import Bouncer
from .util import *
from .meta import MetaClient
from .client import Client, ServerDisconnectedError
from .motd import MOTD
from .cap import Cap
from . import coords
from . import mercenary
from . import options
from . import rcd
from . import sound
from .coords import n2ss, n2gs, n2ts, gs2n, ts2n, s2g, cursor, intragalactic, d2a, s2d, n_o, o_d, n_d
from . import models
from .models import (Local, Planet, Ship, Torp, Plasma, Phaser, Tractor,
                     Tag, NegativeEnergyBarrier, Galaxy, NUMDETFRAMES)
from . import game_sprites
from .game_sprites import (PlanetSprite, PlanetGalacticSprite, PlanetTacticalSprite,
                           ShipSprite, ShipGalacticSprite, ShipTacticalSprite,
                           TorpSprite, TorpTacticalSprite,
                           PlasmaSprite, PlasmaTacticalSprite)
from . import overlays
from .overlays import (Halos, Lines, Borders, LocatorSprite, Alerts,
                       TacticalAlerts, GalacticAlerts, Subgalactic,
                       DebugSprite, ReportSprite, WarningSprite,
                       MessageLine, InfoSprite, MessageSprite)
overlays.UE_BOUNCER = UE_BOUNCER

from . import packets
from .packets import (
    cp_table, sp_table, sp,
    cp_socket, cp_bye, cp_login, cp_outfit, cp_speed, cp_direction,
    cp_planlock, cp_playlock, cp_updates, cp_bomb, cp_beam, cp_cloak,
    cp_repair, cp_shield, cp_message, cp_phaser, cp_plasma, cp_torp,
    cp_quit, cp_war, cp_practr, cp_orbit, cp_det_torps, cp_det_mytorp,
    cp_copilot, cp_refit, cp_tractor, cp_repress, cp_coup, cp_options,
    cp_dockperm, cp_resetstats, cp_reserved, cp_scan, cp_udp_req,
    cp_feature, cp_ping_response,
    sp_warning, sp_login, sp_mask, sp_pickok, sp_badversion,
)

def _sync_me(new_me):
    global me
    me = new_me
    phases.me = new_me
    achievements.me = new_me
packets._me_update_hooks.append(_sync_me)

VERSION = "0.9"
packets.VERSION = VERSION

WELCOME = [
"Gytha %s" % (VERSION),
"Copyright (C) 2007-2020 James Cameron <quozl@us.netrek.org>",
"",
"This program comes with ABSOLUTELY NO WARRANTY; for details see source.",
"This is free software, and you are welcome to redistribute it under certain",
"conditions; see source for details."
]

INSTRUCTIONS_SERVERS = [
'Welcome to Netrek, a multi-player real-time 2D strategy game.',
'',
'Pick a server to begin playing.',
'',
'Each Netrek galaxy is shared to players through a server.  These servers are',
'listed here, from the Netrek metaserver.  Number of players is shown to the',
'right.  Click on a server with your middle mouse button to join as an',
'anonymous mercenary, or with your left button to login.'
]

# number of rounds played this session
rounds = 0

from . import phases
phases.UE_TIMER = UE_TIMER
phases.NETWORK_DATA_READY = NETWORK_DATA_READY
phases.WELCOME = WELCOME
phases.INSTRUCTIONS_SERVERS = INSTRUCTIONS_SERVERS
phases.rounds = rounds

# rectangle of entire window
# changed when screen capabilities are determined
r_main = Rect((0, 0), (1100, 1100))

# rectangle of tactical and galactic area inside entire window
r_us = Rect((50, 50), (1000, 1000))

#
# there are several different coordinate types:
#
# 1.  netrek coordinates: represent a position of a game object, are
# used by the netrek protocol, and are a cartesian pair normally
# ranging from (0, 0) to (GWIDTH, GWIDTH)
#
# 2.  netrek direction: represent a vector from your own ship out into
# surrounding space, are used by the netrek protocol, and are a value
# of range 0 to 255, representing a full circle,
#
# 3.  tactical screen coordinates: represent a position on screen
# relative to the main window, matching a netrek coordinate relative
# to your own ship, are local to the client, are not used in the
# netrek protocol, and range from (0, 0) to the main window, r_main,
#
# 4.  galactic screen coordinates: represent a position on screen
# relative to the main window, matching a netrek coordinate which is
# absolute, are local to the client, are not used in the netrek
# protocol, and have the same range as above.
#
# the following functions are for conversions between these coordinate
# types.
#



galaxy = Galaxy()
models.galaxy = galaxy
overlays.galaxy = galaxy
packets.galaxy = galaxy
phases.galaxy = galaxy
me = None

# Wire sprite factory class attributes on model classes now that sprites are defined.
models.Planet._TacticalSprite = PlanetTacticalSprite
models.Planet._GalacticSprite = PlanetGalacticSprite
models.Ship._TacticalSprite = ShipTacticalSprite
models.Ship._GalacticSprite = ShipGalacticSprite
models.Torp._TacticalSprite = TorpTacticalSprite
models.Plasma._TacticalSprite = PlasmaTacticalSprite

def mc_init():
    """ metaserver client socket initialisation """
    mc = MetaClient()
    # query metaserver early,
    # to make good use of pygame startup and splash delay
    mc.query(opt.metaserver)
    return mc

def nt_init():
    """ netrek client socket initialisation """
    nt = Client(sp)
    if opt.tcp_only:
        nt.mode_requested = COMM_TCP
    nt.cp_udp_req = cp_udp_req
    return nt

def nt_start_thread():
    """Start the background network I/O thread for the game server connection.
    Posts NETWORK_DATA_READY pygame events when packets arrive so the main
    thread wakes from pygame.event.wait() without any X11 fd dependency."""
    nt.start_network_thread(NETWORK_DATA_READY)

def nt_shutdown():
    """Shut down the game server connection and drain any NETWORK_DATA_READY
    events the network thread posted before it stopped, so they do not trigger
    ServerDisconnectedError in the next phase."""
    nt.shutdown()
    pygame.event.clear(NETWORK_DATA_READY)

from . import achievements
from .achievements import ac_load, ac_save, ac_done, ac_done_later, ac_deliver, ac_progress
achievements.sound = sound
models.ac_done = ac_done
overlays.ac_done = ac_done


def pg_init():
    """ pygame initialisation """
    global t_planets, t_players, t_torps, t_plasma, g_planets, g_players, g_locator, b_warning_sprite, b_warning, b_reports, b_message, b_info, background, galactic_factor, subgalactic_factor, r_main, r_us, r_sg

    pygame.mixer.pre_init(44100, -16, 2, 1024)

    pygame.display.init()
    pygame.init()
    pygame.key.set_repeat(250, 100)
    size = width, height = 1000, 1000
    sound.prepare(opt.sounds)
    ac_load()
    ac_save()

    videoinfo = pygame.display.Info()
    print("current display resolution is %d x %d pixels" % (videoinfo.current_w, videoinfo.current_h))

    screen = None
    undersize = (videoinfo.current_w < 1000 or videoinfo.current_h < 1000)

    if opt.manual_width != None or opt.manual_height != None:
        print("you gave manual override for display size")
        manual_width = videoinfo.current_w
        if opt.manual_width != None:
            manual_width = opt.manual_width
        manual_height = videoinfo.current_h
        if opt.manual_height != None:
            manual_height = opt.manual_height
        if opt.fullscreen:
            screen = pygame.display.set_mode((manual_width, manual_height),
                                             FULLSCREEN)
        else:
            screen = pygame.display.set_mode((manual_width, manual_height))
        undersize = False

    if not screen and undersize:
        print("trying best resolution for game")
        try:
            screen = pygame.display.set_mode((1000, 1000), FULLSCREEN)
            undersize = False
        except:
            print("could not switch display resolution")

    if not screen and undersize:
        print("trying a standard resolution above best for game")
        try:
            screen = pygame.display.set_mode((1280, 1024), FULLSCREEN)
            undersize = False
        except:
            print("could not switch display resolution")

    if not screen and undersize:
        print("trying a standard resolution below best for game")
        try:
            screen = pygame.display.set_mode((1024, 768), FULLSCREEN)
        except:
            print("could not switch display resolution")

    if not screen and opt.fullscreen:
        if videoinfo.current_w != -1 and videoinfo.current_h != -1:
            print("trying current resolution in full screen mode")
            screen = pygame.display.set_mode((videoinfo.current_w,
                                              videoinfo.current_h), FULLSCREEN)

    if not screen:
        screen = pygame.display.set_mode()

    surface = pygame.display.get_surface()
    width = surface.get_width()
    height = surface.get_height()
    size = width, height
    print("have a surface size %d x %d pixels" % (width, height))
    r_main = Rect((0, 0), (width, height))
    r_us = r_main
    if width > 1000 and height > 1000:
        left = (width - 1000) / 2
        top = (height - 1000) / 2
        r_us = Rect((left, top), (1000, 1000))

    short = min(r_us.width, r_us.height)
    galactic_factor = GWIDTH / short

    gap = 50
    dia = 200
    r_sg = Rect((r_us.left+gap, r_us.bottom-gap-dia), (dia, dia))
    subgalactic_factor = GWIDTH / dia

    coords.r_us = r_us
    coords.r_sg = r_sg
    coords.galactic_factor = galactic_factor
    coords.subgalactic_factor = subgalactic_factor

    overlays.r_us = r_us
    overlays.r_sg = r_sg
    overlays.r_main = r_main
    overlays.screen = screen
    overlays.sp_warning = sp_warning
    overlays.cp_message = cp_message

    t_planets = pygame.sprite.OrderedUpdates(())
    t_players = pygame.sprite.OrderedUpdates(())
    t_torps = pygame.sprite.OrderedUpdates(())
    t_plasma = pygame.sprite.OrderedUpdates(())
    g_locator = pygame.sprite.OrderedUpdates(())
    g_locator.add(LocatorSprite())
    g_planets = pygame.sprite.OrderedUpdates(())
    g_players = pygame.sprite.OrderedUpdates(())
    b_warning = pygame.sprite.OrderedUpdates()
    b_warning_sprite = WarningSprite()
    b_warning.add(b_warning_sprite)
    b_reports = pygame.sprite.OrderedUpdates()
    b_reports.add(ReportSprite())
    if opt.debug:
        b_reports.add(DebugSprite())
    b_message = pygame.sprite.OrderedUpdates()
    b_message.add(MessageSprite())
    b_info = pygame.sprite.OrderedUpdates()

    models.screen = screen
    models.b_info = b_info
    overlays.b_info = b_info
    game_sprites.t_planets = t_planets
    game_sprites.t_players = t_players
    game_sprites.t_torps = t_torps
    game_sprites.t_plasma = t_plasma
    game_sprites.g_planets = g_planets
    game_sprites.g_players = g_players

    phases.screen = screen
    phases.r_main = r_main
    phases.r_us = r_us
    phases.b_info = b_info
    achievements.b_info = b_info
    phases.b_warning = b_warning
    phases.b_warning_sprite = b_warning_sprite
    phases.b_reports = b_reports
    phases.b_message = b_message
    phases.g_planets = g_planets
    phases.g_players = g_players
    phases.g_locator = g_locator
    phases.t_planets = t_planets
    phases.t_players = t_players
    phases.t_torps = t_torps
    phases.t_plasma = t_plasma

    background = screen.copy()
    background.fill((0, 0, 0))
    screen.blit(background, (0, 0))
    phases.background = background
    pygame.display.flip()
    return screen

def pg_quit():
    """ pygame termination """
    pygame.display.quit()
    pygame.quit()
    ac_save()

phases.pg_quit = pg_quit
phases.nt_start_thread = nt_start_thread
phases.nt_shutdown = nt_shutdown
phases.ac_save = ac_save
phases.ac_done = ac_done
phases.ac_done_later = ac_done_later
phases.ac_deliver = ac_deliver
phases.ac_progress = ac_progress

def main(argv=sys.argv[1:]):
    global opt, screen, mc, nt

    for line in WELCOME: print(line)
    print()

    opt = options.parser.parse_args(argv)
    models.opt = opt
    game_sprites.opt = opt
    overlays.opt = opt
    packets.opt = opt
    phases.opt = opt
    achievements.opt = opt
    if opt.ubertweak:
        import getpass
        opt.name = opt.password = opt.login = getpass.getuser()

    mc = None
    if opt.server == None: mc = mc_init()
    nt = nt_init()
    overlays.nt = nt
    packets.nt = nt
    phases.nt = nt
    phases.mc = mc
    if opt.server is not None:
        opt.chosen = opt.server
        if not nt.connect(opt.chosen, opt.port):
            print("connection failed")
            # server was requested on command line, but not available
            return 1
    screen = pg_init()
    if opt.server is not None:
        nt_start_thread()

    phases.nt_play()
    if opt.debug:
        ic.statistics()
    pg_quit()
    return 0

# FIXME: planets to be partial alpha in tactical view as ships close in?

# FIXME: add graphic indicator of connection status
# FIXME: discover servers from a cache

# FIXME: when other slot frees, free all torps

# FIXME: add a help aka documentation button on metaserver list, also
# accessible from other modes but will force a disconnection from
# server, to contain tutorial, ship classes, and rank information.

# FIXME: mouse-over hint for word "clue", explain terms (says Petria)

# FIXME: new version notification

# FIXME: explanation of how to get an account on a netrek server

# FIXME: configuration settings, store in a YAML

# FIXME: dual display

# FIXME: keymap feature, allow use of function keys for actions.

# FIXME: dashboard should show percentages or proportions, per petria
